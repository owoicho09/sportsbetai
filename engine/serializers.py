from rest_framework import serializers
from .models import (
    League,
    Team,
    TeamStats,
    Standing,
    Fixture,
    H2HMatch,
    TeamFeatureStore,
    MatchInsight
)


# -------------------------
# League Serializer
# -------------------------
class LeagueSerializer(serializers.ModelSerializer):
    class Meta:
        model = League
        fields = "__all__"


# -------------------------
# Team Serializer
# -------------------------
class TeamSerializer(serializers.ModelSerializer):

    league_name = serializers.CharField(
        source="league.name",
        read_only=True
    )

    class Meta:
        model = Team
        fields = "__all__"


# -------------------------
# TeamStats Serializer
# -------------------------
class TeamStatsSerializer(serializers.ModelSerializer):

    team_name = serializers.CharField(
        source="team.name",
        read_only=True
    )

    league_name = serializers.CharField(
        source="league.name",
        read_only=True
    )

    class Meta:
        model = TeamStats
        fields = "__all__"


# -------------------------
# Standing Serializer
# -------------------------
class StandingSerializer(serializers.ModelSerializer):

    team_name = serializers.CharField(
        source="team.name",
        read_only=True
    )

    league_name = serializers.CharField(
        source="league.name",
        read_only=True
    )

    class Meta:
        model = Standing
        fields = "__all__"


# -------------------------
# Fixture Serializer
# -------------------------
class FixtureSerializer(serializers.ModelSerializer):

    class Meta:
        model = Fixture
        fields = "__all__"


# -------------------------
# H2H Match Serializer
# -------------------------
class H2HMatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = H2HMatch
        fields = "__all__"


# -------------------------
# Team Feature Store Serializer
# -------------------------
class TeamFeatureStoreSerializer(serializers.ModelSerializer):

    team_name_display = serializers.CharField(
        source="team.name",
        read_only=True
    )

    league_name_display = serializers.CharField(
        source="league.name",
        read_only=True
    )

    class Meta:
        model = TeamFeatureStore
        fields = "__all__"


# -------------------------
# Match Insight Serializer
# -------------------------
class MatchInsightSerializer(serializers.ModelSerializer):

    fixture_display = serializers.StringRelatedField(
        source="fixture",
        read_only=True
    )

    class Meta:
        model = MatchInsight
        fields = "__all__"


# -------------------------
# Nested Serializers (Advanced API usage)
# -------------------------

class TeamWithStatsSerializer(serializers.ModelSerializer):

    teamstats = TeamStatsSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Team
        fields = "__all__"


class LeagueWithTeamsSerializer(serializers.ModelSerializer):

    teams = TeamSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = League
        fields = "__all__"