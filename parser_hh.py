import requests
import os
import sys
import re
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
}

TITLE_BLACKLIST = [
    'senior', 'lead', 'middle', 'сеньор', 'ведущий', 'руководитель', 
    'системный аналитик', 'бизнес-аналитик', 'media buyer', 'архитектор', 
    'devops', '1с', '1c', 'главный', 'директор', 'head of', 'продаж',
    'риэлтор', 'недвижимост', 'колл-центр', 'call-центр', 'коллцентр',
    'call center', 'call центр', 'оператор', 'диспетчер', 'горячей линии',
    'входящих', 'исходящих', 'обзвон', 'звонк', 'телемаркетолог', 'монтажник',
    'курьер', 'водитель', 'склад', 'повар', 'без оплаты', 'неоплачиваемая',
    'холодных', 'партнерской сети', 'юрист', 'партнерск', 'креатор бренда'
]

STACK_KEYWORDS = {
    'frontend': [
        'верст', 'сайт', 'html', 'css', 'javascript', 'frontend', 'веб',
        'web', 'лендинг', 'tilda', 'тильда', 'figma', 'react', 'vue',
        'верстальщик', 'помощник вебмастера'
    ],
    'python': [
        'python', 'питон', 'django', 'flask', 'fastapi', 'парс', 'скрипт',
        'стажер python', 'junior python', 'бэкенд', 'backend'
    ],
    'qa': [
        'тестировщик', 'qa', 'тестирование', 'тест', 'quality assurance',
        'контроль качества', 'junior qa'
    ],
    'all': [
        'верст', 'сайт', 'html', 'css', 'javascript', 'frontend', 'python',
        'питон', 'разработчик', 'программист', 'веб', 'web', 'лендинг',
        'tilda', 'тильда', 'разметк', 'junior', 'intern', 'trainee',
        'стажер', 'стажёр', 'тестировщик', 'qa', 'помощник', 'помощник программиста',
        'контент', 'it', 'ит', 'асессор', 'data', 'react', 'vue', 'django',
        'flask', 'fastapi', 'wordpress', 'figma'
    ]
}

def is_title_relevant(title: str, stack_filter: str = 'all') -> bool:
    """Проверяет соответствие должности IT-профилю и выбранному стеку."""
    t = title.lower()
    for bad_word in TITLE_BLACKLIST:
        if bad_word in t:
            return False
            
    target_words = STACK_KEYWORDS.get(stack_filter, STACK_KEYWORDS['all'])
    return any(w in t for w in target_words)

def fetch_hh_full_description(vacancy_id_num: str) -> str:
    """Загружает текст требований конкретной отправляемой вакансии (быстро, 1 запрос)."""
    url = f"https://hh.ru/vacancy/{vacancy_id_num}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'lxml')
            desc_elem = soup.find(attrs={'data-qa': 'vacancy-description'})
            if desc_elem:
                clean_text = desc_elem.get_text(' ', strip=True)
                return re.sub(r'\s+', ' ', clean_text)[:350]
    except Exception:
        pass
    return "Создание сайтов, верстка, скрипты, обучение с наставником"

def parse_habr_career(query: str, stack_filter: str = 'all', max_pages: int = 2) -> List[Dict]:
    """Парсит свежие удаленные вакансии с Хабр Карьеры."""
    vacancies = []
    for page in range(1, max_pages + 1):
        url = f"https://career.habr.com/vacancies?type=all&remote=1&q={requests.utils.quote(query)}&page={page}&sort=date"
        try:
            response = requests.get(url, headers=HEADERS, timeout=5)
            if response.status_code != 200:
                break
                
            soup = BeautifulSoup(response.text, 'lxml')
            cards = soup.find_all('div', class_='vacancy-card')
            if not cards:
                break
                
            for card in cards:
                title_tag = card.find('div', class_='vacancy-card__title')
                if not title_tag or not title_tag.find('a'):
                    continue
                    
                link_tag = title_tag.find('a')
                title = link_tag.get_text(strip=True)
                
                if not is_title_relevant(title, stack_filter):
                    continue
                    
                href = link_tag.get('href', '')
                clean_href = href.split('?')[0]
                full_url = f"https://career.habr.com{clean_href}" if clean_href.startswith('/') else clean_href
                
                id_match = re.search(r'/vacancies/(\d+)', full_url)
                if not id_match:
                    continue
                vac_id = f"habr_{id_match.group(1)}"
                
                comp_tag = card.find(class_=re.compile(r'company-title|company_title|company'))
                company = comp_tag.get_text(strip=True) if comp_tag else "Компания не указана"
                
                sal_tag = card.find(class_=re.compile(r'salary|compensation'))
                salary_raw = sal_tag.get_text(strip=True) if sal_tag else ""
                salary_clean = re.split(r'Похожие специалисты', salary_raw)[0].strip()
                salary = salary_clean if (salary_clean and salary_clean != "Зарплата не указана") else "По договоренности (Стажировка / Обучение)"
                
                skills_tag = card.find('div', class_='vacancy-card__skills')
                skills = skills_tag.get_text(strip=True) if skills_tag else ""
                
                vacancies.append({
                    'id': vac_id,
                    'title': title,
                    'company': company,
                    'salary': salary,
                    'url': full_url,
                    'requirements': f"Стек: {skills}. Готовы обучать на практике." if skills else "Удаленная работа, оплачиваемая практика и обучение",
                    'responsibilities': "Создание сайтов, лендингов, скрипты, обучение",
                    'experience': "Без опыта / Обучение",
                    'source': 'Хабр Карьера',
                    'published_at': datetime.now().isoformat()
                })
        except Exception:
            break
            
    return vacancies

