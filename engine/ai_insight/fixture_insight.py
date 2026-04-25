"""
generate_insight.py
====================
Generates (or returns cached) AI betting insight for a fixture.

LLM provider is configurable — defaults to OpenAI GPT.
Set LLM_PROVIDER in your .env to switch:

    LLM_PROVIDER=openai    # default
    LLM_PROVIDER=claude    # use Anthropic Claude

Required .env keys:
    OPENAI_API_KEY=sk-...              (if using openai)
    OPENAI_MODEL=gpt-4o               (optional, defaults to gpt-4o)
    ANTHROPIC_API_KEY=sk-ant-...       (if using claude)
    ANTHROPIC_MODEL=claude-sonnet-...  (optional)
"""

import os
import sys
import json
import hashlib
import requests as http_requests
from django.db.models import Q

# --- Django Setup ---
BASE_DIR = os.path.abspath(os.path.join(__file__, "../../.."))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from dotenv import load_dotenv
load_dotenv()

from engine.models import Fixture, League, Team, TeamFeatureStore, H2HMatch, MatchInsight

# ---------------------------------------------------------------------------
# Config — read from .env, default to openai
# ---------------------------------------------------------------------------
LLM_PROVIDER      = os.getenv("LLM_PROVIDER", "openai").lower()   # "openai" | "claude"

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL      = os.getenv("OPENAI_MODEL", "gpt-4o")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL   = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")


# ---------------------------------------------------------------------------
# LLM backends
# ---------------------------------------------------------------------------

