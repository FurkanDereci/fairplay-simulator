import unittest
import uuid
from fastapi.testclient import TestClient
from src.backend.app import app
from src.backend.match_engine import VirtualMatchEngine

class TestVirtualMatchEngine(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_derive_lambdas(self):
        # Favorite Home Team (Arsenal 1.50 vs Chelsea 6.00)
        odds = {'HOME': 1.50, 'DRAW': 4.20, 'AWAY': 6.00}
        lh, la = VirtualMatchEngine.derive_lambdas(odds)
        self.assertGreater(lh, la)
        self.assertGreater(lh, 0.25)
        self.assertGreater(la, 0.25)
        self.assertAlmostEqual(lh + la, 2.70, places=1)

    def test_sample_poisson_statistical_mean(self):
        lam = 1.80
        samples = [VirtualMatchEngine.sample_poisson(lam) for _ in range(5000)]
        mean = sum(samples) / len(samples)
        # Sample mean should be within 5% of true lambda
        self.assertAlmostEqual(mean, lam, delta=0.15)

    def test_simulate_match_deterministic(self):
        # Seed ensures reproducibility
        res1 = VirtualMatchEngine.simulate_match('m1', 'Arsenal', 'Chelsea', odds_1x2={'HOME': 1.95, 'DRAW': 3.5, 'AWAY': 4.1}, seed=123)
        res2 = VirtualMatchEngine.simulate_match('m1', 'Arsenal', 'Chelsea', odds_1x2={'HOME': 1.95, 'DRAW': 3.5, 'AWAY': 4.1}, seed=123)
        self.assertEqual(res1.home_score, res2.home_score)
        self.assertEqual(res1.away_score, res2.away_score)
        self.assertEqual(res1.outcome_1x2, res2.outcome_1x2)
        self.assertEqual(len(res1.events), len(res2.events))

    def test_monte_carlo_distribution(self):
        dist = VirtualMatchEngine.run_monte_carlo(lambda_home=1.75, lambda_away=0.95, iterations=5000, seed=42)
        self.assertEqual(dist.iterations, 5000)
        total_pct = dist.home_win_pct + dist.draw_pct + dist.away_win_pct
        self.assertAlmostEqual(total_pct, 100.0, delta=0.5)
        self.assertGreater(dist.fair_odds_1x2['HOME'], 1.0)
        self.assertGreater(dist.fair_odds_1x2['DRAW'], 1.0)
        self.assertGreater(dist.fair_odds_1x2['AWAY'], 1.0)

    def test_api_simulate_and_auto_settle_wager(self):
        unique_id = str(uuid.uuid4())[:8]
        res_reg = self.client.post('/api/auth/register', json={
            'email': f'sim_{unique_id}@fairplay.com',
            'username': f'sim_{unique_id}',
            'password': 'Password123!'
        })
        token = res_reg.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        # Place wager on fixture
        fixtures = self.client.get('/api/fixtures').json()['fixtures']
        match_id = fixtures[0]['match_id']

        res_wager = self.client.post('/api/wager', json={
            'match_id': match_id,
            'market_type': '1X2',
            'selection': 'HOME',
            'stake': 100.0
        }, headers=headers)
        self.assertEqual(res_wager.status_code, 200)

        # Simulate match
        res_sim = self.client.post('/api/matches/simulate', json={
            'match_id': match_id,
            'seed': 42
        }, headers=headers)
        self.assertEqual(res_sim.status_code, 200)
        sim_data = res_sim.json()
        self.assertIn('score', sim_data)
        self.assertIn('outcomes', sim_data)
        self.assertIn('settled_wagers', sim_data)
        self.assertEqual(len(sim_data['settled_wagers']), 1)

if __name__ == '__main__':
    unittest.main()
