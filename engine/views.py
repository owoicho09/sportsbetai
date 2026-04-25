from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date

import datetime

from .models import (
    League,
    Team,
    TeamStats,
    Standing,
    Fixture,
    MatchInsight
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
# Health Endpoints
# =========================================

@api_view(['GET'])
def health_check(request):
    return Response({
        "status": "healthy",
        "message": "API is running"
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
def ping(request):
    return Response({"message": "pong"}, status=status.HTTP_200_OK)


# =========================================
# Fixture ViewSet
# =========================================

class FixtureViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/fixtures/
    GET /api/fixtures/{id}/
    GET /api/fixtures/{id}/insight/
    """
    queryset = Fixture.objects.all().order_by("date")
    serializer_class = FixtureSerializer
    lookup_field = "fixture_id"

    @action(detail=True, methods=["get"])
    def insight(self, request, fixture_id=None):
        fixture = get_object_or_404(Fixture, fixture_id=fixture_id)

        # Return cached insight if exists
        # MatchInsight uses OneToOneField with related_name="insight"
        cached = MatchInsight.objects.filter(fixture=fixture).first()
        if cached:
            return Response(
                _format_insight_response(fixture, cached, from_cache=True),
                status=status.HTTP_200_OK
            )

        try:
            result = generate_fixture_insight(fixture_id=fixture.fixture_id)
            if result is None:
                return Response(
                    {"error": "Failed to generate insight"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
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
# Match Insight ViewSet
# =========================================

class MatchInsightViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MatchInsight.objects.select_related("fixture").all()
    serializer_class = MatchInsightSerializer


# =========================================
# League ViewSet
# =========================================

class LeagueViewSet(viewsets.ReadOnlyModelViewSet):
    # Only return active leagues — bot uses this to build league buttons
    queryset = League.objects.filter(active=True).order_by("name")
    serializer_class = LeagueSerializer


# =========================================
# Team ViewSet
# =========================================

class TeamViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Team.objects.select_related("league").all()
    serializer_class = TeamSerializer


# =========================================
# Team Stats ViewSet
# =========================================

class TeamStatsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeamStats.objects.select_related("team", "league").all()
    serializer_class = TeamStatsSerializer


# =========================================
# Standing ViewSet
# =========================================

class StandingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Standing.objects.select_related("team", "league").all()
    serializer_class = StandingSerializer


# =========================================
# Fixture List — Optimized for Bot
# =========================================

class FixtureListAPIView(APIView):
    """
    GET /api/fixtures/list/

    Query params:
      league_id  — Fixture.league_id (IntegerField) — e.g. 39 for Premier League
      upcoming   — "true" returns only fixtures from today onwards
      date       — specific date YYYY-MM-DD
      days       — next N days (max 7)
      limit      — page size (default 8, max 20)
      offset     — pagination offset (default 0)

    Bot calls:
      /api/fixtures/list/?league_id=39&upcoming=true&limit=8&offset=0
    """

    def get(self, request):
        today = timezone.now().date()

        # --- Read params ---
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

        # --- Base queryset ---
        # Fixture.league_id is a plain IntegerField — filter directly
        fixtures = Fixture.objects.only(
            "fixture_id",
            "home_team_name",
            "away_team_name",
            "date",
            "league_name",
            "league_round",
            "league_id",
            "status_short"
        ).order_by("date")

        # --- League filter ---
        # Fixture.league_id is IntegerField, not FK — use direct filter
        if league_id:
            try:
                fixtures = fixtures.filter(league_id=int(league_id))
            except ValueError:
                return Response(
                    {"error": "league_id must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # --- Exclude finished matches (status_short = 'FT', 'AET', 'PEN') ---
        finished_statuses = ["FT", "AET", "PEN", "AWD", "WO"]

        # --- Date / upcoming filter ---
        if upcoming:
            # Primary bot mode — future and today's unplayed fixtures
            #fixtures = fixtures.filter(
             #   date__date__gte=today
            #).exclude(
            #    status_short__in=finished_statuses
            #)
            pass

        elif date_param:
            target_date = parse_date(date_param)
            if not target_date:
                return Response(
                    {"error": "Invalid date format. Use YYYY-MM-DD"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            fixtures = fixtures.filter(date__date=target_date)

        elif days_param:
            try:
                days = min(int(days_param), 7)
            except ValueError:
                days = 3
            end_date = today + datetime.timedelta(days=days)
            fixtures = fixtures.filter(
                date__date__gte=today,
                date__date__lte=end_date
            ).exclude(status_short__in=finished_statuses)

        else:
            # Default: today only, unplayed
            fixtures = fixtures.filter(
                date__date=today
            ).exclude(status_short__in=finished_statuses)

        # --- Total count before pagination ---
        total = fixtures.count()

        # --- Paginate ---
        page_fixtures = fixtures[offset: offset + limit]
        serializer = FixtureSerializer(page_fixtures, many=True)

        # --- Resolve league name ---
        # Fixture stores league_name directly — use first result if available
        league_name = "Fixtures"
        if serializer.data:
            league_name = serializer.data[0].get("league_name", "Fixtures") or "Fixtures"
        elif league_id:
            # Fallback: look up League model by api_id
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
# Generate Insight — Optimized for Bot
# =========================================

@api_view(["GET"])
def get_fixture_insight(request, fixture_id):
    """
    GET /api/fixture-insight/{fixture_id}/

    Returns cached insight if available, generates if not.
    MatchInsight fields used: insight_text, predicted_winner,
    confidence, btts_probability, over_25_probability, recommended_bet
    """
    fixture = get_object_or_404(Fixture, fixture_id=fixture_id)

    # Check cache first — MatchInsight.insight_text (not insight_data)
    cached = MatchInsight.objects.filter(fixture=fixture).first()
    if cached:
        return Response(
            _format_insight_response(fixture, cached, from_cache=True),
            status=status.HTTP_200_OK
        )

    try:
        result = generate_fixture_insight(fixture_id=fixture.fixture_id)

        if result is None:
            return Response(
                {"error": "Insight generation failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Re-fetch after generation in case it was saved
        cached = MatchInsight.objects.filter(fixture=fixture).first()
        if cached:
            return Response(
                _format_insight_response(fixture, cached, from_cache=False),
                status=status.HTTP_200_OK
            )

        # generate_fixture_insight returned raw result (not saved yet)
        return Response({
            "fixture_id": fixture.fixture_id,
            "home_team": fixture.home_team_name,
            "away_team": fixture.away_team_name,
            "insight": result,
            "cached": False
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# =========================================
# Upcoming Fixtures — Next 3 Days
# =========================================

@api_view(["GET"])
def upcoming_fixtures(request):
    """
    GET /api/fixtures/upcoming/
    Returns next 3 days of fixtures grouped by date.
    """
    today = timezone.now().date()
    end_date = today + datetime.timedelta(days=3)

    fixtures = Fixture.objects.only(
        "fixture_id",
        "home_team_name",
        "away_team_name",
        "date",
        "league_name",
        "league_round"
    ).filter(
        date__date__gte=today,
        date__date__lte=end_date
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
# Helper: Format MatchInsight for Response
# =========================================

def _format_insight_response(fixture, insight_obj, from_cache=True):
    """
    Builds a consistent insight response dict from a MatchInsight instance.
    Uses the correct field names from the MatchInsight model:
      - insight_text        (TextField)
      - predicted_winner    (CharField)
      - confidence          (CharField)
      - btts_probability    (CharField)
      - over_25_probability (CharField)
      - recommended_bet     (CharField)
    """
    return {
        "fixture_id": fixture.fixture_id,
        "home_team": fixture.home_team_name,
        "away_team": fixture.away_team_name,
        "cached": from_cache,
        "insight": {
            "analysis":          insight_obj.insight_text,
            "predicted_winner":  insight_obj.predicted_winner,
            "confidence":        insight_obj.confidence,
            "btts":              insight_obj.btts_probability,
            "over_2_5":          insight_obj.over_25_probability,
            "recommended_bet":   insight_obj.recommended_bet,
        }
    }