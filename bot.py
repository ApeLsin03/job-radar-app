import requests
import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from ai_cover_letter import get_cover_letter

load_dotenv()

HTTP_SESSION = requests.Session()

def get_bot_credentials():
    token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()
    return token, chat_id

def send_telegram_message(text: str, reply_markup: dict = None, disable_notification: bool = False, chat_id: str = None) -> dict:
    token, default_chat_id = get_bot_credentials()
    target_chat = str(chat_id) if chat_id else default_chat_id
    if not token or not target_chat:
        return {}
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
        "disable_notification": disable_notification
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
        
    try:
        response = HTTP_SESSION.post(url, json=payload, timeout=8)
        if response.status_code == 200:
            return response.json().get('result', {})
        else:
            print(f"Ошибка отправки Telegram ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Исключение при отправке в Telegram: {e}")
    return {}

def edit_telegram_message(message_id: int, text: str, reply_markup: dict = None, chat_id: str = None) -> bool:
    token, default_chat_id = get_bot_credentials()
    target_chat = str(chat_id) if chat_id else default_chat_id
    if not token or not target_chat or not message_id:
        return False
        
    url = f"https://api.telegram.org/bot{token}/editMessageText"
    payload = {
        "chat_id": target_chat,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
        
    try:
        response = HTTP_SESSION.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            send_telegram_message(text, reply_markup=reply_markup, chat_id=target_chat)
        return response.status_code == 200
    except Exception:
        send_telegram_message(text, reply_markup=reply_markup, chat_id=target_chat)
        return False

def edit_telegram_reply_markup(message_id: int, reply_markup: dict) -> bool:
    token, chat_id = get_bot_credentials()
    if not token or not chat_id or not message_id:
        return False
        
    url = f"https://api.telegram.org/bot{token}/editMessageReplyMarkup"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": json.dumps(reply_markup)
    }
    try:
        response = HTTP_SESSION.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def send_telegram_document(filepath: str, caption: str = "") -> bool:
    token, chat_id = get_bot_credentials()
    if not token or not chat_id:
        return True
        
    url = f"https://api.telegram.org/bot{token}/sendDocument"
    try:
        with open(filepath, 'rb') as f:
            files = {'document': f}
            data = {
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=data, files=files, timeout=30)
            return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки документа в Telegram: {e}")
        return False

def escape_html(text: str) -> str:
    if not text:
        return ""
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def format_status_icon(status: str) -> str:
    icons = {
        'Откликнулся': '🟡 Откликнулся',
        'Тестовое задание': '📝 Тестовое',
        'Собеседование': '🗣️ Собес',
        'Оффер': '🎉 Оффер!',
        'Отказ': '❌ Отказ',
        'Не откликался': '⚪ Не откликался'
    }
    return icons.get(status, f"📌 {status}")

def send_vacancy_card(vacancy: dict, disable_notification: bool = False) -> bool:
    vac_id = vacancy.get('id', '')
    title = escape_html(vacancy.get('title', 'Без названия'))
    company = escape_html(vacancy.get('company', 'Компания не указана'))
    salary = escape_html(vacancy.get('salary', 'З/п не указана'))
    experience = escape_html(vacancy.get('experience', 'Без опыта'))
    requirements = escape_html(vacancy.get('requirements', ''))
    source = escape_html(vacancy.get('source', 'Сайт'))
    url = vacancy.get('url', 'https://hh.ru')
    status = vacancy.get('status', 'Не откликался')
    status_label = format_status_icon(status)
    
    cover_letter = get_cover_letter(vacancy)
    cover_letter_escaped = escape_html(cover_letter)
    
    message = f"""🔥 <b>НОВАЯ ВАКАНСИЯ БЕЗ ОПЫТА</b> [{source}]

💼 <b>Должность:</b> {title}
🏢 <b>Компания:</b> {company}
💵 <b>Зарплата:</b> <b>{salary}</b>
📍 <b>Формат:</b> 100% Удаленно ({experience})

📝 <b>Стек и требования:</b>
<i>{requirements[:320]}{'...' if len(requirements) > 320 else ''}</i>

✉️ <b>Персонализированное сопроводительное письмо:</b>
<code>{cover_letter_escaped}</code>
"""

    reply_markup = {
        "inline_keyboard": [
            [
                {"text": f"🔗 Откликнуться на {source}", "url": url},
                {"text": "⭐ В избранное", "callback_data": f"fav_{vac_id}"}
            ],
            [
                {"text": f"📌 Статус: {status_label}", "callback_data": f"status_menu_{vac_id}"},
                {"text": "🚫 Скрыть компанию", "callback_data": f"bl_comp_{vac_id}"}
            ]
        ]
    }
    
    res = send_telegram_message(message, reply_markup=reply_markup, disable_notification=disable_notification)
    return bool(res)

