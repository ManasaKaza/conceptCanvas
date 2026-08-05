import os
import unittest
from pathlib import Path
from unittest.mock import patch

from app.grounding_provider import CatalogGroundingProvider, EvidenceCandidate, HttpGroundingProvider
from app.grounding_service import attach_grounding_to_storyboard, extract_claims, ground_explanation
from app.quality_evaluator import evaluate_lesson_quality
from app.storyboard_service import create_storyboard


DNS_EXPLANATION = {
    "title": "DNS Resolution",
    "quickMeaning": "DNS uses a distributed hierarchy of name servers to resolve a domain name into an address.",
    "deepExplanation": "A resolver may use cached information before it queries name servers.",
    "stepByStep": ["The resolver queries a name server for the requested domain."],
    "realWorldExample": "A browser resolves example.com before connecting.",
    "analogy": "It is like looking up a number in a directory.",
    "technicalDetails": ["Resolvers can cache DNS answers."],
    "commonConfusions": [],
    "interviewAngle": "Explain the hierarchy and resolver role.",
    "summary": "DNS resolution uses resolvers and hierarchical name servers.",
    "takeaways": ["Caching can avoid some repeated queries."],
}


def make_ai_scene(index: int) -> dict:
    left = f"client_{index}"
    right = f"server_{index}"
    edge = f"request_{index}"
    return {
        "id": f"scene_{index}",
        "title": f"Request stage {index}",
        "narration": "The client and server exchange one visible request in this stage.",
        "visual": {
            "schemaVersion": "2.0",
            "diagramType": "sequence",
            "orientation": "left_to_right",
            "elements": [
                {"type": "node", "id": left, "label": "Client", "nodeKind": "client"},
                {"type": "node", "id": right, "label": "Server", "nodeKind": "server"},
                {"type": "edge", "id": edge, "fromId": left, "toId": right, "relation": "request"},
            ],
        },
        "narrationSegments": [{
            "id": "segment_1",
            "order": 1,
            "spokenText": "The client sends a request to the server during this stage.",
            "subtitleText": "Client sends request",
            "targetElementIds": [left, edge, right],
            "action": "trace",
            "estimatedDurationMs": 3000,
        }],
    }


class ContradictingProvider:
    name = "test_contradiction"

    def find_evidence(self, *, claim, question, max_results=3):
        return [
            EvidenceCandidate(
                source_id="source_test_authority",
                title="Authoritative Test Source",
                publisher="Test Standards Body",
                url="https://example.org/authority",
                authority="official",
                stance="contradicts",
                excerpt="The tested claim is explicitly false under the stated conditions.",
                confidence=0.94,
                locator="Section 1",
            )
        ]


class BatchOnlyProvider:
    name = "test_batch"

    def __init__(self):
        self.batch_calls = 0

    def find_evidence_batch(self, *, claims, question, max_results=3):
        self.batch_calls += 1
        return {
            claim["claimId"]: [
                EvidenceCandidate(
                    source_id="source_test_batch",
                    title="Batch Verification Source",
                    publisher="Test Standards Body",
                    url="https://example.org/batch-source",
                    authority="official",
                    stance="supports",
                    excerpt=f"Evidence supporting: {claim['text']}",
                    confidence=0.91,
                    locator="Batch section",
                )
            ]
            for claim in claims
        }

    def find_evidence(self, *, claim, question, max_results=3):
        raise AssertionError("Per-claim retrieval should not run when batch results are complete")


class GroundingExtractionTests(unittest.TestCase):
    def test_claims_keep_section_and_list_item_location(self):
        claims = extract_claims(DNS_EXPLANATION)
        self.assertEqual(claims[0].claim_id, "claim_1")
        step_claim = next(claim for claim in claims if claim.section == "stepByStep")
        self.assertEqual(step_claim.item_index, 0)
        self.assertTrue(step_claim.text.startswith("The resolver"))


class GroundingProviderTests(unittest.TestCase):
    def test_catalog_produces_claim_level_sources_and_evidence(self):
        catalog = Path(__file__).parents[1] / "grounding" / "source_catalog.json"
        report = ground_explanation(
            question="Explain DNS resolution",
            explanation=DNS_EXPLANATION,
            mode="preferred",
            provider=CatalogGroundingProvider(catalog),
        )
        self.assertEqual(report["provider"], "catalog")
        self.assertGreater(report["metrics"]["supportedClaims"], 0)
        self.assertGreater(len(report["sources"]), 0)
        supported = next(claim for claim in report["claims"] if claim["status"] == "supported")
        self.assertTrue(supported["sourceIds"])
        self.assertTrue(supported["evidenceIds"])

    def test_batch_provider_is_called_once_for_all_verifiable_claims(self):
        provider = BatchOnlyProvider()
        report = ground_explanation(
            question="Explain DNS resolution",
            explanation=DNS_EXPLANATION,
            mode="preferred",
            provider=provider,
        )
        self.assertEqual(provider.batch_calls, 1)
        self.assertEqual(
            report["metrics"]["supportedClaims"],
            report["metrics"]["verifiableClaims"],
        )
        self.assertFalse(any("provider failed" in item.lower() for item in report["warnings"]))

    def test_contradictory_evidence_fails_grounding(self):
        explanation = {
            **DNS_EXPLANATION,
            "quickMeaning": "The tested claim is true under every condition.",
        }
        report = ground_explanation(
            question="Verify the tested claim",
            explanation=explanation,
            mode="required",
            provider=ContradictingProvider(),
        )
        self.assertEqual(report["status"], "fail")
        self.assertGreater(report["metrics"]["contradictedClaims"], 0)
        self.assertTrue(any(claim["status"] == "contradicted" for claim in report["claims"]))


    def test_grounding_is_attached_to_visual_narration_segments(self):
        catalog = Path(__file__).parents[1] / "grounding" / "source_catalog.json"
        report = ground_explanation(
            question="Explain DNS resolution",
            explanation=DNS_EXPLANATION,
            mode="preferred",
            provider=CatalogGroundingProvider(catalog),
        )
        storyboard = create_storyboard(
            question="Explain DNS resolution",
            explanation=DNS_EXPLANATION,
            requested_scene_count=3,
        ).storyboard
        grounded = attach_grounding_to_storyboard(storyboard, report)
        segments = [
            segment
            for scene in grounded["scenes"]
            for segment in scene["narrationSegments"]
        ]
        self.assertTrue(any(segment.get("claimIds") for segment in segments))
        self.assertTrue(any(segment.get("sourceIds") for segment in segments))


    def test_http_provider_rejects_non_https_remote_endpoint(self):
        with self.assertRaises(ValueError):
            HttpGroundingProvider("http://localhost.evil.example/verify")
        HttpGroundingProvider("http://127.0.0.1:9000/verify")

    def test_required_mode_reports_unavailable_provider(self):
        with patch.dict(os.environ, {"GROUNDING_PROVIDER": "disabled"}, clear=False):
            report = ground_explanation(
                question="Explain an unknown topic",
                explanation=DNS_EXPLANATION,
                mode="required",
            )
        self.assertEqual(report["status"], "unavailable")
        self.assertEqual(report["metrics"]["coverageScore"], 0)


