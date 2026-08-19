import time
import os
import sys
import threading
import requests
from datetime import datetime
from dotenv import load_dotenv

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from database import (
    init_db, is_vacancy_seen, save_vacancy, get_stats, get_vacancy_by_id,
    add_favorite_by_id, remove_favorite_by_id, get_favorites,
    get_user_filter, set_user_filter, get_salary_filter, set_salary_filter,
    is_salary_matching, get_setting, set_setting, is_night_mode_enabled,
    is_daily_digest_enabled, get_top_vacancies_today,
    get_interval_minutes, set_interval_minutes,
    add_blacklisted_company, remove_blacklisted_company, get_blacklisted_companies,
    update_vacancy_status, get_tracked_vacancies
)
from parser_hh import get_all_fresh_vacancies as get_hh_and_habr, fetch_hh_full_description
from parser_avito import get_all_avito_vacancies
from parser_telegram_feed import get_all_telegram_vacancies
from bot import (
    send_vacancy_card, send_batch_footer, send_telegram_message,
    send_telegram_document, send_filters_menu, send_salary_menu,
    send_modes_menu, send_interval_menu, format_interval_text,
    send_status_picker, send_applications_tracker, send_blacklist_menu,
    format_status_icon, send_evening_digest_message, send_favorites_list,
    send_market_analytics_message, send_portfolio_builder_message,
    send_mini_app_message,
    edit_telegram_message, edit_telegram_reply_markup,
    get_bot_credentials, HTTP_SESSION, MINI_APP_HTTPS_URL
)
from export_excel import create_excel_export

load_dotenv()

MINI_APP_HTTPS_URL = os.getenv('RENDER_EXTERNAL_URL', 'https://job-radar-app.onrender.com')

SCAN_LOCK = threading.Lock()
BATCH_LIMIT = 10

def print_banner():
    print("=" * 65)
    print("🚀 JOB RADAR v2.9 — Персональный охотник за вакансиями без опыта")
    print("=" * 65)
    print("🌐 Источники: HeadHunter | Хабр Карьера | Авито Работа | Telegram")
    print(f"⏱️ Интервал автопоиска: {format_interval_text(get_interval_minutes())}")
    print("📌 Трекер откликов: АКТИВИРОВАН | 🚫 Черный список компаний: АКТИВИРОВАН")
    
    token, chat_id = get_bot_credentials()
    if token and chat_id:
        print(f"✅ Telegram-уведомления: ПОДКЛЮЧЕНЫ (Chat ID: {chat_id})")
    else:
        print("⚠️ Telegram-токены не настроены в .env")
    print("=" * 65)

def handle_excel_export():
    """Генерирует Excel файл и отправляет пользователю в Telegram."""
    send_telegram_message("📊 <i>Формирую Excel-таблицу со всеми сохраненными вакансиями...</i>")
    try:
        file_path = create_excel_export()
        stats = get_stats()
        caption = (
            f"📑 <b>Ваша сводная таблица вакансий готова!</b>\n\n"
            f"• Всего вакансий в файле: <b>{stats['total']}</b>\n"
            f"• Активных откликов: <b>{stats.get('tracked', 0)}</b>\n"
            f"• Вкладки: <i>📋 Все вакансии, 🔴 HeadHunter, 🔵 Хабр Карьера, 📱 Telegram</i>\n"
            f"• Все статусы отклика подсвечены цветом, ссылки кликабельны."
        )
        send_telegram_document(file_path, caption=caption)
    except Exception as e:
        send_telegram_message(f"❌ Ошибка создания Excel: {e}")

