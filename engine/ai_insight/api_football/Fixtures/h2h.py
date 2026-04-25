import os
import sys
import time
import requests
from dotenv import load_dotenv
from django.db import transaction
from django.utils.dateparse import parse_datetime

# --- Django Setup ---
BASE_DIR = os.path.abspath(os.path.join(__file__, "../../../../../"))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from engine.models import H2HMatch, Team  # adjust if needed

# --- Load Env ---
load_dotenv()
API_KEY = os.getenv("api_football_access_token")
BASE_URL = "https://v3.football.api-sports.io"

# --- Rate limit ---
REQUEST_INTERVAL = 2  # seconds between requests


def fetch_h2h(team1_id: int, team2_id: int, last: int = 5):
    """
    Fetch last N H2H matches between two teams and store only new fixtures.
    """
    # Canonical order for easy querying
    team_a_id, team_b_id = sorted([team1_id, team2_id])
    pair_key = f"{team_a_id}-{team_b_id}"
    print(f"\n➡️ Fetching H2H for pair {pair_key}...")

    headers = {"x-apisports-key": API_KEY}
    url = f"{BASE_URL}/fixtures/headtohead?h2h={team_a_id}-{team_b_id}"

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ API request failed: {e}")
        return

    data = response.json()
    fixtures = data.get("response", [])
    if not fixtures:
        print("ℹ️ No H2H data returned for this pair.")
        return

    # Sort by date descending and pick last N matches
    fixtures_sorted = sorted(
        fixtures,
        key=lambda x: parse_datetime(x["fixture"]["date"]),
        reverse=True
    )[:last]

    new_count = 0
    with transaction.atomic():
        for item in fixtures_sorted:
            fixture = item["fixture"]
            league = item["league"]
            teams = item["teams"]
            goals = item["goals"]
            status = fixture["status"]

            fixture_id = fixture["id"]

            # Skip if fixture already exists
            if H2HMatch.objects.filter(fixture_id=fixture_id).exists():
                continue

            obj = H2HMatch.objects.create(
                fixture_id=fixture_id,
                date=parse_datetime(fixture["date"]),

            # League info
                league_id=league["id"],
                league_name=league["name"],
                league_round=league.get("round"),

                # Home team
                home_team_id=teams["home"]["id"],
                home_team_name=teams["home"]["name"],

                # Away team
                away_team_id=teams["away"]["id"],
                away_team_name=teams["away"]["name"],

                # Scores
                home_goals=goals["home"],
                away_goals=goals["away"],

                # Status
                status_short=status["short"],
                status_long=status["long"]
            )
            new_count += 1
            print(f"✔ Added new H2H fixture: {fixture_id} | {teams['home']['name']} vs {teams['away']['name']}")

    print(f"✅ Done. {new_count} new H2H fixtures added for pair {pair_key}.")


def update_h2h_for_all_teams(last: int = 5):
    """
    Update H2H for all unique team pairs.
    """
    teams = list(Team.objects.all())
    total_pairs = len(teams) * (len(teams) - 1) // 2
    print(f"🔹 Updating H2H for {total_pairs} team pairs...")

    pair_counter = 1
    for i, team1 in enumerate(teams):
        for team2 in teams[i + 1:]:  # ensures no duplicates and skips self
            print(f"\n[{pair_counter}/{total_pairs}] {team1.name} vs {team2.name}")
            try:
                fetch_h2h(team1.api_id, team2.api_id, last=last)
                pair_counter += 1
                time.sleep(REQUEST_INTERVAL)  # rate limit
            except Exception as e:
                print(f"⚠️ Failed to fetch H2H for {team1.name}-{team2.name}: {e}")


if __name__ == "__main__":
    update_h2h_for_all_teams(last=5)
