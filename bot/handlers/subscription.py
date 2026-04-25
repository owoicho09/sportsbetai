# bot/handlers/subscription.py

import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from bot.messages import (
    PAYMENT_INSTRUCTIONS_MESSAGE,
    PAID_NOTIFY_MESSAGE,
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

ADMIN_ID = int(os.getenv("ADMIN_TELEGRAM_ID", "0"))
PAYMENT_LINK = os.getenv("PAYMENT_LINK", "https://your-payment-link.com")


async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if is_premium(user_id):
        await query.edit_message_text(
            PREMIUM_ALREADY_ACTIVE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscription_active_keyboard()
        )
    else:
        await query.edit_message_text(
            SUBSCRIPTION_INACTIVE_MESSAGE,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=subscription_inactive_keyboard()
        )


async def subscribe_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show payment instructions."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        PAYMENT_INSTRUCTIONS_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=pay_now_keyboard(PAYMENT_LINK)
    )


async def paid_notify_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User claims they paid — notify admin."""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    user_id = user.id
    username = f"@{user.username}" if user.username else user.first_name

    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"💳 *New Payment Claim*\n\n"
                f"👤 User: {username}\n"
                f"🆔 ID: `{user_id}`\n\n"
                f"To grant access, reply:\n"
                f"`/grant {user_id}`\n\n"
                f"To revoke access:\n"
                f"`/revoke {user_id}`"
            ),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        pass  # Don't break user flow if admin notify fails

    await query.edit_message_text(
        PAID_NOTIFY_MESSAGE,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=back_to_menu_keyboard()
    )


async def grant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /grant <user_id>"""
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target_id = int(context.args[0])
        grant_premium(target_id)

        await update.message.reply_text(f"✅ User `{target_id}` granted premium.", parse_mode=ParseMode.MARKDOWN)

        await context.bot.send_message(
            chat_id=target_id,
            text=PREMIUM_GRANTED_MESSAGE,
            parse_mode=ParseMode.MARKDOWN
        )

    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/grant <user_id>`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"Error: `{str(e)}`", parse_mode=ParseMode.MARKDOWN)


async def revoke_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin: /revoke <user_id>"""
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        target_id = int(context.args[0])
        revoke_premium(target_id)

        await update.message.reply_text(f"✅ User `{target_id}` revoked.", parse_mode=ParseMode.MARKDOWN)

        await context.bot.send_message(
            chat_id=target_id,
            text="⚠️ Your Premium access has been revoked.\n\nContact admin if you believe this is an error.",
        )

    except (IndexError, ValueError):
        await update.message.reply_text("Usage: `/revoke <user_id>`", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.message.reply_text(f"Error: `{str(e)}`", parse_mode=ParseMode.MARKDOWN)