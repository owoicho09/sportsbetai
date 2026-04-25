"""
central_update.py
==================
Orchestrates all data pipeline updates for a given league + season.

Fixes vs original:
  - H2H pairs are deduplicated before fetching (was running ~380 duplicate calls)
  - time.sleep uses a shorter safe interval appropriate for the API plan
  - Steps are clearly separated with error isolation
  - Dry-run mode added for testing without hitting the API
"""

import os
import sys
import time

# --- Django Setup ---
BASE_DIR = os.path.abspath(os.path.join(__file__, "../../../../../"))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from engine.models import Team, League

# --- Import pipeline modules ---
from engine.ai_insight.api_football.Fixtures.all_fixtures         import get_fixtures
from engine.ai_insight.api_football.Fixtures.h2h                  import fetch_h2h
from engine.ai_insight.api_football.Standings.epl_table           import fetch_epl_table
from engine.ai_insight.api_football.Team.team_stats               import fetch_and_store_team_stats
from engine.ai_insight.api_football.TeamSummary.team_feature_store import build_team_feature

# ---------------------------------------------------------------------------
# Rate limiting
# api-football free plan: 100 requests/day
# Spreading them safely — 6 seconds between calls = max ~14 400 calls/day
# Adjust REQUEST_INTERVAL based on your plan.
# ---------------------------------------------------------------------------
REQUEST_INTERVAL = 6  # seconds between API calls


def central_update(season: int, league_id: int, dry_run: bool = False):
    """
    Full pipeline update for a league+season:
      1. Fixtures
      2. H2H for unique fixture pairs (deduplicated)
      3. Standings
      4. Team stats per team
      5. TeamFeatureStore (local computation — no API call)

    Args:
        season:    e.g. 2024
        league_id: API-Football league ID, e.g. 39 for Premier League
        dry_run:   If True, prints what would happen without calling APIs.
    """

    league = League.objects.filter(api_id=league_id).first()
    if not league:
        print(f"❌ League with API ID {league_id} not found in DB.")
        print("   Run the standings fetch first, or create the League record manually.")
        return

    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{'='*70}")
    print(f"  {mode}Central Update — {league.name}  |  Season {season}")
    print(f"{'='*70}\n")

    # ------------------------------------------------------------------ #
    # Step 1 — Fixtures                                                    #
    # ------------------------------------------------------------------ #
    print("STEP 1 — Fetching all fixtures")
    print("-" * 50)
    fixtures = []
    try:
        if not dry_run:
            fixtures = get_fixtures(season, league_id)
        total_fixtures = len(fixtures)
        print(f"✅ {total_fixtures} fixtures retrieved")
    except Exception as e:
        print(f"❌ Error fetching fixtures: {e}")

    # ------------------------------------------------------------------ #
    # Step 2 — H2H (FIXED: deduplicated pairs)                            #
    # ------------------------------------------------------------------ #
    print("\nSTEP 2 — Fetching H2H for unique team pairs")
    print("-" * 50)

    # Build unique canonical pairs from the fixture list
    unique_pairs: set[tuple[int, int]] = set()
    for f in fixtures:
        home_id = f.get("home_team_id")
        away_id = f.get("away_team_id")
        if home_id and away_id:
            unique_pairs.add(tuple(sorted([home_id, away_id])))

    total_pairs = len(unique_pairs)
    print(f"   {total_fixtures} fixtures  →  {total_pairs} unique pairs (saved "
          f"{total_fixtures - total_pairs} redundant API calls)")

    for idx, (team_a_id, team_b_id) in enumerate(sorted(unique_pairs), start=1):
        print(f"   [{idx}/{total_pairs}] H2H: {team_a_id} vs {team_b_id}")
        if not dry_run:
            try:
                fetch_h2h(team_a_id, team_b_id, last=5)
                time.sleep(REQUEST_INTERVAL)
            except Exception as e:
                print(f"   ⚠️  H2H failed for {team_a_id}-{team_b_id}: {e}")

    print("✅ H2H complete")

    # ------------------------------------------------------------------ #
    # Step 3 — Standings                                                   #
    # ------------------------------------------------------------------ #
    print("\nSTEP 3 — Fetching standings")
    print("-" * 50)
    try:
        if not dry_run:
            fetch_epl_table(league_id, season)
            time.sleep(REQUEST_INTERVAL)
        print("✅ Standings updated")
    except Exception as e:
        print(f"❌ Error fetching standings: {e}")

    # ------------------------------------------------------------------ #
    # Step 4 — Team stats                                                  #
    # ------------------------------------------------------------------ #
    print("\nSTEP 4 — Fetching team stats")
    print("-" * 50)
    teams = Team.objects.all()
    total_teams = teams.count()
    print(f"   {total_teams} teams found")

    for idx, team in enumerate(teams, start=1):
        print(f"   [{idx}/{total_teams}] {team.name}")
        if not dry_run:
            try:
                fetch_and_store_team_stats(season, team.api_id, league_id)
                time.sleep(REQUEST_INTERVAL)
            except Exception as e:
                print(f"   ⚠️  Stats failed for {team.name}: {e}")

    print("✅ Team stats complete")

    # ------------------------------------------------------------------ #
    # Step 5 — TeamFeatureStore (local, no API)                           #
    # ------------------------------------------------------------------ #
    print("\nSTEP 5 — Building TeamFeatureStore (local)")
    print("-" * 50)
    try:
        build_team_feature(season)
        print("✅ TeamFeatureStore updated")
    except Exception as e:
        print(f"❌ Failed to build TeamFeatureStore: {e}")

    # ------------------------------------------------------------------ #
    # Summary                                                              #
    # ------------------------------------------------------------------ #
    print(f"\n{'='*70}")
    print(f"  {mode}Central update complete.")
    print(f"  API calls made (approx): 1 (fixtures) + {total_pairs} (H2H) + 1 (standings) + {total_teams} (team stats)")
    print(f"  Total estimated: {1 + total_pairs + 1 + total_teams} calls")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the full data pipeline update")
    parser.add_argument("--season",    type=int, default=2024,  help="Season year (default: 2024)")
    parser.add_argument("--league",    type=int, default=39,    help="API-Football league ID (default: 39)")
    parser.add_argument("--dry-run",   action="store_true",     help="Print plan without hitting APIs")
    args = parser.parse_args()

    central_update(args.season, args.league, dry_run=args.dry_run)