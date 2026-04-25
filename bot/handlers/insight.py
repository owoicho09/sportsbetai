# bot/handlers/insight.py

import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.messages import (
    GENERATING_MESSAGE,
    TEASER_PAYWALL_MESSAGE,
    insight_message,
    ERROR_TIMEOUT,
    ERROR_CONNECTION,
    ERROR_GENERAL
)
from bot.keyboards import after_insight_keyboard, subscribe_keyboard
from bot.middleware import is_premium

load_dotenv()
API_BASE = os.getenv("API_BASE")


async def insight_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, fixture_id: str, league_id: str = "0"):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    premium = is_premium(user_id)

    print(f"\n[INSIGHT] fixture_id={fixture_id}, league_id={league_id}, user_id={user_id}, premium={premium}")

    if not premium:
        print(f"[INSIGHT] User {user_id} is not premium — showing paywall")
        await query.edit_message_text(
            TEASER_PAYWALL_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscribe_keyboard()
        )
        return

    await query.edit_message_text(GENERATING_MESSAGE)
    print(f"[INSIGHT] Calling: {API_BASE}/fixture-insight/{fixture_id}/")

    try:
        response = requests.get(
            f"{API_BASE}/fixture-insight/{fixture_id}/",
            timeout=60
        )

        print(f"[INSIGHT] API status code: {response.status_code}")
        data = response.json()
        print(f"[INSIGHT] Response keys: {list(data.keys())}")

        if "error" in data:
            print(f"[INSIGHT] API returned error: {data['error']}")
            await query.edit_message_text(
                f"❌ Could not generate prediction: {data['error']}",
                reply_markup=after_insight_keyboard(fixture_id, league_id)
            )
            return

        home = data.get("home_team", "Home")
        away = data.get("away_team", "Away")
        insight = data.get("insight", {})

        print(f"[INSIGHT] home={home}, away={away}")
        print(f"[INSIGHT] insight type: {type(insight).__name__}")
        print(f"[INSIGHT] insight content: {str(insight)[:200]}")

        message = insight_message(home, away, insight)

        await query.edit_message_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_insight_keyboard(fixture_id, league_id)
        )

        print(f"[INSIGHT] Successfully displayed prediction")

    except requests.exceptions.Timeout:
        print("[INSIGHT] ERROR: Timeout after 60s")
        await query.edit_message_text(
            "⏱ The AI is taking longer than usual. Please try again.",
            reply_markup=after_insight_keyboard(fixture_id, league_id)
        )
    except requests.exceptions.ConnectionError:
        print("[INSIGHT] ERROR: Connection error")
        await query.edit_message_text(ERROR_CONNECTION)
    except Exception as e:
        print(f"[INSIGHT] ERROR: {str(e)}")
        await query.edit_message_text(f"{ERROR_GENERAL}\n\n`{str(e)}`", parse_mode=ParseMode.MARKDOWN)


async def preview_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, fixture_id: str):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    print(f"\n[PREVIEW] fixture_id={fixture_id}, user_id={user_id} — showing paywall")

    await query.edit_message_text(
        TEASER_PAYWALL_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=subscribe_keyboard()
    )