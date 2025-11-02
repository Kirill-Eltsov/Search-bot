import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # pyright: ignore[reportMissingImports]
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters  # pyright: ignore[reportMissingImports]

# Импорт конфигурации
try:
    from config import BOT_TOKEN, MANAGER_CONTACTS
except ImportError:
    raise ImportError(
        "Не найден файл config.py. Создайте файл config.py с переменными BOT_TOKEN и MANAGER_CONTACTS.\n"
        "Скопируйте config.py.example и заполните реальными данными."
    )

# Состояния для ConversationHandler
WAITING_PHONE, WAITING_VERIFICATION = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start - приветствие и запрос номера телефона."""
    user_id = update.effective_user.id
    
    # Проверяем, авторизован ли пользователь
    if context.user_data.get('verified', False):
        await show_main_menu(update, context)
        return
    
    # Приветственное сообщение с правилами
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
    
    # Устанавливаем состояние ожидания номера телефона
    context.user_data['state'] = WAITING_PHONE


async def handle_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода номера телефона."""
    user_id = update.effective_user.id
    phone = update.message.text.strip()
    
    # Проверяем, авторизован ли пользователь
    if context.user_data.get('verified', False):
        await show_main_menu(update, context)
        return
    
    # Проверяем формат номера телефона
    phone_pattern = r'^\+7\d{10}$'
    if not re.match(phone_pattern, phone):
        error_message = (
            "❌ Неверный формат номера телефона!\n\n"
            "Пожалуйста, введите номер в формате:\n"
            "+7XXXXXXXXXX\n\n"
            "Например: +79991234567"
        )
        await update.message.reply_text(error_message)
        return
    
    # Сохраняем номер телефона
    context.user_data['phone'] = phone
    context.user_data['state'] = WAITING_VERIFICATION
    
    # Отправляем запрос на верификацию с кнопками
    verification_message = (
        f"✅ Номер телефона принят: {phone}\n\n"
        "🔍 Проверка авторизации пользователя...\n\n"
        "Выберите статус авторизации:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("✅ Пользователь авторизован", callback_data="verified_yes")
        ],
        [
            InlineKeyboardButton("❌ Пользователь не авторизован", callback_data="verified_no")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(verification_message, reply_markup=reply_markup)


async def handle_verification_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки верификации."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    callback_data = query.data
    
    if callback_data == "verified_yes":
        # Пользователь авторизован
        context.user_data['verified'] = True
        context.user_data['state'] = None
        
        success_message = (
            "✅ Верификация успешно завершена!\n\n"
            "🎉 Добро пожаловать! Вы получили доступ к поиску товаров.\n\n"
            "Используйте доступные команды для работы с ботом."
        )
        
        await query.edit_message_text(success_message)
        await show_main_menu(update, context)
        
    elif callback_data == "verified_no":
        # Пользователь не авторизован
        context.user_data['verified'] = False
        context.user_data['state'] = None
        
        not_verified_message = (
            "❌ Пользователь не найден в системе.\n\n"
            "📝 Перед использованием услуг бота, вам необходимо зарегистрироваться в системе.\n"
            "Для этого свяжитесь с нашим менеджером:\n"
            f"{MANAGER_CONTACTS}"
            "После регистрации вы сможете использовать все возможности бота."
        )
        
        await query.edit_message_text(not_verified_message)
        
        # Завершаем сессию - пользователь не может продолжить работу
        context.user_data.clear()


async def get_back_to_menu_button():
    """Создает кнопку для возврата в главное меню."""
    keyboard = [[InlineKeyboardButton("◀️ Назад в меню", callback_data="menu_back")]]
    return InlineKeyboardMarkup(keyboard)


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки главного меню."""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    
    if callback_data == "menu_back":
        # Возврат в главное меню
        await show_main_menu_edit(query, context)
        return
    
    if callback_data == "menu_operator":
        # Оператор - отправляем контакты
        back_button = await get_back_to_menu_button()
        await query.edit_message_text(MANAGER_CONTACTS, reply_markup=back_button)
        
    elif callback_data == "menu_rules":
        # Правила запроса товаров (заглушка)
        rules_message = (
            "📋 Правила запроса товаров\n\n"
            "Здесь будут правила формирования корректного запроса к боту.\n\n"
            "⚠️ Раздел находится в разработке."
        )
        back_button = await get_back_to_menu_button()
        await query.edit_message_text(rules_message, reply_markup=back_button)
        
    elif callback_data == "menu_request":
        # Поиск товаров (заглушка, кнопка не работает)
        request_message = (
            "🛒 Поиск товаров\n\n"
            "⚠️ Данная функция временно недоступна.\n"
            "Раздел находится в разработке."
        )
        await query.answer(request_message, show_alert=True)
        
    elif callback_data == "menu_commands":
        # Перечень всех команд
        commands_message = (
            "📝 Перечень команд бота:\n\n"
            "/start - Начать работу с ботом\n"
            "/operator - Получить контакты оператора\n\n"
            "Доступные кнопки в главном меню:\n"
            "• 📞 Оператор - контакты для связи с оператором\n"
            "• 📋 Правила запросов - правила формирования запроса\n"
            "• 🛒 Поиск товаров - поиск товаров (в разработке)\n"
            "• 📝 Перечень команд - список всех доступных команд\n"
            "• 👋 Завершить - завершить работу с ботом"
        )
        back_button = await get_back_to_menu_button()
        await query.edit_message_text(commands_message, reply_markup=back_button)
        
    elif callback_data == "menu_finish":
        # Завершить работу
        finish_message = (
            "👋 Спасибо за использование бота!\n\n"
            "До свидания! Если вам понадобится помощь, "
            "вы можете запустить бота снова через команду /start"
        )
        await query.edit_message_text(finish_message)
        # Очищаем данные пользователя
        context.user_data.clear()


async def operator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /operator - вывод контактов менеджера."""
    await update.message.reply_text(MANAGER_CONTACTS)


async def show_main_menu_edit(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Редактирует сообщение, показывая главное меню."""
    menu_message = (
        "🎯 Главное меню\n\n"
        "✅ Вы успешно авторизованы!\n\n"
        "Выберите действие:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📞 Оператор", callback_data="menu_operator"),
            InlineKeyboardButton("📋 Правила запросов", callback_data="menu_rules")
        ],
        [
            InlineKeyboardButton("🛒 Поиск товаров", callback_data="menu_request")
        ],
        [
            InlineKeyboardButton("📝 Перечень команд", callback_data="menu_commands"),
            InlineKeyboardButton("👋 Завершить", callback_data="menu_finish")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu_message, reply_markup=reply_markup)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает главное меню после успешной верификации."""
    menu_message = (
        "🎯 Главное меню\n\n"
        "✅ Вы успешно авторизованы!\n\n"
        "Выберите действие:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("📞 Оператор", callback_data="menu_operator"),
            InlineKeyboardButton("📋 Правила запросов", callback_data="menu_rules")
        ],
        [
            InlineKeyboardButton("🛒 Поиск товаров", callback_data="menu_request")
        ],
        [
            InlineKeyboardButton("📝 Перечень команд", callback_data="menu_commands"),
            InlineKeyboardButton("👋 Завершить", callback_data="menu_finish")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.message.reply_text(menu_message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(menu_message, reply_markup=reply_markup)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений."""
    user_id = update.effective_user.id
    state = context.user_data.get('state')
    
    # Если пользователь авторизован, обрабатываем как обычное сообщение
    if context.user_data.get('verified', False):
        # Показываем главное меню для авторизованных пользователей
        await show_main_menu(update, context)
        return
    
    # Если ожидаем номер телефона
    if state == WAITING_PHONE:
        await handle_phone_number(update, context)
    else:
        # Если пользователь не авторизован, предлагаем начать с /start
        await update.message.reply_text(
            "Для начала работы используйте команду /start"
        )


def main() -> None:
    """Запускает бота."""
    # Создаём приложение и передаём токен бота
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("operator", operator))
    
    # Обработчик кнопок верификации
    application.add_handler(CallbackQueryHandler(handle_verification_callback, pattern="^verified_"))
    
    # Обработчик кнопок главного меню
    application.add_handler(CallbackQueryHandler(handle_menu_callback, pattern="^menu_"))
    
    # Обработчик текстовых сообщений (должен быть последним)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
