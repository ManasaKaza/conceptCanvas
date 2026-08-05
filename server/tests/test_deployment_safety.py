import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class DeploymentSafetyTests(unittest.TestCase):
    def test_health_exposes_staging_relevant_status(self):
        with TestClient(app) as client:
            response = client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertIn("environment", payload)
        self.assertIn("historyEnabled", payload)
        self.assertEqual(payload["schemaVersion"], "1.5")

    def test_disabled_history_returns_ephemeral_turn_without_persistence(self):
        payload = {
            "conversationId": None,
            "question": "Explain a simple concept",
            "mode": "text",
            "result": {"status": "success"},
        }
        with patch("app.main.HISTORY_ENABLED", False):
            with TestClient(app) as client:
                conversations = client.get("/api/conversations")
                saved = client.post("/api/conversations/turns", json=payload)

        self.assertEqual(conversations.status_code, 200)
        self.assertEqual(conversations.json()["conversations"], [])
        self.assertFalse(conversations.json()["historyEnabled"])
        self.assertEqual(saved.status_code, 200)
        self.assertIsNone(saved.json()["conversationId"])
        self.assertTrue(saved.json()["turnId"].startswith("ephemeral-"))


if __name__ == "__main__":
    unittest.main()
