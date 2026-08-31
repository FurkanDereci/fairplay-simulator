import uuid
from datetime import datetime, timedelta, timezone
from src.data_ingestion.odds_normalizer import OddsNormalizer, NormalizedMarket

class MockDataGenerator:
    """Generates realistic mock football fixtures and betting odds for offline dev/testing."""
    
    SAMPLE_MATCHES = [
        ("Arsenal", "Chelsea", "Premier League"),
        ("Real Madrid", "Barcelona", "La Liga"),
        ("Inter Milan", "AC Milan", "Serie A"),
        ("Galatasaray", "Fenerbahçe", "Süper Lig"),
        ("Bayern Munich", "Borussia Dortmund", "Bundesliga")
    ]

    @classmethod
    def generate_fixtures_and_odds(cls) -> list[dict]:
        fixtures = []
        now = datetime.now(timezone.utc)
        
        for idx, (home, away, league) in enumerate(cls.SAMPLE_MATCHES):
            match_id = str(uuid.uuid4())
            kickoff = now + timedelta(days=idx + 1, hours=19)
            
            # Raw odds with built-in ~4-6% overround
            raw_1x2 = {"HOME": 1.95, "DRAW": 3.50, "AWAY": 4.10}
            raw_ou = {"OVER_2.5": 1.85, "UNDER_2.5": 2.02}
            
            normalized_1x2 = OddsNormalizer.normalize_market("1X2", raw_1x2)
            normalized_ou = OddsNormalizer.normalize_market("OVER_UNDER_2.5", raw_ou)
            
            fixtures.append({
                "match_id": match_id,
                "league": league,
                "home_team": home,
                "away_team": away,
                "kickoff_time": kickoff.isoformat(),
                "status": "SCHEDULED",
                "markets": {
                    "1X2": normalized_1x2.__dict__,
                    "OVER_UNDER_2.5": normalized_ou.__dict__
                }
            })
        return fixtures
