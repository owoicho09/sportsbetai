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


