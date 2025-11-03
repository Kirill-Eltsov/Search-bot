import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # pyright: ignore
from telegram.ext import ContextTypes


# Состояния
WAITING_PHONE, WAITING_VERIFICATION, WAITING_SEARCH = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('verified', False):
        from handlers.menu import show_main_menu
        await show_main_menu(update, context)
        return

    welcome_message = (
        "👋 Добро пожаловать в бота!\n\n"
        "📋 Правила формирования корректного запроса:\n"
        "• Используйте команды для навигации\n"
        "• Следуйте инструкциям бота\n"
        "• Для связи с менеджером используйте команду /operator\n\n"
        "📱 Для продолжения работы необходимо пройти верификацию.\n"
        "Пожалуйста, введите ваш номер телефона в формате:\n"
        "+7XXXXXXXXXX\n\n"
        "Например: +79991234567"
    )
    await update.message.reply_text(welcome_message)
    context.user_data['state'] = WAITING_PHONE


async def handle_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('verified', False):
        from handlers.menu import show_main_menu
        await show_main_menu(update, context)
        return

    phone = update.message.text.strip()
    phone_pattern = r'^\+7\d{10}$'
    if not re.match(phone_pattern, phone):
        await update.message.reply_text(
            "❌ Неверный формат номера телефона!\n\n"
            "Пожалуйста, введите номер в формате:\n"
            "+7XXXXXXXXXX\n\n"
            "Например: +79991234567"
        )
        return

    context.user_data['phone'] = phone
    context.user_data['state'] = WAITING_VERIFICATION

    verification_message = (
        f"✅ Номер телефона принят: {phone}\n\n"
        "🔍 Проверка авторизации пользователя...\n\n"
        "Выберите статус авторизации:"
    )
    keyboard = [
        [InlineKeyboardButton("✅ Пользователь авторизован", callback_data="verified_yes")],
        [InlineKeyboardButton("❌ Пользователь не авторизован", callback_data="verified_no")],
    ]
    await update.message.reply_text(verification_message, reply_markup=InlineKeyboardMarkup(keyboard))


async def handle_verification_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "verified_yes":
        context.user_data['verified'] = True
        context.user_data['state'] = None
        await query.edit_message_text(
            "✅ Верификация успешно завершена!\n\n"
            "🎉 Добро пожаловать! Вы получили доступ к поиску товаров.\n\n"
            "Используйте доступные команды для работы с ботом."
        )
        from handlers.menu import show_main_menu
        await show_main_menu(update, context)
        return

    if query.data == "verified_no":
        context.user_data['verified'] = False
        context.user_data['state'] = None
        from handlers.operator import MANAGER_CONTACTS_TEXT
        await query.edit_message_text(
            "❌ Пользователь не найден в системе.\n\n"
            "📝 Перед использованием услуг бота, вам необходимо зарегистрироваться в системе.\n"
            "Для этого свяжитесь с нашим менеджером:\n"
            f"{MANAGER_CONTACTS_TEXT}"
            "После регистрации вы сможете использовать все возможности бота."
        )
        context.user_data.clear()


