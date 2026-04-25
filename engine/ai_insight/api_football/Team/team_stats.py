import os
import sys
import django,requests

BASE_DIR = os.path.abspath(
    os.path.join(__file__, "../../../../../")
)

sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "core.settings"
)

django.setup()


import http.client
import json,os
from django.utils import timezone
from engine.models import TeamStats, Team, League
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('api_football_access_token')


REQUEST_TIMEOUT = 15  # seconds
REQUEST_INTERVAL = 2  # seconds between calls


def fetch_and_store_team_stats(
    season: int,
    team_id: int,
    league_id: int,
):
    print("\n=== FETCHING TEAM STATISTICS ===")
    print(f"Season: {season}, Team ID: {team_id}, League ID: {league_id}")

    url = "https://v3.football.api-sports.io/teams/statistics"

    headers = {
        "x-apisports-key": api_key
    }

    params = {
        "season": season,
        "team": team_id,
        "league": league_id,
    }

    try:
        print("📡 Sending request...")
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        print(f"HTTP Status: {response.status_code}")

        if response.status_code != 200:
            print("❌ API request failed")
            print("Response:", response.text)
            return None

        payload = response.json()

    except requests.exceptions.Timeout:
        print("⏳ Request timed out")
        return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

    if payload.get("errors"):
        print("❌ API returned errors:", payload["errors"])
        return None

    response_data = payload.get("response")
    if not response_data:
        print("❌ No response data found")
        return None

    print("✅ API response received successfully")

    fixtures = response_data.get("fixtures", {})
    goals = response_data.get("goals", {})
    clean_sheet = response_data.get("clean_sheet", {})
    failed_to_score = response_data.get("failed_to_score", {})

    try:
        league = League.objects.get(api_id=league_id)
        team = Team.objects.get(api_id=team_id)
    except (League.DoesNotExist, Team.DoesNotExist):
        print("❌ League or Team not found in DB")
        return None

    team_stats, created = TeamStats.objects.update_or_create(
        league=league,
        team=team,
        season=season,

    defaults={
            "form": response_data.get("form", "null"),

            "matches_played_home": fixtures.get("played", {}).get("home", 0),
            "matches_played_away": fixtures.get("played", {}).get("away", 0),
            "matches_played_total": fixtures.get("played", {}).get("total", 0),

            "wins_home": fixtures.get("wins", {}).get("home", 0),
            "wins_away": fixtures.get("wins", {}).get("away", 0),
            "wins_total": fixtures.get("wins", {}).get("total", 0),

            "draws_home": fixtures.get("draws", {}).get("home", 0),
            "draws_away": fixtures.get("draws", {}).get("away", 0),
            "draws_total": fixtures.get("draws", {}).get("total", 0),

            "losses_home": fixtures.get("loses", {}).get("home", 0),
            "losses_away": fixtures.get("loses", {}).get("away", 0),
            "losses_total": fixtures.get("loses", {}).get("total", 0),

            "goals_home": goals.get("for", {}).get("total", {}).get("home", 0),
            "goals_away": goals.get("for", {}).get("total", {}).get("away", 0),
            "goals_total": goals.get("for", {}).get("total", {}).get("total", 0),

            "avg_goals_home": float(goals.get("for", {}).get("average", {}).get("home", 0) or 0),
            "avg_goals_away": float(goals.get("for", {}).get("average", {}).get("away", 0) or 0),
            "avg_goals_total": float(goals.get("for", {}).get("average", {}).get("total", 0) or 0),

            "conceded_home": goals.get("against", {}).get("total", {}).get("home", 0),
            "conceded_away": goals.get("against", {}).get("total", {}).get("away", 0),
            "conceded_total": goals.get("against", {}).get("total", {}).get("total", 0),

            "avg_conceded_home": float(goals.get("against", {}).get("average", {}).get("home", 0) or 0),
            "avg_conceded_away": float(goals.get("against", {}).get("average", {}).get("away", 0) or 0),
            "avg_conceded_total": float(goals.get("against", {}).get("average", {}).get("total", 0) or 0),

            "over_15": goals.get("for", {}).get("under_over", {}).get("1.5", {}).get("over", 0),
            "under_15": goals.get("for", {}).get("under_over", {}).get("1.5", {}).get("under", 0),

            "over_25": goals.get("for", {}).get("under_over", {}).get("2.5", {}).get("over", 0),
            "under_25": goals.get("for", {}).get("under_over", {}).get("2.5", {}).get("under", 0),

            "over_35": goals.get("for", {}).get("under_over", {}).get("3.5", {}).get("over", 0),
            "under_35": goals.get("for", {}).get("under_over", {}).get("3.5", {}).get("under", 0),

            "clean_sheet_home": clean_sheet.get("home", 0),
            "clean_sheet_away": clean_sheet.get("away", 0),
            "clean_sheet_total": clean_sheet.get("total", 0),

            "failed_to_score_home": failed_to_score.get("home", 0),
            "failed_to_score_away": failed_to_score.get("away", 0),
            "failed_to_score_total": failed_to_score.get("total", 0),

            "updated_at": timezone.now(),
        }
    )

    print("✅ TeamStats saved successfully")
    print("Created new record" if created else "Updated existing record")

    return team_stats

if __name__ == "__main__":
    season = 2024
    team_id = 40
    league_id = 39
    fetch_and_store_team_stats(season,team_id,league_id)

