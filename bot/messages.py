# bot/messages.py

WELCOME_MESSAGE = """
🤖 *SportsBet AI*

Your personal AI football analyst.
Data-driven predictions. No noise. No guesswork.

*Every prediction includes:*
✅ Predicted winner & confidence rating
✅ Both Teams to Score probability
✅ Over / Under 2.5 goals
✅ Best recommended bet

Free users get a preview.
Premium unlocks everything — *$5/month.*

👇 What would you like to do?
"""

HOW_IT_WORKS_MESSAGE = """
🧠 *How SportsBet AI Works*

*① Data Collection*
We pull live stats from top football data providers —
form, H2H history, home/away records, goals data and more.

*② AI Analysis*
Our model processes every data point and builds
a complete match profile. No gut feeling. Pure data.

*③ Your Prediction*
You receive a clear, structured breakdown:
• Predicted winner with confidence level
• Both Teams to Score probability  
• Over/Under 2.5 goals
• Best recommended bet

*④ You Decide*
Use it as your edge. We give you the analysis —
the final call is always yours.

━━━━━━━━━━━━━━━━━━
💎 *Premium — $5/month*
Unlimited predictions. Every match. Every league.
Multi-match analysis in one tap.
Cancel anytime.
"""

CHOOSE_LEAGUE_MESSAGE = """
🏆 *Select a League*

Choose the league you want predictions for.
"""

NO_LEAGUES_MESSAGE = """
😕 *No leagues available right now.*

We're loading fixtures for the next matchday.
Check back soon — we update regularly.
"""

NO_FIXTURES_MESSAGE = """
📭 *No upcoming fixtures found.*

All matches may have been played or fixtures
haven't been published yet for this league.

Try another league or check back closer to matchday.
"""

TEASER_PAYWALL_MESSAGE = """
🔒 *Full Prediction Locked*

You're one step away from the full AI breakdown.

*What Premium unlocks:*
✅ Predicted winner with confidence rating
✅ Both Teams to Score probability
✅ Over / Under 2.5 analysis
✅ AI-recommended best bet
✅ Multiple match predictions 

*$5/month — less than the cost of one bad bet.*
Cancel anytime. Instant access after payment.

👇 Tap below to unlock.
"""

PAYMENT_INSTRUCTIONS_MESSAGE = """
💳 *Upgrade to Premium*

*Price:* $5 / month
*Access:* Unlimited predictions. All matches. All leagues.

*How it works:*
1️⃣ Tap the button below
2️⃣ Complete payment securely via Paystack
3️⃣ You're unlocked *instantly* ✅

_Your access activates the moment payment is confirmed._
"""

PREMIUM_ALREADY_ACTIVE = """
✅ *Premium Active*

You have full access to all predictions.

Go get your edge 🎯
"""

PREMIUM_GRANTED_MESSAGE = """
🎉 *You're In — Welcome to Premium!*

Payment confirmed. Your access is now active.

Here's what you can do:
⚽ Get AI predictions for any match
📊 Analyse multiple fixtures at once
🎯 See confidence ratings & best bets

Tap below to get your first prediction 👇
"""

SUBSCRIPTION_INACTIVE_MESSAGE = """
❌ *No Active Subscription*

You're currently on the free plan.

Upgrade to Premium for *$5/month* and unlock:
✅ Full AI predictions for every match
✅ Confidence ratings & recommended bets
✅ Multi-match predictions in one tap
✅ Unlimited access — all leagues

👇 Tap below to upgrade instantly.
"""

GENERATING_MESSAGE = """
⚙️ *Analysing match data...*

Pulling stats, form, H2H records and team news.
This usually takes 10–20 seconds.

"""

GENERATING_MULTI_MESSAGE = """
⚙️ *Analysing multiple fixtures...*

Running AI analysis on each match.
This may take 30–60 seconds depending on the number selected.

"""

