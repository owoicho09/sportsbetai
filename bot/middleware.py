# bot/middleware.py

import os
import django
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from engine.models import BotUser
from django.utils import timezone
import datetime


def _is_premium_sync(user_id: int) -> bool:
    try:
        user = BotUser.objects.get(telegram_id=user_id)
        if not user.is_premium:
            return False
        # None = no expiry (e.g. admin-granted)
        if user.subscription_end is not None and user.subscription_end < timezone.now():
            user.is_premium = False
            user.save()
            return False
        return True
    except BotUser.DoesNotExist:
        return False
    except Exception as e:
        print(f"[MIDDLEWARE] ERROR: {e}")
        return False


def _grant_premium_sync(user_id: int):
    user, _ = BotUser.objects.get_or_create(telegram_id=user_id)
    user.is_premium = True
    user.subscription_start = timezone.now()
    user.subscription_end = timezone.now() + datetime.timedelta(days=30)
    user.save()


def _revoke_premium_sync(user_id: int):
    try:
        user = BotUser.objects.get(telegram_id=user_id)
        user.is_premium = False
        user.save()
    except BotUser.DoesNotExist:
        pass


def _register_user_sync(telegram_user):
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
    return user, created  # ← return the tuple so start_handler knows if new

register_user = sync_to_async(_register_user_sync)

is_premium = sync_to_async(_is_premium_sync)
grant_premium = sync_to_async(_grant_premium_sync)
revoke_premium = sync_to_async(_revoke_premium_sync)