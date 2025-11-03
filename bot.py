import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup  # pyright: ignore[reportMissingImports]
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters  # pyright: ignore[reportMissingImports]
from handlers.menu import handle_menu_callback as _menu_cb_h, show_main_menu as _show_menu_h, show_main_menu_edit as _show_menu_edit_h  # pyright: ignore[reportMissingImports]
from handlers.operator import operator as _operator_h  # pyright: ignore[reportMissingImports]
from handlers.auth import start as _start_h, handle_phone_number as _handle_phone_h, handle_verification_callback as _verify_cb_h  # pyright: ignore[reportMissingImports]
from handlers.text import handle_text_message as text_handler  # pyright: ignore[reportMissingImports]


try:
    from config import BOT_TOKEN, MANAGER_CONTACTS
except ImportError:
    raise ImportError(
        "Не найден файл config.py. Создайте файл config.py с переменными BOT_TOKEN и MANAGER_CONTACTS.\n"
        "Скопируйте config.py.example и заполните реальными данными."
    )

WAITING_PHONE, WAITING_VERIFICATION, WAITING_SEARCH = range(3)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _start_h(update, context)


async def handle_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ввода номера телефона."""
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
    await _verify_cb_h(update, context)


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _menu_cb_h(update, context)


async def operator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /operator - вывод контактов менеджера."""
    await _operator_h(update, context)


async def show_main_menu_edit(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Редактирует сообщение, показывая главное меню."""
    await _show_menu_edit_h(query, context)


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает главное меню после успешной верификации."""
    await _show_menu_h(update, context)



def main() -> None:
    """Запускает бота."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", _start_h))
    application.add_handler(CommandHandler("operator", operator))
    
    application.add_handler(CallbackQueryHandler(handle_verification_callback, pattern="^verified_"))
    
    application.add_handler(CallbackQueryHandler(_menu_cb_h, pattern="^menu_"))
    application.add_handler(CallbackQueryHandler(_menu_cb_h, pattern="^search_"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    print("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
