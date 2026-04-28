from engine.models import Team, League
# Find Premier League
league_name = "Premier League"

try:
    league = League.objects.get(name=league_name)
except League.DoesNotExist:
    print(f"❌ League '{league_name}' not found")
    raise SystemExit

teams_data = [
    (67, "Blackburn"),
    (68, "Bolton"),
    (69, "Derby"),
    (70, "Middlesbrough"),
    (71, "Norwich"),
    (72, "QPR"),
    (73, "Rotherham"),
    (74, "Sheffield Wednesday"),
    (75, "Stoke City"),
    (746, "Sunderland"),
    (747, "Barnsley"),
    (748, "Burton Albion"),
    (1333, "AFC Wimbledon"),
    (1334, "Bristol Rovers"),
    (1335, "Charlton"),
    (1336, "Fleetwood Town"),
    (1337, "Northampton"),
    (1338, "Oxford United"),
    (1339, "Rochdale"),
    (1340, "Scunthorpe"),
    (1341, "Southend"),
    (1342, "Walsall"),
    (1343, "Bradford"),
    (1344, "Bury"),
    (1345, "Chesterfield"),
    (134, "Coventry"),
]

existing_ids = set(
    Team.objects.values_list("api_id", flat=True)
)

new_teams = []

for api_id, name in teams_data:
    if api_id not in existing_ids:
        new_teams.append(
            Team(
                api_id=api_id,
                name=name,
                league=league
            )
        )

Team.objects.bulk_create(new_teams)

print("\nDone.")
print(f"Created: {len(new_teams)}")
print(f"Skipped: {len(teams_data) - len(new_teams)}")