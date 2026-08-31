import unittest
from datetime import datetime, timedelta, timezone
from src.backend.nav_engine import NAVPortfolioEngine
from src.backend.cooldown_engine import CooldownEngine

class TestBackendCore(unittest.TestCase):
    def test_nav_portfolio_engine_refill_invariance(self):
        portfolio = NAVPortfolioEngine(initial_balance=1000.0, base_nav=100.0)
        self.assertEqual(portfolio.nav, 100.0)
        self.assertEqual(portfolio.total_units, 10.0)
        
        # Place wager of 500 TL
        placed = portfolio.place_wager(500.0)
        self.assertTrue(placed)
        self.assertEqual(portfolio.cash_balance, 500.0)
        self.assertEqual(portfolio.locked_stakes, 500.0)
        self.assertEqual(portfolio.nav, 100.0) # NAV unchanged prior to outcome
        
        # Win wager with 2.0 odds -> payout 1000 TL
        portfolio.settle_wager(stake=500.0, payout=1000.0)
        self.assertEqual(portfolio.cash_balance, 1500.0)
        self.assertEqual(portfolio.total_portfolio_value, 1500.0)
        self.assertEqual(portfolio.nav, 150.0) # NAV increases to 150.0 (+50%)
        
        # Refill deposit 1500 TL -> NAV must remain 150.0
        portfolio.deposit_refill(1500.0)
        self.assertEqual(portfolio.nav, 150.0)
        self.assertEqual(portfolio.total_units, 20.0) # Units increase from 10 to 20
        self.assertEqual(portfolio.cash_balance, 3000.0)

    def test_cooldown_engine_exponential_backoff(self):
        engine = CooldownEngine()
        now = datetime.now(timezone.utc)
        
        # 1st Bankruptcy -> 1h lockout
        res1 = engine.trigger_bankruptcy(now)
        self.assertEqual(res1["lockout_hours"], 1.0)
        self.assertFalse(engine.check_and_unlock(now + timedelta(minutes=30)))
        self.assertTrue(engine.check_and_unlock(now + timedelta(hours=1, minutes=1)))
        
        # 2nd Bankruptcy -> 4h lockout
        res2 = engine.trigger_bankruptcy(now)
        self.assertEqual(res2["lockout_hours"], 4.0)
        
        # 3rd Bankruptcy -> 16h lockout
        res3 = engine.trigger_bankruptcy(now)
        self.assertEqual(res3["lockout_hours"], 16.0)

    def test_cooldown_tier_decay(self):
        engine = CooldownEngine()
        engine.bankruptcy_tier = 3
        
        # 3 active solvent days -> tier decays to 2
        engine.record_solvent_day()
        engine.record_solvent_day()
        engine.record_solvent_day()
        self.assertEqual(engine.bankruptcy_tier, 2)

if __name__ == '__main__':
    unittest.main()
