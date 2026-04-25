import os
import sys
from django.db import transaction
from django.db.models import Q

# --- Django Setup ---
BASE_DIR = os.path.abspath(os.path.join(__file__, "../../../../../"))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from engine.models import TeamFeatureStore, TeamStats, Standing, Team, Fixture


def compute_last_5_stats(team_api_id: int, season: int) -> dict:
    """
    Compute last 5 finished matches for a team from the Fixture table.
    Returns a dict with wins, draws, losses, goals_for, goals_against.
    """
    finished_statuses = ["FT", "AET", "PEN"]

    recent_fixtures = Fixture.objects.filter(
        Q(home_team_id=team_api_id) | Q(away_team_id=team_api_id),
        season=season,
        status_short__in=finished_statuses,
    ).order_by("-date")[:5]

    stats = {
        "last_5_matches_played": 0,
        "last_5_wins": 0,
        "last_5_draws": 0,
        "last_5_losses": 0,
        "last_5_goals_for": 0,
        "last_5_goals_against": 0,
    }

    for fixture in recent_fixtures:
        stats["last_5_matches_played"] += 1
        is_home = fixture.home_team_id == team_api_id

        goals_for     = (fixture.goals_home if is_home else fixture.goals_away) or 0
        goals_against = (fixture.goals_away if is_home else fixture.goals_home) or 0

        stats["last_5_goals_for"]     += goals_for
        stats["last_5_goals_against"] += goals_against

        if goals_for > goals_against:
            stats["last_5_wins"] += 1
        elif goals_for == goals_against:
            stats["last_5_draws"] += 1
        else:
            stats["last_5_losses"] += 1

    return stats


def build_team_feature(season: int):
    """
    Populate/Update TeamFeatureStore for all teams for a given season.
    Idempotent: safe to run multiple times.

    Fixes applied vs original:
      - TeamStats lookup now filters by season (was silently using wrong season)
      - last_5_* fields are now computed from real Fixture data (were hardcoded 0)
    """

    teams = Team.objects.select_related("league").all()
    total_teams = teams.count()

    print(f"\n🔹 Building team features for season {season}")
    print(f"🔹 Found {total_teams} teams\n")

    created_count  = 0
    updated_count  = 0
    skipped_count  = 0

    for idx, team in enumerate(teams, start=1):
        print(f"[{idx}/{total_teams}] Processing: {team.name}")

        league = team.league

        try:
            with transaction.atomic():

                # --- TeamStats (FIXED: added season filter) ---
                stats = TeamStats.objects.filter(
                    team=team,
                    league=league,
                    season=season          # ← was missing; caused wrong-season data
                ).first()

                if not stats:
                    print(f"  ⚠️  No TeamStats for {team.name} season {season}. Skipping.")
                    skipped_count += 1
                    continue

                # --- Standing ---
                standing = Standing.objects.filter(
                    team=team,
                    league=league,
                    season=season
                ).first()

                if not standing:
                    print(f"  ⚠️  No Standing for {team.name} ({season}) — will store nulls.")

                # --- Last 5 Fixtures (FIXED: was always 0) ---
                last_5 = compute_last_5_stats(team.api_id, season)
                print(
                    f"  ↳ Last 5 → "
                    f"W{last_5['last_5_wins']} "
                    f"D{last_5['last_5_draws']} "
                    f"L{last_5['last_5_losses']} | "
                    f"GF:{last_5['last_5_goals_for']} "
                    f"GA:{last_5['last_5_goals_against']}"
                )

                obj, created = TeamFeatureStore.objects.update_or_create(
                    team=team,
                    league=league,
                    season=season,
                    defaults={
                        # Basic Info
                        "team_name":  team.name,
                        "logo_url":   team.logo_url,
                        "venue_name": team.venue_name,

                        # TeamStats
                        "matches_played_home":  stats.matches_played_home,
                        "matches_played_away":  stats.matches_played_away,
                        "matches_played_total": stats.matches_played_total,

                        "wins_home":  stats.wins_home,
                        "wins_away":  stats.wins_away,
                        "wins_total": stats.wins_total,

                        "draws_home":  stats.draws_home,
                        "draws_away":  stats.draws_away,
                        "draws_total": stats.draws_total,

                        "losses_home":  stats.losses_home,
                        "losses_away":  stats.losses_away,
                        "losses_total": stats.losses_total,

                        "goals_home":  stats.goals_home,
                        "goals_away":  stats.goals_away,
                        "goals_total": stats.goals_total,

                        "avg_goals_home":  stats.avg_goals_home,
                        "avg_goals_away":  stats.avg_goals_away,
                        "avg_goals_total": stats.avg_goals_total,

                        "conceded_home":  stats.conceded_home,
                        "conceded_away":  stats.conceded_away,
                        "conceded_total": stats.conceded_total,

                        "avg_conceded_home":  stats.avg_conceded_home,
                        "avg_conceded_away":  stats.avg_conceded_away,
                        "avg_conceded_total": stats.avg_conceded_total,

                        "over_15":  stats.over_15,
                        "under_15": stats.under_15,
                        "over_25":  stats.over_25,
                        "under_25": stats.under_25,
                        "over_35":  stats.over_35,
                        "under_35": stats.under_35,

                        "clean_sheet_home":  stats.clean_sheet_home,
                        "clean_sheet_away":  stats.clean_sheet_away,
                        "clean_sheet_total": stats.clean_sheet_total,

                        "failed_to_score_home":  stats.failed_to_score_home,
                        "failed_to_score_away":  stats.failed_to_score_away,
                        "failed_to_score_total": stats.failed_to_score_total,

                        # Standing (nullable safe)
                        "rank":        standing.rank        if standing else None,
                        "points":      standing.points      if standing else None,
                        "goals_diff":  standing.goals_diff  if standing else None,
                        "last_5_form": standing.last_5_form if standing else "",
                        "form":        stats.form,

                        # Last 5 matches (FIXED: now computed from real fixtures)
                        **last_5,
                    }
                )

                if created:
                    print(f"  ✔ Created feature row")
                    created_count += 1
                else:
                    print(f"  ↻ Updated feature row")
                    updated_count += 1

        except Exception as e:
            print(f"  ❌ Error processing {team.name}: {e}")
            skipped_count += 1

    print(f"\n✅ Team feature building complete.")
    print(f"   Created: {created_count} | Updated: {updated_count} | Skipped: {skipped_count}\n")


if __name__ == "__main__":
    season = 2024
    build_team_feature(season)