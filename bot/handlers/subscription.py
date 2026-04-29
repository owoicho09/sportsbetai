# bot/handlers/subscription.py

import os
import asyncio
import django
import requests as http_requests
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
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_AMOUNT_KOBO = int(os.getenv("PAYSTACK_AMOUNT_KOBO", "500000"))  # default 5000 NGN


# =========================================
# Helpers
# =========================================

def _initialize_paystack_transaction(telegram_id: int, username: str = "") -> str | None:
    """
    Call Paystack Initialize Transaction API so metadata.telegram_id
    is embedded in the transaction and returned in the webhook.
    This replaces the old static payment page link approach which
    did NOT forward query params back in the webhook.
    """
    payload = {
        "email": f"{telegram_id}@sportsbetai.app",
        "amount": PAYSTACK_AMOUNT_KOBO,
        "metadata": {
            "telegram_id": str(telegram_id),
            "username": username,
        },
    }

    try:
        resp = http_requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers={
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("status"):
            url = data["data"]["authorization_url"]
            print(f"[SUBSCRIPTION] Paystack transaction initialized for {telegram_id}: {url}")
            return url
        else:
            print(f"[SUBSCRIPTION] Paystack init failed: {data.get('message')}")
            return None
    except Exception as e:
        print(f"[SUBSCRIPTION] Exception during Paystack init: {e}")
        return None


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

    if await is_premium(user_id):
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
    """Generate a personalised Paystack transaction link and show payment page."""
    query = update.callback_query
    await query.answer()

    user = query.from_user

    # Register user in DB so webhook can find them
    #await _register_user(user)

    # Initialize transaction via Paystack API — this embeds telegram_id in metadata
    # so the webhook can identify who paid
    loop = asyncio.get_event_loop()
    payment_link = await loop.run_in_executor(
        None, _initialize_paystack_transaction, user.id, user.username or ""
    )

    if not payment_link:
        await query.edit_message_text(
            "⚠️ Could not generate payment link. Please try again later.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard()
        )
        return

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
        await grant_premium(target_id)

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
        await revoke_premium(target_id)

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