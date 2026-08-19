import http.server
import socketserver
import json
import os
import sys
import threading
import sqlite3
from dotenv import load_dotenv

load_dotenv()

# Порт, предоставляемый облачным хостингом (Koyeb, Render, Railway, etc.)
PORT = int(os.environ.get('PORT', 8000))
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'vacancies_v2.db')

import database
import ai_cover_letter
from market_analytics import get_market_insights

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

import urllib.parse
import requests
from parser_hh import is_title_relevant

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()

def get_swipe_feed(limit=50, stack_filter=None, salary_filter=None):
    if not stack_filter:
        stack_filter = database.get_user_filter()
    if not salary_filter:
        salary_filter = database.get_salary_filter()
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.vacancy_id, v.title, v.company, v.salary, v.url, v.source, v.published_at, v.status, v.created_at
        FROM seen_vacancies v
        WHERE v.company NOT IN (SELECT company_name FROM blacklisted_companies)
          AND v.vacancy_id NOT IN (SELECT vacancy_id FROM skipped_vacancies)
          AND v.vacancy_id NOT IN (SELECT vacancy_id FROM favorites)
        ORDER BY v.id DESC
        LIMIT 200
    """)
    rows = cursor.fetchall()
    conn.close()
    
    feed = []
    for r in rows:
        if len(feed) >= limit:
            break
        sal = r['salary'] or 'З/П не указана'
        title = r['title'] or ''
        
        # 1. Фильтрация по зарплате
        if not database.is_salary_matching(sal, salary_filter):
            continue
            
        # 2. Фильтрация по направлению (если не "все")
        if stack_filter != 'all' and not is_title_relevant(title, stack_filter):
            continue
            
        feed.append({
            'vacancy_id': r['vacancy_id'],
            'title': title,
            'company': r['company'],
            'salary': sal,
            'url': r['url'],
            'source': r['source'] or 'HeadHunter',
            'published_at': r['published_at'] or '',
            'status': r['status'] or 'new'
        })
    return feed

def get_kanban_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.vacancy_id, v.title, v.company, v.salary, v.url, v.source, v.status
        FROM seen_vacancies v
        WHERE v.status IN ('applied', 'test_task', 'interview', 'offer', 'rejected')
        ORDER BY v.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    kanban = {
        'applied': [],
        'test_task': [],
        'interview': [],
        'offer': [],
        'rejected': []
    }
    for r in rows:
        st = r['status']
        if st in kanban:
            kanban[st].append({
                'vacancy_id': r['vacancy_id'],
                'title': r['title'],
                'company': r['company'],
                'salary': r['salary'] or 'З/П не указана',
                'url': r['url'],
                'source': r['source'] or 'HeadHunter'
            })
    return kanban

def generate_custom_letter(vacancy_id: str, tone: str = 'business') -> str:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seen_vacancies WHERE vacancy_id = ?", (vacancy_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        vac_dict = {
            'title': 'Junior Frontend / Python разработчик',
            'company': 'вашей компании',
            'requirements': 'Адаптивная верстка, HTML5/CSS3, JavaScript, скрипты на Python, работа с Figma',
            'url': ''
        }
    else:
        vac_dict = {
            'title': row['title'],
            'company': row['company'],
            'requirements': f"{row['title']} в компании {row['company']}. 100% удаленка, верстка по Figma, скрипты на Python.",
            'url': row['url']
        }

    if tone == 'short':
        return (
            f"Здравствуйте!\n\n"
            f"Откликаюсь на вакансию «{vac_dict['title']}» в компании {vac_dict['company']}.\n"
            f"Имею практические навыки адаптивной верстки (HTML5/CSS3, JavaScript, перенос из Figma пиксель в пиксель) и опыт разработки автоматизированных скриптов на Python. "
            f"Внимателен к деталям, быстро вникаю в процессы и нацелен на результат.\n\n"
            f"Готов оперативно выполнить тестовое задание и приступить к работе!\n\n"
            f"С уважением, Алексей Юпатов\n"
            f"Telegram: @ApeLsinn03 | Тел: +7 923 162 9223"
        )
    elif tone == 'wb_analytics':
        return (
            f"Добрый день!\n\n"
            f"Меня заинтересовала вакансия «{vac_dict['title']}» в компании {vac_dict['company']}.\n"
            f"Помимо навыков фронтенд-разработки и скриптов на Python, имею крепкий бэкграунд в аналитике данных, SEO-оптимизации и работе с цифровыми витринами (Wildberries). "
            f"Умею анализировать требования, структурировать информацию и находить узкие места.\n\n"
            f"Буду рад применить аналитический подход и технические навыки в вашей команде. Готов к тестовому заданию!\n\n"
            f"С уважением, Алексей Юпатов\n"
            f"Telegram: @ApeLsinn03 | Тел: +7 923 162 9223"
        )
    else:
        return ai_cover_letter.get_cover_letter(vac_dict)
    """Генерирует продающее описание для портфолио через Google Gemini API."""
    if not GEMINI_API_KEY:
        return "Специализируюсь на адаптивной верстке сайтов по макетам Figma и разработке скриптов на Python. Пишу чистый семантичный код на HTML5/CSS3/JavaScript. Нацелен на результат, соблюдаю дедлайны и готов быстро расти в сильной команде."

    prompt = f"""
