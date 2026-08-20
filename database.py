import sqlite3
import os
import sys
import re
import hashlib
from datetime import datetime
from typing import Optional, List, Dict

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_NAME = os.path.join(os.path.dirname(__file__), 'vacancies_v2.db')

def get_connection():
    return sqlite3.connect(DB_NAME)

def generate_fingerprint(company: str, title: str) -> str:
    """Создает нормализованный отпечаток вакансии для отсева перезаливов."""
    comp_clean = re.sub(r'[^a-zа-я0-9]', '', (company or '').lower())
    title_clean = re.sub(r'[^a-zа-я0-9]', '', (title or '').lower())
    raw = f"{comp_clean}:{title_clean}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def init_db():
    """Инициализирует структуру таблиц SQLite с поддержкой статусов и черного списка компаний."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Таблица всех просмотренных вакансий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seen_vacancies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vacancy_id TEXT UNIQUE NOT NULL,
                fingerprint TEXT UNIQUE,
                title TEXT NOT NULL,
                company TEXT,
                salary TEXT,
                url TEXT NOT NULL,
                source TEXT,
                published_at TEXT,
                status TEXT DEFAULT 'Не откликался',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_vac_id ON seen_vacancies (vacancy_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fingerprint ON seen_vacancies (fingerprint)')
        
        # Добавляем колонку status если база была создана ранее
        try:
            cursor.execute("ALTER TABLE seen_vacancies ADD COLUMN status TEXT DEFAULT 'Не откликался'")
        except sqlite3.OperationalError:
            pass # Колонка уже существует
        
        # 2. Таблица Избранного
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vacancy_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                company TEXT,
                salary TEXT,
                url TEXT NOT NULL,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fav_vac_id ON favorites (vacancy_id)')
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklisted_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_name TEXT UNIQUE,
                created_at TEXT
            )
        """)
        
        # 4. Таблица пропущенных вакансий
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skipped_vacancies (
                vacancy_id TEXT PRIMARY KEY,
                created_at TEXT
            )
        """)
        
        # 5. Таблица настроек пользователя (стек, зарплата, ночной режим, дайджест, интервал)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        default_settings = [
            ('filter_stack', 'all'),
            ('filter_salary', 'salary_any'),
            ('check_interval', '30'),
            ('night_mode', 'on'),
            ('daily_digest', 'on'),
            ('last_digest_date', '')
        ]
        for k, v in default_settings:
            cursor.execute("INSERT OR IGNORE INTO user_settings (key, value) VALUES (?, ?)", (k, v))
            
        conn.commit()

# ==================== ЧЕРНЫЙ СПИСОК КОМПАНИЙ ====================

def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    # Очищаем от кавычек, ООО, ИП, АО для гибкого сравнения
    cleaned = re.sub(r'(?i)\b(ооо|ип|ао|зао|пао|llc|inc|gmbh)\b', '', name)
    cleaned = re.sub(r'["«»„“\s]', '', cleaned).strip().lower()
    return cleaned if len(cleaned) > 2 else name.strip().lower()

def add_blacklisted_company(company_name: str) -> bool:
    """Добавляет компанию в черный список."""
    c_clean = company_name.strip()
    if not c_clean or c_clean == "Компания не указана":
        return False
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO blacklisted_companies (company_name) VALUES (?)', (c_clean,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return True

def remove_blacklisted_company(company_name: str) -> bool:
    """Удаляет компанию из черного списка."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM blacklisted_companies WHERE company_name = ?', (company_name.strip(),))
        conn.commit()
        return cursor.rowcount > 0

