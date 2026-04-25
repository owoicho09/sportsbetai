# bot/handlers/fixtures.py

import os
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.messages import (
    upcoming_fixtures_message,
    NO_FIXTURES_MESSAGE,
    fixture_detail_message,
    ERROR_TIMEOUT,
    ERROR_CONNECTION,
    ERROR_GENERAL
)
from bot.keyboards import fixtures_keyboard, fixture_detail_keyboard
from bot.middleware import is_premium

load_dotenv()
API_BASE = os.getenv("API_BASE")

PAGE_SIZE = 8


async def fixtures_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, league_id: str, page: int = 0):
    query = update.callback_query
    await query.answer()

    offset = page * PAGE_SIZE

    print(f"\n[FIXTURES] league_id received from bot: '{league_id}' (type: {type(league_id).__name__})")
    print(f"[FIXTURES] page={page}, offset={offset}")
    print(f"[FIXTURES] Calling: {API_BASE}/fixtures/list/?league_id={league_id}&upcoming=true&limit={PAGE_SIZE}&offset={offset}")

    try:
        response = requests.get(
            f"{API_BASE}/fixtures/list/",
            params={
                "league_id": league_id,
                "upcoming": "true",
                "limit": PAGE_SIZE,
                "offset": offset
            },
            timeout=20
        )

        print(f"[FIXTURES] API status code: {response.status_code}")
        data = response.json()

        print(f"[FIXTURES] API response keys: {list(data.keys())}")
        print(f"[FIXTURES] total={data.get('total')}, has_more={data.get('has_more')}, league_name={data.get('league_name')}")

        fixtures = data.get("fixtures", [])
        league_name = data.get("league_name", "Fixtures")

        print(f"[FIXTURES] fixtures returned: {len(fixtures)}")
        if fixtures:
            print(f"[FIXTURES] First fixture: {fixtures[0].get('home_team_name')} vs {fixtures[0].get('away_team_name')}")

        if not fixtures:
            print(f"[FIXTURES] No fixtures — page={page}, showing empty message")
            if page == 0:
                await query.edit_message_text(
                    NO_FIXTURES_MESSAGE,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await query.answer("No more fixtures available.", show_alert=True)
            return

        await query.edit_message_text(
            upcoming_fixtures_message(league_name, page),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=fixtures_keyboard(fixtures, league_id, page)
        )

        print(f"[FIXTURES] Successfully displayed {len(fixtures)} fixtures")

    except requests.exceptions.Timeout:
        print("[FIXTURES] ERROR: Timeout")
        await query.edit_message_text(ERROR_TIMEOUT)
    except requests.exceptions.ConnectionError:
        print("[FIXTURES] ERROR: Connection error")
        await query.edit_message_text(ERROR_CONNECTION)
    except Exception as e:
        print(f"[FIXTURES] ERROR: {str(e)}")
        await query.edit_message_text(f"{ERROR_GENERAL}\n\n`{str(e)}`", parse_mode=ParseMode.MARKDOWN)


async def fixture_detail_handler(update: Update, context: ContextTypes.DEFAULT_TYPE, fixture_id: str, league_id: str = "0"):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    premium = is_premium(user_id)

    print(f"\n[FIXTURE DETAIL] fixture_id={fixture_id}, league_id={league_id}, premium={premium}")
    print(f"[FIXTURE DETAIL] Calling: {API_BASE}/fixtures/{fixture_id}/")

    try:
        response = requests.get(f"{API_BASE}/fixtures/{fixture_id}/", timeout=15)

        print(f"[FIXTURE DETAIL] API status code: {response.status_code}")
        f = response.json()

        print(f"[FIXTURE DETAIL] Response keys: {list(f.keys()) if isinstance(f, dict) else 'NOT A DICT'}")

        raw_date = f.get("date", "")
        match_date = raw_date[:10] if raw_date else "TBD"
        match_time = raw_date[11:16] if len(raw_date) > 10 else "TBD"

        home = f.get("home_team_name", "Home Team")
        away = f.get("away_team_name", "Away Team")
        league = f.get("league_name", "N/A")
        round_ = f.get("league_round", "N/A")

        print(f"[FIXTURE DETAIL] {home} vs {away} | {match_date} {match_time} | {league} | {round_}")

        text = fixture_detail_message(
            home=home,
            away=away,
            league=league,
            match_date=match_date,
            match_time=match_time,
            round_=round_,
            is_premium=premium
        )

        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=fixture_detail_keyboard(fixture_id, league_id, is_premium=premium)
        )

        print(f"[FIXTURE DETAIL] Successfully displayed fixture detail")

    except requests.exceptions.Timeout:
        print("[FIXTURE DETAIL] ERROR: Timeout")
        await query.edit_message_text(ERROR_TIMEOUT)
    except requests.exceptions.ConnectionError:
        print("[FIXTURE DETAIL] ERROR: Connection error")
        await query.edit_message_text(ERROR_CONNECTION)
    except Exception as e:
        print(f"[FIXTURE DETAIL] ERROR: {str(e)}")
        await query.edit_message_text(f"{ERROR_GENERAL}\n\n`{str(e)}`", parse_mode=ParseMode.MARKDOWN)