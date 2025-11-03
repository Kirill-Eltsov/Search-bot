from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # pyright: ignore
from telegram.ext import ContextTypes
from handlers.auth import WAITING_PHONE, WAITING_VERIFICATION, WAITING_SEARCH, handle_phone_number
from handlers.menu import show_main_menu
from search_service import parse_query, search_products, format_search_results


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = context.user_data.get('state')

    if context.user_data.get('verified', False):
        if state == WAITING_SEARCH:
            query_text = update.message.text.strip()
            parsed = parse_query(query_text)
            if parsed.kind == "unknown":
                await update.message.reply_text("Неверный формат запроса. Примеры: 8008M, 177814M=55, SPA2000, B85")
                return
            rows = search_products(query_text)
            await update.message.reply_text(format_search_results(rows))
            # Показать кнопки: Меню | Продолжить поиск
            controls = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 Меню", callback_data="menu_back"),
                    InlineKeyboardButton("🔎 Продолжить поиск", callback_data="search_continue"),
                ]
            ])
            await update.message.reply_text("Выберите действие:", reply_markup=controls)
            # Состояние сбрасывать не будем — новую команду зададим через кнопку
            return
        await show_main_menu(update, context)
        return

    if state == WAITING_PHONE:
        await handle_phone_number(update, context)
        return

    await update.message.reply_text("Для начала работы используйте команду /start")


