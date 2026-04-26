from django.contrib import admin
from .models import *


class LeagueAdmin(admin.ModelAdmin):
    list_display = ('name', 'api_id')


class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'league', 'api_id')


class TeamStatsAdmin(admin.ModelAdmin):
    list_display = ('league','team', 'form', 'wins_total', 'goals_total')


class StandingAdmin(admin.ModelAdmin):
    list_display = ('league','team', 'rank', 'points', 'goals_diff', 'last_5_form')


class FixtureAdmin(admin.ModelAdmin):
    list_display = ('home_team_name', 'away_team_name', 'home_winner', 'away_winner', 'goals_home', 'goals_away')
    search_fields = ('home_team_name', 'away_team_name')

class H2HMatchAdmin(admin.ModelAdmin):
    list_display = ('league_name', 'league_round', 'home_team_name', 'away_team_name', 'home_goals', 'away_goals', 'status_short', 'date')
    search_fields = ('home_team_name', 'away_team_name')

class TeamFeatureStoreAdmin(admin.ModelAdmin):
    list_display = ('team_name', 'season', 'rank', 'points', 'matches_played_total', 'wins_total', 'losses_total', 'draws_total')


class MatchInsightAdmin(admin.ModelAdmin):
    list_display = ('fixture', 'insight_text')




admin.site.register(League,LeagueAdmin)
admin.site.register(Team,TeamAdmin)
admin.site.register(TeamStats,TeamStatsAdmin)
admin.site.register(Standing,StandingAdmin)
admin.site.register(Fixture,FixtureAdmin)
admin.site.register(MatchInsight,MatchInsightAdmin)

admin.site.register(H2HMatch,H2HMatchAdmin)

admin.site.register(TeamFeatureStore,TeamFeatureStoreAdmin)


from django.contrib import admin
from .models import BotUser


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
        "subscription_start",
        "subscription_end",
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

    actions = ["grant_premium", "revoke_premium"]

    @admin.action(description="✅ Grant Premium to selected users")
    def grant_premium(self, request, queryset):
        from django.utils import timezone
        import datetime
        queryset.update(
            is_premium=True,
            subscription_start=timezone.now(),
            subscription_end=timezone.now() + datetime.timedelta(days=30)
        )
        self.message_user(request, f"Premium granted to {queryset.count()} user(s).")

    @admin.action(description="❌ Revoke Premium from selected users")
    def revoke_premium(self, request, queryset):
        queryset.update(is_premium=False)
        self.message_user(request, f"Premium revoked from {queryset.count()} user(s).")