def get_blacklisted_companies() -> List[str]:
    """Возвращает список заблокированных компаний."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT company_name FROM blacklisted_companies ORDER BY id DESC')
        return [row[0] for row in cursor.fetchall()]

def is_company_blacklisted(company_name: str) -> bool:
    """Проверяет, заблокирована ли компания пользователем."""
    if not company_name:
        return False
    norm_target = normalize_company_name(company_name)
    all_b = get_blacklisted_companies()
    for b in all_b:
        if normalize_company_name(b) in norm_target or norm_target in normalize_company_name(b):
            return True
    return False

# ==================== ПРОВЕРКА И СОХРАНЕНИЕ ВАКАНСИЙ ====================

def is_vacancy_seen(vacancy_id: str, company: str = '', title: str = '') -> bool:
    """Проверяет вакансию по ID, отпечатку и черному списку компаний."""
    if company and is_company_blacklisted(company):
        return True
        
    clean_id = str(vacancy_id).strip()
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM seen_vacancies WHERE vacancy_id = ?', (clean_id,))
        if cursor.fetchone() is not None:
            return True
            
        return False

def save_vacancy(vacancy: dict) -> bool:
    """Сохраняет вакансию в базу с генерацией отпечатка."""
    clean_id = str(vacancy['id']).strip()
    title = vacancy.get('title', 'Без названия')
    company = vacancy.get('company', 'Компания не указана')
    
    if is_company_blacklisted(company):
        return False
        
    fp = generate_fingerprint(company, title)
    
    if is_vacancy_seen(clean_id, company, title):
        return False
        
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO seen_vacancies (vacancy_id, fingerprint, title, company, salary, url, source, published_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                clean_id,
                fp,
                title,
                company,
                vacancy.get('salary', 'Не указана'),
                vacancy.get('url', ''),
                vacancy.get('source', 'Не указан'),
                vacancy.get('published_at', datetime.now().isoformat()),
                'Не откликался'
            ))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def get_vacancy_by_id(vacancy_id: str) -> Optional[dict]:
    clean_id = str(vacancy_id).strip()
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM seen_vacancies WHERE vacancy_id = ?', (clean_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

# ==================== ТРЕКЕР СТАТУСОВ ОТКЛИКОВ ====================

def update_vacancy_status(vacancy_id: str, new_status: str) -> bool:
    """Обновляет статус отклика по вакансии ('Не откликался', 'Откликнулся', 'Тестовое', 'Собеседование', 'Оффер', 'Отказ')."""
    clean_id = str(vacancy_id).strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE seen_vacancies SET status = ? WHERE vacancy_id = ?', (new_status, clean_id))
        conn.commit()
        return cursor.rowcount > 0

def get_tracked_vacancies(status_filter: Optional[str] = None) -> List[dict]:
    """Возвращает вакансии с активными статусами отклика."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if status_filter and status_filter != 'all':
            cursor.execute('''
                SELECT vacancy_id, title, company, salary, url, source, status, created_at
                FROM seen_vacancies
                WHERE status = ?
                ORDER BY id DESC
            ''', (status_filter,))
        else:
            cursor.execute('''
                SELECT vacancy_id, title, company, salary, url, source, status, created_at
                FROM seen_vacancies
                WHERE status != 'Не откликался' AND status IS NOT NULL
                ORDER BY id DESC
            ''')
        return [dict(row) for row in cursor.fetchall()]

# ==================== ПАРСИНГ И ФИЛЬТРАЦИЯ ЗАРПЛАТ ====================

def parse_salary_numbers(salary_str: str) -> tuple[Optional[int], Optional[int]]:
    if not salary_str or "договоренности" in salary_str.lower() or "не указана" in salary_str.lower():
        return None, None
    cleaned = salary_str.replace('\u202f', '').replace(' ', '').replace('\xa0', '')
    numbers = [int(n) for n in re.findall(r'\d+', cleaned)]
    ruble_numbers = [n for n in numbers if n >= 1000]
    if not ruble_numbers:
        return None, None
    elif len(ruble_numbers) == 1:
        return ruble_numbers[0], ruble_numbers[0]
    else:
        return min(ruble_numbers), max(ruble_numbers)

def is_salary_matching(salary_str: str, salary_filter: str) -> bool:
    if salary_filter == 'salary_any':
        return True
    min_val, max_val = parse_salary_numbers(salary_str)
    if salary_filter == 'salary_specified':
        return max_val is not None and max_val > 0
    elif salary_filter == 'salary_40k':
        return max_val is not None and max_val >= 40000
    elif salary_filter == 'salary_60k':
        return max_val is not None and max_val >= 60000
    return True

# ==================== ИЗБРАННОЕ ====================

def add_favorite_by_id(vacancy_id: str) -> Optional[dict]:
    clean_id = str(vacancy_id).strip()
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM seen_vacancies WHERE vacancy_id = ?', (clean_id,))
        row = cursor.fetchone()
        if not row:
            return None
        vac = dict(row)
        try:
            cursor.execute('''
                INSERT INTO favorites (vacancy_id, title, company, salary, url, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                clean_id,
                vac.get('title', 'Без названия'),
                vac.get('company', 'Компания не указана'),
                vac.get('salary', 'По договоренности'),
                vac.get('url', ''),
                vac.get('source', 'Сайт')
            ))
            conn.commit()
            return vac
        except sqlite3.IntegrityError:
            return vac

def remove_favorite_by_id(vacancy_id: str) -> bool:
    clean_id = str(vacancy_id).strip()
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM favorites WHERE vacancy_id = ?', (clean_id,))
        conn.commit()
        return cursor.rowcount > 0

def get_favorites() -> List[dict]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM favorites ORDER BY id DESC')
        return [dict(row) for row in cursor.fetchall()]

# ==================== НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ ====================

def get_setting(key: str, default: str = '') -> str:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM user_settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

def set_setting(key: str, value: str):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        ''', (key, value))
        conn.commit()

