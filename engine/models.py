from django.db import models


class League(models.Model):
    api_id = models.IntegerField(unique=True)  # API-Football league ID (e.g. 39)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True)
    season = models.IntegerField()
    active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name}"


class Team(models.Model):
    api_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=100)

    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name="teams"
    )

    logo_url = models.URLField(blank=True, null=True)
    venue_name = models.CharField(max_length=150, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TeamStats(models.Model):
    league = models.ForeignKey(
        League,
        on_delete=models.CASCADE,
        related_name="teamstats"
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="teamstats"
    )
    season = models.IntegerField()

    form = models.CharField(max_length=150)
    matches_played_home = models.IntegerField()
    matches_played_away = models.IntegerField()
    matches_played_total = models.IntegerField()

    wins_home = models.IntegerField()
    wins_away = models.IntegerField()
    wins_total = models.IntegerField()

    draws_home = models.IntegerField()
    draws_away = models.IntegerField()
    draws_total = models.IntegerField()

    losses_home = models.IntegerField()
    losses_away = models.IntegerField()
    losses_total = models.IntegerField()


    goals_home = models.IntegerField()
    goals_away = models.IntegerField()
    goals_total = models.IntegerField()

    avg_goals_home = models.FloatField()
    avg_goals_away = models.FloatField()
    avg_goals_total = models.FloatField()

    conceded_home = models.IntegerField()
    conceded_away = models.IntegerField()
    conceded_total = models.IntegerField()

    avg_conceded_home = models.FloatField()
    avg_conceded_away = models.FloatField()
    avg_conceded_total = models.FloatField()

    over_15 = models.IntegerField()
    under_15 = models.IntegerField()

    over_25 = models.IntegerField()
    under_25 = models.IntegerField()

    over_35 = models.IntegerField()
    under_35 = models.IntegerField()

    clean_sheet_home = models.IntegerField()
    clean_sheet_away = models.IntegerField()
    clean_sheet_total = models.IntegerField()


    failed_to_score_home = models.IntegerField()
    failed_to_score_away = models.IntegerField()
    failed_to_score_total = models.IntegerField()

    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("league", "team", "season")


class Standing(models.Model):
    league = models.ForeignKey(League, on_delete=models.CASCADE, related_name="standings")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="standings")
    season = models.IntegerField()

    rank = models.IntegerField()
    points = models.IntegerField()
    goals_diff = models.IntegerField()
    last_5_form = models.CharField(max_length=10)

    # Total stats
    played_total = models.IntegerField()
    wins_total = models.IntegerField()
    draws_total = models.IntegerField()
    losses_total = models.IntegerField()
    goals_for_total = models.IntegerField()
    goals_against_total = models.IntegerField()

    # Home stats
    played_home = models.IntegerField()
    wins_home = models.IntegerField()
    draws_home = models.IntegerField()
    losses_home = models.IntegerField()
    goals_for_home = models.IntegerField()
    goals_against_home = models.IntegerField()

    # Away stats
    played_away = models.IntegerField()
    wins_away = models.IntegerField()
    draws_away = models.IntegerField()
    losses_away = models.IntegerField()
    goals_for_away = models.IntegerField()
    goals_against_away = models.IntegerField()

    description = models.CharField(max_length=255, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("league", "team", "season")



class Fixture(models.Model):
    # Fixture info
    fixture_id = models.CharField(max_length=255, null=True, blank=True)
    referee = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField(null=True, blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    elapsed = models.IntegerField(null=True, blank=True)
    status_short = models.CharField(max_length=10, null=True, blank=True)
    status_long = models.CharField(max_length=50, null=True, blank=True)
    season = models.IntegerField()

    # Venue info
    venue_id = models.IntegerField(null=True, blank=True)
    venue_name = models.CharField(max_length=255, null=True, blank=True)
    venue_city = models.CharField(max_length=255, null=True, blank=True)

    # League info
    league_id = models.IntegerField(null=True, blank=True)
    league_name = models.CharField(max_length=255, null=True, blank=True)
    league_country = models.CharField(max_length=100, null=True, blank=True)
    league_season = models.IntegerField(null=True, blank=True)
    league_round = models.CharField(max_length=100, null=True, blank=True)

    # Teams info
    home_team_id = models.IntegerField(null=True, blank=True)
    home_team_name = models.CharField(max_length=255, null=True, blank=True)
    away_team_id = models.IntegerField(null=True, blank=True)
    away_team_name = models.CharField(max_length=255, null=True, blank=True)

    # Match winner
    home_winner = models.BooleanField(null=True, blank=True)
    away_winner = models.BooleanField(null=True, blank=True)

    # Scores
    goals_home = models.IntegerField(null=True, blank=True)
    goals_away = models.IntegerField(null=True, blank=True)
    halftime_home = models.IntegerField(null=True, blank=True)
    halftime_away = models.IntegerField(null=True, blank=True)
    fulltime_home = models.IntegerField(null=True, blank=True)
    fulltime_away = models.IntegerField(null=True, blank=True)
    extratime_home = models.IntegerField(null=True, blank=True)
    extratime_away = models.IntegerField(null=True, blank=True)
    penalty_home = models.IntegerField(null=True, blank=True)
    penalty_away = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        date_str = self.date.date() if self.date else "No date"
        return f"{self.home_team_name} vs {self.away_team_name} ({date_str})"




class H2HMatch(models.Model):
    fixture_id = models.IntegerField(unique=True)
    date = models.DateTimeField()

    # League info
    league_id = models.IntegerField()
    league_name = models.CharField(max_length=255)
    league_round = models.CharField(max_length=255, blank=True, null=True)

    # Home team info
    home_team_id = models.IntegerField()
    home_team_name = models.CharField(max_length=255)

    # Away team info
    away_team_id = models.IntegerField()
    away_team_name = models.CharField(max_length=255)

    # Score info
    home_goals = models.IntegerField(blank=True, null=True)
    away_goals = models.IntegerField(blank=True, null=True)

    # Fixture status
    status_short = models.CharField(max_length=10)
    status_long = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["home_team_id", "away_team_id"], name="h2h_home_away_idx"),
            models.Index(fields=["league_id"], name="h2h_league_idx"),
        ]

    def __str__(self):
        return f"{self.home_team_name} vs {self.away_team_name} ({self.date.date()})"






