import unittest

from evaluation.live_benchmark import evaluate_live_response, summarize_live_results


class LiveBenchmarkTests(unittest.TestCase):
    def test_live_response_records_grounding_and_citation_integrity(self):
        payload = {
            "topicType": "concept_explanation",
            "lessonSchemaVersion": "2.1",
            "storyboard": {"schemaVersion": "2.1", "scenes": [{}, {}, {}, {}]},
            "storyboardSource": "groq",
            "storyboardValidation": {"exactSceneCount": True, "fallbackUsed": False},
            "qualityReport": {
                "status": "pass",
                "overallScore": 92,
                "metrics": {"technicalRiskScore": 4},
                "issues": [],
            },
            "groundingReport": {
                "status": "pass",
                "metrics": {
                    "coverageScore": 100,
                    "supportedClaims": 2,
                    "contradictedClaims": 0,
                },
                "sources": [{"sourceId": "source_one"}],
                "claims": [{"sourceIds": ["source_one"]}],
            },
        }
        result = evaluate_live_response(
            {"id": "case_1", "question": "Explain DNS", "sceneCount": 4},
            payload,
            1250,
        )
        self.assertTrue(result["schemaValid"])
        self.assertTrue(result["exactSceneCount"])
        self.assertTrue(result["citationIntegrity"])
        self.assertFalse(result["reviewRequired"])

    def test_summary_surfaces_cases_requiring_review(self):
        summary = summarize_live_results([
            {
                "id": "good",
                "schemaValid": True,
                "exactSceneCount": True,
                "fallbackUsed": False,
                "citationIntegrity": True,
                "elapsedMs": 1000,
                "groundingCoverage": 90,
                "qualityStatus": "pass",
                "groundingStatus": "pass",
                "contradictedClaims": 0,
                "reviewRequired": False,
            },
            {
                "id": "review",
                "schemaValid": True,
                "exactSceneCount": True,
                "fallbackUsed": True,
                "citationIntegrity": False,
                "elapsedMs": 2000,
                "groundingCoverage": 20,
                "qualityStatus": "warn",
                "groundingStatus": "warn",
                "contradictedClaims": 0,
                "reviewRequired": True,
            },
        ])
        self.assertEqual(summary["totalCases"], 2)
        self.assertEqual(summary["fallbackRate"], 0.5)
        self.assertEqual(summary["reviewRequiredIds"], ["review"])


if __name__ == "__main__":
    unittest.main()
