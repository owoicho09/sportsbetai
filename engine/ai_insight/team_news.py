"""
team_news.py
============
Fetches recent football news for a team from trusted RSS feeds,
then uses a cheap LLM call to extract only prediction-relevant
information (injuries, suspensions, form, squad news, manager comments).

Used as a pre-step in generate_fixture_insight.py before the main
prediction prompt is built.

How it works:
    1. Fetch latest articles from trusted football RSS feeds
    2. Filter articles that mention the team name
    3. Pass filtered headlines to cheap LLM to extract only
       prediction-relevant bullets (injuries, suspensions, etc.)
    4. Return clean bullet points to be injected into the prediction prompt

Cache: 10 hours per team name (Django cache framework).
Fallback: if anything fails, returns empty string — prediction continues.

No API key needed for RSS feeds.

.env keys required:
    OPENAI_API_KEY or ANTHROPIC_API_KEY (whichever LLM_PROVIDER is set to)
"""

import os
import sys
import hashlib
import feedparser
import requests as http_requests
from datetime import datetime, timedelta, timezone

# --- Django Setup (must happen before any Django imports) ---
BASE_DIR = os.path.abspath(os.path.join(__file__, "../../.."))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

LLM_PROVIDER   = os.getenv("LLM_PROVIDER", "openai").lower()

OPENAI_API_KEY    = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Cheap/fast models for the pre-filter step
OPENAI_CHEAP_MODEL    = "gpt-4o-mini"
ANTHROPIC_CHEAP_MODEL = "claude-haiku-4-5-20251001"

# Cache duration in seconds (10 hours)
CACHE_TTL = 60 * 60 * 10

# How many days back to include articles
NEWS_DAYS_BACK = 5

# Max articles to send to LLM filter
MAX_ARTICLES = 12

# ---------------------------------------------------------------------------
# Trusted football RSS feeds
# Free, no auth, always fresh
# ---------------------------------------------------------------------------
RSS_FEEDS = [
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.skysports.com/rss/12040",
    "https://www.goal.com/feeds/en/news",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.theguardian.com/football/rss",
    "https://www.football365.com/feed",
    "https://talksport.com/football/feed/",
]


# ---------------------------------------------------------------------------
# RSS fetch and filter
# ---------------------------------------------------------------------------

def _fetch_rss_articles(team_name: str) -> list[dict]:
    """
    Fetch articles from all RSS feeds and filter to only those
    that mention the team name. Returns list of {title, description} dicts.
    """
    team_lower = team_name.lower()
    cutoff     = datetime.now(timezone.utc) - timedelta(days=NEWS_DAYS_BACK)
    found      = []

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)

            for entry in feed.entries:
                title       = (getattr(entry, "title",   "") or "").strip()
                description = (getattr(entry, "summary", "") or "").strip()
                published   = getattr(entry, "published_parsed", None)

                # Skip if too old
                if published:
                    pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
                    if pub_dt < cutoff:
                        continue

                # Only keep articles that mention the team name
                combined = f"{title} {description}".lower()
                if team_lower not in combined:
                    continue

                # Avoid duplicates by title
                if any(a["title"] == title for a in found):
                    continue

                found.append({
                    "title":       title,
                    "description": description,
                })

                if len(found) >= MAX_ARTICLES:
                    break

        except Exception as e:
            print(f"[TEAM_NEWS] RSS feed failed ({feed_url}): {e}")
            continue

        if len(found) >= MAX_ARTICLES:
            break

    print(f"[TEAM_NEWS] {team_name}: {len(found)} relevant articles found across RSS feeds")
    return found


# ---------------------------------------------------------------------------
# LLM pre-filter — cheap model only
# ---------------------------------------------------------------------------

