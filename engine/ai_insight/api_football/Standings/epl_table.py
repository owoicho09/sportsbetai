import http.client
import json

import os
import sys
import django
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(
    os.path.join(__file__, "../../../../../")
)

sys.path.insert(0, BASE_DIR)

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "core.settings"
)

django.setup()


from engine.models import League, Team, Standing  # adjust import according to your project


load_dotenv()
api_key = os.getenv('api_football_access_token')

import requests

def fetch_epl_table(league_id, season):
    print(f"\nFetching standings for League {league_id}, Season {season}")

    url = "https://v3.football.api-sports.io/standings"
    headers = {"x-apisports-key": api_key}
    params = {"league": league_id, "season": season}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        print("HTTP Status:", response.status_code)

        if response.status_code != 200:
            print("API Error:", response.text)
            return

        parsed = response.json()

    except requests.RequestException as e:
        print("Request failed:", e)
        return

    if parsed.get("errors"):
        print("API returned errors:", parsed["errors"])
        return

    standings_data = parsed["response"][0]["league"]["standings"][0]

    print(f"Processing {len(standings_data)} teams...")

    league_obj, _ = League.objects.get_or_create(
        api_id=league_id,
        defaults={"name": parsed["response"][0]["league"]["name"]}
    )

    for team_data in standings_data:

        team_id = team_data["team"]["id"]
        team_name = team_data["team"]["name"]

        rank = team_data["rank"]
        points = team_data["points"]
        goals_diff = team_data["goalsDiff"]
        form = team_data["form"]

        all_stats = team_data["all"]
        home_stats = team_data["home"]
        away_stats = team_data["away"]

        team_obj, _ = Team.objects.get_or_create(
            api_id=team_id,
            defaults={"name": team_name, "league": league_obj}
        )

        Standing.objects.update_or_create(
            league=league_obj,
            team=team_obj,
            season=season,
            defaults={
                "rank": rank,
                "points": points,
                "goals_diff": goals_diff,
                "last_5_form": form,

                "played_total": all_stats["played"],
                "wins_total": all_stats["win"],
                "draws_total": all_stats["draw"],
                "losses_total": all_stats["lose"],
                "goals_for_total": all_stats["goals"]["for"],
                "goals_against_total": all_stats["goals"]["against"],

                "played_home": home_stats["played"],
                "wins_home": home_stats["win"],
                "draws_home": home_stats["draw"],
                "losses_home": home_stats["lose"],
                "goals_for_home": home_stats["goals"]["for"],
                "goals_against_home": home_stats["goals"]["against"],

                "played_away": away_stats["played"],
                "wins_away": away_stats["win"],
                "draws_away": away_stats["draw"],
                "losses_away": away_stats["lose"],
                "goals_for_away": away_stats["goals"]["for"],
                "goals_against_away": away_stats["goals"]["against"],

                "description": team_data.get("description"),
            }
        )

        print(f"✔ Saved standing: {team_name}")

    print("✅ All standings processed successfully!")


if __name__ == "__main__":
    fetch_epl_table(season, league_id)

