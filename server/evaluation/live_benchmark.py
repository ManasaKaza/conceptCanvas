from __future__ import annotations

from statistics import mean


def evaluate_live_response(case: dict, payload: dict, elapsed_ms: int) -> dict:
    storyboard = payload.get("storyboard") or {}
    scenes = storyboard.get("scenes") or []
    validation = payload.get("storyboardValidation") or {}
    quality = payload.get("qualityReport") or {}
    grounding = payload.get("groundingReport") or {}
    expected_scene_count = case.get("sceneCount", 4)

    schema_valid = (
        payload.get("topicType") == "concept_explanation"
        and payload.get("lessonSchemaVersion") == "2.1"
        and storyboard.get("schemaVersion") == "2.1"
    )
    exact_scene_count = len(scenes) == expected_scene_count and validation.get("exactSceneCount") is True
    citation_integrity = all(
        source_id in {source.get("sourceId") for source in grounding.get("sources", [])}
        for claim in grounding.get("claims", [])
        for source_id in claim.get("sourceIds", [])
    )

    return {
        "id": case.get("id"),
        "question": case.get("question"),
        "elapsedMs": elapsed_ms,
        "schemaValid": schema_valid,
        "exactSceneCount": exact_scene_count,
        "storyboardSource": payload.get("storyboardSource"),
        "fallbackUsed": bool(validation.get("fallbackUsed")),
        "qualityStatus": quality.get("status"),
        "qualityScore": quality.get("overallScore"),
        "technicalRiskScore": quality.get("metrics", {}).get("technicalRiskScore"),
        "groundingStatus": grounding.get("status"),
        "groundingCoverage": grounding.get("metrics", {}).get("coverageScore"),
        "supportedClaims": grounding.get("metrics", {}).get("supportedClaims", 0),
        "contradictedClaims": grounding.get("metrics", {}).get("contradictedClaims", 0),
        "citationIntegrity": citation_integrity,
        "issueCodes": [issue.get("code") for issue in quality.get("issues", [])],
        "reviewRequired": (
            quality.get("status") != "pass"
            or grounding.get("status") in {"fail", "unavailable"}
            or not citation_integrity
        ),
    }


def summarize_live_results(results: list[dict]) -> dict:
    total = len(results)
    if total == 0:
        return {
            "schemaVersion": "1.0",
            "totalCases": 0,
            "schemaPassRate": 0,
            "exactSceneCountRate": 0,
            "fallbackRate": 0,
            "citationIntegrityRate": 0,
            "averageLatencyMs": 0,
            "averageGroundingCoverage": 0,
            "reviewRequiredIds": [],
        }

    coverage_values = [
        result["groundingCoverage"]
        for result in results
        if isinstance(result.get("groundingCoverage"), (int, float))
    ]
    return {
        "schemaVersion": "1.0",
        "totalCases": total,
        "schemaPassRate": round(sum(result["schemaValid"] for result in results) / total, 3),
        "exactSceneCountRate": round(sum(result["exactSceneCount"] for result in results) / total, 3),
        "fallbackRate": round(sum(result["fallbackUsed"] for result in results) / total, 3),
        "citationIntegrityRate": round(sum(result["citationIntegrity"] for result in results) / total, 3),
        "averageLatencyMs": round(mean(result["elapsedMs"] for result in results)),
        "averageGroundingCoverage": round(mean(coverage_values), 1) if coverage_values else 0,
        "qualityPassRate": round(sum(result["qualityStatus"] == "pass" for result in results) / total, 3),
        "groundingPassRate": round(sum(result["groundingStatus"] == "pass" for result in results) / total, 3),
        "contradictedClaimCaseIds": [
            result["id"] for result in results if result.get("contradictedClaims", 0) > 0
        ],
        "reviewRequiredIds": [result["id"] for result in results if result["reviewRequired"]],
    }