def _build_filter_prompt(team_name: str, articles: list[dict]) -> str:
    lines = []
    for i, a in enumerate(articles, 1):
        lines.append(f"{i}. {a['title']}")
        if a["description"]:
            desc = a["description"][:200]
            lines.append(f"   {desc}")

    articles_text = "\n".join(lines)

    return f"""
You are a football analyst assistant. Below are recent news headlines about {team_name}.

Your job: extract ONLY information that would help predict the outcome of {team_name}'s next match.

Relevant information includes:
- Injuries or fitness concerns for key players
- Suspensions or bans
- Players returning from injury
- Manager changes or tactical shifts
- Squad morale issues or internal conflict
- Rotation hints or key players being rested
- Any other factor that directly affects match performance

Rules:
- Return a maximum of 4 bullet points
- Each bullet must be a single clear sentence
- Only include information that is genuinely prediction-relevant
- If none of the headlines contain prediction-relevant information, return exactly: NO_RELEVANT_NEWS
- Do not include transfer rumours, historical stats, or general club news unless it directly affects the upcoming match
- No markdown, no headers, just bullet points starting with "•"

Headlines:
{articles_text}
""".strip()


def _call_cheap_llm(prompt: str) -> str:
    try:
        if LLM_PROVIDER == "claude":
            headers = {
                "x-api-key":         ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
            }
            body = {
                "model":      ANTHROPIC_CHEAP_MODEL,
                "max_tokens": 300,
                "system":     "You are a concise football analyst. Follow instructions exactly.",
                "messages":   [{"role": "user", "content": prompt}],
            }
            response = http_requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=body,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()["content"][0]["text"].strip()

        else:  # openai
            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type":  "application/json",
            }
            body = {
                "model":       OPENAI_CHEAP_MODEL,
                "messages": [
                    {
                        "role":    "system",
                        "content": "You are a concise football analyst. Follow instructions exactly.",
                    },
                    {"role": "user", "content": prompt},
                ],
                "max_tokens":  300,
                "temperature": 0.1,
            }
            response = http_requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=body,
                timeout=15,
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print(f"[TEAM_NEWS] LLM filter call failed: {e}")
        return ""


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def get_team_news(team_name: str) -> str:
    """
    Main entry point. Returns prediction-relevant news bullets for a team,
    or empty string if nothing found. Cached for 10 hours.
    """
    from django.core.cache import cache

    if not team_name:
        return ""

    date_str  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cache_key = f"team_news_{hashlib.md5(f'{team_name}{date_str}'.encode()).hexdigest()}"

    cached = cache.get(cache_key)
    if cached is not None:
        print(f"[TEAM_NEWS] {team_name}: returning cached news")
        return cached

    articles = _fetch_rss_articles(team_name)

    if not articles:
        print(f"[TEAM_NEWS] {team_name}: no articles found — continuing without news")
        cache.set(cache_key, "", CACHE_TTL)
        return ""

    prompt   = _build_filter_prompt(team_name, articles)
    raw_text = _call_cheap_llm(prompt)

    if not raw_text or raw_text.strip() == "NO_RELEVANT_NEWS":
        print(f"[TEAM_NEWS] {team_name}: no prediction-relevant news found")
        cache.set(cache_key, "", CACHE_TTL)
        return ""

    result = raw_text.strip()
    print(f"[TEAM_NEWS] {team_name}: extracted news:\n{result}")

    cache.set(cache_key, result, CACHE_TTL)
    return result


# ---------------------------------------------------------------------------
# CLI / debug — run as: python team_news.py Arsenal
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    team = sys.argv[1] if len(sys.argv) > 1 else "manchester united"
    print(f"\n=== Testing team news for: {team} ===\n")

    articles = _fetch_rss_articles(team)

    print("\n--- RAW ARTICLES ---")
    for a in articles:
        print(f"• {a['title']}")
        if a["description"]:
            print(f"  {a['description'][:150]}")
    print()

    if articles:
        prompt = _build_filter_prompt(team, articles)
        print("--- LLM FILTER RESPONSE ---")
        raw = _call_cheap_llm(prompt)
        print(raw)

    print("\n--- FINAL RESULT ---")
    from django.core.cache import cache
    date_str  = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cache_key = f"team_news_{hashlib.md5(f'{team}{date_str}'.encode()).hexdigest()}"
    cache.delete(cache_key)

    result = get_team_news(team)
    print(result if result else "(no relevant news found)")