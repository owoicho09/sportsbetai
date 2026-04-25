from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import *

# =========================================
# Router Configuration
# =========================================

router = DefaultRouter()

# Register ViewSets
router.register(
    r'fixtures',
    FixtureViewSet,
    basename='fixtures'
)

router.register(
    r'insights',
    MatchInsightViewSet,
    basename='insights'
)

router.register(
    r'leagues',
    LeagueViewSet,
    basename='leagues'
)

router.register(
    r'teams',
    TeamViewSet,
    basename='teams'
)

router.register(
    r'team-stats',
    TeamStatsViewSet,
    basename='team-stats'
)

router.register(
    r'standings',
    StandingViewSet,
    basename='standings'
)


# =========================================
# URL Patterns
# =========================================

urlpatterns = [

    # Health Routes
    path('health/', health_check, name='health-check'),
    path('ping/', ping, name='ping'),
    path('fixtures/upcoming/', upcoming_fixtures, name='fixture-upcoming'),

    # Custom Endpoints
    path(
        'fixtures/list/',
        FixtureListAPIView.as_view(),
        name='fixture-list'
    ),

    path(
        'fixture-insight/<str:fixture_id>/',
        get_fixture_insight,
        name='fixture-insight'
    ),

    # Router Endpoints
    path('', include(router.urls)),

]