def send_batch_footer(sent_count: int, active_filter: str = "all", active_salary: str = "salary_any"):
    filter_names = {
        'all': '🌐 Все',
        'frontend': '💻 Frontend/Верстка',
        'python': '🐍 Python',
        'qa': '🧪 QA'
    }
    salary_names = {
        'salary_any': 'Любая',
        'salary_specified': 'С точной суммой',
        'salary_40k': 'От 40 тыс. ₽',
        'salary_60k': 'От 60 тыс. ₽'
    }
    cur_f = filter_names.get(active_filter, '🌐 Все')
    cur_s = salary_names.get(active_salary, 'Любая')

    text = f"""📊 <b>Подборка из {sent_count} вакансий сформирована!</b>
🎯 Стек: <b>{cur_f}</b> | 💵 З/П: <b>{cur_s}</b>
⏳ Следующий автоматический поиск запустится по расписанию.

Выберите действие ниже 👇"""

    markup = {
        "inline_keyboard": [
            [
                {"text": "🚀 Открыть Radar Mini App", "web_app": {"url": "http://localhost:5175"}},
                {"text": "🔍 Найти 10 вакансий", "callback_data": "fetch_more"}
            ],
            [
                {"text": "⭐ Мое избранное", "callback_data": "view_favorites"},
                {"text": "📌 Мои отклики", "callback_data": "menu_tracker"}
            ],
            [
                {"text": "🎨 Мой сайт-портфолио", "callback_data": "menu_portfolio"},
                {"text": "📊 Аналитика рынка", "callback_data": "menu_market"}
            ],
            [
                {"text": "💵 Фильтр З/П", "callback_data": "menu_salary"},
                {"text": "⚙️ Настройки и Режимы", "callback_data": "menu_modes"}
            ]
        ]
    }
    send_telegram_message(text, reply_markup=markup)

MINI_APP_HTTPS_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://job-radar-app.onrender.com')

def setup_telegram_menu_button():
    """Устанавливает нативную кнопку в левом нижнем углу чата Telegram для открытия Mini App в 1 тап."""
    token, chat_id = get_bot_credentials()
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/setChatMenuButton"
    payload = {
        "chat_id": chat_id,
        "menu_button": {
            "type": "web_app",
            "text": "🚀 Radar App",
            "web_app": {"url": MINI_APP_HTTPS_URL}
        }
    }
    try:
        r = HTTP_SESSION.post(url, json=payload, timeout=6)
        if r.status_code == 200:
            print("✅ Нативная кнопка '🚀 Radar App' успешно активирована в строке ввода Telegram!")
    except Exception as e:
        print(f"Ошибка настройки MenuButton: {e}")