SELECT_FIXTURES_MESSAGE = """
📋 *Select Fixtures to Analyse*

Tap the matches you want predictions for.
When you're done, tap *✅ Get Predictions*.

_Premium feature — unlimited selections._
"""

ERROR_TIMEOUT = """
⏱ *Request timed out.*

The server took too long to respond.
Please try again in a moment.
"""

ERROR_CONNECTION = """
🔌 *Could not reach the server.*

Please check your connection and try again.
If this keeps happening, our server may be restarting.
"""

ERROR_GENERAL = """
❌ *Something went wrong.*

Please try again. If the issue persists,
contact support.
"""


def upcoming_fixtures_message(league_name: str, page: int = 0) -> str:
    page_num = page + 1
    return (
        f"📅 *{league_name}*\n\n"
        f"Select a fixture to see the AI prediction.\n"
        f"_Page {page_num}_"
    )


def fixture_detail_message(home, away, league, match_date, match_time, round_, is_premium):
    status = "💎 *Premium*" if is_premium else "🆓 *Free Preview*"
    base = (
        f"⚽ *{home} vs {away}*\n\n"
        f"🏆 {league}\n"
        f"📅 {match_date}   🕐 {match_time}\n"
        f"🔄 {round_}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Account: {status}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
    )
    if is_premium:
        base += "Tap below to get the full AI prediction 👇"
    else:
        base += (
            "Tap *See Preview* for a free teaser.\n"
            "Unlock the full breakdown with Premium — *$5/month.*"
        )
    return base


def insight_message(home, away, insight):
    if isinstance(insight, str):
        return (
            f"🔮 *{home} vs {away}*\n\n"
            f"{insight}\n\n"
            f"_Powered by SportsBet AI_"
        )

    analysis    = insight.get("analysis", "")
    winner      = (insight.get("predicted_winner") or "N/A").title()
    confidence  = (insight.get("confidence") or "N/A").title()
    btts        = (insight.get("btts") or "N/A").title()
    over        = (insight.get("over_2_5") or "N/A").title()
    bet         = insight.get("recommended_bet", "N/A")

    # Confidence emoji
    conf_emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(confidence, "⚪")

    return (
        f"🔮 *{home} vs {away}*\n\n"
        f"📊 *Analysis*\n"
        f"{analysis}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏆 *Winner:* {winner}\n"
        f"🎯 *Confidence:* {conf_emoji} {confidence}\n"
        f"⚽ *BTTS:* {btts}\n"
        f"📈 *Over 2.5:* {over}\n"
        f"💡 *Best Bet:* {bet}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"_Powered by SportsBet AI_"
    )


def multi_insight_message(predictions: list[dict]) -> str:
    """
    Format multiple predictions into one clean message.
    predictions: list of dicts with home, away, insight keys
    """
    lines = [f"🔮 *Multi-Match AI Predictions*\n"]

    for i, pred in enumerate(predictions, 1):
        home    = pred.get("home", "Home")
        away    = pred.get("away", "Away")
        insight = pred.get("insight", {})

        if isinstance(insight, str) or not insight:
            lines.append(f"*{i}. {home} vs {away}*\n❌ Prediction unavailable\n")
            continue

        winner     = (insight.get("predicted_winner") or "N/A").title()
        confidence = (insight.get("confidence") or "N/A").title()
        btts       = (insight.get("btts") or "N/A").title()
        over       = (insight.get("over_2_5") or "N/A").title()
        bet        = insight.get("recommended_bet", "N/A")
        conf_emoji = {"High": "🟢", "Medium": "🟡", "Low": "🔴"}.get(confidence, "⚪")

        lines.append(
            f"*{i}. {home} vs {away}*\n"
            f"🏆 {winner}  {conf_emoji} {confidence}\n"
            f"⚽ BTTS: {btts}  📈 O2.5: {over}\n"
            f"💡 {bet}\n"
        )

    lines.append("━━━━━━━━━━━━━━━━━━")
    lines.append("_Powered by SportsBet AI_")
    return "\n".join(lines)