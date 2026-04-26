# bot/keyboards.py

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

PAST_RESULTS_CHANNEL = "https://t.me/+2P7LAlcGZBc4ZmM0"


# =========================================
# Main Menu
# =========================================

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚽ Get Prediction", callback_data="get_prediction")],
        [InlineKeyboardButton("📈 Past Results", url=PAST_RESULTS_CHANNEL)],
        [InlineKeyboardButton("💎 My Subscription", callback_data="subscription")],
        [InlineKeyboardButton("💡 How It Works", callback_data="how_it_works")],
    ]
    return InlineKeyboardMarkup(keyboard)


# =========================================
# League Selection
# =========================================

def leagues_keyboard(leagues):
    """
    leagues: list of dicts with 'id' and 'name'
    """
    keyboard = []
    for league in leagues:
        label = f"🏴 {league['name']}"
        callback = f"league_{league['id']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)


# =========================================
# Fixture List
# =========================================

def fixtures_keyboard(fixtures, league_id, page=0):
    """
    fixtures: list of fixture dicts
    Shows 8 per page with pagination
    """
    keyboard = []

    for f in fixtures:
        home = f.get("home_team_name", "Home")
        away = f.get("away_team_name", "Away")
        raw_date = f.get("date", "")
        match_date = raw_date[5:10] if raw_date else "TBD"   # MM-DD
        match_time = raw_date[11:16] if len(raw_date) > 10 else ""

        if match_time:
            label = f"{home} vs {away}  |  {match_date} {match_time}"
        else:
            label = f"{home} vs {away}  |  {match_date}"

        callback = f"fixture_{f['fixture_id']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

    # Pagination row
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅ Previous", callback_data=f"fixtures_{league_id}_{page - 1}"))
    nav_row.append(InlineKeyboardButton("🔄 Load More", callback_data=f"fixtures_{league_id}_{page + 1}"))
    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton("🔙 Back to Leagues", callback_data="get_prediction")])
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])

    return InlineKeyboardMarkup(keyboard)


# =========================================
# Fixture Detail
# =========================================

def fixture_detail_keyboard(fixture_id, league_id, is_premium):
    if is_premium:
        keyboard = [
            [InlineKeyboardButton("🔮 Get Full AI Prediction", callback_data=f"insight_{fixture_id}")],
            [InlineKeyboardButton("🔙 Back to Fixtures", callback_data=f"fixtures_{league_id}_0")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("👁 See Preview (Free)", callback_data=f"preview_{fixture_id}")],
            [InlineKeyboardButton("🔒 Unlock Full Prediction — $5/mo", callback_data="subscribe")],
            [InlineKeyboardButton("🔙 Back to Fixtures", callback_data=f"fixtures_{league_id}_0")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
    return InlineKeyboardMarkup(keyboard)


# =========================================
# Insight / Prediction Screen
# =========================================

def after_insight_keyboard(fixture_id, league_id):
    keyboard = [
        [InlineKeyboardButton("🔙 Back to Fixtures", callback_data=f"fixtures_{league_id}_0")],
        [InlineKeyboardButton("📈 Past Results", url=PAST_RESULTS_CHANNEL)],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# =========================================
# Paywall / Subscribe Screen
# =========================================

def subscribe_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 Pay Now — $5/month", callback_data="pay_now")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def pay_now_keyboard(payment_link):
    keyboard = [
        [InlineKeyboardButton("💳 Complete Payment", url=payment_link)],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# =========================================
# Subscription Status Screen
# =========================================

def subscription_active_keyboard():
    keyboard = [
        [InlineKeyboardButton("⚽ Get Prediction", callback_data="get_prediction")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def subscription_inactive_keyboard():
    keyboard = [
        [InlineKeyboardButton("💎 Upgrade to Premium", callback_data="subscribe")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# =========================================
# Generic Back to Menu
# =========================================

def back_to_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)