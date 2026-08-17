import os
import sys
import re
import requests
from dotenv import load_dotenv

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

CANDIDATE_NAME = "Алексей Юпатов"
CANDIDATE_TG = "@ApeLsinn03"
CANDIDATE_PHONE = "+7 923 162 9223"
CANDIDATE_EMAIL = "yupatov.alesha@gmail.com"

SIGNATURE = f"""С уважением, Алексей
Telegram: {CANDIDATE_TG} | Тел: {CANDIDATE_PHONE}"""

def extract_key_skills(text: str) -> list:
    """Извлекает ключевые технологии и навыки из описания вакансии."""
    skills = []
    text_lower = text.lower()
    
    mapping = {
        'figma': 'макетами в Figma',
        'html': 'чистым HTML5/CSS3',
        'javascript': 'JavaScript',
        'js': 'JavaScript',
        'python': 'скриптами на Python',
        'tilda': 'платформой Tilda',
        'лендинг': 'созданием конверсионных лендингов',
        'адаптив': 'адаптивной версткой под мобильные устройства',
        'api': 'интеграцией с API',
        'wordpress': 'CMS WordPress',
        'разметк': 'аккуратной разметкой данных',
        'контент': 'наполнением и ведением контента',
        'тест': 'тестированием и вниманием к деталям',
        'wildberries': 'аналитикой и карточками Wildberries',
        'seo': 'SEO-оптимизацией и структурой'
    }
    
    for key, val in mapping.items():
        if key in text_lower and val not in skills:
            skills.append(val)
            
    return skills

def generate_cover_letter_with_ai(vacancy: dict, api_key: str) -> str:
    """Генерирует высококонверсионное сопроводительное письмо через Google Gemini Interactions API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/interactions?key={api_key}"
    
    title = vacancy.get('title', 'стажер / начинающий специалист')
    company = vacancy.get('company', 'вашей компании')
    req = vacancy.get('requirements', '')
    
    prompt = f"""
Ты — профессиональный IT-карьерный консультант. Напиши сильное, убедительное и персонализированное сопроводительное письмо на русском языке для отклика на вакансию «{title}» в компании «{company}».

Требования работодателя: {req}
Кандидат: {CANDIDATE_NAME} (21 год). 
Навыки: создание сайтов и лендингов (HTML/CSS/JS), скрипты и парсеры на Python, работа с макетами Figma, опыт в SEO/аналитике данных (Wildberries), высокая концентрация и быстрая обучаемость.

ПРАВИЛА И СТРУКТУРА ПИСЬМА:
1. НИКАКИХ заезженных фраз ("Я внимательно ознакомился", "Прошу рассмотреть мое резюме", "Имею честь").
2. 1-й абзац (Крючок): Сразу назови вакансию и объясни, почему ты готов закрывать именно эти задачи (верстка сайтов, лендинги, скрипты на Python, работа с контентом/данными).
3. 2-й абзац (Польза для компании): Покажи, что умеешь аккуратно работать по ТЗ, писать чистый код, внимателен к деталям и готов разгрузить команду от рутины под руководством наставника.
4. 3-й абзац (Призыв к действию): Предложи выполнить практическое тестовое задание и созвониться на 10-15 минут.
5. Заверши письмо подписью:
{SIGNATURE}
6. Объем: ровно 3 коротких абзаца + подпись. Тон: уверенный, профессиональный, без лишней воды.
"""

    for model_name in ['gemini-3.7-flash', 'gemini-3.5-flash', 'gemini-2.5-pro']:
        payload = {
            "model": model_name,
            "input": prompt
        }
        try:
            response = requests.post(url, json=payload, timeout=12)
            if response.status_code == 200:
                data = response.json()
                outputs = data.get('outputs', [])
                if outputs:
                    last_out = outputs[-1]
                    text = last_out.get('text') or last_out.get('content') or ''
                    if text and len(text.strip()) > 50:
                        return text.strip()
        except Exception:
            continue
            
    return generate_dynamic_fallback_letter(vacancy)

def generate_dynamic_fallback_letter(vacancy: dict) -> str:
    """Генерирует специализированное письмо на основе типа вакансии и ключевых навыков."""
    title = vacancy.get('title', 'начинающий специалист')
    company = vacancy.get('company', 'вашей компании')
    req = vacancy.get('requirements', '')
    
    t_lower = (title + " " + req).lower()
    skills = extract_key_skills(req)
    skills_str = ", ".join(skills[:3]) if skills else "HTML/CSS, созданием лендингов и скриптами на Python"
    
    # Вариант 1: Верстка / Веб-разработка / Лендинги
    if any(w in t_lower for w in ['верст', 'html', 'css', 'веб', 'лендинг', 'frontend', 'сайт']):
        return f"""Здравствуйте!