def send_mini_app_message(message_id: int = None, chat_id: str = None):
    text = """🚀 <b>JOB RADAR TELEGRAM MINI APP</b>

Ваш персональный центр управления прямо внутри Telegram:

🔥 <b>Tinder для вакансий:</b> свайпайте карточки одной рукой (вправо — сохранить, влево — пропустить, вверх — скрыть компанию).
🗂️ <b>Канбан-доска:</b> отслеживайте этапы откликов (Отклик ➔ Тестовое ➔ Собес ➔ Оффер).
✍️ <b>Студия ИИ-писем:</b> 3 тональности отклика с готовой подписью.
📊 <b>Аналитика и тепловая карта:</b> пиковые часы активности HR.

👉 <b>Нажмите кнопку ниже, чтобы открыть всплывающее окно приложения:</b>"""

    markup = {
        "inline_keyboard": [
            [{"text": "🚀 Открыть окно Radar Mini App", "web_app": {"url": MINI_APP_HTTPS_URL}}],
            [{"text": "🏠 Главное меню", "callback_data": "menu_main"}]
        ]
    }
    if message_id:
        edit_telegram_message(message_id, text, markup)
    else:
        send_telegram_message(text, reply_markup=markup, chat_id=chat_id)

def send_portfolio_builder_message(message_id: int = None):
    text = """🎨 <b>КОНСТРУКТОР САЙТА-ПОРТФОЛИО И РЕЗЮМЕ</b>

Готовый личный сайт с вашими работами и проектами повышает шансы на приглашение на собеседование в <b>3–5 раз</b>!

✨ <b>Конструктор запущен и доступен по адресу:</b>
👉 <b>http://localhost:5174</b>

🚀 <b>Возможности веб-конструктора:</b>
• <b>Live-превью:</b> редактируйте текст и проекты, сразу видя готовый сайт.
• <b>🤖 ИИ-Ассистент:</b> Gemini сформулирует сильное продающее описание.
• <b>Dark / Light темы:</b> современный стеклянный дизайн (Glassmorphism).
• <b>📥 Экспорт в ZIP:</b> чистый код (HTML5 / CSS3 / JS) без лишних фреймворков.
• <b>Бесплатный деплой:</b> публикация на <i>GitHub Pages</i> за 2 минуты!"""

    markup = {
        "inline_keyboard": [
            [{"text": "🌐 Открыть конструктор (localhost:5174)", "url": "http://localhost:5174"}],
            [
                {"text": "📥 Скачать Excel с вакансиями", "callback_data": "export_excel"},
                {"text": "🔍 Найти 10 вакансий", "callback_data": "fetch_more"}
            ],
            [{"text": "🏠 Главное меню", "callback_data": "menu_main"}]
        ]
    }
    if message_id:
        edit_telegram_message(message_id, text, markup)
    else:
        send_telegram_message(text, reply_markup=markup)

def send_market_analytics_message(message_id: int = None):
    from market_analytics import format_market_report
    text = format_market_report()
    markup = {
        "inline_keyboard": [
            [
                {"text": "📥 Скачать базу в Excel (.xlsx)", "callback_data": "export_excel"},
                {"text": "🔍 Найти 10 вакансий", "callback_data": "fetch_more"}
            ],
            [
                {"text": "🎯 Сменить стек", "callback_data": "menu_filters"},
                {"text": "💵 Фильтр З/П", "callback_data": "menu_salary"}
            ],
            [{"text": "🏠 Главное меню", "callback_data": "menu_main"}]
        ]
    }
    if message_id:
        edit_telegram_message(message_id, text, markup)
    else:
        send_telegram_message(text, reply_markup=markup)

# ==================== МЕНЮ СТАТУСОВ ОТКЛИКА ====================

