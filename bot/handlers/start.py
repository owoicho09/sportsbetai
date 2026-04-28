# bot/handlers/start.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.messages import WELCOME_MESSAGE
from bot.keyboards import main_menu_keyboard
from bot.middleware import register_user
from bot.handlers.emailer import send_new_user_email
import asyncio

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Returns (db_user, created) — only email if brand new user
    db_user, created = await register_user(user)

    if created:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            None,
            send_new_user_email,
            user.id,
            user.username or "",
            user.first_name or ""
        )

    await update.message.reply_text(
        WELCOME_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_keyboard()
    )