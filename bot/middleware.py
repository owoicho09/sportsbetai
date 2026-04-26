# bot/middleware.py

import os
import django
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from engine.models import BotUser
from django.utils import timezone
import datetime


# =========================================
# Sync DB functions (called via sync_to_async)
# =========================================

def _is_premium_sync(user_id: int) -> bool:
    try:
        user = BotUser.objects.get(telegram_id=user_id)
        return user.is_active_subscriber()
    except BotUser.DoesNotExist:
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


# =========================================
# Async wrappers — use these in bot handlers
# =========================================

is_premium = sync_to_async(_is_premium_sync)
grant_premium = sync_to_async(_grant_premium_sync)
revoke_premium = sync_to_async(_revoke_premium_sync)