def send_status_picker(vac_id: str, current_status: str = 'Не откликался', message_id: int = None):
    text = (
        "📌 <b>Управление статусом отклика:</b>\n\n"
        f"Текущий статус: <b>{format_status_icon(current_status)}</b>\n\n"
        "Отметьте этап, на котором вы сейчас находитесь по этой вакансии:"
    )
    markup = {
        "inline_keyboard": [
            [
                {"text": "🟡 Откликнулся", "callback_data": f"setstat_{vac_id}_applied"},
                {"text": "📝 Тестовое задание", "callback_data": f"setstat_{vac_id}_test"}
            ],
            [
                {"text": "🗣️ Собеседование", "callback_data": f"setstat_{vac_id}_interview"},
                {"text": "🎉 Получил оффер!", "callback_data": f"setstat_{vac_id}_offer"}
            ],
            [
                {"text": "❌ Отказ", "callback_data": f"setstat_{vac_id}_rejected"},
                {"text": "⚪ Сброс (Не откликался)", "callback_data": f"setstat_{vac_id}_reset"}
            ],
            [{"text": "◀️ Закрыть меню", "callback_data": f"close_status_menu_{vac_id}"}]
        ]
    }
    if message_id:
        edit_telegram_message(message_id, text, markup)
    else:
        send_telegram_message(text, reply_markup=markup)

def send_applications_tracker(tracked_vacancies: list, message_id: int = None):
    if not tracked_vacancies:
        text = (
            "📌 <b>Ваш трекер откликов пока пуст.</b>\n\n"
            "Нажимайте кнопку <b>«📌 Статус»</b> под вакансиями, когда вы отправляете отклики, получаете тестовые или приглашения на интервью!\n"
            "Все статусы также автоматически выгружаются в Excel-файл."
        )
        markup = {
            "inline_keyboard": [
                [{"text": "🔍 Найти вакансии", "callback_data": "fetch_more"}],
                [{"text": "◀️ Главное меню", "callback_data": "menu_main"}]
            ]
        }
        if message_id:
            edit_telegram_message(message_id, text, markup)
        else:
            send_telegram_message(text, reply_markup=markup)
        return

    text = f"📌 <b>Трекер откликов ({len(tracked_vacancies)} активных):</b>\n\n"
    keyboard = []
    
    for idx, v in enumerate(tracked_vacancies[:8], 1):
        vac_id = v.get('vacancy_id', '')
        title = escape_html(v.get('title', 'Без названия'))
        company = escape_html(v.get('company', 'Компания'))
        status = v.get('status', 'Откликнулся')
        icon = format_status_icon(status)
        url = v.get('url', 'https://hh.ru')
        
        text += f"<b>{idx}. {title}</b> ({company})\n"
        text += f"Этап: <b>{icon}</b> | <a href='{url}'>Ссылка</a>\n\n"
        
        keyboard.append([
            {"text": f"Изменить #{idx}", "callback_data": f"status_menu_{vac_id}"},
            {"text": f"🔗 Открыть #{idx}", "url": url}
        ])
        
    keyboard.append([{"text": "📥 Скачать таблицу Excel (.xlsx)", "callback_data": "export_excel"}])
    keyboard.append([{"text": "◀️ Главное меню", "callback_data": "menu_main"}])
    
    if message_id:
        edit_telegram_message(message_id, text, {"inline_keyboard": keyboard})
    else:
        send_telegram_message(text, reply_markup={"inline_keyboard": keyboard})

# ==================== ЧЕРНЫЙ СПИСОК КОМПАНИЙ ====================

def send_blacklist_menu(companies: list, message_id: int = None):
    if not companies:
        text = "🚫 <b>Черный список компаний пуст.</b>\n\nВы можете нажать <b>«🚫 Скрыть компанию»</b> под любой вакансией, чтобы навсегда скрыть этого работодателя из поиска."
        markup = {
            "inline_keyboard": [
                [{"text": "◀️ Назад в настройки", "callback_data": "menu_modes"}],
                [{"text": "🏠 Главное меню", "callback_data": "menu_main"}]
            ]
        }
        if message_id:
            edit_telegram_message(message_id, text, markup)
        else:
            send_telegram_message(text, reply_markup=markup)
        return

    text = f"🚫 <b>Черный список компаний ({len(companies)} шт.):</b>\n\nВакансии этих компаний больше не показываются:\n\n"
    keyboard = []
    for idx, c in enumerate(companies[:10], 1):
        text += f"• <b>{escape_html(c)}</b>\n"
        keyboard.append([{"text": f"❌ Разблокировать: {c[:22]}", "callback_data": f"unblock_comp_{idx-1}"}])
        
    keyboard.append([{"text": "◀️ Назад в настройки", "callback_data": "menu_modes"}])
    keyboard.append([{"text": "🏠 Главное меню", "callback_data": "menu_main"}])
    
    if message_id:
        edit_telegram_message(message_id, text, {"inline_keyboard": keyboard})
    else:
        send_telegram_message(text, reply_markup={"inline_keyboard": keyboard})