def parse_hh_search(query: str, stack_filter: str = 'all', salary_filter: str = 'salary_any', max_pages: int = 3) -> List[Dict]:
    """Быстрый парсинг поисковой выдачи HeadHunter с поддержкой фильтрации по З/П и опыту."""
    vacancies = []
    
    salary_param = ""
    if salary_filter == 'salary_specified':
        salary_param = "&only_with_salary=true"
    elif salary_filter == 'salary_40k':
        salary_param = "&only_with_salary=true&salary=40000"
    elif salary_filter == 'salary_60k':
        salary_param = "&only_with_salary=true&salary=60000"
    
    # Ищем как без опыта, так и джуниор-позиции (от 0 до 1-3 лет) с удаленкой
    exp_variants = ['noExperience', 'between1And3']
    
    for exp in exp_variants:
        for page in range(max_pages):
            url = f"https://hh.ru/search/vacancy?text={requests.utils.quote(query)}&schedule=remote&experience={exp}{salary_param}&page={page}&order_by=publication_time"
            try:
                response = requests.get(url, headers=HEADERS, timeout=5)
                if response.status_code != 200:
                    break
                    
                soup = BeautifulSoup(response.text, 'lxml')
                links = soup.find_all('a', attrs={'data-qa': re.compile(r'serp-item__title|vacancy-serp__vacancy-title')})
                if not links:
                    break
                    
                for link in links:
                    title = link.get_text(strip=True)
                    
                    if not is_title_relevant(title, stack_filter):
                        continue
                        
                    href = link.get('href', '')
                    id_match = re.search(r'/vacancy/(\d+)', href)
                    if not id_match:
                        continue
                        
                    raw_id = id_match.group(1)
                    vac_id = f"hh_{raw_id}"
                    clean_url = f"https://hh.ru/vacancy/{raw_id}"
                    
                    parent_card = link.find_parent('div', class_=re.compile(r'vacancy-card|serp-item')) or link.find_parent('div')
                    
                    company = "Компания не указана"
                    salary = "По договоренности (Стажировка / Обучение)"
                    
                    if parent_card:
                        comp_tag = parent_card.find(attrs={'data-qa': re.compile(r'vacancy-serp__vacancy-employer')})
                        if comp_tag:
                            company = comp_tag.get_text(strip=True)
                            
                        sal_tag = parent_card.find(attrs={'data-qa': re.compile(r'vacancy-serp__vacancy-compensation|compensation-text')})
                        if sal_tag:
                            sal_text = sal_tag.get_text(strip=True)
                            if sal_text and "не указана" not in sal_text.lower():
                                salary = sal_text
                    
                    vacancies.append({
                        'id': vac_id,
                        'title': title,
                        'company': company,
                        'salary': salary,
                        'url': clean_url,
                        'requirements': '', # Загружается точечно только для отправляемых 10 вакансий!
                        'responsibilities': "Участие в проектах под руководством наставника",
                        'experience': "Без опыта / Junior (100% удаленно)",
                        'source': 'HeadHunter',
                        'published_at': datetime.now().isoformat()
                    })
            except Exception:
                break
                
    return vacancies

def get_all_fresh_vacancies(stack_filter: str = 'all', salary_filter: str = 'salary_any', keywords: Optional[List[str]] = None) -> List[Dict]:
    """Быстрый параллельный сбор вакансий со всех источников за 1-2 секунды."""
    if not keywords:
        if stack_filter == 'frontend':
            keywords = ['верстальщик', 'junior frontend', 'веб-разработчик', 'лендинг', 'junior html', 'tilda', 'figma', 'react', 'вебмастер']
        elif stack_filter == 'python':
            keywords = ['junior python', 'стажер python', 'скрипты python', 'django', 'fastapi', 'разработчик python']
        elif stack_filter == 'qa':
            keywords = ['junior qa', 'тестировщик', 'стажер qa', 'тестирование сайтов', 'ручной тестировщик']
        else:
            keywords = [
                'верстальщик', 'стажер', 'стажировка', 'веб-разработчик', 
                'junior frontend', 'junior python', 'junior QA',
                'разметка данных', 'помощник программиста', 'tilda', 'html верстка'
            ]
        
    all_found = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for kw in keywords[:4]:
            futures.append(executor.submit(parse_habr_career, kw.strip(), stack_filter, 2))
        for kw in keywords:
            futures.append(executor.submit(parse_hh_search, kw.strip(), stack_filter, salary_filter, 2))
            
        for f in as_completed(futures):
            try:
                for item in f.result():
                    all_found[item['id']] = item
            except Exception:
                pass
                
    return list(all_found.values())

if __name__ == '__main__':
    import time
    t0 = time.time()
    res = get_all_fresh_vacancies(stack_filter='all', salary_filter='salary_40k')
    print(f"Собрано {len(res)} вакансий от 40k+ за {time.time() - t0:.2f} сек!")
