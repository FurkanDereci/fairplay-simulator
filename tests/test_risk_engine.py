import unittest
from src.backend.risk_engine import QuantRiskEngine

class TestQuantRiskEngine(unittest.TestCase):
    def test_returns_series(self):
        navs = [100.0, 105.0, 110.25]
        rets = QuantRiskEngine.calculate_returns_series(navs)
        self.assertEqual(len(rets), 2)
        self.assertAlmostEqual(rets[0], 0.05, places=4)
        self.assertAlmostEqual(rets[1], 0.05, places=4)

    def test_sharpe_ratio(self):
        # Stable 5% returns with tiny variance -> high Sharpe
        returns = [0.05, 0.06, 0.04, 0.05, 0.05]
        sharpe = QuantRiskEngine.calculate_sharpe_ratio(returns)
        self.assertGreater(sharpe, 5.0)

        # High variance oscillating returns -> lower Sharpe
        wild_returns = [0.20, -0.15, 0.25, -0.20, 0.10]
        wild_sharpe = QuantRiskEngine.calculate_sharpe_ratio(wild_returns)
        self.assertLess(wild_sharpe, sharpe)

    def test_sortino_ratio(self):
        # Only upside returns -> downside dev is 0 -> high Sortino
        upside_returns = [0.02, 0.04, 0.08, 0.01, 0.05]
        sortino = QuantRiskEngine.calculate_sortino_ratio(upside_returns)
        self.assertGreater(sortino, 0.0)

    def test_max_drawdown(self):
        # Peak 100 -> 120 -> drop to 90 (drop is (120-90)/120 = 25%) -> recover to 110
        navs = [100.0, 110.0, 120.0, 90.0, 105.0, 110.0]
        mdd = QuantRiskEngine.calculate_max_drawdown(navs)
        self.assertEqual(mdd, 25.0)

        # Monotonically increasing NAV -> 0% drawdown
        mono_navs = [100.0, 105.0, 112.0, 120.0]
        self.assertEqual(QuantRiskEngine.calculate_max_drawdown(mono_navs), 0.0)

    def test_beta_and_alpha(self):
        # Player moves 2x the benchmark
        b_returns = [0.02, 0.04, -0.01, 0.03, -0.02]
        p_returns = [0.04, 0.08, -0.02, 0.06, -0.04]
        beta, alpha = QuantRiskEngine.calculate_beta_and_alpha(p_returns, b_returns)
        self.assertAlmostEqual(beta, 2.0, places=1)

    def test_trade_analytics(self):
        wagers = [
            {'status': 'WON', 'stake': 100.0, 'payout': 250.0},  # gain +150
            {'status': 'LOST', 'stake': 50.0, 'payout': 0.0},    # loss -50
            {'status': 'WON', 'stake': 50.0, 'payout': 100.0},   # gain +50
            {'status': 'PENDING', 'stake': 100.0, 'payout': 0.0} # ignored
        ]
        stats = QuantRiskEngine.calculate_trade_analytics(wagers)
        self.assertEqual(stats['total_trades'], 3)
        self.assertAlmostEqual(stats['win_rate_pct'], 66.67, places=1)
        self.assertEqual(stats['gross_profit'], 200.0)
        self.assertEqual(stats['gross_loss'], 50.0)
        self.assertEqual(stats['profit_factor'], 4.0) # 200 / 50

    def test_risk_adjusted_score(self):
        # High TWR with low drawdown and good Sharpe -> high score
        score1 = QuantRiskEngine.calculate_risk_adjusted_score(twr_pct=50.0, max_drawdown_pct=5.0, sharpe=2.0)
        # Same TWR with huge 60% drawdown -> low score
        score2 = QuantRiskEngine.calculate_risk_adjusted_score(twr_pct=50.0, max_drawdown_pct=60.0, sharpe=0.5)
        self.assertGreater(score1, score2)

if __name__ == '__main__':
    unittest.main()
