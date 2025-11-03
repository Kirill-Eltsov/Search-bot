from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # pyright: ignore
from telegram.ext import ContextTypes
from telegram.constants import ParseMode  # pyright: ignore


async def get_back_to_menu_button():
    return InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в меню", callback_data="menu_back")]])


async def show_main_menu_edit(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    menu_message = (
        "🎯 Главное меню\n\n"
        "✅ Вы успешно авторизованы!\n\n"
        "Выберите действие:"
    )
    keyboard = [
        [InlineKeyboardButton("📞 Оператор", callback_data="menu_operator"),
         InlineKeyboardButton("📋 Правила запросов", callback_data="menu_rules")],
        [InlineKeyboardButton("🛒 Поиск товаров", callback_data="menu_request")],
        [InlineKeyboardButton("📝 Перечень команд", callback_data="menu_commands"),
         InlineKeyboardButton("👋 Завершить", callback_data="menu_finish")],
    ]
    await query.edit_message_text(menu_message, reply_markup=InlineKeyboardMarkup(keyboard))


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    menu_message = (
        "🎯 Главное меню\n\n"
        "✅ Вы успешно авторизованы!\n\n"
        "Выберите действие:"
    )
    keyboard = [
        [InlineKeyboardButton("📞 Оператор", callback_data="menu_operator"),
         InlineKeyboardButton("📋 Правила запросов", callback_data="menu_rules")],
        [InlineKeyboardButton("🛒 Поиск товаров", callback_data="menu_request")],
        [InlineKeyboardButton("📝 Перечень команд", callback_data="menu_commands"),
         InlineKeyboardButton("👋 Завершить", callback_data="menu_finish")],
    ]
    if update.callback_query:
        await update.callback_query.message.reply_text(menu_message, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(menu_message, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "menu_back":
        await show_main_menu_edit(query, context)
        return

    if data == "menu_operator":
        from handlers.operator import MANAGER_CONTACTS_TEXT
        back = await get_back_to_menu_button()
        await query.edit_message_text(MANAGER_CONTACTS_TEXT, reply_markup=back)
        return

    if data == "menu_rules":
        rules_message = (
            "📋 ПРАВИЛА ПОИСКА ТОВАРОВ\n\n"
            "• <b>Синхронные ремни</b>: сначала длина, затем профиль.\n"
            "  Примеры: 8008M, 177814M, 240L, 1700H, 630T5, 1010T10\n\n"
            "• <b>С шириной</b>: без пробелов через '=' (ширина в мм).\n"
            "  Примеры: 8008M=30, 177814M=55, 240L=30\n\n"
            "• <b>Клиновые ремни</b> (штучные): сначала профиль, затем длина (дюйм./расч.).\n"
            "  Примеры: B85, B2000, SPB2000, A79, A800, 8V2000\n\n"
        )
        back = await get_back_to_menu_button()
        await query.edit_message_text(rules_message, reply_markup=back, parse_mode=ParseMode.HTML)
        return

    if data == "menu_request":
        context.user_data['state'] = 2  # WAITING_SEARCH
        await query.edit_message_text("🛒 Поиск товаров\n\nВведите запрос по правилам (например: 8008M, 177814M=55, SPA2000, B85):")
        return

    if data == "menu_commands":
        back = await get_back_to_menu_button()
        await query.edit_message_text(
            "📝 Перечень команд бота:\n\n"
            "/start - Начать работу с ботом\n"
            "/operator - Получить контакты оператора\n\n"
            "Доступные кнопки в главном меню:\n"
            "• 📞 Оператор\n"
            "• 📋 Правила запросов\n"
            "• 🛒 Поиск товаров\n"
            "• 📝 Перечень команд\n"
            "• 👋 Завершить",
            reply_markup=back,
        )
        return

    if data == "menu_finish":
        await query.edit_message_text(
            "👋 Спасибо за использование бота!\n\n"
            "До свидания! Вы можете запустить бота снова через команду /start"
        )
        context.user_data.clear()

    if data == "search_continue":
        # Повторный запрос поиска
        context.user_data['state'] = 2  # WAITING_SEARCH
        await query.edit_message_text(
            "🛒 Поиск товаров\n\nВведите запрос по правилам (например: 8008M, 177814M=55, SPA2000, B85):"
        )