def run_single_scan(limit: int = BATCH_LIMIT, verbose: bool = True) -> int:
    """Выполняет один цикл сканирования с учетом фильтров стека, зарплаты и черного списка компаний."""
    with SCAN_LOCK:
        active_filter = get_user_filter()
        active_salary = get_salary_filter()
        now_dt = datetime.now()
        now_str = now_dt.strftime("%H:%M:%S")
        
        is_night = (now_dt.hour >= 23 or now_dt.hour < 9) and is_night_mode_enabled()
        
        if verbose:
            print(f"\n[{now_str}] 🔎 Поиск (стек: {active_filter}, З/П: {active_salary}, ночь: {is_night})...")

        all_raw_vacancies = []

        try:
            hh_habr_items = get_hh_and_habr(stack_filter=active_filter, salary_filter=active_salary)
            all_raw_vacancies.extend(hh_habr_items)
            if verbose:
                print(f"[{now_str}] 📦 HeadHunter + Хабр: {len(hh_habr_items)} предложений")
        except Exception as e:
            print(f"Ошибка сбора HH/Хабр: {e}")

        try:
            avito_items = get_all_avito_vacancies()
            all_raw_vacancies.extend(avito_items)
            if verbose:
                print(f"[{now_str}] 📦 Авито Работа: {len(avito_items)} предложений")
        except Exception as e:
            print(f"Ошибка сбора Авито: {e}")

        try:
            tg_items = get_all_telegram_vacancies()
            all_raw_vacancies.extend(tg_items)
            if verbose:
                print(f"[{now_str}] 📦 Telegram-каналы: {len(tg_items)} предложений")
        except Exception as e:
            print(f"Ошибка сбора Telegram: {e}")

        new_count = 0
        token, chat_id = get_bot_credentials()

        for v in all_raw_vacancies:
            if new_count >= limit:
                break
                
            if not is_salary_matching(v.get('salary', ''), active_salary):
                continue
                
            if not is_vacancy_seen(v['id'], v.get('company', ''), v.get('title', '')):
                if save_vacancy(v):
                    new_count += 1
                    
                    if (not v.get('requirements') or len(v.get('requirements')) < 10) and v['id'].startswith('hh_'):
                        raw_num = v['id'].replace('hh_', '')
                        v['requirements'] = fetch_hh_full_description(raw_num)
                    
                    print(f"\n🔥 [НОВАЯ ВАКАНСИЯ #{new_count}/{limit}] [{v.get('source', 'Сайт')}]")
                    print(f"💼 {v.get('title')} | 🏢 {v.get('company')}")
                    print(f"💵 {v.get('salary')} | 📍 {v.get('experience')}")
                    print(f"🔗 {v.get('url')}")
                    
                    send_vacancy_card(v, disable_notification=is_night, chat_id=chat_id)
                    
                    if token and chat_id:
                        time.sleep(1.0)

        stats = get_stats()
        print(f"\n[{now_str}] 🏁 Выдано вакансий: {new_count}. Всего в базе: {stats['total']}")
        
        cur_int_str = format_interval_text(get_interval_minutes())
        if new_count > 0 and token and chat_id:
            send_batch_footer(new_count, active_filter=active_filter, active_salary=active_salary)
        elif new_count == 0 and token and chat_id and verbose:
            from database import get_top_matching_vacancies
            matching_vacs = get_top_matching_vacancies(active_filter, active_salary, limit=5)
            if matching_vacs:
                send_telegram_message(
                    f"✨ <b>В базе найдено {len(matching_vacs)} подходящих вакансий по фильтрам (Стек: {active_filter}, З/П: {active_salary}):</b>",
                    chat_id=chat_id,
                    disable_notification=is_night
                )
                for vac in matching_vacs:
                    send_vacancy_card(vac, disable_notification=is_night, chat_id=chat_id)
                    time.sleep(0.8)
                send_batch_footer(len(matching_vacs), active_filter=active_filter, active_salary=active_salary)
            else:
                send_telegram_message(
                    f"🔎 <i>Новых вакансий по вашим фильтрам (Стек: {active_filter}, З/П: {active_salary}) за этот цикл не появилось. Все найденные предложения сохранены в базе и Excel! Следующая автопроверка через {cur_int_str}.</i>",
                    disable_notification=is_night,
                    chat_id=chat_id
                )
            
        return new_count

def check_daily_digest_trigger():
    """Проверяет необходимость отправки вечернего дайджеста в 20:00."""
    now = datetime.now()
    if now.hour == 20 and is_daily_digest_enabled():
        today_str = now.strftime("%Y-%m-%d")
        last_sent = get_setting('last_digest_date', '')
        if last_sent != today_str:
            set_setting('last_digest_date', today_str)
            print(f"[{now.strftime('%H:%M:%S')}] 📈 Отправляю вечерний дайджест...")
            stats = get_stats()
            top_vacs = get_top_vacancies_today(3)
            send_evening_digest_message(stats, top_vacs)