# ==================== ДРУГИЕ МЕНЮ ====================

def get_filters_menu_data(current_filter: str = "all"):
    text = (
        "🎯 <b>Настройка фильтра стека технологий:</b>\n\n"
        "• <b>Верстка / Frontend:</b> HTML/CSS, лендинги, JavaScript, Tilda, Figma\n"
        "• <b>Python / Скрипты:</b> парсинг, скрипты автоматизации, бэкенд\n"
        "• <b>QA / Тестирование:</b> ручное тестирование веб-сайтов и приложений\n"
        "• <b>Все направления:</b> общий поток всех доступных IT-стажировок"
    )
    markup = {
        "inline_keyboard": [
            [{"text": f"{'✅ ' if current_filter == 'frontend' else ''}💻 Верстка и Frontend", "callback_data": "set_filter_frontend"}],
            [{"text": f"{'✅ ' if current_filter == 'python' else ''}🐍 Python и автоматизация", "callback_data": "set_filter_python"}],
            [{"text": f"{'✅ ' if current_filter == 'qa' else ''}🧪 QA и тестирование", "callback_data": "set_filter_qa"}],
            [{"text": f"{'✅ ' if current_filter == 'all' else ''}🌐 Все направления (IT)", "callback_data": "set_filter_all"}],
            [{"text": "◀️ Главное меню", "callback_data": "menu_main"}]
        ]
    }
    return text, markup

def send_filters_menu(current_filter: str = "all", message_id: int = None):
    text, markup = get_filters_menu_data(current_filter)
    if message_id:
        edit_telegram_message(message_id, text, markup)
    else:
        send_telegram_message(text, reply_markup=markup)

def get_salary_menu_data(current_salary: str = "salary_any"):
    text = (
        "💵 <b>Настройка фильтра по зарплате:</b>\n\n"
        "Выберите минимальный порог дохода для вакансий:\n\n"
        "• <b>Любая зарплата:</b> включает стажировки и оплату по договоренности\n"
        "• <b>Только с указанной суммой:</b> отсекает «по договоренности»\n"
        "• <b>От 40 000+ ₽:</b> вакансии с доходом от 40 тыс. рублей\n"
        "• <b>От 60 000+ ₽:</b> топовые оплачиваемые позиции для начинающих"
    )
    markup = {
        "inline_keyboard": [
            [{"text": f"{'✅ ' if current_salary == 'salary_any' else ''}🌐 Любая (включая стажировки)", "callback_data": "set_sal_salary_any"}],
            [{"text": f"{'✅ ' if current_salary == 'salary_specified' else ''}💵 Только с точной З/П", "callback_data": "set_sal_salary_specified"}],
            [{"text": f"{'✅ ' if current_salary == 'salary_40k' else ''}💰 От 40 000+ ₽", "callback_data": "set_sal_salary_40k"}],
            [{"text": f"{'✅ ' if current_salary == 'salary_60k' else ''}💎 От 60 000+ ₽", "callback_data": "set_sal_salary_60k"}],
            [{"text": "◀️ Главное меню", "callback_data": "menu_main"}]
        ]
    }
    return text, markup

