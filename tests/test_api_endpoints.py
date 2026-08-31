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

if __name__ == '__main__':
    unittest.main()
