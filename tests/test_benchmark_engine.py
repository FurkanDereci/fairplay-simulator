import unittest
from src.backend.benchmark_engine import BenchmarkBot, BenchmarkManager

class TestBenchmarkEngine(unittest.TestCase):
    def test_strategy_selection_rules(self):
        market = {'HOME': 1.60, 'DRAW': 3.80, 'AWAY': 5.50}

        home_bot = BenchmarkBot('Home Bot', 'HOME_BIAS')
        sel, odds = home_bot.pick_selection(market)
        self.assertEqual(sel, 'HOME')
        self.assertEqual(odds, 1.60)

        fav_bot = BenchmarkBot('Fav Bot', 'FAVORITE')
        sel_fav, odds_fav = fav_bot.pick_selection(market)
        self.assertEqual(sel_fav, 'HOME') # 1.60 is favorite
        self.assertEqual(odds_fav, 1.60)

        away_fav_market = {'HOME': 4.50, 'DRAW': 3.60, 'AWAY': 1.70}
        sel_away, odds_away = fav_bot.pick_selection(away_fav_market)
        self.assertEqual(sel_away, 'AWAY') # 1.70 is favorite
        self.assertEqual(odds_away, 1.70)

        rand_bot = BenchmarkBot('Rand Bot', 'RANDOM')
        sel_r, odds_r = rand_bot.pick_selection(market, seed=42)
        self.assertIn(sel_r, ['HOME', 'DRAW', 'AWAY'])

    def test_bot_wager_and_settlement_nav_evolution(self):
        bot = BenchmarkBot('Home Bot', 'HOME_BIAS', initial_balance=1000.0, base_nav=100.0)
        self.assertEqual(bot.portfolio.nav, 100.0)

        # Place bet on Match 1 (5% of 1000 = 50 TL, odds 2.0)
        placed = bot.place_match_wager('m1', {'HOME': 2.0, 'DRAW': 3.0, 'AWAY': 3.0}, stake_fraction=0.05)
        self.assertTrue(placed)
        self.assertEqual(bot.portfolio.cash_balance, 950.0)
        self.assertEqual(bot.portfolio.locked_stakes, 50.0)

        # Match 1 ends with HOME win -> Payout 100 TL
        bot.settle_match('m1', outcome_1x2='HOME')
        self.assertEqual(bot.portfolio.cash_balance, 1050.0)
        self.assertEqual(bot.portfolio.nav, 105.0) # +5%
        self.assertEqual(bot.portfolio.calculate_twr(), 5.0)

        # Match 2 (stake 5% of 1050 = 52.50 TL) -> ends with AWAY win (loss)
        bot.place_match_wager('m2', {'HOME': 2.0, 'DRAW': 3.0, 'AWAY': 3.0}, stake_fraction=0.05)
        bot.settle_match('m2', outcome_1x2='AWAY')
        self.assertLess(bot.portfolio.nav, 105.0)

    def test_benchmark_manager_multi_match_simulation(self):
        manager = BenchmarkManager()
        market = {'HOME': 2.0, 'DRAW': 3.2, 'AWAY': 3.6}

        # Simulate 5 matches
        manager.process_match('m1', market, outcome_1x2='HOME', seed=1)
        manager.process_match('m2', market, outcome_1x2='DRAW', seed=2)
        manager.process_match('m3', market, outcome_1x2='AWAY', seed=3)
        manager.process_match('m4', market, outcome_1x2='HOME', seed=4)
        manager.process_match('m5', market, outcome_1x2='HOME', seed=5)

        summary = manager.get_benchmarks_summary(player_nav=110.0)
        self.assertEqual(summary['player_nav'], 110.0)
        self.assertIn('random_walk_index', summary)
        self.assertIn('favorite_heavy_index', summary)
        self.assertIn('home_advantage_index', summary)
        self.assertIn('twr', summary)
        self.assertEqual(summary['twr']['player'], 10.0)

if __name__ == '__main__':
    unittest.main()
