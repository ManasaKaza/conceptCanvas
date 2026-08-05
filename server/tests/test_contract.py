import os
import unittest

from pydantic import ValidationError

from app.lesson_constraints import extract_scene_count, resolve_scene_count
from app.models import ExplainRequest, Storyboard, VisualSpec
from app.storyboard_service import create_storyboard


EXPLANATION = {
    "title": "How DNS Resolution Works",
    "quickMeaning": "DNS translates a domain name into an IP address before a browser connects.",
    "stepByStep": [
        "The browser checks its local DNS cache for a recent answer.",
        "A recursive resolver asks the DNS hierarchy when the cache misses.",
        "The authoritative DNS server returns the requested IP address.",
        "The resolver caches the answer and sends it back to the browser.",
        "The browser connects to the web server using the returned IP address.",
    ],
    "realWorldExample": "Opening example.com triggers the lookup before the page request begins.",
    "technicalDetails": ["DNS records can be cached according to their time to live."],
    "summary": "DNS maps readable names to network addresses through a hierarchical lookup.",
    "takeaways": ["Name resolution happens before the browser contacts the website server."],
}

RECURSION_EXPLANATION = {
    **EXPLANATION,
    "title": "How Recursion Uses the Call Stack",
    "quickMeaning": "Recursion lets a function solve a problem by calling itself with a smaller input.",
    "stepByStep": [
        "The original function call creates the first stack frame.",
        "Each recursive call adds another frame while earlier calls wait.",
        "A base case stops new calls and returns a concrete value.",
        "The stack unwinds as each waiting call uses the returned value.",
    ],
    "summary": "Recursion builds stack frames until the base case, then returns through them in reverse order.",
}


def make_valid_ai_scene(index: int) -> dict:
    client = f"dns_client_{index}"
    resolver = f"recursive_resolver_{index}"
    answer = f"dns_answer_{index}"
    request_edge = f"client_to_resolver_{index}"
    response_edge = f"resolver_to_answer_{index}"

    return {
        "id": f"scene_{index}",
        "title": f"Resolver interaction {index}",
        "narration": "The resolver follows one specific and visible part of the DNS lookup flow.",
        "visual": {
            "schemaVersion": "2.0",
            "diagramType": "sequence",
            "orientation": "left_to_right",
            "elements": [
                {
                    "type": "node",
                    "id": client,
                    "label": "Browser",
                    "nodeKind": "client",
                },
                {
                    "type": "node",
                    "id": resolver,
                    "label": "Recursive resolver",
                    "nodeKind": "service",
                },
                {
                    "type": "node",
                    "id": answer,
                    "label": "DNS answer",
                    "nodeKind": "data",
                },
                {
                    "type": "edge",
                    "id": request_edge,
                    "fromId": client,
                    "toId": resolver,
                    "relation": "request",
                    "label": "Resolve domain",
                },
                {
                    "type": "edge",
                    "id": response_edge,
                    "fromId": resolver,
                    "toId": answer,
                    "relation": "response",
                    "label": "Return address",
                },
            ],
        },
        "narrationSegments": [
            {
                "id": "segment_1",
                "order": 1,
                "spokenText": "The browser sends its domain lookup request to the recursive resolver.",
                "subtitleText": "The browser asks the resolver",
                "targetElementIds": [client, resolver, request_edge],
                "action": "trace",
                "estimatedDurationMs": 3500,
            },
            {
                "id": "segment_2",
                "order": 2,
                "spokenText": "The resolver returns a DNS answer containing the address needed by the browser.",
                "subtitleText": "The resolver returns the address",
                "targetElementIds": [resolver, answer, response_edge],
                "action": "trace",
                "estimatedDurationMs": 4000,
            },
        ],
    }


class ExplainRequestTests(unittest.TestCase):
    def test_question_is_trimmed(self):
        request = ExplainRequest(question="  Explain DNS  ")
        self.assertEqual(request.question, "Explain DNS")

    def test_blank_question_is_rejected(self):
        with self.assertRaises(ValidationError):
            ExplainRequest(question="   ")

    def test_scene_count_outside_supported_range_is_rejected(self):
        with self.assertRaises(ValidationError):
            ExplainRequest(question="Explain DNS", requestedSceneCount=8)


