import unittest
from src.data_ingestion.odds_normalizer import OddsNormalizer
from src.data_ingestion.mock_data_generator import MockDataGenerator

class TestDataIngestion(unittest.TestCase):
    def test_odds_normalizer_1x2(self):
        outcomes = {"HOME": 1.90, "DRAW": 3.60, "AWAY": 4.20}
        norm = OddsNormalizer.normalize_market("1X2", outcomes)
        
        self.assertEqual(norm.market_type, "1X2")
        self.assertAlmostEqual(norm.overround, 0.0422, places=3)
        self.assertAlmostEqual(norm.bookmaker_margin_pct, 4.05, places=1)
        self.assertEqual(norm.fair_odds["HOME"], 1.98)
        self.assertEqual(norm.fair_odds["DRAW"], 3.75)
        self.assertEqual(norm.fair_odds["AWAY"], 4.38)

    def test_mock_data_generator(self):
        fixtures = MockDataGenerator.generate_fixtures_and_odds()
        self.assertEqual(len(fixtures), 5)
        
        first = fixtures[0]
        self.assertEqual(first["home_team"], "Arsenal")
        self.assertEqual(first["away_team"], "Chelsea")
        self.assertIn("1X2", first["markets"])
        self.assertIn("OVER_UNDER_2.5", first["markets"])
        
        market_1x2 = first["markets"]["1X2"]
        self.assertGreater(market_1x2["overround"], 0.0)

if __name__ == '__main__':
    unittest.main()
