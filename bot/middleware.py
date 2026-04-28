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


is_premium = sync_to_async(_is_premium_sync)
grant_premium = sync_to_async(_grant_premium_sync)
revoke_premium = sync_to_async(_revoke_premium_sync)