class LessonConstraintTests(unittest.TestCase):
    def test_numeric_scene_count_is_detected_from_question(self):
        self.assertEqual(extract_scene_count("Explain DNS in exactly 4 scenes"), 4)

    def test_word_scene_count_is_detected_from_question(self):
        self.assertEqual(extract_scene_count("Explain recursion in four scenes"), 4)

    def test_scene_count_with_descriptive_words_is_detected(self):
        self.assertEqual(
            extract_scene_count("Explain DNS in exactly 5 beginner-friendly visual scenes"),
            5,
        )

    def test_explicit_ui_choice_overrides_question(self):
        self.assertEqual(resolve_scene_count("Explain DNS in 4 scenes", 6), 6)

    def test_unsupported_text_scene_count_is_rejected(self):
        with self.assertRaises(ValueError):
            extract_scene_count("Explain DNS in 10 scenes")


class LessonV2SchemaTests(unittest.TestCase):
    def test_duplicate_visual_ids_are_rejected(self):
        raw = make_valid_ai_scene(1)["visual"]
        raw["elements"][1]["id"] = raw["elements"][0]["id"]
        with self.assertRaises(ValidationError):
            VisualSpec.model_validate(raw)

    def test_edge_to_undeclared_node_is_rejected(self):
        raw = make_valid_ai_scene(1)["visual"]
        raw["elements"][3]["toId"] = "missing_node"
        with self.assertRaises(ValidationError):
            VisualSpec.model_validate(raw)


class StoryboardContractTests(unittest.TestCase):
    def test_fallback_returns_exact_requested_count_and_canonical_order(self):
        for requested_count in (3, 4, 5, 6, 7):
            with self.subTest(requested_count=requested_count):
                result = create_storyboard(
                    question="Explain DNS resolution",
                    explanation=EXPLANATION,
                    requested_scene_count=requested_count,
                )
                scenes = result.storyboard["scenes"]
                self.assertEqual(result.storyboard["schemaVersion"], "2.1")
                self.assertEqual(len(scenes), requested_count)
                self.assertEqual(
                    [scene["id"] for scene in scenes],
                    [f"scene_{index}" for index in range(1, requested_count + 1)],
                )
                self.assertEqual(
                    [scene["order"] for scene in scenes],
                    list(range(1, requested_count + 1)),
                )
                self.assertTrue(all(scene["visual"] for scene in scenes))
                self.assertTrue(all(scene["narrationSegments"] for scene in scenes))
                Storyboard.model_validate(result.storyboard)
                self.assertEqual(result.source, "rule_based")
                self.assertTrue(result.fallback_used)

    def test_dns_fallback_uses_explanation_entities_and_structure(self):
        result = create_storyboard(
            question="Explain DNS resolution in five scenes",
            explanation=EXPLANATION,
            requested_scene_count=5,
        )
        profile = result.storyboard["planningProfile"]
        elements = [
            element
            for scene in result.storyboard["scenes"]
            for element in scene["visual"]["elements"]
        ]
        labels = {element.get("label") for element in elements if element.get("label")}
        self.assertEqual(profile["subjectDomain"], "computing")
        self.assertIn("hierarchy", profile["knowledgeShapes"])
        self.assertTrue(any("recursive resolver" in label.lower() for label in labels))
        self.assertTrue(any("authoritative dns server" in label.lower() for label in labels))
        self.assertFalse(any(element.get("nodeKind") == "generic" for element in elements))

    def test_recursion_fallback_uses_stack_frames(self):
        result = create_storyboard(
            question="Explain recursion using factorial",
            explanation=RECURSION_EXPLANATION,
            requested_scene_count=5,
        )
        node_kinds = {
            element["nodeKind"]
            for scene in result.storyboard["scenes"]
            for element in scene["visual"]["elements"]
            if element["type"] == "node"
        }
        self.assertIn("stack_frame", node_kinds)
        self.assertTrue(
            all(
                scene["visual"]["diagramType"] == "stack"
                for scene in result.storyboard["scenes"]
            )
        )

    def test_legacy_player_fields_are_derived_from_lesson_v2(self):
        result = create_storyboard(
            question="Explain DNS resolution",
            explanation=EXPLANATION,
            requested_scene_count=4,
        )
        for scene in result.storyboard["scenes"]:
            node_ids = [
                element["id"]
                for element in scene["visual"]["elements"]
                if element["type"] == "node"
            ]
            self.assertEqual(scene["visualElements"], node_ids)
            self.assertTrue(scene["actions"])
            self.assertTrue(scene["subtitleLines"])

    def test_unknown_topic_uses_knowledge_shape_instead_of_topic_branch(self):
        result = create_storyboard(
            question="Explain a custom distributed widget protocol",
            explanation={**EXPLANATION, "title": "Custom Widget Protocol"},
            requested_scene_count=4,
        )
        profile = result.storyboard["planningProfile"]
        self.assertTrue(profile["knowledgeShapes"])
        self.assertNotEqual(profile["primaryArchetype"], "fallback")
        self.assertFalse(
            any(
                element.get("nodeKind") == "generic"
                for scene in result.storyboard["scenes"]
                for element in scene["visual"]["elements"]
                if element.get("type") == "node"
            )
        )

    def test_wrong_ai_scene_count_repairs_only_the_missing_scene(self):
        ai_storyboard = {"scenes": [make_valid_ai_scene(index) for index in range(1, 5)]}
        result = create_storyboard(
            question="Explain DNS resolution",
            explanation=EXPLANATION,
            requested_scene_count=5,
            ai_storyboard=ai_storyboard,
            ai_source="groq",
            ai_model_used="test-model",
        )

        self.assertEqual(result.source, "hybrid")
        self.assertTrue(result.fallback_used)
        self.assertEqual(len(result.storyboard["scenes"]), 5)
        self.assertEqual(result.repair_summary["preservedSceneIds"], [
            "scene_1", "scene_2", "scene_3", "scene_4"
        ])
        self.assertEqual(result.repair_summary["replacedSceneIds"], ["scene_5"])
        self.assertIn("Expected exactly 5 scenes, received 4.", result.issues)

    def test_valid_typed_ai_storyboard_is_retained(self):
        ai_storyboard = {"scenes": [make_valid_ai_scene(index) for index in range(1, 5)]}
        result = create_storyboard(
            question="Explain DNS resolution",
            explanation=EXPLANATION,
            requested_scene_count=4,
            ai_storyboard=ai_storyboard,
            ai_source="groq",
            ai_model_used="test-model",
        )

        self.assertEqual(result.source, "groq")
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.model_used, "test-model")
        self.assertEqual(len(result.storyboard["scenes"]), 4)
        self.assertEqual(result.issues, [])
        Storyboard.model_validate(result.storyboard)

    def test_undeclared_narration_target_replaces_only_invalid_scene(self):
        scenes = [make_valid_ai_scene(index) for index in range(1, 4)]
        scenes[1]["narrationSegments"][0]["targetElementIds"] = ["not_declared"]
        result = create_storyboard(
            question="Explain DNS resolution",
            explanation=EXPLANATION,
            requested_scene_count=3,
            ai_storyboard={"scenes": scenes},
            ai_source="gemini",
        )

        self.assertEqual(result.source, "hybrid")
        self.assertEqual(result.repair_summary["preservedSceneIds"], ["scene_1", "scene_3"])
        self.assertEqual(result.repair_summary["replacedSceneIds"], ["scene_2"])
        self.assertTrue(
            any("undeclared visual elements" in issue for issue in result.issues)
        )


class ApiContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["USE_AI"] = "false"
        from fastapi.testclient import TestClient
        from app.main import app

        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)

    def test_visual_api_returns_lesson_v2_and_exact_scene_metadata(self):
        response = self.client.post(
            "/api/explain",
            json={
                "question": "Explain DNS resolution",
                "mode": "visual",
                "requestedSceneCount": 4,
                "audienceLevel": "beginner",
                "explanationDepth": "standard",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["schemaVersion"], "1.1")
        self.assertEqual(payload["lessonSchemaVersion"], "2.1")
        self.assertEqual(payload["storyboard"]["schemaVersion"], "2.1")
        self.assertEqual(len(payload["storyboard"]["scenes"]), 4)
        self.assertTrue(payload["storyboardValidation"]["exactSceneCount"])
        self.assertTrue(payload["storyboardValidation"]["typedVisualSchemaValid"])
        self.assertTrue(payload["storyboardValidation"]["narrationTimelineValid"])
        self.assertEqual(payload["storyboardSource"], "rule_based")
        self.assertIn("planningProfile", payload["storyboard"])
        self.assertIn(payload["qualityReport"]["status"], {"pass", "warn"})
        self.assertEqual(payload["qualityReport"]["schemaVersion"], "1.1")
        self.assertEqual(payload["groundingReport"]["schemaVersion"], "1.0")
        self.assertIn(payload["groundingReport"]["status"], {"pass", "warn", "unavailable"})

    def test_api_detects_scene_count_from_question(self):
        response = self.client.post(
            "/api/explain",
            json={
                "question": "Explain DNS resolution in exactly 4 scenes",
                "mode": "visual",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["storyboardValidation"]["requestedSceneCount"], 4)
        self.assertEqual(len(payload["storyboard"]["scenes"]), 4)

    def test_api_rejects_blank_question(self):
        response = self.client.post(
            "/api/explain",
            json={"question": "   ", "mode": "text"},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