Меня очень заинтересовала вакансия «{title}» в {company}. Мой основной практический фокус — качественная верстка сайтов и посадочных страниц. Умею работать с {skills_str}, переношу макеты из Figma пиксель в пиксель, уделяю внимание адаптивности под смартфоны и аккуратности кода.

Быстро учусь, умею читать техническую документацию и готов взять на себя задачи по верстке и поддержке страниц, чтобы с первых дней разгрузить команду.

Готов оперативно выполнить тестовое задание, чтобы подтвердить качество своего кода на деле. Буду рад пообщаться на коротком интервью!

{SIGNATURE}"""

    # Вариант 2: Стажировка на Python / Backend / Скрипты
    elif any(w in t_lower for w in ['python', 'питон', 'бэкенд', 'backend', 'скрипт', 'парс']):
        return f"""Здравствуйте!

Увидел вашу позицию «{title}» в {company} и хочу предложить свою кандидатуру. Пишу скрипты на Python, занимаюсь автоматизацией задач, парсингом и работой с API. Базово понимаю принципы клиент-серверного взаимодействия и создания веб-страниц.

Ищу компанию, где смогу под руководством опытных коллег приносить пользу проекту и быстро расти по навыкам. К задачам подхожу ответственно, умею искать решения и быстро разбираться в новом коде.

С удовольствием сделаю тестовое задание. Буду рад обсудить возможность стажировки на онлайн-созвоне!

{SIGNATURE}"""

    # Вариант 3: Контент-менеджер / Разметка данных / IT-поддержка
    elif any(w in t_lower for w in ['контент', 'разметк', 'поддержк', 'саппорт', 'оператор']):
        return f"""Здравствуйте!

Меня заинтересовала вакансия «{title}» в {company}. Я технически грамотен, имею практический опыт работы с контентом, SEO-оптимизацией, карточками товаров и веб-технологиями (HTML/CSS, базовые скрипты на Python). Умею работать с большими объемами информации с высокой концентрацией и вниманием к деталям.

Умею следовать регламентам, быстро осваиваю внутренние инструменты компании и готов оперативно включиться в работу на полную ставку удаленно.

Готов пройти пробное задание или тестирование. Буду рад познакомиться на собеседовании!

{SIGNATURE}"""

    # Вариант 4: Общий веб-стажер с обучением
    else:
        return f"""Здравствуйте!

Пишу по поводу вакансии «{title}» в {company}. Имею крепкую базу в веб-разработке (создание сайтов, HTML5/CSS3, JavaScript) и опыт написания скриптов автоматизации на Python.

Ищу возможность начать карьеру в сильной команде, где ценится трудолюбие, быстрая обучаемость и желание доводить задачи до идеального результата. Готов работать с полной отдачей и перенимать опыт наставников.

С готовностью возьмусь за тестовое задание. Буду рад ответить на вопросы на интервью!

{SIGNATURE}"""

def get_cover_letter(vacancy: dict) -> str:
    """Главная точка входа для получения сопроводительного письма."""
    api_key = os.getenv('GEMINI_API_KEY', '').strip()
    if api_key and not api_key.startswith('ВАШ_'):
        return generate_cover_letter_with_ai(vacancy, api_key)
    else:
        return generate_dynamic_fallback_letter(vacancy)

if __name__ == '__main__':
    mock = {
        'title': 'Junior Верстальщик сайтов на HTML и CSS',
        'company': 'Digital Art Studio',
        'requirements': 'Адаптивная верстка по Figma, знание HTML5, CSS3, внимание к деталям',
        'salary': 'от 45 000 ₽',
        'experience': 'Без опыта'
    }
    print("Пример письма с контактами:\n")
    print(get_cover_letter(mock))
