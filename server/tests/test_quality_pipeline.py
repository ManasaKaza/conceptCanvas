import json
import unittest
from pathlib import Path

from app.quality_evaluator import evaluate_lesson_quality
from app.storyboard_service import create_storyboard
from scripts.run_quality_benchmark import run_benchmark


BASE_EXPLANATION = {
    "title": "Client Server Communication",
    "quickMeaning": "A client sends a request and a server returns a response.",
    "deepExplanation": "The two systems exchange messages through an ordered interaction.",
    "stepByStep": [
        "The client creates a request.",
        "The server receives and processes the request.",
        "The server returns a response.",
    ],
    "realWorldExample": "A browser requests a web page from a server.",
    "analogy": "It is similar to asking a librarian for a book.",
    "technicalDetails": [],
    "commonConfusions": [],
    "interviewAngle": "Explain the participants and the ordered exchange.",
    "summary": "The client and server communicate through request and response messages.",
    "takeaways": ["The interaction has identifiable participants and messages."],
}


def make_scene(index: int, *, invalid_target: bool = False, mismatch: bool = False) -> dict:
    client_id = f"client_{index}"
    server_id = f"server_{index}"
    edge_id = f"request_{index}"
    target_ids = ["missing_target"] if invalid_target else [client_id, edge_id, server_id]
    spoken = (
        "Unrelated weather patterns change during the year."
        if mismatch
        else f"The client {index} sends a request to the server {index}."
    )
    return {
        "id": f"scene_{index}",
        "title": f"Request exchange {index}",
        "narration": f"The client and server complete communication stage {index} through a visible request.",
        "visual": {
            "schemaVersion": "2.0",
            "diagramType": "sequence",
            "orientation": "left_to_right",
            "elements": [
                {
                    "type": "node",
                    "id": client_id,
                    "label": f"Client {index}",
                    "nodeKind": "client",
                },
                {
                    "type": "node",
                    "id": server_id,
                    "label": f"Server {index}",
                    "nodeKind": "server",
                },
                {
                    "type": "edge",
                    "id": edge_id,
                    "fromId": client_id,
                    "toId": server_id,
                    "relation": "request",
                    "label": "Send request",
                },
            ],
        },
        "narrationSegments": [
            {
                "id": "segment_1",
                "order": 1,
                "spokenText": spoken,
                "subtitleText": f"Client {index} sends a request",
                "targetElementIds": target_ids,
                "action": "trace",
                "estimatedDurationMs": 3200,
            }
        ],
    }


class QualityEvaluatorTests(unittest.TestCase):
    def test_narration_visual_mismatch_is_reported(self):
        result = create_storyboard(
            question="Explain client server interaction",
            explanation=BASE_EXPLANATION,
            requested_scene_count=3,
            ai_storyboard={"scenes": [make_scene(1), make_scene(2, mismatch=True), make_scene(3)]},
            ai_source="groq",
        )
        codes = {issue["code"] for issue in result.quality_report["issues"]}
        self.assertIn("narration_visual_mismatch", codes)
        self.assertEqual(result.quality_report["status"], "warn")

    def test_absolute_and_numeric_claims_are_flagged_as_risk(self):
        explanation = {
            **BASE_EXPLANATION,
            "technicalDetails": [
                "This approach always guarantees a 40% performance improvement."
            ],
        }
        result = create_storyboard(
            question="Explain client server interaction",
            explanation=explanation,
            requested_scene_count=3,
        )
        codes = {issue["code"] for issue in result.quality_report["issues"]}
        self.assertIn("absolute_always", codes)
        self.assertIn("unsupported_guarantee", codes)
        self.assertIn("unverified_performance_number", codes)
        self.assertGreater(result.quality_report["metrics"]["technicalRiskScore"], 0)

    def test_opposite_direction_claims_are_flagged(self):
        explanation = {
            **BASE_EXPLANATION,
            "technicalDetails": [
                "Higher cache size increases response speed.",
                "Higher cache size decreases response speed.",
            ],
        }
        result = create_storyboard(
            question="Explain cache size and response speed",
            explanation=explanation,
            requested_scene_count=3,
        )
        codes = {issue["code"] for issue in result.quality_report["issues"]}
        self.assertIn("possible_direction_contradiction", codes)


class RepairPipelineTests(unittest.TestCase):
    def test_invalid_scene_is_replaced_without_discarding_valid_scenes(self):
        result = create_storyboard(
            question="Explain client server interaction",
            explanation=BASE_EXPLANATION,
            requested_scene_count=3,
            ai_storyboard={
                "scenes": [make_scene(1), make_scene(2, invalid_target=True), make_scene(3)]
            },
            ai_source="groq",
        )
        self.assertEqual(result.source, "hybrid")
        self.assertEqual(result.repair_summary["preservedSceneIds"], ["scene_1", "scene_3"])
        self.assertEqual(result.repair_summary["replacedSceneIds"], ["scene_2"])
        self.assertEqual(len(result.storyboard["scenes"]), 3)

    def test_model_repair_can_return_a_valid_full_storyboard(self):
        invalid = {"scenes": [make_scene(1), make_scene(2, invalid_target=True), make_scene(3)]}
        repaired = {"scenes": [make_scene(1), make_scene(2), make_scene(3)]}
        callback_calls = []

        def repair_callback(candidate, issues):
            callback_calls.append((candidate, issues))
            return repaired

        result = create_storyboard(
            question="Explain client server interaction",
            explanation=BASE_EXPLANATION,
            requested_scene_count=3,
            ai_storyboard=invalid,
            ai_source="gemini",
            ai_model_used="test-model",
            repair_callback=repair_callback,
        )
        self.assertEqual(len(callback_calls), 1)
        self.assertEqual(result.source, "gemini")
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.repair_summary["strategy"], "model_repair")
        self.assertTrue(result.repair_summary["modelRepairSucceeded"])


class BenchmarkTests(unittest.TestCase):
    def test_fifty_topic_benchmark_meets_foundation_thresholds(self):
        dataset = Path(__file__).parents[1] / "benchmarks" / "quality_benchmark.json"
        payload = json.loads(dataset.read_text())
        self.assertEqual(len(payload["cases"]), 50)

        report = run_benchmark(dataset)
        summary = report["summary"]
        self.assertEqual(summary["totalCases"], 50)
        self.assertEqual(summary["exactSceneCountRate"], 1.0)
        self.assertEqual(summary["schemaPassRate"], 1.0)
        self.assertGreaterEqual(summary["domainAccuracy"], 0.95)
        self.assertGreaterEqual(summary["archetypeAccuracy"], 0.95)
        self.assertEqual(summary["failedCaseIds"], [])


if __name__ == "__main__":
    unittest.main()
