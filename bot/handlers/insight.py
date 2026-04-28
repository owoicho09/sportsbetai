# bot/handlers/insight.py

import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.messages import (
    GENERATING_MESSAGE,
    GENERATING_MULTI_MESSAGE,
    TEASER_PAYWALL_MESSAGE,
    insight_message,
    multi_insight_message,
    ERROR_TIMEOUT,
    ERROR_CONNECTION,
    ERROR_GENERAL,
)
from bot.keyboards import (
    after_insight_keyboard,
    after_multi_insight_keyboard,
    subscribe_keyboard,
    back_to_menu_keyboard,
)
from bot.middleware import is_premium

load_dotenv()
API_BASE = os.getenv("API_BASE")


async def _get_insight(fixture_id: str) -> dict:
    """Fetch insight for a single fixture. Returns data dict or raises."""
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/fixture-insight/{fixture_id}/",
            timeout=aiohttp.ClientTimeout(total=90),  # AI generation can take time
        ) as resp:
            return await resp.json()


# =========================================
# Single Fixture Prediction
# =========================================

async def insight_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    fixture_id: str,
    league_id: str = "0",
):
    query   = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    premium = await is_premium(user_id)

    if not premium:
        print(f"[INSIGHT] User {user_id} not premium — showing paywall")
        await query.edit_message_text(
            TEASER_PAYWALL_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscribe_keyboard(),
        )
        return

    # Show loading state immediately so user knows something is happening
    await query.edit_message_text(
        GENERATING_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
    )

    print(f"[INSIGHT] fixture_id={fixture_id}, user_id={user_id}")

    try:
        data = await _get_insight(fixture_id)

        if "error" in data:
            print(f"[INSIGHT] API error: {data['error']}")
            await query.edit_message_text(
                f"❌ Could not generate prediction.\n\n_{data['error']}_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=after_insight_keyboard(fixture_id, league_id),
            )
            return

        home    = data.get("home_team", "Home")
        away    = data.get("away_team", "Away")
        insight = data.get("insight", {})

        await query.edit_message_text(
            insight_message(home, away, insight),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_insight_keyboard(fixture_id, league_id),
        )

        print(f"[INSIGHT] Prediction delivered for {home} vs {away}")

    except asyncio.TimeoutError:
        print("[INSIGHT] Timeout after 90s")
        await query.edit_message_text(
            "⏱ *The AI is taking longer than usual.*\n\n"
            "This happens occasionally with complex matches.\n"
            "Please try again in a moment.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_insight_keyboard(fixture_id, league_id),
        )
    except aiohttp.ClientConnectorError:
        await query.edit_message_text(
            ERROR_CONNECTION,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard(),
        )
    except Exception as e:
        print(f"[INSIGHT] Error: {e}")
        await query.edit_message_text(
            ERROR_GENERAL,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_insight_keyboard(fixture_id, league_id),
        )


# =========================================
# Multi-Fixture Prediction (Premium)
# =========================================

async def multi_insight_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    league_id: str,
):
    query   = update.callback_query
    await query.answer()

    user_id      = query.from_user.id
    premium      = await is_premium(user_id)
    selected_ids = context.user_data.get("selected_fixture_ids", [])

    if not premium:
        await query.edit_message_text(
            TEASER_PAYWALL_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscribe_keyboard(),
        )
        return

    if not selected_ids:
        await query.answer("No fixtures selected.", show_alert=True)
        return

    # Show loading state
    await query.edit_message_text(
        GENERATING_MULTI_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
    )

    print(f"[MULTI INSIGHT] Running predictions for {len(selected_ids)} fixtures: {selected_ids}")

    # Fetch all insights concurrently for speed
    tasks   = [_get_insight(fid) for fid in selected_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    predictions = []
    for fid, result in zip(selected_ids, results):
        if isinstance(result, Exception):
            print(f"[MULTI INSIGHT] Failed for fixture {fid}: {result}")
            predictions.append({
                "home":    fid,
                "away":    "",
                "insight": None,
            })
            continue

        predictions.append({
            "home":    result.get("home_team", "Home"),
            "away":    result.get("away_team", "Away"),
            "insight": result.get("insight", {}),
        })

    # Clear selection after running
    context.user_data["selected_fixture_ids"] = []

    successful = sum(1 for p in predictions if p.get("insight"))
    print(f"[MULTI INSIGHT] {successful}/{len(selected_ids)} predictions successful")

    await query.edit_message_text(
        multi_insight_message(predictions),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=after_multi_insight_keyboard(league_id),
    )


# =========================================
# Free Preview
# =========================================

async def preview_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    fixture_id: str,
):
    query = update.callback_query
    await query.answer()

    print(f"[PREVIEW] fixture_id={fixture_id} — showing paywall")

    await query.edit_message_text(
        TEASER_PAYWALL_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=subscribe_keyboard(),
    )