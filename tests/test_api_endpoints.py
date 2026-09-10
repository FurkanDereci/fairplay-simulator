import unittest
import uuid
from fastapi.testclient import TestClient
from src.backend.app import app

class TestAPIEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_get_fixtures(self):
        res = self.client.get("/api/fixtures")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("fixtures", data)
        self.assertGreater(len(data["fixtures"]), 0)

    def test_unauthenticated_protected_endpoints(self):
        res_port = self.client.get("/api/portfolio")
        self.assertEqual(res_port.status_code, 401)
        
        res_wager = self.client.post("/api/wager", json={"match_id": "1", "market_type": "1X2", "selection": "HOME", "stake": 100})
        self.assertEqual(res_wager.status_code, 401)

    def test_serve_frontend_root(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

    def test_energy_depletion_blocks_wager(self):
        unique_id = str(uuid.uuid4())[:8]
        res_reg = self.client.post("/api/auth/register", json={
            "email": f"energy_{unique_id}@example.com",
            "username": f"energy_{unique_id}",
            "password": "Password123!"
        })
        self.assertEqual(res_reg.status_code, 200)
        headers = {"Authorization": f"Bearer {res_reg.json()['access_token']}"}

        # 100 energy / 10 per bet -> the first ten wagers are accepted.
        for i in range(10):
            res = self.client.post("/api/wager", json={
                "match_id": f"energy-{i}", "market_type": "1X2", "selection": "HOME", "stake": 10.0
            }, headers=headers)
            self.assertEqual(res.status_code, 200, res.text)

        # The eleventh is rejected until energy recharges.
        res_blocked = self.client.post("/api/wager", json={
            "match_id": "energy-final", "market_type": "1X2", "selection": "HOME", "stake": 10.0
        }, headers=headers)
        self.assertEqual(res_blocked.status_code, 429)

        portfolio = self.client.get("/api/portfolio", headers=headers).json()
        self.assertEqual(portfolio["simulation_energy"], 0)

    def test_energy_recharges_over_time(self):
        from datetime import datetime, timedelta, timezone
        from src.backend.models.database import SessionLocal, UserBalanceModel

        unique_id = str(uuid.uuid4())[:8]
        res_reg = self.client.post("/api/auth/register", json={
            "email": f"regen_{unique_id}@example.com",
            "username": f"regen_{unique_id}",
            "password": "Password123!"
        })
        user_id = res_reg.json()["user"]["id"]
        headers = {"Authorization": f"Bearer {res_reg.json()['access_token']}"}

        # Drain the balance and backdate the clock by two hours.
        db = SessionLocal()
        bal = db.query(UserBalanceModel).filter(UserBalanceModel.user_id == user_id).first()
        bal.simulation_energy = 0
        bal.last_energy_update = datetime.now(timezone.utc) - timedelta(hours=2)
        db.commit()
        db.close()

        # 2 hours at 10/hour -> 20 energy recharged.
        portfolio = self.client.get("/api/portfolio", headers=headers).json()
        self.assertEqual(portfolio["simulation_energy"], 20)

if __name__ == '__main__':
    unittest.main()
