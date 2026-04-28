# bot/handlers/fixtures.py

import os
import asyncio
import aiohttp
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.messages import (
    upcoming_fixtures_message,
    NO_FIXTURES_MESSAGE,
    fixture_detail_message,
    SELECT_FIXTURES_MESSAGE,
    ERROR_TIMEOUT,
    ERROR_CONNECTION,
    ERROR_GENERAL,
)
from bot.keyboards import (
    fixtures_keyboard,
    fixture_detail_keyboard,
    multi_select_keyboard,
)
from bot.middleware import is_premium

load_dotenv()
API_BASE = os.getenv("API_BASE")
PAGE_SIZE = 8


# =========================================
# Helpers
# =========================================

async def _get(url: str, params: dict = None, timeout: int = 20) -> dict:
    """Async HTTP GET. Raises on timeout or connection error."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
            return await resp.json()


# =========================================
# Fixtures List
# =========================================

async def fixtures_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    league_id: str,
    page: int = 0,
):
    query  = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    premium = await is_premium(user_id)

    offset = page * PAGE_SIZE

    # Show loading state immediately
    await query.edit_message_text("⏳ Loading fixtures...")

    print(f"[FIXTURES] league_id={league_id}, page={page}, offset={offset}")

    try:
        data = await _get(
            f"{API_BASE}/fixtures/list/",
            params={
                "league_id": league_id,
                "upcoming":  "true",
                "limit":     PAGE_SIZE,
                "offset":    offset,
            },
            timeout=20,
        )

        fixtures    = data.get("fixtures", [])
        league_name = data.get("league_name", "Fixtures")

        print(f"[FIXTURES] {len(fixtures)} fixtures returned for league {league_id}")

        if not fixtures:
            if page == 0:
                await query.edit_message_text(
                    NO_FIXTURES_MESSAGE,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=__import__("bot.keyboards", fromlist=["back_to_menu_keyboard"]).back_to_menu_keyboard()
                )
            else:
                await query.answer("No more fixtures on this page.", show_alert=True)
                # Go back to previous page automatically
                await fixtures_handler(update, context, league_id=league_id, page=page - 1)
            return

        await query.edit_message_text(
            upcoming_fixtures_message(league_name, page),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=fixtures_keyboard(fixtures, league_id, page, is_premium=premium),
        )

        # Store fixtures in user_data for multi-select
        context.user_data["current_fixtures"]  = fixtures
        context.user_data["current_league_id"] = league_id
        context.user_data["current_page"]      = page

    except asyncio.TimeoutError:
        print("[FIXTURES] Timeout")
        await query.edit_message_text(
            ERROR_TIMEOUT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=__import__("bot.keyboards", fromlist=["back_to_menu_keyboard"]).back_to_menu_keyboard()
        )
    except aiohttp.ClientConnectorError:
        print("[FIXTURES] Connection error")
        await query.edit_message_text(
            ERROR_CONNECTION,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=__import__("bot.keyboards", fromlist=["back_to_menu_keyboard"]).back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"[FIXTURES] Error: {e}")
        await query.edit_message_text(
            ERROR_GENERAL,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=__import__("bot.keyboards", fromlist=["back_to_menu_keyboard"]).back_to_menu_keyboard()
        )


# =========================================
# Fixture Detail
# =========================================

async def fixture_detail_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    fixture_id: str,
    league_id: str = "0",
):
    query   = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    premium = await is_premium(user_id)

    await query.edit_message_text("⏳ Loading match details...")

    print(f"[FIXTURE DETAIL] fixture_id={fixture_id}, premium={premium}")

    try:
        f = await _get(f"{API_BASE}/fixtures/{fixture_id}/", timeout=15)

        raw_date   = f.get("date", "")
        match_date = raw_date[:10] if raw_date else "TBD"
        match_time = raw_date[11:16] if len(raw_date) > 10 else "TBD"

        home   = f.get("home_team_name", "Home Team")
        away   = f.get("away_team_name", "Away Team")
        league = f.get("league_name", "N/A")
        round_ = f.get("league_round", "N/A")

        await query.edit_message_text(
            fixture_detail_message(
                home=home, away=away, league=league,
                match_date=match_date, match_time=match_time,
                round_=round_, is_premium=premium,
            ),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=fixture_detail_keyboard(fixture_id, league_id, is_premium=premium),
        )

    except asyncio.TimeoutError:
        await query.edit_message_text(
            ERROR_TIMEOUT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=__import__("bot.keyboards", fromlist=["back_to_menu_keyboard"]).back_to_menu_keyboard()
        )
    except aiohttp.ClientConnectorError:
        await query.edit_message_text(
            ERROR_CONNECTION,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=__import__("bot.keyboards", fromlist=["back_to_menu_keyboard"]).back_to_menu_keyboard()
        )
    except Exception as e:
        print(f"[FIXTURE DETAIL] Error: {e}")
        await query.edit_message_text(
            ERROR_GENERAL,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=__import__("bot.keyboards", fromlist=["back_to_menu_keyboard"]).back_to_menu_keyboard()
        )


# =========================================
# Multi-Select Screen (Premium)
# =========================================

async def multi_select_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    league_id: str,
    page: int,
):
    query   = update.callback_query
    await query.answer()

    fixtures     = context.user_data.get("current_fixtures", [])
    selected_ids = context.user_data.get("selected_fixture_ids", [])

    if not fixtures:
        await query.edit_message_text(
            "⚠️ Session expired. Please go back and reload the fixtures.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=__import__("bot.keyboards", fromlist=["back_to_menu_keyboard"]).back_to_menu_keyboard()
        )
        return

    await query.edit_message_text(
        SELECT_FIXTURES_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=multi_select_keyboard(fixtures, league_id, page, selected_ids),
    )


async def toggle_fixture_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    fixture_id: str,
):
    """Toggle a fixture in/out of the multi-select list."""
    query = update.callback_query
    await query.answer()

    selected_ids = context.user_data.get("selected_fixture_ids", [])

    if fixture_id in selected_ids:
        selected_ids.remove(fixture_id)
    else:
        if len(selected_ids) >= 5:
            await query.answer("Maximum 5 fixtures at once.", show_alert=True)
            return
        selected_ids.append(fixture_id)

    context.user_data["selected_fixture_ids"] = selected_ids

    # Refresh the multi-select screen
    fixtures  = context.user_data.get("current_fixtures", [])
    league_id = context.user_data.get("current_league_id", "0")
    page      = context.user_data.get("current_page", 0)

    await query.edit_message_text(
        SELECT_FIXTURES_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=multi_select_keyboard(fixtures, league_id, page, selected_ids),
    )