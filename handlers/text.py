from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # pyright: ignore
from telegram.ext import ContextTypes
from handlers.auth import WAITING_PHONE, WAITING_VERIFICATION, WAITING_SEARCH, handle_phone_number
from handlers.menu import show_main_menu
from search_service import parse_query, search_products, format_search_results, search_products_structured
from ai_service import ai_extract_parameters
import re

try:
    from config import MANAGER_CONTACTS as MANAGER_CONTACTS_TEXT
except ImportError:
    MANAGER_CONTACTS_TEXT = "Контакты менеджера не настроены."


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')
    verified = context.user_data.get('verified', False)
    # print(f"[DEBUG] handle_text_message вызван: verified={verified}, state={state}, WAITING_SEARCH={WAITING_SEARCH}")

    if verified:
        if state == WAITING_SEARCH:
            query_text = update.message.text.strip()
            # print(f"[DEBUG] Получен запрос: {query_text}")
            parsed = parse_query(query_text)
            # print(f"[DEBUG] Парсер вернул: kind={parsed.kind}, length={parsed.length_mm}, profile={parsed.profile}, width={parsed.width_mm}")
            if parsed.kind == "unknown":
                # print(f"[DEBUG] Запрос распознан как unknown, проверяю fallback regex")
                # Попытка вычленить валидный токен из свободного текста
                # Ищем более полные паттерны: 8008M, SPA2000, SPA 2000, B85, 177814M=55
                # Убираем пробелы для поиска токена
                text_no_spaces = query_text.upper().replace(" ", "")
                m = re.search(r"(\d+[A-Z0-9]+(?:=\d+)?|[A-Z]+\d+(?:=\d+)?)", text_no_spaces)
                if m:
                    cleaned = m.group(1)
                    # print(f"[DEBUG] Regex нашел токен: {cleaned}")
                    reparsed = parse_query(cleaned)
                    # print(f"[DEBUG] Перепарсинг токена вернул: kind={reparsed.kind}, length={reparsed.length_mm}, profile={reparsed.profile}")
                    # Проверяем, что токен действительно валидный и содержит профиль (не цифру) или специфичный формат
                    # Профиль должен быть буквами (8M, 14M, SPA, B и т.д.), а не цифрой
                    has_valid_profile = reparsed.profile and not reparsed.profile.isdigit() and len(reparsed.profile) > 0
                    if reparsed.kind != "unknown" and (has_valid_profile or "=" in cleaned):
                        # print(f"[DEBUG] Токен валидный и содержит профиль/ширину, выполняю поиск напрямую без ИИ")
                        rows = search_products(cleaned)
                        controls = InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("📋 Меню", callback_data="menu_back"),
                                InlineKeyboardButton("🔎 Продолжить поиск", callback_data="search_continue"),
                            ]
                        ])
                        await update.message.reply_text(format_search_results(rows), reply_markup=controls)
                        return
                    # else: токен найден, но неполный (нет профиля), вызываю ИИ
                # else: regex не нашел валидный токен, вызываю ИИ
                # print(f"[AI] Вызываю ИИ для запроса: {query_text}")
                ai = ai_extract_parameters(query_text)
                # print(f"[AI] Результат ИИ: {ai}")
                if ai and ai.get("kind") and (ai.get("profile") or ai.get("length_mm")):
                    # Логирование 
                    # print(f"[AI] Извлечено: kind={ai.get('kind')}, length={ai.get('length_mm')}, profile={ai.get('profile')}, width={ai.get('width_mm')}")
                    rows = search_products_structured(
                        kind=ai.get("kind") or "unknown",
                        length_mm=ai.get("length_mm"),
                        profile=(ai.get("profile") or None),
                        width_mm=ai.get("width_mm"),
                        original_text=query_text,
                    )
                    # print(f"[AI] Найдено результатов: {len(rows)}")
                    if not rows:
                        # Если товар не найден после поиска с ИИ, выдаем контакты менеджера
                        controls = InlineKeyboardMarkup([
                            [
                                InlineKeyboardButton("📋 Меню", callback_data="menu_back"),
                                InlineKeyboardButton("🔎 Продолжить поиск", callback_data="search_continue"),
                            ]
                        ])
                        await update.message.reply_text(MANAGER_CONTACTS_TEXT, reply_markup=controls)
                        return
                    controls = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("📋 Меню", callback_data="menu_back"),
                            InlineKeyboardButton("🔎 Продолжить поиск", callback_data="search_continue"),
                        ]
                    ])
                    await update.message.reply_text(format_search_results(rows), reply_markup=controls)
                    return
                else:
                    # print(f"[AI] ИИ не вернул валидные параметры или вернул None")
                    await update.message.reply_text(
                        "Неверный формат запроса. Примеры: 8008M, 177814M=55, SPA2000, B85\n"
                        "Попробуйте изменить запрос в соответствии с правилами или напишите 'оператор', и мы вам поможем"
                    )
                    return
            else:
                # print(f"[DEBUG] Парсер распознал запрос как валидный (kind={parsed.kind}), выполняю поиск напрямую")
                rows = search_products(query_text)
                # print(f"[DEBUG] Найдено результатов: {len(rows)}")
            controls = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 Меню", callback_data="menu_back"),
                    InlineKeyboardButton("🔎 Продолжить поиск", callback_data="search_continue"),
                ]
            ])
            await update.message.reply_text(format_search_results(rows), reply_markup=controls)
            return
        await show_main_menu(update, context)
        return

    if state == WAITING_PHONE:
        await handle_phone_number(update, context)
        return

    await update.message.reply_text("Для начала работы используйте команду /start")


