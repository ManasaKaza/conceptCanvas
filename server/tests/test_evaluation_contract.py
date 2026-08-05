import json
import unittest
from pathlib import Path


class HumanReviewRubricTests(unittest.TestCase):
    def test_rubric_weights_and_critical_release_gate_are_valid(self):
        path = Path(__file__).parents[1] / "evaluation" / "human_review_rubric.json"
        rubric = json.loads(path.read_text(encoding="utf-8"))
        dimensions = rubric["dimensions"]
        self.assertAlmostEqual(sum(item["weight"] for item in dimensions), 1.0)
        self.assertGreaterEqual(len([item for item in dimensions if item["critical"]]), 3)
        self.assertGreaterEqual(rubric["releaseGate"]["minimumCriticalDimensionScore"], 4)

    def test_rubric_endpoint_returns_versioned_contract(self):
        from fastapi.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            response = client.get("/api/evaluation/human-review-rubric")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["schemaVersion"], "1.0")
        self.assertEqual(len(payload["dimensions"]), 8)


if __name__ == "__main__":
    unittest.main()
