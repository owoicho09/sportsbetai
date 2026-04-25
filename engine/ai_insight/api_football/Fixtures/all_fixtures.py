import http.client
import json
from datetime import datetime
import os
import sys
import django
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(__file__, "../../../../../"))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from engine.models import Fixture

load_dotenv()
api_key = os.getenv('api_football_access_token')

def get_fixtures(season, league_id):
    """
    Fetch all fixtures for a given season and league and store/update in DB.
    Returns list of fixture dictionaries.
    """
    fixtures_list = []

    # === API Connection ===
    conn = http.client.HTTPSConnection("v3.football.api-sports.io")
    headers = {'x-apisports-key': api_key}

    try:
        print(f"Requesting fixtures for league {league_id}, season {season}...")
        conn.request("GET", f"/fixtures?league={league_id}&season={season}", headers=headers)
        res = conn.getresponse()
        data = res.read()
        print("Response received!")
    except Exception as e:
        print(f"❌ Error fetching fixtures: {e}")
        return fixtures_list

    # === Parse JSON ===
    try:
        fixtures_json = json.loads(data.decode("utf-8"))
        fixtures = fixtures_json.get("response", [])
        print(f"Total fixtures received: {len(fixtures)}")
    except json.JSONDecodeError:
        print("❌ Error decoding JSON response!")
        return fixtures_list

    # === Stats counters ===
    added_count = 0
    updated_count = 0

    # === Process and save fixtures ===
    for item in fixtures:
        f = item.get("fixture", {})
        l = item.get("league", {})
        t = item.get("teams", {})
        g = item.get("goals", {})
        s = f.get("score", {}) or item.get("score", {})

        # Extract safely
        fixture_id = f.get("id")
        referee = f.get("referee")
        date_str = f.get("date")
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except Exception:
            date = None
        timezone = f.get("timezone", "UTC")
        elapsed = f.get("status", {}).get("elapsed")
        status_short = f.get("status", {}).get("short")
        status_long = f.get("status", {}).get("long")

        venue = f.get("venue", {})
        venue_name = venue.get("name")
        venue_city = venue.get("city")

        home = t.get("home", {})
        away = t.get("away", {})

        fixture_data = {
            "fixture_id": fixture_id,
            "referee": referee,
            "league_id":league_id,
            "date": date,
            "timezone": timezone,
            "elapsed": elapsed,
            "status_short": status_short,
            "status_long": status_long,
            "venue_name": venue_name,
            "venue_city": venue_city,
            "league_name": l.get("name"),
            "league_country": l.get("country"),
            "league_season": l.get("season"),
            "league_round": l.get("round"),
            "home_team_id": home.get("id"),
            "home_team_name": home.get("name"),
            "away_team_id": away.get("id"),
            "away_team_name": away.get("name"),
            "home_winner": home.get("winner"),
            "away_winner": away.get("winner"),
            "goals_home": g.get("home"),
            "goals_away": g.get("away"),

            "halftime_home": s.get("halftime", {}).get("home"),
            "halftime_away": s.get("halftime", {}).get("away"),
            "fulltime_home": s.get("fulltime", {}).get("home"),
            "fulltime_away": s.get("fulltime", {}).get("away"),
            "extratime_home": s.get("extratime", {}).get("home"),
            "extratime_away": s.get("extratime", {}).get("away"),
            "penalty_home": s.get("penalty", {}).get("home"),
            "penalty_away": s.get("penalty", {}).get("away"),
        }

        try:
            obj, created = Fixture.objects.update_or_create(
                fixture_id=fixture_id,
                season=season,
                defaults=fixture_data
            )
            if created:
                added_count += 1
                print(f"✔ Added fixture: {fixture_id} | {home.get('name')} vs {away.get('name')}")
            else:
                updated_count += 1
                print(f"↻ Updated fixture: {fixture_id} | {home.get('name')} vs {away.get('name')}")
        except Exception as e:
            print(f"⚠️ Failed to save fixture {fixture_id}: {e}")
            continue

        fixtures_list.append(fixture_data)

    print("-" * 80)
    print(f"Fixtures added: {added_count}")
    print(f"Fixtures updated: {updated_count}")

    return fixtures_list


if __name__ == "__main__":
    SEASON = 2023
    LEAGUE_ID = 39
    get_fixtures(SEASON, LEAGUE_ID)
