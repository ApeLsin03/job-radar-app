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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"
}

def parse_avito_vacancies(query: str = "стажер верстальщик удаленно") -> List[Dict]:
    """Парсит удаленные вакансии без опыта с Авито Работа."""
    url = f"https://www.avito.ru/rossiya/vakansii?q={requests.utils.quote(query)}&s=104"
    vacancies = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'lxml')
        items = soup.find_all('div', attrs={'data-marker': 'item'})
        
        for item in items:
            title_tag = item.find('a', attrs={'data-marker': 'item-title'}) or item.find('h3')
            if not title_tag:
                continue
                
            title = title_tag.get_text(strip=True)
            
            # Исключаем нерелевантные ключевые слова
            t_lower = title.lower()
            bad_words = ['senior', 'lead', 'водитель', 'курьер', 'продаж', 'колл-центр', 'коллцентр', 'call center', 'оператор', 'диспетчер', 'обзвон', 'горячей линии', 'партнерск']
            if any(w in t_lower for w in bad_words):
                continue
                
            href = title_tag.get('href', '') if title_tag.name == 'a' else ''
            if not href and title_tag.find_parent('a'):
                href = title_tag.find_parent('a').get('href', '')
                
            clean_href = href.split('?')[0]
            full_url = f"https://www.avito.ru{clean_href}" if clean_href.startswith('/') else clean_href
            
            id_match = re.search(r'_(\d+)$', clean_href)
            vac_id = f"avito_{id_match.group(1)}" if id_match else f"avito_{hash(full_url)}"
            
            # Зарплата
            price_tag = item.find(attrs={'data-marker': 'item-price'}) or item.find('meta', itemprop='price')
            salary = price_tag.get_text(strip=True) if price_tag else "По договоренности"
            if not salary or "договор" in salary.lower():
                salary = "По договоренности (Стажировка / Обучение)"
                
            # Описание / компания
            desc_tag = item.find(attrs={'data-marker': 'item-description'}) or item.find('p')
            desc = desc_tag.get_text(strip=True) if desc_tag else "Создание сайтов, лендингов, верстка, базовые скрипты на Python"
            
            vacancies.append({
                'id': vac_id,
                'title': title,
                'company': "Прямой работодатель (Авито)",
                'salary': salary,
                'url': full_url,
                'requirements': desc[:250],
                'responsibilities': "Создание сайтов, лендингов, скрипты, обучение с наставником",
                'experience': "Без опыта (Обучение на месте)",
                'source': 'Авито Работа',
                'published_at': datetime.now().isoformat()
            })
    except Exception as e:
        print(f"Ошибка парсинга Авито ({query}): {e}")
        
    return vacancies

def get_all_avito_vacancies() -> List[Dict]:
    """Сканирует Авито по целевым запросам для начинающих."""
    queries = [
        "верстальщик удаленно",
        "стажер программист удаленно",
        "веб разработчик без опыта удаленно",
        "помощник вебмастера удаленно"
    ]
    all_found = {}
    for q in queries:
        for v in parse_avito_vacancies(q):
            all_found[v['id']] = v
            
    return list(all_found.values())

if __name__ == '__main__':
    print("Тестирую парсер Авито Работа...")
    res = get_all_avito_vacancies()
    print(f"Найдено вакансий на Авито: {len(res)}")
    for i, v in enumerate(res[:3], 1):
        print(f"#{i} {v['title']} | {v['salary']} | {v['url']}")
