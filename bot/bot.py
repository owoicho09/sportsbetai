# bot/bot.py

import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

from bot.handlers.start import start_handler
from bot.handlers.leagues import leagues_handler
from bot.handlers.fixtures import (
    fixtures_handler,
    fixture_detail_handler,
    multi_select_handler,
    toggle_fixture_handler,
)
from bot.handlers.insight import (
    insight_handler,
    preview_handler,
    multi_insight_handler,
)
from bot.handlers.subscription import (
    subscription_handler,
    subscribe_handler,
    grant_handler,
    revoke_handler,
)
from bot.messages import WELCOME_MESSAGE, HOW_IT_WORKS_MESSAGE
from bot.keyboards import main_menu_keyboard, back_to_menu_keyboard

load_dotenv()
logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data  = query.data

    # ── Main Menu ────────────────────────────────────────────
    if data == "main_menu":
        await query.answer()
        await query.edit_message_text(
            WELCOME_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_keyboard(),
        )

    # ── League / Fixture flow ────────────────────────────────
    elif data == "get_prediction":
        await leagues_handler(update, context)

    elif data.startswith("league_"):
        league_id = data.replace("league_", "")
        context.user_data["current_league_id"] = league_id
        await fixtures_handler(update, context, league_id=league_id, page=0)

    elif data.startswith("fixtures_"):
        parts = data.split("_")
        if len(parts) == 3:
            league_id = parts[1]
            try:
                page = int(parts[2])
            except ValueError:
                page = 0
            context.user_data["current_league_id"] = league_id
            await fixtures_handler(update, context, league_id=league_id, page=page)

    elif data.startswith("fixture_"):
        fixture_id = data.replace("fixture_", "")
        league_id  = context.user_data.get("current_league_id", "0")
        context.user_data["current_fixture_id"] = fixture_id
        await fixture_detail_handler(update, context, fixture_id=fixture_id, league_id=league_id)

    # ── Multi-select flow (Premium) ──────────────────────────
    elif data.startswith("multi_select_"):
        # multi_select_{league_id}_{page}
        parts     = data.split("_")
        league_id = parts[2]
        page      = int(parts[3]) if len(parts) > 3 else 0
        # Clear any previous selection when entering multi-select
        context.user_data["selected_fixture_ids"] = []
        await multi_select_handler(update, context, league_id=league_id, page=page)

    elif data.startswith("toggle_"):
        fixture_id = data.replace("toggle_", "")
        await toggle_fixture_handler(update, context, fixture_id=fixture_id)

    elif data.startswith("run_multi_"):
        league_id = data.replace("run_multi_", "")
        await multi_insight_handler(update, context, league_id=league_id)

    # ── Predictions ──────────────────────────────────────────
    elif data.startswith("preview_"):
        fixture_id = data.replace("preview_", "")
        await preview_handler(update, context, fixture_id=fixture_id)

    elif data.startswith("insight_"):
        fixture_id = data.replace("insight_", "")
        league_id  = context.user_data.get("current_league_id", "0")
        await insight_handler(update, context, fixture_id=fixture_id, league_id=league_id)

    # ── Subscription ─────────────────────────────────────────
    elif data == "subscription":
        await subscription_handler(update, context)

    elif data in ["subscribe", "pay_now"]:
        await subscribe_handler(update, context)

    # ── How it works ─────────────────────────────────────────
    elif data == "how_it_works":
        await query.answer()
        await query.edit_message_text(
            HOW_IT_WORKS_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard(),
        )

    else:
        await query.answer("Unknown action.", show_alert=False)


async def league_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Single entry point for all callback queries."""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data.startswith("league_"):
        league_id = data.replace("league_", "")
        context.user_data["current_league_id"] = league_id

    await callback_router(update, context)


def run_bot():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("grant", grant_handler))
    app.add_handler(CommandHandler("revoke", revoke_handler))
    app.add_handler(CallbackQueryHandler(league_router))

    print("🤖 SportsBet AI Bot is running...")
    #app.run_polling(drop_pending_updates=True)
    return app