def _call_openai(prompt: str) -> dict:
    if not OPENAI_API_KEY:
        raise EnvironmentError("OPENAI_API_KEY is not set in your .env file.")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type":  "application/json",
    }
    body = {
        "model":           OPENAI_MODEL,
        "response_format": {"type": "json_object"},  # native JSON mode — no parsing surprises
        "messages": [
            {
                "role":    "system",
                "content": (
                    "You are an expert football betting analyst. "
                    "You respond ONLY with valid JSON matching the schema in the user prompt. "
                    "No markdown, no code fences, no extra text."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens":  1024,
        "temperature": 0.3,
    }

    response = http_requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers=headers,
        json=body,
        timeout=30,
    )
    response.raise_for_status()
    raw_text = response.json()["choices"][0]["message"]["content"].strip()
    return json.loads(raw_text)


def _call_claude(prompt: str) -> dict:
    if not ANTHROPIC_API_KEY:
        raise EnvironmentError("ANTHROPIC_API_KEY is not set in your .env file.")

    headers = {
        "x-api-key":         ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type":      "application/json",
    }
    body = {
        "model":      ANTHROPIC_MODEL,
        "max_tokens": 1024,
        "system": (
            "You are an expert football betting analyst. "
            "You respond ONLY with valid JSON matching the schema in the user prompt. "
            "No markdown, no code fences, no extra text."
        ),
        "messages": [{"role": "user", "content": prompt}],
    }

    response = http_requests.post(
        "https://api.anthropic.com/v1/messages",
        headers=headers,
        json=body,
        timeout=30,
    )
    response.raise_for_status()
    raw_text = response.json()["content"][0]["text"].strip()
    return json.loads(raw_text)


def call_llm(prompt: str) -> dict:
    """
    Route to the active LLM provider.
    Provider is set by LLM_PROVIDER env var (default: openai).
    Can be overridden at runtime by setting the module-level LLM_PROVIDER variable.
    """
    provider = LLM_PROVIDER
    model    = OPENAI_MODEL if provider == "openai" else ANTHROPIC_MODEL
    #print(f"🤖 LLM: {provider.upper()} / {model}")

    try:
        if provider == "claude":
            result = _call_claude(prompt)
        else:
            result = _call_openai(prompt)

        required = {
            "insight_text", "predicted_winner", "confidence",
            "btts_probability", "over_25_probability", "recommended_bet",
        }
        missing = required - result.keys()
        if missing:
            print(f"⚠️  LLM response missing keys: {missing}")

        return result

    except json.JSONDecodeError as e:
        print(f"⚠️  LLM returned non-JSON: {e}")
        return {"insight_text": "", "error": "json_parse_failed"}
    except Exception as e:
        print(f"❌ LLM call failed: {e}")
        return {"insight_text": "", "error": str(e)}


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------
def build_prompt(
    home: "TeamFeatureStore",
    away: "TeamFeatureStore",
    fixture: "Fixture",
    h2h_text: str,
) -> str:

    def pct(count, total):
        if not total:
            return "0%"
        return f"{round(count / total * 100)}%"

    h_mp  = home.matches_played_home  or 1
    a_mp  = away.matches_played_away  or 1
    h_tot = home.matches_played_total or 1
    a_tot = away.matches_played_total or 1

    return f"""
Analyse this fixture and respond ONLY with a JSON object matching this exact schema:

{{
  "insight_text":        "<3-5 sentences of natural language analysis>",
  "predicted_winner":    "<home|away|draw>",
  "confidence":          "<low|medium|high>",
  "btts_probability":    "<low|medium|high>",
  "over_25_probability": "<low|medium|high>",
  "recommended_bet":     "<short betting tip e.g. 'Home Win & Over 2.5'>"
}}

=== FIXTURE ===
{home.team_name} (Home) vs {away.team_name} (Away)
Season: {fixture.season}  |  Round: {fixture.league_round or 'N/A'}

=== FORM ===
{home.team_name} season form : {home.form or 'N/A'}
{home.team_name} last-5 form : {home.last_5_form or 'N/A'}  (W{home.last_5_wins} D{home.last_5_draws} L{home.last_5_losses}, GF:{home.last_5_goals_for} GA:{home.last_5_goals_against})
{away.team_name} season form : {away.form or 'N/A'}
{away.team_name} last-5 form : {away.last_5_form or 'N/A'}  (W{away.last_5_wins} D{away.last_5_draws} L{away.last_5_losses}, GF:{away.last_5_goals_for} GA:{away.last_5_goals_against})

=== STANDINGS ===
{home.team_name} : Rank {home.rank} | {home.points} pts | GD {home.goals_diff}
{away.team_name} : Rank {away.rank} | {away.points} pts | GD {away.goals_diff}

=== GOALS (home venue / away venue) ===
{home.team_name} at home — scored: {home.goals_home} ({home.avg_goals_home:.2f}/g) | conceded: {home.conceded_home} ({home.avg_conceded_home:.2f}/g) in {h_mp} matches
{away.team_name} away    — scored: {away.goals_away} ({away.avg_goals_away:.2f}/g) | conceded: {away.conceded_away} ({away.avg_conceded_away:.2f}/g) in {a_mp} matches

=== CLEAN SHEETS ===
{home.team_name} at home : {home.clean_sheet_home}/{h_mp} ({pct(home.clean_sheet_home, h_mp)})
{away.team_name} away    : {away.clean_sheet_away}/{a_mp} ({pct(away.clean_sheet_away, a_mp)})

=== FAILED TO SCORE ===
{home.team_name} at home : {home.failed_to_score_home}/{h_mp} ({pct(home.failed_to_score_home, h_mp)})
{away.team_name} away    : {away.failed_to_score_away}/{a_mp} ({pct(away.failed_to_score_away, a_mp)})

=== OVER/UNDER (total matches) ===
{home.team_name} — Over 1.5: {home.over_15}/{h_tot} | Over 2.5: {home.over_25}/{h_tot} ({pct(home.over_25, h_tot)}) | Over 3.5: {home.over_35}/{h_tot}
{away.team_name} — Over 1.5: {away.over_15}/{a_tot} | Over 2.5: {away.over_25}/{a_tot} ({pct(away.over_25, a_tot)}) | Over 3.5: {away.over_35}/{a_tot}

=== HEAD-TO-HEAD (last 5) ===
{h2h_text}

=== INSTRUCTIONS ===
- Base every claim strictly on the stats above — do NOT hallucinate.
- insight_text must cover: form trend, H2H pattern, attacking/defensive tendencies, and prediction rationale.
- predicted_winner must be exactly one of: home, away, draw.
- Respond with the JSON object only. No extra text outside the JSON.
""".strip()


# ---------------------------------------------------------------------------
# Main insight generator
# ---------------------------------------------------------------------------
def generate_fixture_insight(fixture_id, force: bool = False) -> dict | None:
    """
    Generate (or return cached) AI insight for a fixture.

    Args:
        fixture_id : The Fixture.fixture_id value (int or str).
        force      : If True, regenerate even if a cached insight exists.

    Returns:
        dict with insight fields, or None on failure.
    """
    print(f"\n=== Generating AI Insight for Fixture ID: {fixture_id} ===")

    # --- Fixture ---
    try:
        fixture = Fixture.objects.get(fixture_id=fixture_id)
    except Fixture.DoesNotExist:
        print(f"❌ Fixture {fixture_id} not found")
        return None

    # --- Related objects ---
    try:
        league    = League.objects.get(api_id=fixture.league_id)
        home_team = Team.objects.get(api_id=fixture.home_team_id)
        away_team = Team.objects.get(api_id=fixture.away_team_id)
    except (League.DoesNotExist, Team.DoesNotExist) as e:
        print(f"❌ Missing League/Team record: {e}")
        return None

    # --- Feature store rows ---
    try:
        home_stats = TeamFeatureStore.objects.get(team=home_team, league=league)
        away_stats = TeamFeatureStore.objects.get(team=away_team, league=league)
    except TeamFeatureStore.DoesNotExist as e:
        print(f"❌ TeamFeatureStore missing: {e}")
        return None

    # --- H2H summary (bidirectional) ---
    h2h_matches = H2HMatch.objects.filter(
        Q(home_team_id=fixture.home_team_id, away_team_id=fixture.away_team_id) |
        Q(home_team_id=fixture.away_team_id, away_team_id=fixture.home_team_id)
    ).order_by("-date")[:5]

    if h2h_matches.exists():
        h2h_lines = [
            f"  {m.home_team_name} {m.home_goals}-{m.away_goals} {m.away_team_name}"
            f"  ({m.date.strftime('%Y-%m-%d')})"
            for m in h2h_matches
        ]
        h2h_text = "\n".join(h2h_lines)
    else:
        h2h_text = "No H2H data available."

    print(f" H2H matches found: {h2h_matches.count()}")

    # --- Build prompt & hash ---
    prompt     = build_prompt(home_stats, away_stats, fixture, h2h_text)
    input_hash = hashlib.sha256(prompt.encode()).hexdigest()

    # --- Cache check ---
    existing = getattr(fixture, "insight", None)
    if existing and not force:
        if existing.input_hash == input_hash:
            print("✅ Insight up-to-date (data unchanged). Returning cached.")
            return _insight_to_dict(existing)
        else:
            print("↻ Data changed — regenerating insight.")
            existing.delete()

    # --- Call LLM ---
    result = call_llm(prompt)

    if not result.get("insight_text"):
        print(f"❌ LLM returned empty insight. Error: {result.get('error')}")
        return None

    # --- Persist ---
    MatchInsight.objects.create(
        fixture=fixture,
        input_hash=input_hash,
        insight_text=result.get("insight_text", ""),
        predicted_winner=result.get("predicted_winner"),
        confidence=result.get("confidence"),
        btts_probability=result.get("btts_probability"),
        over_25_probability=result.get("over_25_probability"),
        recommended_bet=result.get("recommended_bet"),
    )

    print(" Insight generated and stored.")
    print(f"\n--- INSIGHT ---\n{result.get('insight_text')}")
    print(f"Predicted winner : {result.get('predicted_winner')}")
    print(f"Confidence       : {result.get('confidence')}")
    print(f"BTTS             : {result.get('btts_probability')}")
    print(f"Over 2.5         : {result.get('over_25_probability')}")
    print(f"Recommended bet  : {result.get('recommended_bet')}")

    return result


def _insight_to_dict(insight: "MatchInsight") -> dict:
    return {
        "insight_text":        insight.insight_text,
        "predicted_winner":    insight.predicted_winner,
        "confidence":          insight.confidence,
        "btts_probability":    insight.btts_probability,
        "over_25_probability": insight.over_25_probability,
        "recommended_bet":     insight.recommended_bet,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate AI insight for a fixture")
    parser.add_argument("fixture_id",  help="Fixture ID to analyse")
    parser.add_argument("--force",     action="store_true", help="Force regeneration even if cached")
    parser.add_argument(
        "--provider",
        choices=["openai", "claude"],
        help="Override LLM_PROVIDER from .env for this run",
    )
    args = parser.parse_args()

    # Runtime provider override without touching .env
    if args.provider:
        import engine.ai_insight.generate_insight as _self
        _self.LLM_PROVIDER = args.provider
        print(f"⚙️  Provider overridden via CLI: {args.provider.upper()}")

    generate_fixture_insight(args.fixture_id, force=args.force)