# bot/middleware.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from engine.models import BotUser


def is_premium(user_id: int) -> bool:
    try:
        user = BotUser.objects.get(telegram_id=user_id)
        return user.is_active_subscriber()
    except BotUser.DoesNotExist:
        return False


def grant_premium(user_id: int):
    from django.utils import timezone
    import datetime
    user, _ = BotUser.objects.get_or_create(telegram_id=user_id)
    user.is_premium = True
    user.subscription_start = timezone.now()
    user.subscription_end = timezone.now() + datetime.timedelta(days=30)
    user.save()


def revoke_premium(user_id: int):
    try:
        user = BotUser.objects.get(telegram_id=user_id)
        user.is_premium = False
        user.save()
    except BotUser.DoesNotExist:
        pass