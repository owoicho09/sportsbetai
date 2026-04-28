# bot/webhook.py
"""
Telegram Webhook Handler
========================
Receives POST requests from Telegram and processes them
using the same bot application as before — just triggered
by HTTP instead of polling.

This replaces run_polling entirely.
The bot lives inside Django — no separate process needed.
"""

import os
import logging
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from dotenv import load_dotenv
load_dotenv()

import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
)

from bot.handlers.start import start_handler
from bot.handlers.subscription import grant_handler, revoke_handler
from bot.bot import league_router  # reuse your existing router

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Build the application once at module level
# Django loads this once when the server starts — not on every request
_app = None


def get_app():
    global _app
    if _app is None:
        _app = ApplicationBuilder().token(BOT_TOKEN).build()
        _app.add_handler(CommandHandler("start", start_handler))
        _app.add_handler(CommandHandler("grant", grant_handler))
        _app.add_handler(CommandHandler("revoke", revoke_handler))
        _app.add_handler(CallbackQueryHandler(league_router))
    return _app


async def process_update(update_data: dict):
    """
    Parse and process a single Telegram update.
    Called by the Django webhook view on every incoming POST.
    """
    app = get_app()

    # Initialize app if not already done
    if not app.running:
        await app.initialize()

    update = Update.de_json(update_data, app.bot)
    await app.process_update(update)