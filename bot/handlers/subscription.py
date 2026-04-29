# bot/handlers/subscription.py

import os
import asyncio
import requests as http_requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.messages import (
    PAYMENT_INSTRUCTIONS_MESSAGE,
    PREMIUM_ALREADY_ACTIVE,
    PREMIUM_GRANTED_MESSAGE,
    SUBSCRIPTION_INACTIVE_MESSAGE,
)
from bot.keyboards import (
    pay_now_keyboard,
    subscription_active_keyboard,
    subscription_inactive_keyboard,
    back_to_menu_keyboard,
)
from bot.middleware import is_premium, grant_premium, revoke_premium

load_dotenv()

ADMIN_ID             = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
PAYSTACK_SECRET_KEY  = os.getenv("PAYSTACK_SECRET_KEY", "")
PAYSTACK_AMOUNT_KOBO = int(os.getenv("PAYSTACK_AMOUNT_KOBO", "500000"))


def _initialize_paystack_transaction(telegram_id: int, username: str = "") -> str | None:
    payload = {
        "email":  f"{telegram_id}@sportsbetai.app",
        "amount": PAYSTACK_AMOUNT_KOBO,
        "metadata": {
            "telegram_id": str(telegram_id),
            "username":    username,
        },
    }
    try:
        resp = http_requests.post(
            "https://api.paystack.co/transaction/initialize",
            json=payload,
            headers={
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
                "Content-Type":  "application/json",
            },
            timeout=10,
        )
        data = resp.json()
        if data.get("status"):
            return data["data"]["authorization_url"]
        print(f"[SUBSCRIPTION] Paystack init failed: {data.get('message')}")
        return None
    except Exception as e:
        print(f"[SUBSCRIPTION] Paystack exception: {e}")
        return None


# =========================================
# Handlers
# =========================================

async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query   = update.callback_query
    # NO query.answer() — already called in callback_router

    user_id = query.from_user.id

    if await is_premium(user_id):
        await query.edit_message_text(
            PREMIUM_ALREADY_ACTIVE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscription_active_keyboard(),
        )
    else:
        await query.edit_message_text(
            SUBSCRIPTION_INACTIVE_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscription_inactive_keyboard(),
        )


async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    # NO query.answer() — already called in callback_router

    user  = query.from_user

    await query.edit_message_text("⏳ Generating your payment link...")

    loop         = asyncio.get_event_loop()
    payment_link = await loop.run_in_executor(
        None, _initialize_paystack_transaction, user.id, user.username or ""
    )

    if not payment_link:
        await query.edit_message_text(
            "⚠️ Could not generate payment link. Please try again.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_to_menu_keyboard(),
        )
        return

    await query.edit_message_text(
        PAYMENT_INSTRUCTIONS_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=pay_now_keyboard(payment_link),
    )


async def grant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_id = int(context.args[0])
        await grant_premium(target_id)
        await update.message.reply_text(f"✅ User `{target_id}` granted premium.", parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_message(chat_id=target_id, text=PREMIUM_GRANTED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/grant <user_id>`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"Error: `{str(e)}`", parse_mode=ParseMode.MARKDOWN)


async def revoke_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    try:
        target_id = int(context.args[0])
        await revoke_premium(target_id)
        await update.message.reply_text(f"✅ User `{target_id}` revoked.", parse_mode=ParseMode.MARKDOWN)
        await context.bot.send_message(
            chat_id=target_id,
            text="⚠️ *Your Premium access has been revoked.*\n\nContact admin if you believe this is an error.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/revoke <user_id>`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"Error: `{str(e)}`", parse_mode=ParseMode.MARKDOWN)