def get_main_menu_data():
    active_filter = get_user_filter()
    active_salary = get_salary_filter()
    cur_interval_str = format_interval_text(get_interval_minutes())
    
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
    
    cur_f = filter_names.get(active_filter, active_filter)
    cur_s = salary_names.get(active_salary, active_salary)

    text = (
        "👋 <b>Главное меню Job Radar:</b>\n\n"
        f"🎯 Стек: <b>{cur_f}</b>\n"
        f"💵 Зарплата: <b>{cur_s}</b>\n"
        f"⏱️ Интервал поиска: <b>{cur_interval_str}</b>\n"
        f"🌙 Ночной режим: <b>{'Вкл' if is_night_mode_enabled() else 'Выкл'}</b>\n\n"
        "Выберите нужное действие 👇"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "🚀 Открыть Radar Mini App", "web_app": {"url": MINI_APP_HTTPS_URL}}],
            [{"text": "🔍 Найти 10 свежих вакансий", "callback_data": "fetch_more"}],
            [
                {"text": "⭐ Мое избранное", "callback_data": "view_favorites"},
                {"text": "📌 Мои отклики", "callback_data": "menu_tracker"}
            ],
            [
                {"text": "🎨 Мой сайт-портфолио", "callback_data": "menu_portfolio"},
                {"text": "📊 Аналитика рынка", "callback_data": "menu_market"}
            ],
            [
                {"text": "📥 Скачать Excel", "callback_data": "export_excel"},
                {"text": "🎯 Сменить стек", "callback_data": "menu_filters"}
            ],
            [
                {"text": "💵 Фильтр З/П", "callback_data": "menu_salary"},
                {"text": "⚙️ Настройки и Режимы", "callback_data": "menu_modes"}
            ]
        ]
    }
    return text, markup

def send_main_menu(message_id: int = None, chat_id: str = None):
    text, markup = get_main_menu_data()
    if message_id:
        edit_telegram_message(message_id, text, markup, chat_id=chat_id)
    else:
        send_telegram_message(text, reply_markup=markup, chat_id=chat_id)