Ты — топовый IT-карьерный консультант. Напиши краткое, сильное, продающее описание «Обо мне» (3-4 емких предложения) для личного сайта-портфолио начинающего разработчика.

Роль: {role}
Ключевые навыки: {skills}

Требования:
1. Без банальных фраз ("я целеустремленный и стрессоустойчивый").
2. Фокус на твердых навыках: верстка по макетам Figma, чистый код, адаптивность, скрипты автоматизации, решение реальных задач.
3. Готовность быстро обучаться и погружаться в стек компании.
4. Текст от первого лица, уверенный, но дружелюбный тон.
Верни ТОЛЬКО готовый текст описания.
"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 300}
    }
    try:
        r = requests.post(url, json=payload, timeout=8)
        if r.status_code == 200:
            res = r.json()
            return res['candidates'][0]['content']['parts'][0]['text'].strip()
    except Exception as e:
        print(f"Ошибка Gemini API: {e}")

    return "Специализируюсь на адаптивной верстке сайтов по макетам Figma и разработке скриптов на Python. Пишу чистый семантичный код на HTML5/CSS3/JavaScript. Нацелен на результат, соблюдаю дедлайны и готов быстро расти в сильной команде."

def send_portfolio_summary_to_telegram(data: dict) -> bool:
    token = os.getenv('TELEGRAM_BOT_TOKEN', '8863351782:AAEeLRftLdK_dw-OxtuZtmo9zfwAqd5MeZo').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '6092880160').strip()
    if not token or not chat_id:
        return False

    name = data.get('name', 'Алексей Юпатов')
    role = data.get('role', 'Junior Frontend / Python')
    bio = data.get('bio', '')
    projects_count = len(data.get('projects', []))
    skills_str = ", ".join([s.get('name', '') for s in data.get('skills', [])[:6]])
    tg = data.get('socials', {}).get('telegram', '@ApeLsinn03')

    text = f"""🎨 <b>ВАШЕ ПОРТФОЛИО СФОРМИРОВАНО!</b>

👤 <b>{name}</b> — <i>{role}</i>
🛠️ <b>Стек:</b> {skills_str}
💻 <b>Проектов в портфолио:</b> {projects_count} шт.

📝 <b>Самопрезентация для откликов:</b>
<code>{bio}</code>

🔗 <b>Контакты для HR:</b> {tg}
🚀 <i>Сайт можно опубликовать на GitHub Pages и вставлять ссылку в отклики на HeadHunter!</i>"""

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=6)
        return True
    except Exception:
        return False

class CloudAppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == '/api/feed':
            st = query.get('stack', [None])[0]
            sal = query.get('salary', [None])[0]
            self.send_json(get_swipe_feed(stack_filter=st, salary_filter=sal))
            return
        elif path == '/api/kanban':
            self.send_json(get_kanban_data())
            return
        elif path == '/api/analytics':
            self.send_json(get_market_insights())
            return
        elif path == '/api/blacklist':
            self.send_json(database.get_blacklisted_companies())
            return
        elif path == '/api/settings':
            self.send_json({
                'filter_stack': database.get_user_filter(),
                'filter_salary': database.get_salary_filter(),
                'interval': database.get_interval_minutes(),
                'night_mode': database.get_setting('night_mode', 'on'),
                'daily_digest': database.get_setting('daily_digest', 'on')
            })
            return
        elif path == '/api/stats/summary':
            st = database.get_stats()
            st['skipped'] = database.get_skipped_vacancies_count()
            self.send_json(st)
            return
        elif path == '/healthz' or path == '/ping':
            self.send_json({'status': 'ok', 'online': True})
            return
        elif path == '/portfolio' or path == '/portfolio/':
            portfolio_index = os.path.join(DIRECTORY, 'portfolio', 'index.html')
            if os.path.exists(portfolio_index):
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                with open(portfolio_index, 'rb') as f:
                    self.wfile.write(f.read())
                return
        super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        req_data = json.loads(body.decode('utf-8')) if body else {}

        if self.path == '/api/swipe':
            v_id = req_data.get('vacancy_id')
            action = req_data.get('action')
            company = req_data.get('company')
            
            if action == 'favorite':
                database.add_favorite_by_id(v_id)
            elif action == 'skip':
                database.add_skipped_vacancy(v_id)
            elif action == 'blacklist' and company:
                database.add_blacklisted_company(company)
                database.add_skipped_vacancy(v_id)
            
            self.send_json({'status': 'ok'})
            return

        elif self.path == '/api/settings/update':
            if 'filter_stack' in req_data:
                database.set_user_filter(req_data['filter_stack'])
            if 'filter_salary' in req_data:
                database.set_salary_filter(req_data['filter_salary'])
            self.send_json({'status': 'ok', 'filter_stack': database.get_user_filter(), 'filter_salary': database.get_salary_filter()})
            return

        elif self.path == '/api/ai-generate-bio':
            role = req_data.get('role', 'Junior Frontend')
            skills = req_data.get('skills', 'HTML, CSS, JS, Figma, Python')
            generated_text = generate_ai_bio_with_gemini(role, skills)
            self.send_json({'text': generated_text})
            return

        elif self.path == '/api/send-to-telegram':
            send_portfolio_summary_to_telegram(req_data)
            self.send_json({'status': 'ok'})
            return

        elif self.path == '/api/skipped/reset':
            cnt = database.reset_skipped_vacancies()
            self.send_json({'status': 'ok', 'reset_count': cnt})
            return

        elif self.path == '/api/kanban/move':
            v_id = req_data.get('vacancy_id')
            new_status = req_data.get('status')
            database.update_vacancy_status(v_id, new_status)
            self.send_json({'status': 'ok'})
            return

        elif self.path == '/api/generate-letter':
            v_id = req_data.get('vacancy_id', '')
            tone = req_data.get('tone', 'business')
            letter = generate_custom_letter(v_id, tone)
            self.send_json({'letter': letter})
            return

        elif self.path == '/api/blacklist/remove':
            comp = req_data.get('company')
            if comp:
                database.remove_blacklisted_company(comp)
            self.send_json({'status': 'ok'})
            return

        super().do_POST()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def send_json(self, data):
        payload = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

def start_telegram_bot():
    """Запускает Telegram бота и циклический парсер в фоновом потоке."""
    import main
    try:
        main.main_loop()
    except Exception as e:
        print(f"Ошибка бота: {e}")

def start_server():
    database.init_db()
    
    # 1. Запуск Telegram бота в фоне
    bot_thread = threading.Thread(target=start_telegram_bot, daemon=True)
    bot_thread.start()
    print("🤖 Telegram Bot Worker успешно запущен в фоне!")

    # 2. Запуск HTTP веб-сервера для Telegram Mini App
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), CloudAppHandler) as httpd:
        print("=" * 65)
        print("🚀 JOB RADAR CLOUD SERVER — Успешно запущен 24/7!")
        print(f"🌐 Mini App HTTP Server активен на порту: {PORT}")
        print("=" * 65)
        httpd.serve_forever()

if __name__ == '__main__':
    start_server()
