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
    keyboard = []
    for league in leagues:
        label    = f"🏴 {league['name']}"
        callback = f"league_{league['id']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="main_menu")])
    return InlineKeyboardMarkup(keyboard)


# =========================================
# Fixture List
# =========================================

def fixtures_keyboard(fixtures, league_id, page=0, is_premium=False):
    keyboard = []

    for f in fixtures:
        home      = f.get("home_team_name", "Home")
        away      = f.get("away_team_name", "Away")
        raw_date  = f.get("date", "")
        match_date = raw_date[5:10] if raw_date else "TBD"
        match_time = raw_date[11:16] if len(raw_date) > 10 else ""

        label    = f"{home} vs {away}  |  {match_date} {match_time}".strip()
        callback = f"fixture_{f['fixture_id']}"
        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

    # Multi-fixture button for premium users only
    if is_premium and fixtures:
        keyboard.append([
            InlineKeyboardButton(
                "📊 Select Multiple Fixtures",
                callback_data=f"multi_select_{league_id}_{page}"
            )
        ])

    # Pagination
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅ Prev", callback_data=f"fixtures_{league_id}_{page - 1}"))
    nav_row.append(InlineKeyboardButton("More ➡", callback_data=f"fixtures_{league_id}_{page + 1}"))
    keyboard.append(nav_row)

    keyboard.append([InlineKeyboardButton("🔙 Back to Leagues", callback_data="get_prediction")])
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])

    return InlineKeyboardMarkup(keyboard)


# =========================================
# Multi-Fixture Selection (Premium)
# =========================================

def multi_select_keyboard(fixtures, league_id, page, selected_ids: list):
    """
    Shows fixtures as toggleable checkboxes.
    selected_ids: list of fixture_ids currently selected
    """
    keyboard = []

    for f in fixtures:
        fid       = str(f.get("fixture_id", ""))
        home      = f.get("home_team_name", "Home")
        away      = f.get("away_team_name", "Away")
        raw_date  = f.get("date", "")
        match_date = raw_date[5:10] if raw_date else "TBD"

        is_selected = fid in selected_ids
        check   = "✅" if is_selected else "⬜"
        label   = f"{check} {home} vs {away} | {match_date}"
        callback = f"toggle_{fid}"

        keyboard.append([InlineKeyboardButton(label, callback_data=callback)])

    # Action row
    count = len(selected_ids)
    if count > 0:
        keyboard.append([
            InlineKeyboardButton(
                f"🔮 Get {count} Prediction{'s' if count > 1 else ''}",
                callback_data=f"run_multi_{league_id}"
            )
        ])

    keyboard.append([InlineKeyboardButton("🔙 Back to Fixtures", callback_data=f"fixtures_{league_id}_{page}")])
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
            [InlineKeyboardButton("👁 See Free Preview", callback_data=f"preview_{fixture_id}")],
            [InlineKeyboardButton("🔒 Unlock Premium — $5/mo", callback_data="subscribe")],
            [InlineKeyboardButton("🔙 Back to Fixtures", callback_data=f"fixtures_{league_id}_0")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
        ]
    return InlineKeyboardMarkup(keyboard)


# =========================================
# After Insight
# =========================================

def after_insight_keyboard(fixture_id, league_id):
    keyboard = [
        [InlineKeyboardButton("⚽ Another Prediction", callback_data=f"fixtures_{league_id}_0")],
        [InlineKeyboardButton("📈 Past Results", url=PAST_RESULTS_CHANNEL)],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def after_multi_insight_keyboard(league_id):
    keyboard = [
        [InlineKeyboardButton("⚽ More Predictions", callback_data=f"fixtures_{league_id}_0")],
        [InlineKeyboardButton("📈 Past Results", url=PAST_RESULTS_CHANNEL)],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


# =========================================
# Subscription
# =========================================

def subscribe_keyboard():
    keyboard = [
        [InlineKeyboardButton("💳 Upgrade — $5/month", callback_data="pay_now")],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


def pay_now_keyboard(payment_link):
    keyboard = [
        [InlineKeyboardButton("💳 Complete Payment", url=payment_link)],
        [InlineKeyboardButton("🔙 Back", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)


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
# Generic
# =========================================

def back_to_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)