class TeamFeatureStore(models.Model):
    # Link
    team = models.ForeignKey("Team", on_delete=models.CASCADE, related_name="features")
    league = models.ForeignKey("League", on_delete=models.CASCADE, related_name="features")
    season = models.IntegerField()

    # Basic Team Info
    team_name = models.CharField(max_length=100)
    logo_url = models.URLField(blank=True, null=True)
    venue_name = models.CharField(max_length=150, blank=True)

    # TeamStats Aggregates
    matches_played_home = models.IntegerField()
    matches_played_away = models.IntegerField()
    matches_played_total = models.IntegerField()

    wins_home = models.IntegerField()
    wins_away = models.IntegerField()
    wins_total = models.IntegerField()

    draws_home = models.IntegerField()
    draws_away = models.IntegerField()
    draws_total = models.IntegerField()

    losses_home = models.IntegerField()
    losses_away = models.IntegerField()
    losses_total = models.IntegerField()

    goals_home = models.IntegerField()
    goals_away = models.IntegerField()
    goals_total = models.IntegerField()

    avg_goals_home = models.FloatField()
    avg_goals_away = models.FloatField()
    avg_goals_total = models.FloatField()

    conceded_home = models.IntegerField()
    conceded_away = models.IntegerField()
    conceded_total = models.IntegerField()

    avg_conceded_home = models.FloatField()
    avg_conceded_away = models.FloatField()
    avg_conceded_total = models.FloatField()

    over_15 = models.IntegerField()
    under_15 = models.IntegerField()
    over_25 = models.IntegerField()
    under_25 = models.IntegerField()
    over_35 = models.IntegerField()
    under_35 = models.IntegerField()

    clean_sheet_home = models.IntegerField()
    clean_sheet_away = models.IntegerField()
    clean_sheet_total = models.IntegerField()

    failed_to_score_home = models.IntegerField()
    failed_to_score_away = models.IntegerField()
    failed_to_score_total = models.IntegerField()

    # Standings info
    rank = models.IntegerField(null=True, blank=True)
    points = models.IntegerField(null=True, blank=True)
    goals_diff = models.IntegerField(null=True, blank=True)
    form = models.CharField(max_length=10, blank=True)
    last_5_form = models.CharField(max_length=10, blank=True)
    # Recent Fixtures Stats (optional, last 5 matches)
    last_5_matches_played = models.IntegerField(default=0)
    last_5_wins = models.IntegerField(default=0)
    last_5_draws = models.IntegerField(default=0)
    last_5_losses = models.IntegerField(default=0)
    last_5_goals_for = models.IntegerField(default=0)
    last_5_goals_against = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("team", "league", "season")
        indexes = [
            models.Index(fields=["team", "league", "season"], name="team_feature_idx")
        ]

    def __str__(self):
        return f"{self.team_name} ({self.season})"


"""
Updated MatchInsight model — add these fields to your existing models.py
========================================================================
The 5 new fields store the structured prediction returned by Claude.
They are all nullable so existing rows aren't broken.
"""

# Replace your existing MatchInsight class with this:

from django.db import models


class MatchInsight(models.Model):

    WINNER_CHOICES = [
        ("home",  "Home"),
        ("away",  "Away"),
        ("draw",  "Draw"),
    ]
    PROBABILITY_CHOICES = [
        ("low",    "Low"),
        ("medium", "Medium"),
        ("high",   "High"),
    ]

    fixture = models.OneToOneField(
        "Fixture",
        on_delete=models.CASCADE,
        related_name="insight",
    )

    input_hash   = models.CharField(max_length=64)
    insight_text = models.TextField()

    # --- Structured prediction fields (NEW) ---
    predicted_winner    = models.CharField(max_length=10,  blank=True, null=True, choices=WINNER_CHOICES)
    confidence          = models.CharField(max_length=10,  blank=True, null=True, choices=PROBABILITY_CHOICES)
    btts_probability    = models.CharField(max_length=10,  blank=True, null=True, choices=PROBABILITY_CHOICES)
    over_25_probability = models.CharField(max_length=10,  blank=True, null=True, choices=PROBABILITY_CHOICES)
    recommended_bet     = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"Insight for {self.fixture} | "
            f"Winner: {self.predicted_winner} ({self.confidence}) | "
            f"Bet: {self.recommended_bet}"
        )


class BotUser(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    telegram_username = models.CharField(max_length=100, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)

    is_premium = models.BooleanField(default=False)
    subscription_start = models.DateTimeField(null=True, blank=True)
    subscription_end = models.DateTimeField(null=True, blank=True)

    paystack_customer_code = models.CharField(max_length=100, blank=True, null=True)
    paystack_subscription_code = models.CharField(max_length=100, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active_subscriber(self):
        from django.utils import timezone
        if not self.is_premium:
            return False
        if self.subscription_end and self.subscription_end < timezone.now():
            self.is_premium = False
            self.save()
            return False
        return True

    def __str__(self):
        return f"{self.telegram_username or self.telegram_id} — {'Premium' if self.is_premium else 'Free'}"