def send_salary_menu(current_salary: str = "salary_any", message_id: int = None):
    text, markup = get_salary_menu_data(current_salary)
    if message_id:
        edit_telegram_message(message_id, text, markup)
    else:
        send_telegram_message(text, reply_markup=markup)

def format_interval_text(minutes: int) -> str:
    mapping = {
        30: "30 минут",
        60: "1 час",
        120: "2 часа",
        180: "3 часа",
        240: "4 часа",
        480: "8 часов",
        720: "12 часов"
    }
    return mapping.get(minutes, f"{minutes} мин")

def get_interval_menu_data(current_minutes: int = 30):
    text = (
        "⏱️ <b>Настройка интервала автоматического поиска:</b>\n\n"
        "Выберите, как часто бот должен автоматически проверять сайты и Telegram на новые вакансии:\n\n"
        f"Текущий интервал: <b>{format_interval_text(current_minutes)}</b>"
    )
    intervals = [
        (30, "30 минут"),
        (60, "1 час"),
        (120, "2 часа"),
        (180, "3 часа"),
        (240, "4 часа"),
        (480, "8 часов"),
        (720, "12 часов")
    ]
    keyboard = []
    row = []
    for m, label in intervals:
        prefix = "✅ " if m == current_minutes else ""
        row.append({"text": f"{prefix}{label}", "callback_data": f"set_interval_{m}"})
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([{"text": "◀️ Назад в режимы", "callback_data": "menu_modes"}])
    keyboard.append([{"text": "🏠 Главное меню", "callback_data": "menu_main"}])
    return text, {"inline_keyboard": keyboard}

def send_interval_menu(current_minutes: int = 30, message_id: int = None):
    text, markup = get_interval_menu_data(current_minutes)
    if message_id:
        edit_telegram_message(message_id, text, markup)
    else:
        send_telegram_message(text, reply_markup=markup)

def get_modes_menu_data(night_mode: str = "on", daily_digest: str = "on", current_minutes: int = 30):
    night_status = "ВКЛЮЧЕН (23:00–09:00 без звука) 🌙" if night_mode == "on" else "ВЫКЛЮЧЕН (уведомления всегда) 🔔"
    digest_status = "ВКЛЮЧЕН (каждый день в 20:00) 📈" if daily_digest == "on" else "ВЫКЛЮЧЕН 🔕"
    cur_interval_str = format_interval_text(current_minutes)
    
    text = f"""⚙️ <b>Настройка режимов работы и черного списка:</b>

⏱️ <b>Интервал поиска:</b> каждые <b>{cur_interval_str}</b>
<i>Как часто бот сам сканирует новые вакансии.</i>

🌙 <b>Ночной режим «Тишина»:</b>
Текущий статус: <b>{night_status}</b>

📈 <b>Вечерний дайджест:</b>
Текущий статус: <b>{digest_status}</b>"""

    toggle_night_txt = "🌙 Выключить ночной режим" if night_mode == "on" else "🌙 Включить ночной режим"
    toggle_digest_txt = "📈 Выключить дайджест" if daily_digest == "on" else "📈 Включить дайджест"

    markup = {
        "inline_keyboard": [
            [{"text": f"⏱️ Изменить интервал ({cur_interval_str})", "callback_data": "menu_interval"}],
            [{"text": "🚫 Черный список компаний", "callback_data": "menu_blacklist"}],
            [{"text": toggle_night_txt, "callback_data": "toggle_night_mode"}],
            [{"text": toggle_digest_txt, "callback_data": "toggle_daily_digest"}],
            [{"text": "📊 Прислать дайджест прямо сейчас", "callback_data": "send_digest_now"}],
            [{"text": "◀️ Главное меню", "callback_data": "menu_main"}]
        ]
    }
    return text, markup

