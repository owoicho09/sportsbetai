from django.contrib import admin
from django.utils import timezone
import datetime

from .models import (
    League,
    Team,
    TeamStats,
    Standing,
    Fixture,
    H2HMatch,
    TeamFeatureStore,
    MatchInsight,
    BotUser
)


# =========================================
# League
# =========================================

@admin.register(League)
class LeagueAdmin(admin.ModelAdmin):
    list_display = ("name", "api_id", "country", "season", "active")
    list_filter = ("active", "season")
    search_fields = ("name", "country")


# =========================================
# Team
# =========================================

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "league", "api_id")
    search_fields = ("name",)
    list_filter = ("league",)


# =========================================
# Team Stats
# =========================================

@admin.register(TeamStats)
class TeamStatsAdmin(admin.ModelAdmin):
    list_display = ("team", "league", "season", "form", "wins_total", "goals_total")
    list_filter = ("league", "season")
    search_fields = ("team__name",)


# =========================================
# Standing
# =========================================

@admin.register(Standing)
class StandingAdmin(admin.ModelAdmin):
    list_display = ("league", "team", "rank", "points", "goals_diff", "last_5_form")
    list_filter = ("league", "season")
    search_fields = ("team__name",)
    ordering = ("league", "rank")


# =========================================
# Fixture
# =========================================

@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = (
        "home_team_name", "away_team_name",
        "league_name", "date", "status_short",
        "goals_home", "goals_away"
    )
    search_fields = ("home_team_name", "away_team_name", "league_name")
    list_filter = ("status_short", "league_name", "season")
    ordering = ("-date",)


# =========================================
# H2H Match
# =========================================

@admin.register(H2HMatch)
class H2HMatchAdmin(admin.ModelAdmin):
    list_display = (
        "league_name", "league_round",
        "home_team_name", "away_team_name",
        "home_goals", "away_goals",
        "status_short", "date"
    )
    search_fields = ("home_team_name", "away_team_name")
    list_filter = ("status_short", "league_name")
    ordering = ("-date",)


# =========================================
# Team Feature Store
# =========================================

@admin.register(TeamFeatureStore)
class TeamFeatureStoreAdmin(admin.ModelAdmin):
    list_display = (
        "team_name", "season", "rank", "points",
        "matches_played_total", "wins_total",
        "draws_total", "losses_total"
    )
    search_fields = ("team_name",)
    list_filter = ("season", "league")


# =========================================
# Match Insight
# =========================================

@admin.register(MatchInsight)
class MatchInsightAdmin(admin.ModelAdmin):
    list_display = (
        "fixture",
        "predicted_winner",
        "confidence",
        "btts_probability",
        "over_25_probability",
        "recommended_bet",
        "created_at"
    )
    search_fields = ("fixture__home_team_name", "fixture__away_team_name")
    readonly_fields = ("fixture", "input_hash", "created_at", "updated_at")
    ordering = ("-created_at",)


# =========================================
# Bot User
# =========================================

@admin.register(BotUser)
class BotUserAdmin(admin.ModelAdmin):

    list_display = [
        "telegram_id",
        "telegram_username",
        "first_name",
        "is_premium",
        "subscription_start",
        "subscription_end",
        "created_at",
    ]

    list_filter = [
        "is_premium",
    ]

    search_fields = [
        "telegram_id",
        "telegram_username",
        "first_name",
    ]

    readonly_fields = [
        "telegram_id",
        "telegram_username",
        "first_name",
        "paystack_customer_code",
        "paystack_subscription_code",
        "created_at",
        "updated_at",
    ]

    ordering = ["-created_at"]

    fieldsets = (
        ("Telegram Info", {
            "fields": (
                "telegram_id",
                "telegram_username",
                "first_name",
            )
        }),
        ("Subscription", {
            "fields": (
                "is_premium",
                "subscription_start",
                "subscription_end",
            )
        }),
        ("Paystack", {
            "fields": (
                "paystack_customer_code",
                "paystack_subscription_code",
            )
        }),
        ("Timestamps", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    actions = ["action_grant_premium", "action_revoke_premium"]

    @admin.action(description="✅ Grant Premium to selected users")
    def action_grant_premium(self, request, queryset):
        queryset.update(
            is_premium=True,
            subscription_start=timezone.now(),
            subscription_end=timezone.now() + datetime.timedelta(days=30)
        )
        self.message_user(request, f"Premium granted to {queryset.count()} user(s).")

    @admin.action(description="❌ Revoke Premium from selected users")
    def action_revoke_premium(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"Premium revoked from {queryset.count()} user(s).")