class GroundingQualityGateTests(unittest.TestCase):
    def test_required_unverified_grounding_fails_visual_quality_gate(self):
        grounding_report = {
            "schemaVersion": "1.0",
            "mode": "required",
            "status": "fail",
            "provider": "test",
            "metrics": {
                "totalClaims": 2,
                "verifiableClaims": 2,
                "supportedClaims": 0,
                "contradictedClaims": 0,
                "unverifiedClaims": 2,
                "notApplicableClaims": 0,
                "coverageScore": 0,
            },
            "claims": [],
            "sources": [],
            "evidence": [],
            "warnings": ["Required grounding coverage was not met."],
        }
        result = create_storyboard(
            question="Explain DNS resolution",
            explanation=DNS_EXPLANATION,
            requested_scene_count=3,
            grounding_report=grounding_report,
        )
        self.assertEqual(result.quality_report["status"], "fail")
        self.assertEqual(result.quality_report["metrics"]["groundingCoverageScore"], 0)
        codes = {issue["code"] for issue in result.quality_report["issues"]}
        self.assertIn("unverified_grounded_claims", codes)


    def test_grounding_failure_does_not_replace_valid_ai_visuals(self):
        grounding_report = {
            "schemaVersion": "1.0",
            "mode": "required",
            "status": "fail",
            "provider": "test",
            "metrics": {
                "totalClaims": 1,
                "verifiableClaims": 1,
                "supportedClaims": 0,
                "contradictedClaims": 0,
                "unverifiedClaims": 1,
                "notApplicableClaims": 0,
                "coverageScore": 0,
            },
            "claims": [],
            "sources": [],
            "evidence": [],
            "warnings": ["Required grounding coverage was not met."],
        }
        result = create_storyboard(
            question="Explain client server communication",
            explanation=DNS_EXPLANATION,
            requested_scene_count=3,
            ai_storyboard={"scenes": [make_ai_scene(1), make_ai_scene(2), make_ai_scene(3)]},
            ai_source="groq",
            grounding_report=grounding_report,
        )
        self.assertEqual(result.source, "groq")
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.quality_report["status"], "fail")

    def test_contradicted_claim_adds_blocking_quality_error(self):
        report = ground_explanation(
            question="Verify the tested claim",
            explanation={**DNS_EXPLANATION, "quickMeaning": "The tested claim is true."},
            mode="required",
            provider=ContradictingProvider(),
        )
        storyboard = create_storyboard(
            question="Explain DNS resolution",
            explanation=DNS_EXPLANATION,
            requested_scene_count=3,
        ).storyboard
        quality = evaluate_lesson_quality(
            question="Verify the tested claim",
            explanation=DNS_EXPLANATION,
            storyboard=storyboard,
            requested_scene_count=3,
            grounding_report=report,
        )
        self.assertEqual(quality["status"], "fail")
        self.assertIn(
            "source_contradicted_claim",
            {issue["code"] for issue in quality["issues"]},
        )


class GroundingApiTests(unittest.TestCase):
    def test_api_keeps_claim_sources_on_visual_narration_segments(self):
        os.environ["USE_AI"] = "false"
        os.environ["GROUNDING_PROVIDER"] = "catalog"
        from fastapi.testclient import TestClient
        from app.main import app

        with patch("app.main.get_fake_explanation", return_value=DNS_EXPLANATION):
            with TestClient(app) as client:
                response = client.post(
                    "/api/explain",
                    json={
                        "question": "Explain DNS resolution",
                        "mode": "visual",
                        "requestedSceneCount": 3,
                        "groundingMode": "preferred",
                    },
                )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreater(payload["groundingReport"]["metrics"]["supportedClaims"], 0)
        segments = [
            segment
            for scene in payload["storyboard"]["scenes"]
            for segment in scene["narrationSegments"]
        ]
        self.assertTrue(any(segment.get("sourceIds") for segment in segments))


if __name__ == "__main__":
    unittest.main()
