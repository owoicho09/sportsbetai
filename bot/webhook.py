# bot/webhook.py

import os
import logging
from dotenv import load_dotenv

load_dotenv()

from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

from bot.handlers.start import start_handler
from bot.handlers.subscription import grant_handler, revoke_handler
from bot.bot import league_router

logger  = logging.getLogger(__name__)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

_app = None


def get_app():
    global _app
    if _app is None:
        _app = (
            ApplicationBuilder()
            .token(BOT_TOKEN)
            .updater(None)          # ← this is the fix — disables the Updater entirely
            .build()
        )
        _app.add_handler(CommandHandler("start", start_handler))
        _app.add_handler(CommandHandler("grant", grant_handler))
        _app.add_handler(CommandHandler("revoke", revoke_handler))
        _app.add_handler(CallbackQueryHandler(league_router))
    return _app


async def process_update(update_data: dict):
    app = get_app()

    if not app.running:
        await app.initialize()
        await app.start()

    update = Update.de_json(update_data, app.bot)
    await app.process_update(update)