# telegram/handlers/start.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.messages import WELCOME_MESSAGE
from bot.keyboards import main_menu_keyboard

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard()
    )