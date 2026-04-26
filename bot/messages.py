# bot/messages.py

WELCOME_MESSAGE = """
🤖 *SportsBet AI*

Get AI-powered predictions for football matches.
Stats, form, H2H analysis — all done for you.

*What you get:*
✅ Predicted winner
✅ BTTS & Over 2.5 probability
✅ Confidence rating
✅ Best bet recommendation

Free users get a preview.
Premium users get everything. *$5/month.*

👇 What would you like to do?
"""

HOW_IT_WORKS_MESSAGE = """
🧠 *How SportsBet AI Works*

*Step 1 — Data*
We pull live stats from top football APIs.
Form, H2H history, home/away record.

*Step 2 — Analysis*
Our AI processes everything and builds a match profile.
No guessing. Pure data.

*Step 3 — Prediction*
You get a clear, structured prediction:
• Who wins
• Will both teams score
• Over or under 2.5 goals
• Confidence level
• Best recommended bet

*Step 4 — You decide*
Use it as your edge. The rest is up to you.

💎 *Premium — $5/month*
Unlimited predictions. Every match. Every week.
"""

CHOOSE_LEAGUE_MESSAGE = """
🏆 *Choose a League*

Select the league you want predictions for.
More leagues coming soon.
"""

NO_LEAGUES_MESSAGE = """
😕 No leagues available right now.
Check back soon — we're adding more.
"""

NO_FIXTURES_MESSAGE = """
📭 *No upcoming fixtures found.*

Either all matches have been played
or fixtures haven't been loaded yet.

Check back closer to the next matchday.
"""

TEASER_PAYWALL_MESSAGE = """
🔒 *Full Prediction Locked*

You've seen the teams and the matchup.
The full AI breakdown is one step away.

*What's behind the lock:*
✅ Predicted winner with confidence rating
✅ BTTS probability
✅ Over/Under 2.5 analysis
✅ Recommended bet

*$5/month — less than one bet.*
Cancel anytime.

👇 Tap to unlock everything.
"""

PAYMENT_INSTRUCTIONS_MESSAGE = """
💳 *Upgrade to Premium*

*Price:* $5/month
*Access:* Unlimited predictions. All matches.

*How to pay:*
1. Tap the button below
2. Complete payment on Paystack
3. You're unlocked *instantly* ✅

_Payment is processed securely by Paystack._
"""

PREMIUM_ALREADY_ACTIVE = """
✅ *Your Premium is Active*

You have full access to all predictions.
Go get your edge 🎯
"""

PREMIUM_GRANTED_MESSAGE = """
🎉 *Payment Confirmed — You're In!*

Your Premium is now active.
You have full access to all AI predictions.

Tap below to get your first prediction 👇
"""

SUBSCRIPTION_INACTIVE_MESSAGE = """
❌ *No Active Subscription*

You're currently on the free plan.

Upgrade to Premium for *$5/month* and unlock:
✅ Full AI predictions
✅ Confidence ratings
✅ Recommended bets
✅ Unlimited matches

👇 Tap below to upgrade.
"""

GENERATING_MESSAGE = "⏳ Generating AI prediction...\n\nThis takes a few seconds."

ERROR_TIMEOUT = "⏱ Request timed out. Please try again."
ERROR_CONNECTION = "🔌 Server unreachable. Please try again shortly."
ERROR_GENERAL = "❌ Something went wrong. Please try again."


def upcoming_fixtures_message(league_name, page=0):
    page_num = page + 1
    return (
        f"📅 *{league_name} — Upcoming Fixtures*\n\n"
        f"Tap a match to see the AI prediction.\n"
        f"_Page {page_num}_"
    )


def fixture_detail_message(home, away, league, match_date, match_time, round_, is_premium):
    base = (
        f"⚽ *{home} vs {away}*\n\n"
        f"🏆 {league}\n"
        f"📅 {match_date}  🕐 {match_time}\n"
        f"🔄 {round_}\n\n"
    )
    if is_premium:
        base += "🔮 *Tap below to get the full AI prediction.*"
    else:
        base += (
            "👁 *Free Preview Available*\n\n"
            "You'll see a teaser of the analysis.\n"
            "Unlock full prediction with Premium — *$5/month.*"
        )
    return base


def insight_message(home, away, insight):
    if isinstance(insight, str):
        return (
            f"🔮 *AI Prediction — {home} vs {away}*\n\n"
            f"{insight}\n\n"
            f"_Powered by SportsBet AI_"
        )

    analysis = insight.get("analysis", "")
    winner = insight.get("predicted_winner", "N/A")
    confidence = insight.get("confidence", "N/A")
    btts = insight.get("btts", "N/A")
    over = insight.get("over_2_5", "N/A")
    bet = insight.get("recommended_bet", "N/A")

    return (
        f"🔮 *AI Prediction — {home} vs {away}*\n\n"
        f"📊 *Analysis:*\n{analysis}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏆 *Predicted Winner:* {winner}\n"
        f"🎯 *Confidence:* {confidence}\n"
        f"⚽ *BTTS:* {btts}\n"
        f"📈 *Over 2.5:* {over}\n"
        f"💡 *Best Bet:* {bet}\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"_Powered by SportsBet AI_"
    )