def send_modes_menu(night_mode: str = "on", daily_digest: str = "on", current_minutes: int = 30, message_id: int = None):
    text, markup = get_modes_menu_data(night_mode, daily_digest, current_minutes)
    if message_id:
        edit_telegram_message(message_id, text, markup)
    else:
        send_telegram_message(text, reply_markup=markup)

def send_evening_digest_message(stats: dict, top_vacancies: list):
    date_str = datetime.now().strftime("%d.%m.%Y")
    total_today = stats.get('last_24h', 0)
    favs_total = stats.get('favorites', 0)
    tracked_total = stats.get('tracked', 0)
    
    text = f"""📈 <b>ВЕЧЕРНИЙ ДАЙДЖЕСТ ЗА {date_str}</b>

🔥 <b>Итоги дня:</b>
• Новых вакансий за 24ч: <b>{total_today}</b>
• Всего в базе: <b>{stats.get('total', 0)}</b>
• Вакансий в Избранном: <b>{favs_total}</b>
• Активных откликов в трекере: <b>{tracked_total}</b>

🌟 <b>Топ свежих предложений:</b>\n"""

    keyboard = []
    if top_vacancies:
        for idx, v in enumerate(top_vacancies[:3], 1):
            title = escape_html(v.get('title', 'Без названия'))
            company = escape_html(v.get('company', 'Компания'))
            salary = escape_html(v.get('salary', 'По договоренности'))
            url = v.get('url', 'https://hh.ru')
            text += f"\n<b>{idx}. {title}</b>\n🏢 {company} | 💵 <b>{salary}</b>\n"
            keyboard.append([{"text": f"🔗 Откликнуться #{idx}", "url": url}])
    else:
        text += "<i>За сегодня все вакансии уже просмотрены!</i>\n"

    keyboard.append([{"text": "📥 Скачать всю базу в Excel (.xlsx)", "callback_data": "export_excel"}])
    keyboard.append([{"text": "🔍 Найти еще 10 вакансий", "callback_data": "fetch_more"}])

    send_telegram_message(text, reply_markup={"inline_keyboard": keyboard})

def send_favorites_list(favorites: list, message_id: int = None):
    if not favorites:
        text = "⭐ <b>Ваш список избранного пуст.</b>\n\nНажимайте кнопку <b>«⭐ В избранное»</b> под интересными вакансиями, чтобы сохранять их сюда!"
        markup = {
            "inline_keyboard": [
                [{"text": "🔍 Найти вакансии", "callback_data": "fetch_more"}],
                [{"text": "◀️ Главное меню", "callback_data": "menu_main"}],
            ]
        }
        if message_id:
            edit_telegram_message(message_id, text, markup)
        else:
            send_telegram_message(text, reply_markup=markup)
        return
        
    text = f"⭐ <b>Ваши сохраненные вакансии ({len(favorites)} шт.):</b>\n\n"
    keyboard = []
    
    for idx, v in enumerate(favorites[:10], 1):
        vac_id = v.get('vacancy_id', '')
        title = escape_html(v.get('title', 'Без названия'))
        company = escape_html(v.get('company', 'Компания'))
        salary = escape_html(v.get('salary', 'По договоренности'))
        url = v.get('url', 'https://hh.ru')
        
        text += f"<b>{idx}. {title}</b>\n🏢 {company} | 💵 {salary}\n🔗 <a href='{url}'>Открыть вакансию</a>\n\n"
        
        keyboard.append([
            {"text": f"🔗 Открыть #{idx}", "url": url},
            {"text": f"❌ Удалить #{idx}", "callback_data": f"del_fav_{vac_id}"}
        ])
        
    keyboard.append([{"text": "📥 Скачать всё в Excel", "callback_data": "export_excel"}])
    keyboard.append([{"text": "◀️ Главное меню", "callback_data": "menu_main"}])
    
    if message_id:
        edit_telegram_message(message_id, text, {"inline_keyboard": keyboard})
    else:
        send_telegram_message(text, reply_markup={"inline_keyboard": keyboard})
