import math
import unittest

def calculate_cooldown_hours(tier: int) -> float:
    """T(n) = min(168, 1.0 * 4^(n-1))"""
    if tier < 1:
        return 0.0
    return min(168.0, 1.0 * (4.0 ** (tier - 1)))

def calculate_overround_and_vig(odds: list[float]):
    """Calculates implied probability sum, overround, bookmaker margin, and fair odds."""
    implied_probs = [1.0 / o for o in odds]
    total_implied = sum(implied_probs)
    overround = total_implied - 1.0
    margin_pct = (overround / total_implied) * 100.0
    fair_probs = [p / total_implied for p in implied_probs]
    fair_odds = [1.0 / fp for fp in fair_probs]
    return {
        "overround": overround,
        "margin_pct": margin_pct,
        "fair_probs": fair_probs,
        "fair_odds": fair_odds
    }

class TestSimulatorMath(unittest.TestCase):
    def test_cooldown_exponential_backoff(self):
        self.assertEqual(calculate_cooldown_hours(1), 1.0)
        self.assertEqual(calculate_cooldown_hours(2), 4.0)
        self.assertEqual(calculate_cooldown_hours(3), 16.0)
        self.assertEqual(calculate_cooldown_hours(4), 64.0)
        self.assertEqual(calculate_cooldown_hours(5), 168.0)
        self.assertEqual(calculate_cooldown_hours(6), 168.0) # Capped at 168h (7 days)

    def test_overround_and_vig(self):
        # Odds: Home (1.90), Draw (3.60), Away (4.20)
        res = calculate_overround_and_vig([1.90, 3.60, 4.20])
        self.assertAlmostEqual(res["overround"], 0.0422, places=3)
        self.assertAlmostEqual(res["margin_pct"], 4.05, places=1)
        self.assertAlmostEqual(res["fair_odds"][0], 1.98, places=2)
        self.assertAlmostEqual(res["fair_odds"][1], 3.75, places=2)
        self.assertAlmostEqual(res["fair_odds"][2], 4.38, places=2)

if __name__ == '__main__':
    unittest.main()
