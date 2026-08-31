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

if __name__ == '__main__':
    unittest.main()