def get_user_filter() -> str:
    return get_setting('filter_stack', 'all')

def set_user_filter(filter_name: str):
    set_setting('filter_stack', filter_name)

def get_salary_filter() -> str:
    return get_setting('filter_salary', 'salary_any')

def set_salary_filter(filter_name: str):
    set_setting('filter_salary', filter_name)

def is_night_mode_enabled() -> bool:
    return get_setting('night_mode', 'on') == 'on'

def is_daily_digest_enabled() -> bool:
    return get_setting('daily_digest', 'on') == 'on'

def get_interval_minutes() -> int:
    try:
        return int(get_setting('check_interval', '30'))
    except Exception:
        return 30

def set_interval_minutes(minutes: int):
    set_setting('check_interval', str(minutes))

# ==================== ВЫГРУЗКА И СТАТИСТИКА ====================

def get_stats() -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM seen_vacancies')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM favorites')
        favs = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM seen_vacancies WHERE created_at >= datetime('now', '-1 day')")
        today = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM blacklisted_companies")
        bl_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM seen_vacancies WHERE status != 'Не откликался' AND status IS NOT NULL")
        tracked_count = cursor.fetchone()[0]
        
        return {
            'total': total,
            'favorites': favs,
            'last_24h': today,
            'blacklisted': bl_count,
            'tracked': tracked_count,
            'filter_stack': get_user_filter(),
            'filter_salary': get_salary_filter(),
            'interval': get_interval_minutes(),
            'night_mode': get_setting('night_mode', 'on'),
            'daily_digest': get_setting('daily_digest', 'on')
        }

def get_all_vacancies_for_export() -> List[dict]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vacancy_id, title, company, salary, url, source, published_at, status, created_at 
            FROM seen_vacancies 
            ORDER BY id DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def get_top_vacancies_today(limit: int = 5) -> List[dict]:
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vacancy_id, title, company, salary, url, source 
            FROM seen_vacancies 
            WHERE created_at >= datetime('now', '-1 day')
            ORDER BY id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_top_matching_vacancies(stack_filter: str = 'all', salary_filter: str = 'salary_any', limit: int = 5) -> List[dict]:
    """Возвращает актуальные вакансии из базы, удовлетворяющие фильтрам стека и зарплаты."""
    from parser_hh import is_title_relevant
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT vacancy_id as id, title, company, salary, url, source, published_at, status
            FROM seen_vacancies
            WHERE company NOT IN (SELECT company_name FROM blacklisted_companies)
              AND vacancy_id NOT IN (SELECT vacancy_id FROM skipped_vacancies)
            ORDER BY id DESC
            LIMIT 150
        """)
        rows = cursor.fetchall()
        
    result = []
    for r in rows:
        vac = dict(r)
        sal = vac.get('salary', '')
        title = vac.get('title', '')
        if not is_salary_matching(sal, salary_filter):
            continue
        if stack_filter != 'all' and not is_title_relevant(title, stack_filter):
            continue
        result.append(vac)
        if len(result) >= limit:
            break
    return result

def add_skipped_vacancy(vacancy_id: str) -> bool:
    """Добавляет вакансию в список пропущенных (отклоненных)."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO skipped_vacancies (vacancy_id, created_at) VALUES (?, datetime('now'))",
            (str(vacancy_id).strip(),)
        )
        conn.commit()
        return cursor.rowcount > 0

def get_skipped_vacancies_count() -> int:
    """Возвращает количество пропущенных вакансий."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM skipped_vacancies")
        res = cursor.fetchone()
        return res[0] if res else 0

def reset_skipped_vacancies() -> int:
    """Очищает историю пропущенных вакансий для повторного просмотра."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM skipped_vacancies")
        conn.commit()
        return cursor.rowcount

if __name__ == '__main__':
    init_db()
    print("База обновлена. Статистика:", get_stats())
