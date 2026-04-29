# bot/handlers/leagues.py

import os
import aiohttp
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.messages import (
    CHOOSE_LEAGUE_MESSAGE,
    NO_LEAGUES_MESSAGE,
    ERROR_TIMEOUT,
    ERROR_CONNECTION,
    ERROR_GENERAL,
)
from bot.keyboards import leagues_keyboard, back_to_menu_keyboard

load_dotenv()
API_BASE = os.getenv("API_BASE")


async def leagues_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # NO query.answer() here — already called in callback_router

    await query.edit_message_text("⏳ Loading leagues...")

    print(f"\n[LEAGUES] Fetching leagues from {API_BASE}/leagues/")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/leagues/",
                timeout=aiohttp.ClientTimeout(total=15)
            ) as resp:
                data = await resp.json()

        leagues_raw = data.get("results", data) if isinstance(data, dict) else data

        if not leagues_raw:
            await query.edit_message_text(
                NO_LEAGUES_MESSAGE,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=back_to_menu_keyboard(),
            )
            return

        leagues = []
        for league in leagues_raw:
            api_id    = league.get("api_id")
            django_id = league.get("id")
            name      = league.get("name", "Unknown League")
            leagues.append({
                "id":   api_id or django_id,
                "name": name,
            })

        print(f"[LEAGUES] {len(leagues)} leagues loaded")

        await query.edit_message_text(
            CHOOSE_LEAGUE_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=leagues_keyboard(leagues),
        )

    except asyncio.TimeoutError:
        print("[LEAGUES] Timeout")
        await query.edit_message_text(
            ERROR_TIMEOUT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard(),
        )
    except aiohttp.ClientConnectorError:
        print("[LEAGUES] Connection error")
        await query.edit_message_text(
            ERROR_CONNECTION,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard(),
        )
    except Exception as e:
        print(f"[LEAGUES] Error: {e}")
        await query.edit_message_text(
            ERROR_GENERAL,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard(),
        )