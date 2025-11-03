from telegram import Update  # pyright: ignore
from telegram.ext import ContextTypes

try:
    from config import MANAGER_CONTACTS as MANAGER_CONTACTS_TEXT
except ImportError:
    MANAGER_CONTACTS_TEXT = "Контакты менеджера не настроены."


async def operator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(MANAGER_CONTACTS_TEXT)