def restore_card_markup(vac_id: str, message_id: int):
    vac = get_vacancy_by_id(vac_id)
    if not vac or not message_id:
        return
    source = vac.get('source', 'Сайт')
    url = vac.get('url', 'https://hh.ru')
    status = vac.get('status', 'Не откликался')
    status_label = format_status_icon(status)
    
    markup = {
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
    edit_telegram_reply_markup(message_id, markup)

def telegram_polling_worker():
    """Фоновый поток для мгновенной обработки нажатий кнопок и команд в Telegram."""
    token, chat_id = get_bot_credentials()
    if not token:
        token = "8863351782:AAEeLRftLdK_dw-OxtuZtmo9zfwAqd5MeZo"
        
    last_update_id = 0
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    answer_url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
    
    print("🤖 Интерактивный слушатель Telegram запущен на максимальной скорости...")
    
    while True:
        try:
            params = {"offset": last_update_id + 1, "timeout": 2}
            resp = HTTP_SESSION.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get('result', []):
                    last_update_id = update['update_id']
                    
                    # 1. Обработка Inline-кнопок
                    if 'callback_query' in update:
                        cb = update['callback_query']
                        cb_id = cb['id']
                        data_val = cb.get('data', '')
                        msg = cb.get('message', {})
                        msg_id = msg.get('message_id')
                        cb_chat_id = msg.get('chat', {}).get('id')
                        
                        def ans(text=""):
                            try:
                                HTTP_SESSION.post(answer_url, json={"callback_query_id": cb_id, "text": text}, timeout=3)
                            except Exception:
                                pass

                        # --- ПОИСК ---
                        if data_val == 'fetch_more':
                            ans("Ищу следующие 10 вакансий...")
                            send_telegram_message("⏳ <b>Ищу следующую порцию из 10 свежих вакансий...</b>", chat_id=cb_chat_id)
                            threading.Thread(target=run_single_scan, args=(BATCH_LIMIT, True), daemon=True).start()
                            
                        # --- EXCEL ---
                        elif data_val == 'export_excel':
                            ans("Генерирую Excel файл...")
                            threading.Thread(target=handle_excel_export, daemon=True).start()
                            
                        # --- ТРЕКЕР СТАТУСОВ ---
                        elif data_val == 'menu_tracker':
                            ans()
                            send_applications_tracker(get_tracked_vacancies(), message_id=msg_id)
                            
                        elif data_val.startswith('status_menu_'):
                            vac_id = data_val.replace('status_menu_', '')
                            vac = get_vacancy_by_id(vac_id)
                            cur_st = vac.get('status', 'Не откликался') if vac else 'Не откликался'
                            ans()
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
                                        {"text": "⚪ Сброс", "callback_data": f"setstat_{vac_id}_reset"}
                                    ],
                                    [{"text": "◀️ Назад к карточке", "callback_data": f"restore_card_{vac_id}"}]
                                ]
                            }
                            edit_telegram_reply_markup(msg_id, markup, chat_id=cb_chat_id)
                            
                        elif data_val.startswith('setstat_'):
                            parts = data_val.split('_')
                            vac_id = "_".join(parts[1:-1])
                            code = parts[-1]
                            
                            status_map = {
                                'applied': 'Откликнулся',
                                'test': 'Тестовое задание',
                                'interview': 'Собеседование',
                                'offer': 'Оффер',
                                'rejected': 'Отказ',
                                'reset': 'Не откликался'
                            }
                            new_status = status_map.get(code, 'Не откликался')
                            update_vacancy_status(vac_id, new_status)
                            ans(f"Статус: {new_status}")
                            restore_card_markup(vac_id, msg_id)
                            
                        elif data_val.startswith('restore_card_'):
                            vac_id = data_val.replace('restore_card_', '')
                            ans()
                            restore_card_markup(vac_id, msg_id)
                            
                        # --- ЧЕРНЫЙ СПИСОК КОМПАНИЙ ---
                        elif data_val.startswith('bl_comp_'):
                            vac_id = data_val.replace('bl_comp_', '')
                            vac = get_vacancy_by_id(vac_id)
                            if vac and vac.get('company'):
                                comp_name = vac.get('company')
                                add_blacklisted_company(comp_name)
                                ans(f"🚫 {comp_name[:20]} в черном списке!")
                                try:
                                    orig_markup = msg.get('reply_markup', {}).get('inline_keyboard', [])
                                    if orig_markup and len(orig_markup) >= 2:
                                        row1 = orig_markup[0]
                                        btn_status = orig_markup[1][0]
                                        new_markup = {
                                            "inline_keyboard": [
                                                row1,
                                                [btn_status, {"text": "🚫 Скрыто", "callback_data": "already_bl"}]
                                            ]
                                        }
                                        edit_telegram_reply_markup(msg_id, new_markup, chat_id=cb_chat_id)
                                except Exception:
                                    pass
                            else:
                                ans("Компания не найдена")
                                
                        elif data_val == 'already_bl':
                            ans("Эта компания уже в черном списке 🚫")
                            
                        elif data_val == 'menu_blacklist':
                            ans()
                            send_blacklist_menu(get_blacklisted_companies(), message_id=msg_id)
                            
                        elif data_val.startswith('unblock_comp_'):
                            idx_str = data_val.replace('unblock_comp_', '')
                            try:
                                idx = int(idx_str)
                                bl_list = get_blacklisted_companies()
                                if 0 <= idx < len(bl_list):
                                    target_c = bl_list[idx]
                                    remove_blacklisted_company(target_c)
                                    ans(f"✅ {target_c[:20]} разблокирована")
                                    send_blacklist_menu(get_blacklisted_companies(), message_id=msg_id)
                            except Exception:
                                pass
                            
                        # --- ИЗБРАННОЕ ---
                        elif data_val.startswith('fav_'):
                            vac_id = data_val.replace('fav_', '')
                            added = add_favorite_by_id(vac_id)
                            ans("⭐ Добавлено в Избранное!" if added else "Уже в Избранном")
                            
                            if msg_id:
                                try:
                                    orig_markup = msg.get('reply_markup', {}).get('inline_keyboard', [])
                                    if orig_markup and len(orig_markup[0]) >= 2:
                                        url_btn = orig_markup[0][0]
                                        row2 = orig_markup[1] if len(orig_markup) > 1 else []
                                        new_markup = {
                                            "inline_keyboard": [
                                                [url_btn, {"text": "✅ В избранном", "callback_data": f"fav_done"}],
                                                row2
                                            ]
                                        }
                                        edit_telegram_reply_markup(msg_id, new_markup, chat_id=cb_chat_id)
                                except Exception:
                                    pass
                                    
                        elif data_val == 'fav_done':
                            ans("Эта вакансия уже в вашем Избранном ⭐")
                                
                        elif data_val.startswith('del_fav_'):
                            vac_id = data_val.replace('del_fav_', '')
                            remove_favorite_by_id(vac_id)
                            ans("❌ Удалено")
                            send_favorites_list(get_favorites(), message_id=msg_id, chat_id=cb_chat_id)
                            
                        elif data_val == 'view_favorites':
                            ans()
                            send_favorites_list(get_favorites(), message_id=msg_id, chat_id=cb_chat_id)
                            
                        # --- МЕНЮ СТЕКА ---
                        elif data_val == 'menu_filters':
                            ans()
                            send_filters_menu(get_user_filter(), message_id=msg_id, chat_id=cb_chat_id)
                            
                        elif data_val.startswith('set_filter_'):
                            new_filter = data_val.replace('set_filter_', '')
                            set_user_filter(new_filter)
                            ans("Стек обновлен")
                            send_filters_menu(new_filter, message_id=msg_id, chat_id=cb_chat_id)
                            
                        # --- МЕНЮ ЗАРПЛАТЫ ---
                        elif data_val == 'menu_salary':
                            ans()
                            send_salary_menu(get_salary_filter(), message_id=msg_id, chat_id=cb_chat_id)
                            
                        elif data_val.startswith('set_sal_'):
                            new_sal = data_val.replace('set_sal_', '')
                            set_salary_filter(new_sal)
                            ans("Зарплата обновлена")
                            send_salary_menu(new_sal, message_id=msg_id, chat_id=cb_chat_id)
                            
                        # --- МЕНЮ ИНТЕРВАЛА ВРЕМЕНИ ---
                        elif data_val == 'menu_interval':
                            ans()
                            send_interval_menu(get_interval_minutes(), message_id=msg_id, chat_id=cb_chat_id)
                            
                        elif data_val.startswith('set_interval_'):
                            try:
                                m = int(data_val.replace('set_interval_', ''))
                                set_interval_minutes(m)
                                ans(f"Интервал: {format_interval_text(m)}")
                                send_interval_menu(m, message_id=msg_id, chat_id=cb_chat_id)
                            except Exception:
                                pass
                            
                        # --- МЕНЮ РЕЖИМОВ ---
                        elif data_val == 'menu_modes':
                            ans()
                            send_modes_menu(
                                get_setting('night_mode', 'on'),
                                get_setting('daily_digest', 'on'),
                                get_interval_minutes(),
                                message_id=msg_id,
                                chat_id=cb_chat_id
                            )
                            
                        elif data_val == 'toggle_night_mode':
                            cur = get_setting('night_mode', 'on')
                            new_val = 'off' if cur == 'on' else 'on'
                            set_setting('night_mode', new_val)
                            ans(f"Ночной режим: {'ВКЛ' if new_val == 'on' else 'ВЫКЛ'}")
                            send_modes_menu(new_val, get_setting('daily_digest', 'on'), get_interval_minutes(), message_id=msg_id, chat_id=cb_chat_id)
                            
                        elif data_val == 'toggle_daily_digest':
                            cur = get_setting('daily_digest', 'on')
                            new_val = 'off' if cur == 'on' else 'on'
                            set_setting('daily_digest', new_val)
                            ans(f"Дайджест: {'ВКЛ' if new_val == 'on' else 'ВЫКЛ'}")
                            send_modes_menu(get_setting('night_mode', 'on'), new_val, get_interval_minutes(), message_id=msg_id, chat_id=cb_chat_id)
                            
                        elif data_val == 'send_digest_now':
                            ans("Отправляю дайджест...")
                            stats = get_stats()
                            top_vacs = get_top_vacancies_today(3)
                            send_evening_digest_message(stats, top_vacs)
                            
                        # --- MINI APP ---
                        elif data_val == 'menu_mini_app':
                            ans()
                            send_mini_app_message(message_id=msg_id, chat_id=cb_chat_id)
                            
                        # --- АНАЛИТИКА РЫНКА ---
                        elif data_val == 'menu_market':
                            ans()
                            send_market_analytics_message(message_id=msg_id, chat_id=cb_chat_id)
                            
                        # --- САЙТ-ПОРТФОЛИО ---
                        elif data_val == 'menu_portfolio':
                            ans()
                            send_portfolio_builder_message(message_id=msg_id, chat_id=cb_chat_id)
                            
                        # --- ГЛАВНОЕ МЕНЮ ---
                        elif data_val == 'menu_main':
                            ans()
                            send_main_menu(message_id=msg_id, chat_id=cb_chat_id)
                            
                    # 2. Обработка текстовых команд
                    elif 'message' in update:
                        msg = update['message']
                        text = msg.get('text', '').strip().lower()
                        user_chat_id = msg.get('chat', {}).get('id')
                        print(f"📥 Получено сообщение в Telegram: '{text}' (chat_id: {user_chat_id})")
                        
                        if text in ['/start', '/help', '/menu', 'menu', 'меню', 'старт', 'привет', 'главная']:
                            send_main_menu(chat_id=user_chat_id)
                            
                        elif text in ['/app', '/tinder', 'приложение', 'свайпы', 'tma', 'миниапп']:
                            send_mini_app_message()
                            
                        elif text in ['/portfolio', '/site', 'портфолио', 'сайт', 'резюме']:
                            send_portfolio_builder_message()
                            
                        elif text in ['/more', '/search', 'еще', 'ещё', 'поискать еще']:
                            send_telegram_message("⏳ <b>Запускаю поиск еще 10 вакансий...</b>", chat_id=user_chat_id)
                            threading.Thread(target=run_single_scan, args=(BATCH_LIMIT, True), daemon=True).start()
                            
                        elif text in ['/excel', '/export', 'эксель', 'файл', 'скачать эксель', 'таблица']:
                            threading.Thread(target=handle_excel_export, daemon=True).start()
                            
                        elif text in ['/market', 'рынок', 'аналитика', 'зарплаты', 'аналитика рынка']:
                            send_market_analytics_message()
                            
                        elif text in ['/tracker', '/status', 'отклики', 'трекер']:
                            send_applications_tracker(get_tracked_vacancies())
                            
                        elif text in ['/blacklist', '/bl', 'чс', 'черный список']:
                            send_blacklist_menu(get_blacklisted_companies())
                            
                        elif text in ['/fav', '/favorites', 'избранное', 'мои вакансии']:
                            send_favorites_list(get_favorites())
                            
                        elif text in ['/filter', '/filters', 'фильтр', 'стек']:
                            send_filters_menu(get_user_filter())
                            
                        elif text in ['/salary', 'зарплата', 'зп']:
                            send_salary_menu(get_salary_filter())
                            
                        elif text in ['/interval', '/time', 'интервал', 'время']:
                            send_interval_menu(get_interval_minutes())
                            
                        elif text in ['/modes', 'режимы', 'настройки']:
                            send_modes_menu(get_setting('night_mode', 'on'), get_setting('daily_digest', 'on'), get_interval_minutes())
                            
                        elif text in ['/digest', 'дайджест']:
                            stats = get_stats()
                            top_vacs = get_top_vacancies_today(3)
                            send_evening_digest_message(stats, top_vacs)
                            
                        elif text in ['/stats', 'статистика']:
                            stats = get_stats()
                            cur_int_str = format_interval_text(get_interval_minutes())
                            send_telegram_message(
                                f"📊 <b>Статистика базы:</b>\n"
                                f"• Всего отслежено вакансий: <b>{stats['total']}</b>\n"
                                f"• В избранном: <b>{stats.get('favorites', 0)}</b>\n"
                                f"• Активных откликов: <b>{stats.get('tracked', 0)}</b>\n"
                                f"• Компаний в черном списке: <b>{stats.get('blacklisted', 0)}</b>\n"
                                f"• Активный стек: <b>{stats.get('filter_stack', 'all')}</b>\n"
                                f"• Фильтр З/П: <b>{stats.get('filter_salary', 'salary_any')}</b>\n"
                                f"• Интервал поиска: <b>{cur_int_str}</b>",
                                chat_id=user_chat_id
                            )
                        else:
                            # На любой другой текст показываем главное меню с кнопками
                            send_main_menu(chat_id=user_chat_id)
                            
            time.sleep(0.1)
        except Exception as e:
            time.sleep(1)

def main_loop():
    init_db()
    print_banner()

    if '--once' in sys.argv:
        run_single_scan(limit=BATCH_LIMIT, verbose=True)
        return

    polling_thread = threading.Thread(target=telegram_polling_worker, daemon=True)
    polling_thread.start()

    print(f"⏳ Скрипт запущен в режиме динамического мониторинга")
    print("   Нажмите Ctrl+C для остановки.\n")

    last_scan_time = time.time()
    run_single_scan(limit=BATCH_LIMIT, verbose=True)

    while True:
        try:
            check_daily_digest_trigger()
            
            interval_min = get_interval_minutes()
            interval_sec = max(60, interval_min * 60)
            
            if time.time() - last_scan_time >= interval_sec:
                run_single_scan(limit=BATCH_LIMIT, verbose=True)
                last_scan_time = time.time()
                
            time.sleep(10)
        except KeyboardInterrupt:
            print("\n🛑 Мониторинг остановлен пользователем.")
            break
        except Exception as e:
            print(f"\n❌ Ошибка цикла: {e}")
            time.sleep(10)

if __name__ == '__main__':
    main_loop()
