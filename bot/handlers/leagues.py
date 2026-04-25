# bot/handlers/leagues.py

import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.messages import CHOOSE_LEAGUE_MESSAGE, NO_LEAGUES_MESSAGE, ERROR_TIMEOUT, ERROR_CONNECTION, ERROR_GENERAL
from bot.keyboards import leagues_keyboard

load_dotenv()
API_BASE = os.getenv("API_BASE")


async def leagues_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    print(f"\n[LEAGUES] Fetching leagues from {API_BASE}/leagues/")

    try:
        response = requests.get(f"{API_BASE}/leagues/", timeout=15)
        data = response.json()

        print(f"[LEAGUES] Raw response: {data}")

        # Handle both paginated (DRF router) and plain list responses
        leagues_raw = data.get("results", data) if isinstance(data, dict) else data

        print(f"[LEAGUES] leagues_raw count: {len(leagues_raw) if leagues_raw else 0}")
        print(f"[LEAGUES] leagues_raw sample: {leagues_raw[:2] if leagues_raw else 'EMPTY'}")

        if not leagues_raw:
            print("[LEAGUES] No leagues found — showing NO_LEAGUES_MESSAGE")
            await query.edit_message_text(
                NO_LEAGUES_MESSAGE,
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # -------------------------------------------------------
        # FIX: Use api_id (the API Football league ID e.g. 39)
        # NOT id (Django PK e.g. 1)
        # Fixtures.league_id stores the api_id value (39)
        # so we must pass api_id as the league_id to the fixtures endpoint
        # -------------------------------------------------------
        leagues = []
        for league in leagues_raw:
            api_id = league.get("api_id")           # e.g. 39 — matches Fixture.league_id
            django_id = league.get("id")            # e.g. 1  — Django PK, DO NOT USE for fixtures
            name = league.get("name", "Unknown League")

            print(f"[LEAGUES] League: id={django_id}, api_id={api_id}, name={name}")

            leagues.append({
                "id": api_id or django_id,          # prefer api_id
                "name": name
            })

        print(f"[LEAGUES] Final leagues list to display: {leagues}")

        await query.edit_message_text(
            CHOOSE_LEAGUE_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=leagues_keyboard(leagues)
        )

    except requests.exceptions.Timeout:
        print("[LEAGUES] ERROR: Request timed out")
        await query.edit_message_text(ERROR_TIMEOUT)
    except requests.exceptions.ConnectionError:
        print("[LEAGUES] ERROR: Connection error")
        await query.edit_message_text(ERROR_CONNECTION)
    except Exception as e:
        print(f"[LEAGUES] ERROR: {str(e)}")
        await query.edit_message_text(f"{ERROR_GENERAL}\n\n`{str(e)}`", parse_mode=ParseMode.MARKDOWN)