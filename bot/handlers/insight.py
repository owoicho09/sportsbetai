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
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/fixture-insight/{fixture_id}/",
            timeout=aiohttp.ClientTimeout(total=90),
        ) as resp:
            return await resp.json()


# =========================================
# Single Prediction
# =========================================

async def insight_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    fixture_id: str,
    league_id: str = "0",
):
    query   = update.callback_query
    # NO query.answer() — already called in callback_router

    user_id = query.from_user.id
    premium = await is_premium(user_id)

    if not premium:
        await query.edit_message_text(
            TEASER_PAYWALL_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscribe_keyboard(),
        )
        return

    await query.edit_message_text(
        GENERATING_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        data = await _get_insight(fixture_id)

        if "error" in data:
            await query.edit_message_text(
                f"❌ Could not generate prediction.\n\n_{data['error']}_",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=after_insight_keyboard(fixture_id, league_id),
            )
            return

        await query.edit_message_text(
            insight_message(
                data.get("home_team", "Home"),
                data.get("away_team", "Away"),
                data.get("insight", {}),
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_insight_keyboard(fixture_id, league_id),
        )

    except asyncio.TimeoutError:
        await query.edit_message_text(
            "⏱ *The AI is taking longer than usual.*\n\nPlease try again in a moment.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=after_insight_keyboard(fixture_id, league_id),
        )
    except aiohttp.ClientConnectorError:
        await query.edit_message_text(ERROR_CONNECTION, parse_mode=ParseMode.MARKDOWN, reply_markup=back_to_menu_keyboard())
    except Exception as e:
        print(f"[INSIGHT] Error: {e}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode=ParseMode.MARKDOWN, reply_markup=after_insight_keyboard(fixture_id, league_id))


# =========================================
# Multi Prediction (Premium)
# =========================================

async def multi_insight_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    league_id: str,
):
    query        = update.callback_query
    # NO query.answer() — already called in callback_router

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
        await query.edit_message_text(
            "⚠️ No fixtures selected. Go back and select at least one.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await query.edit_message_text(
        GENERATING_MULTI_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
    )

    tasks   = [_get_insight(fid) for fid in selected_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    predictions = []
    for fid, result in zip(selected_ids, results):
        if isinstance(result, Exception):
            print(f"[MULTI INSIGHT] Failed for {fid}: {result}")
            predictions.append({"home": fid, "away": "", "insight": None})
        else:
            predictions.append({
                "home":    result.get("home_team", "Home"),
                "away":    result.get("away_team", "Away"),
                "insight": result.get("insight", {}),
            })

    context.user_data["selected_fixture_ids"] = []

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
    # NO query.answer() — already called in callback_router

    await query.edit_message_text(
        TEASER_PAYWALL_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=subscribe_keyboard(),
    )