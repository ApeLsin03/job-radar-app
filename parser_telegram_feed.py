import requests
import os
import sys
import re
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}

# Популярные каналы со стажировками и вакансиями для начинающих
CHANNELS = [
    'forjunior',          # IT Вакансии для Джуниоров и Стажеров
    'young_june',         # Стажировки и Junior IT
    'it_internships_ru'   # Оплачиваемые стажировки
]

def parse_telegram_channel(channel: str) -> List[Dict]:
    """Парсит публичную веб-ленту Telegram-канала."""
    url = f"https://t.me/s/{channel}"
    vacancies = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'lxml')
        messages = soup.find_all('div', class_='tgme_widget_message')
        
        for msg in messages:
            text_tag = msg.find('div', class_='tgme_widget_message_text')
            if not text_tag:
                continue
                
            text = text_tag.get_text('\n', strip=True)
            t_lower = text.lower()
            
            # Проверяем, связано ли сообщение с удаленной работой/стажировкой
            if not any(w in t_lower for w in ['стажер', 'стажировк', 'junior', 'верстк', 'html', 'python', 'удален']):
                continue
                
            # Исключаем сеньорские посты
            if any(w in t_lower for w in ['senior', 'team lead', 'lead engineer']):
                continue
                
            # Ссылка на пост
            date_link = msg.find('a', class_='tgme_widget_message_date')
            post_url = date_link.get('href', '') if date_link else f"https://t.me/{channel}"
            
            id_match = re.search(r'/([^/]+)/(\d+)$', post_url)
            vac_id = f"tg_{id_match.group(1)}_{id_match.group(2)}" if id_match else f"tg_{hash(post_url)}"
            
            # Заголовок (первая строка сообщения)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            title = lines[0] if lines else "Стажировка / Вакансия без опыта"
            if len(title) > 80:
                title = title[:77] + "..."
                
            # Поиск зарплаты в тексте
            sal_match = re.search(r'(от\s*\d+[\d\s]*\s*(?:руб|₽|k|\$)|до\s*\d+[\d\s]*\s*(?:руб|₽|k|\$)|\d+[\d\s]*\s*[-—]\s*\d+[\d\s]*\s*(?:руб|₽|k|\$))', text, re.IGNORECASE)
            salary = sal_match.group(1).strip() if sal_match else "Оплачиваемая стажировка / По договоренности"
            
            vacancies.append({
                'id': vac_id,
                'title': title,
                'company': f"Telegram @{channel}",
                'salary': salary,
                'url': post_url,
                'requirements': text[:280] + ("..." if len(text) > 280 else ""),
                'responsibilities': "Создание сайтов, лендинги, верстка, скрипты, обучение на практике",
                'experience': "Без опыта / Оплачиваемая стажировка",
                'source': f"Telegram (@{channel})",
                'published_at': datetime.now().isoformat()
            })
    except Exception as e:
        print(f"Ошибка парсинга Telegram-канала @{channel}: {e}")
        
    return vacancies

def get_all_telegram_vacancies() -> List[Dict]:
    """Сканирует все подключенные каналы стажировок."""
    all_found = {}
    for ch in CHANNELS:
        for v in parse_telegram_channel(ch):
            all_found[v['id']] = v
            
    return list(all_found.values())

if __name__ == '__main__':
    print("Тестирую парсер Telegram-каналов со стажировками...")
    res = get_all_telegram_vacancies()
    print(f"Найдено стажировок в Telegram: {len(res)}")
    for i, v in enumerate(res[:3], 1):
        print(f"#{i} [{v['source']}] {v['title']} | {v['salary']} | {v['url']}")
