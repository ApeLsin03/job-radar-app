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

def get_swipe_feed(limit=50):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.vacancy_id, v.title, v.company, v.salary, v.url, v.source, v.published_at, v.status, v.created_at
        FROM seen_vacancies v
        WHERE v.company NOT IN (SELECT company_name FROM blacklisted_companies)
          AND v.vacancy_id NOT IN (SELECT vacancy_id FROM skipped_vacancies)
          AND v.vacancy_id NOT IN (SELECT vacancy_id FROM favorites)
        ORDER BY v.id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    feed = []
    for r in rows:
        feed.append({
            'vacancy_id': r['vacancy_id'],
            'title': r['title'],
            'company': r['company'],
            'salary': r['salary'] or 'З/П не указана',
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
        return "К сожалению, данные по вакансии не найдены."

    vac_dict = {
        'title': row['title'],
        'company': row['company'],
        'description': f"{row['title']} в компании {row['company']}. 100% удаленка.",
        'url': row['url']
    }

    if tone == 'short':
        return (
            f"Здравствуйте!\n\n"
            f"Откликаюсь на вакансию «{vac_dict['title']}» в {vac_dict['company']}.\n"
            f"Имею практические навыки верстки (HTML5/CSS3, JavaScript, адаптив по Figma) и опыт разработки автоматизированных скриптов на Python. "
            f"Быстро вникаю в процессы, внимателен к деталям и нацелен на результат.\n\n"
            f"Готов оперативно выполнить тестовое задание и приступить к работе!\n\n"
            f"С уважением, Алексей\n"
            f"Telegram: @ApeLsinn03 | Тел: +7 923 162 9223"
        )
    elif tone == 'wb_analytics':
        return (
            f"Добрый день!\n\n"
            f"Меня заинтересовала вакансия «{vac_dict['title']}» в компании {vac_dict['company']}.\n"
            f"Помимо навыков фронтенд-разработки и скриптов на Python, имею крепкий бэкграунд в аналитике данных, SEO-оптимизации и работе с цифровыми витринами. "
            f"Умею анализировать требования, структурировать информацию и находить узкие места.\n\n"
            f"Буду рад применить аналитический подход и технические навыки в вашей команде. Готов к тестовому заданию!\n\n"
            f"С уважением, Алексей\n"
            f"Telegram: @ApeLsinn03 | Тел: +7 923 162 9223"
        )
    else:
        return ai_cover_letter.get_cover_letter(vac_dict)

class CloudAppHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        if self.path == '/api/feed':
            self.send_json(get_swipe_feed())
            return
        elif self.path == '/api/kanban':
            self.send_json(get_kanban_data())
            return
        elif self.path == '/api/analytics':
            self.send_json(get_market_insights())
            return
        elif self.path == '/api/blacklist':
            self.send_json(database.get_blacklisted_companies())
            return
        elif self.path == '/api/stats/summary':
            st = database.get_stats()
            st['skipped'] = database.get_skipped_vacancies_count()
            self.send_json(st)
            return
        elif self.path == '/healthz' or self.path == '/ping':
            self.send_json({'status': 'ok', 'online': True})
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
                database.remove_company_from_blacklist(comp)
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
