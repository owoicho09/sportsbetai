# bot/handlers/subscription.py

import os
import urllib.parse
import django
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.messages import (
    PAYMENT_INSTRUCTIONS_MESSAGE,
    PREMIUM_ALREADY_ACTIVE,
    PREMIUM_GRANTED_MESSAGE,
    SUBSCRIPTION_INACTIVE_MESSAGE
)
from bot.keyboards import (
    pay_now_keyboard,
    subscription_active_keyboard,
    subscription_inactive_keyboard,
    back_to_menu_keyboard
)
from bot.middleware import is_premium, grant_premium, revoke_premium

load_dotenv()

# =========================================
# Config
# =========================================

ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
PAYSTACK_PAYMENT_PAGE = os.getenv("PAYMENT_LINK", "https://paystack.shop/pay/9knp4sqd53")


# =========================================
# Helpers
# =========================================

def generate_payment_link(telegram_id: int, username: str = "") -> str:
    """
    Generate Paystack payment URL with telegram_id embedded in metadata.
    Paystack will send this back in the webhook so we know who paid.
    """
    params = urllib.parse.urlencode({
        "telegram_id": telegram_id,
        "ref": f"tg_{telegram_id}",         # unique reference per user
        "email": f"{telegram_id}@sportsbetai.app",  # placeholder — Paystack requires email
    })
    return f"{PAYSTACK_PAYMENT_PAGE}?{params}"


def _register_user(telegram_user):
    """
    Create or update BotUser record when user interacts with subscription flow.
    Ensures user exists in DB before payment.
    """
    try:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
        if not django.conf.settings.configured:
            django.setup()

        from engine.models import BotUser
        user, created = BotUser.objects.get_or_create(
            telegram_id=telegram_user.id,
            defaults={
                "telegram_username": telegram_user.username or "",
                "first_name": telegram_user.first_name or "",
            }
        )
        if not created:
            # Update username in case it changed
            user.telegram_username = telegram_user.username or ""
            user.first_name = telegram_user.first_name or ""
            user.save(update_fields=["telegram_username", "first_name"])

        return user
    except Exception as e:
        print(f"[SUBSCRIPTION] Warning: could not register user in DB: {e}")
        return None


# =========================================
# Handlers
# =========================================

async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show subscription status."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    print(f"[SUBSCRIPTION] User {user_id} checking subscription status")

    if await  is_premium(user_id):
        print(f"[SUBSCRIPTION] User {user_id} is premium")
        await query.edit_message_text(
            PREMIUM_ALREADY_ACTIVE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscription_active_keyboard()
        )
    else:
        print(f"[SUBSCRIPTION] User {user_id} is not premium")
        await query.edit_message_text(
            SUBSCRIPTION_INACTIVE_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscription_inactive_keyboard()
        )


async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment page with personalised Paystack link."""
    query = update.callback_query
    await query.answer()

    user = query.from_user

    # Register user in DB so webhook can find them
    _register_user(user)

    # Generate personalised payment link with telegram_id embedded
    payment_link = generate_payment_link(user.id, user.username or "")

    print(f"[SUBSCRIPTION] Generated payment link for user {user.id}: {payment_link}")

    await query.edit_message_text(
        PAYMENT_INSTRUCTIONS_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=pay_now_keyboard(payment_link)
    )


async def grant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command: /grant <user_id>
    Manual override — useful for testing or resolving payment issues.
    """
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target_id = int(context.args[0])
        grant_premium(target_id)

        print(f"[SUBSCRIPTION] Admin manually granted premium to {target_id}")

        await update.message.reply_text(
            f"✅ User `{target_id}` granted premium.",
            parse_mode=ParseMode.MARKDOWN
        )

        await context.bot.send_message(
            chat_id=target_id,
            text=PREMIUM_GRANTED_MESSAGE,
            parse_mode=ParseMode.MARKDOWN
        )

    except (IndexError, ValueError):
        await update.message.reply_text(
            "Usage: `/grant <user_id>`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(
            f"Error: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )


async def revoke_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin command: /revoke <user_id>
    Manual override — useful for chargebacks or cancellations.
    """
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target_id = int(context.args[0])
        revoke_premium(target_id)

        print(f"[SUBSCRIPTION] Admin manually revoked premium for {target_id}")

        await update.message.reply_text(
            f"✅ User `{target_id}` revoked.",
            parse_mode=ParseMode.MARKDOWN
        )

        await context.bot.send_message(
            chat_id=target_id,
            text=(
                "⚠️ *Your Premium access has been revoked.*\n\n"
                "Contact admin if you believe this is an error."
            ),
            parse_mode=ParseMode.MARKDOWN
        )

    except (IndexError, ValueError):
        await update.message.reply_text(
            "Usage: `/revoke <user_id>`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        await update.message.reply_text(
            f"Error: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN
        )