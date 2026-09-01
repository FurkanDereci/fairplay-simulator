import unittest
import uuid
from fastapi.testclient import TestClient
from src.backend.app import app

class TestFullArchitecture(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        unique_id = str(uuid.uuid4())[:8]
        self.test_email = f"user_{unique_id}@example.com"
        self.test_username = f"user_{unique_id}"
        self.test_password = "SecurePassword123!"

    def test_registration_login_and_authenticated_flow(self):
        # 1. Register User
        res_reg = self.client.post("/api/auth/register", json={
            "email": self.test_email,
            "username": self.test_username,
            "password": self.test_password
        })
        self.assertEqual(res_reg.status_code, 200)
        data_reg = res_reg.json()
        self.assertIn("access_token", data_reg)
        token = data_reg["access_token"]

        # 2. Login User
        res_login = self.client.post("/api/auth/login", json={
            "username": self.test_username,
            "password": self.test_password
        })
        self.assertEqual(res_login.status_code, 200)

        # 3. Authenticated Portfolio Check
        headers = {"Authorization": f"Bearer {token}"}
        res_port = self.client.get("/api/portfolio", headers=headers)
        self.assertEqual(res_port.status_code, 200)
        data_port = res_port.json()
        self.assertEqual(data_port["nav"], 100.0)
        self.assertEqual(data_port["cash_balance"], 1000.0)

        # 4. Place Wager with Ruin Risk Warning (200 TL > 15% of 1000 TL)
        res_wager = self.client.post("/api/wager", json={
            "match_id": "match_1",
            "market_type": "1X2",
            "selection": "HOME",
            "stake": 200.0
        }, headers=headers)
        self.assertEqual(res_wager.status_code, 200)
        data_wager = res_wager.json()
        self.assertTrue(data_wager["ruin_risk_warning"])

        # 5. Refill Virtual Balance
        res_refill = self.client.post("/api/refill", headers=headers)
        self.assertEqual(res_refill.status_code, 200)
        data_refill = res_refill.json()
        self.assertEqual(data_refill["cash_balance"], 1800.0)
        self.assertEqual(data_refill["nav"], 100.0)

        # 6. Settle Wager (Won)
        wager_id = data_wager["wager_id"]
        res_settle = self.client.post("/api/wager/settle", json={
            "wager_id": wager_id,
            "won": True
        }, headers=headers)
        self.assertEqual(res_settle.status_code, 200)
        data_settle = res_settle.json()
        self.assertEqual(data_settle["status"], "WON")
        self.assertGreater(data_settle["nav"], 100.0)

        # 7. Check Portfolio History in Database
        res_port_updated = self.client.get("/api/portfolio", headers=headers)
        self.assertEqual(res_port_updated.status_code, 200)
        port_data = res_port_updated.json()
        self.assertGreater(len(port_data["nav_history"]), 2)

    def test_bankruptcy_lockout_flow(self):
        unique_id = str(uuid.uuid4())[:8]
        res_reg = self.client.post("/api/auth/register", json={
            "email": f"bankrupt_{unique_id}@example.com",
            "username": f"bankrupt_{unique_id}",
            "password": "Password123!"
        })
        token = res_reg.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Bet all 1000 TL
        res_wager = self.client.post("/api/wager", json={
            "match_id": "m1",
            "market_type": "1X2",
            "selection": "HOME",
            "stake": 1000.0
        }, headers=headers)
        self.assertEqual(res_wager.status_code, 200)
        wager_id = res_wager.json()["wager_id"]

        # Settle as Lost -> Balance 0, locked 0 -> Triggers Cooldown Tier 1
        res_settle = self.client.post("/api/wager/settle", json={
            "wager_id": wager_id,
            "won": False
        }, headers=headers)
        self.assertEqual(res_settle.status_code, 200)
        self.assertTrue(res_settle.json()["bankruptcy_triggered"])
        self.assertEqual(res_settle.json()["bankruptcy_tier"], 1)

        # Attempt to wager while in cooldown -> 423 Locked
        res_blocked_wager = self.client.post("/api/wager", json={
            "match_id": "m2",
            "market_type": "1X2",
            "selection": "AWAY",
            "stake": 100.0
        }, headers=headers)
        self.assertEqual(res_blocked_wager.status_code, 423)

        # Attempt to refill while in active cooldown lockout -> 423 Locked
        res_blocked_refill = self.client.post("/api/refill", headers=headers)
        self.assertEqual(res_blocked_refill.status_code, 423)

if __name__ == '__main__':
    unittest.main()
