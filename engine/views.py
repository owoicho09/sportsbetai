from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

import datetime
import hashlib
import hmac
import json
import os
import requests as http_requests

from .models import (
    League,
    Team,
    TeamStats,
    Standing,
    Fixture,
    MatchInsight,
    BotUser
)

from .serializers import (
    LeagueSerializer,
    TeamSerializer,
    TeamStatsSerializer,
    StandingSerializer,
    FixtureSerializer,
    MatchInsightSerializer
)

from engine.ai_insight.fixture_insight import generate_fixture_insight


# =========================================
# Health
# =========================================

@api_view(['GET'])
def health_check(request):
    return Response({"status": "healthy", "message": "API is running"}, status=status.HTTP_200_OK)


# In views.py — replace your ping view
@api_view(['GET', 'HEAD'])
def ping(request):
    return Response({"message": "pong"}, status=status.HTTP_200_OK)
# =========================================
# Fixture ViewSet
# =========================================

class FixtureViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Fixture.objects.all().order_by("date")
    serializer_class = FixtureSerializer
    lookup_field = "fixture_id"

    @action(detail=True, methods=["get"])
    def insight(self, request, fixture_id=None):
        fixture = get_object_or_404(Fixture, fixture_id=fixture_id)
        cached = MatchInsight.objects.filter(fixture=fixture).first()
        if cached:
            return Response(_format_insight_response(fixture, cached, from_cache=True), status=status.HTTP_200_OK)
        try:
            result = generate_fixture_insight(fixture_id=fixture.fixture_id)
            if result is None:
                return Response({"error": "Failed to generate insight"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({
                "fixture_id": fixture.fixture_id,
                "home_team": fixture.home_team_name,
                "away_team": fixture.away_team_name,
                "insight": result,
                "cached": False
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================
# ViewSets
# =========================================

class MatchInsightViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MatchInsight.objects.select_related("fixture").all()
    serializer_class = MatchInsightSerializer


class LeagueViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = League.objects.filter(active=True).order_by("name")
    serializer_class = LeagueSerializer


class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.select_related("league").all()
    serializer_class = TeamSerializer


class TeamStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeamStats.objects.select_related("team", "league").all()
    serializer_class = TeamStatsSerializer


class StandingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Standing.objects.select_related("team", "league").all()
    serializer_class = StandingSerializer


# =========================================
# Fixture List
# =========================================

class FixtureListAPIView(APIView):
    """
    GET /api/fixtures/list/
    Params: league_id, upcoming, date, days, limit, offset
    """

    def get(self, request):
        today = timezone.now().date()

        league_id  = request.query_params.get("league_id")
        upcoming   = request.query_params.get("upcoming") == "true"
        date_param = request.query_params.get("date")
        days_param = request.query_params.get("days")

        try:
            limit = min(int(request.query_params.get("limit", 8)), 20)
        except ValueError:
            limit = 8

        try:
            offset = int(request.query_params.get("offset", 0))
        except ValueError:
            offset = 0

        fixtures = Fixture.objects.only(
            "fixture_id", "home_team_name", "away_team_name",
            "date", "league_name", "league_round", "league_id", "status_short"
        ).order_by("date")

        if league_id:
            try:
                fixtures = fixtures.filter(league_id=int(league_id))
            except ValueError:
                return Response({"error": "league_id must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

        finished_statuses = ["FT", "AET", "PEN", "AWD", "WO"]

        if upcoming:
            pass

        elif date_param:
            target_date = parse_date(date_param)
            if not target_date:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD"}, status=status.HTTP_400_BAD_REQUEST)
            fixtures = fixtures.filter(date__date=target_date)

        elif days_param:
            try:
                days = min(int(days_param), 7)
            except ValueError:
                days = 3
            end_date = today + datetime.timedelta(days=days)
            fixtures = fixtures.filter(
                date__date__gte=today, date__date__lte=end_date
            ).exclude(status_short__in=finished_statuses)

        else:
            fixtures = fixtures.filter(date__date=today).exclude(status_short__in=finished_statuses)

        total = fixtures.count()
        page_fixtures = fixtures[offset: offset + limit]
        serializer = FixtureSerializer(page_fixtures, many=True)

        league_name = "Fixtures"
        if serializer.data:
            league_name = serializer.data[0].get("league_name", "Fixtures") or "Fixtures"
        elif league_id:
            league_obj = League.objects.filter(api_id=int(league_id)).first()
            if league_obj:
                league_name = league_obj.name

        return Response({
            "league_id": league_id,
            "league_name": league_name,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total,
            "fixtures": serializer.data
        }, status=status.HTTP_200_OK)


# =========================================
# Fixture Insight
# =========================================

@api_view(["GET"])
def get_fixture_insight(request, fixture_id):
    fixture = get_object_or_404(Fixture, fixture_id=fixture_id)

    cached = MatchInsight.objects.filter(fixture=fixture).first()
    if cached:
        return Response(_format_insight_response(fixture, cached, from_cache=True), status=status.HTTP_200_OK)

    try:
        result = generate_fixture_insight(fixture_id=fixture.fixture_id)
        if result is None:
            return Response({"error": "Insight generation failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        cached = MatchInsight.objects.filter(fixture=fixture).first()
        if cached:
            return Response(_format_insight_response(fixture, cached, from_cache=False), status=status.HTTP_200_OK)

        return Response({
            "fixture_id": fixture.fixture_id,
            "home_team": fixture.home_team_name,
            "away_team": fixture.away_team_name,
            "insight": result,
            "cached": False
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# =========================================
# Upcoming Fixtures
# =========================================

@api_view(["GET"])
def upcoming_fixtures(request):
    today = timezone.now().date()
    end_date = today + datetime.timedelta(days=3)

    fixtures = Fixture.objects.only(
        "fixture_id", "home_team_name", "away_team_name",
        "date", "league_name", "league_round"
    ).filter(
        date__date__gte=today, date__date__lte=end_date
    ).exclude(
        status_short__in=["FT", "AET", "PEN", "AWD", "WO"]
    ).order_by("date")[:30]

    grouped = {}
    for f in fixtures:
        day = str(f.date.date())
        if day not in grouped:
            grouped[day] = []
        grouped[day].append({
            "fixture_id": f.fixture_id,
            "home_team": f.home_team_name,
            "away_team": f.away_team_name,
            "league": f.league_name,
            "round": f.league_round,
            "time": f.date.strftime("%H:%M") if f.date else "TBD"
        })

    return Response({
        "from": str(today),
        "to": str(end_date),
        "total": fixtures.count(),
        "fixtures_by_date": grouped
    }, status=status.HTTP_200_OK)


# =========================================
# Helper
# =========================================

def _format_insight_response(fixture, insight_obj, from_cache=True):
    return {
        "fixture_id": fixture.fixture_id,
        "home_team": fixture.home_team_name,
        "away_team": fixture.away_team_name,
        "cached": from_cache,
        "insight": {
            "analysis":         insight_obj.insight_text,
            "predicted_winner": insight_obj.predicted_winner,
            "confidence":       insight_obj.confidence,
            "btts":             insight_obj.btts_probability,
            "over_2_5":         insight_obj.over_25_probability,
            "recommended_bet":  insight_obj.recommended_bet,
        }
    }


# =========================================
# Paystack Webhook
# =========================================

@csrf_exempt
def paystack_webhook(request):
    if request.method != "POST":
        return HttpResponse(status=405)

    paystack_secret = os.getenv("PAYSTACK_SECRET_KEY", "")
    signature = request.headers.get("x-paystack-signature", "")
    computed = hmac.new(
        paystack_secret.encode("utf-8"),
        request.body,
        hashlib.sha512
    ).hexdigest()

    if signature != computed:
        print("[WEBHOOK] Invalid signature — rejected")
        return HttpResponse(status=401)

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    event = payload.get("event")
    data = payload.get("data", {})

    print(f"[WEBHOOK] Event received: {event}")

    if event == "charge.success":
        _handle_charge_success(data)
    elif event in ["subscription.disable", "subscription.not_renew"]:
        _handle_subscription_disable(data)

    return HttpResponse(status=200)


def _extract_telegram_id(data):
    metadata = data.get("metadata", {})
    if isinstance(metadata, dict):
        tid = metadata.get("telegram_id")
        if tid:
            return int(tid)

    # Fallback: email was set as {telegram_id}@sportsbetai.app
    customer = data.get("customer", {})
    email = customer.get("email", "")
    if "@sportsbetai.app" in email:
        try:
            return int(email.split("@")[0])
        except ValueError:
            pass

    print(f"[WEBHOOK] Could not extract telegram_id — email: {email}")
    return None


def _handle_charge_success(data):
    # Debug logs so you can see exactly what Paystack sends
    print(f"[WEBHOOK] charge.success — metadata: {data.get('metadata')}")
    print(f"[WEBHOOK] charge.success — customer email: {data.get('customer', {}).get('email')}")

    telegram_id = _extract_telegram_id(data)
    if not telegram_id:
        print("[WEBHOOK] charge.success — could not resolve telegram_id, aborting")
        return

    customer_code = data.get("customer", {}).get("customer_code", "")

    user, created = BotUser.objects.get_or_create(telegram_id=telegram_id)
    user.is_premium = True
    user.subscription_start = timezone.now()
    user.subscription_end = timezone.now() + datetime.timedelta(days=30)
    user.paystack_customer_code = customer_code
    user.save()

    print(f"[WEBHOOK] Premium granted — telegram_id={telegram_id}, expires={user.subscription_end}, new_user={created}")
    # Send payment notification email to yourself
    from bot.handlers.emailer import send_payment_email
    send_payment_email(
        telegram_id=telegram_id,
        username=user.telegram_username or "",
        first_name=user.first_name or ""
    )


    _send_telegram_message(
        telegram_id,
        text=(
            "🎉 *Payment Confirmed — You're In!*\n\n"
            "Your Premium is now active.\n"
            "You have full access to all AI predictions.\n\n"
            "Tap below to get your first prediction 👇"
        ),
        reply_markup={
            "inline_keyboard": [[
                {"text": "⚽ Get My First Prediction", "callback_data": "get_prediction"}
            ]]
        }
    )


def _handle_subscription_disable(data):
    customer_code = data.get("customer", {}).get("customer_code", "")
    if not customer_code:
        return

    users = BotUser.objects.filter(paystack_customer_code=customer_code)
    for user in users:
        user.is_premium = False
        user.save()
        print(f"[WEBHOOK] Premium revoked — telegram_id={user.telegram_id}")
        _send_telegram_message(
            user.telegram_id,
            text=(
                "⚠️ *Your Premium subscription has ended.*\n\n"
                "Renew anytime to restore full access.\n"
                "Tap /start to subscribe again."
            )
        )


def _send_telegram_message(telegram_id, text, reply_markup=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        print("[WEBHOOK] No TELEGRAM_BOT_TOKEN set")
        return
    payload = {
        "chat_id": telegram_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        http_requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json=payload,
            timeout=10
        )
        print(f"[WEBHOOK] Message sent to telegram_id={telegram_id}")
    except Exception as e:
        print(f"[WEBHOOK] Failed to send message: {e}")





# =========================================
# Telegram Webhook View
# — append this to the bottom of engine/views.py
# =========================================

import asyncio
from asgiref.sync import async_to_sync

@csrf_exempt
def telegram_webhook(request):
    """
    Receives POST requests from Telegram.
    Telegram calls this URL every time a user sends a message or taps a button.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        update_data = json.loads(request.body)
    except json.JSONDecodeError:
        return HttpResponse(status=400)

    try:
        from bot.webhook import process_update
        async_to_sync(process_update)(update_data)
    except Exception as e:
        # Never return non-200 to Telegram — it will retry repeatedly
        print(f"[TELEGRAM WEBHOOK] Error processing update: {e}")

    # Always return 200 to Telegram immediately
    return HttpResponse(status=200)