from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from app.models import Storyboard
from app.storyboard_service import create_storyboard


def build_explanation(case: dict) -> dict:
    steps = case["steps"]
    summary = case["summary"]
    return {
        "title": case["title"],
        "quickMeaning": summary,
        "deepExplanation": summary,
        "stepByStep": steps,
        "realWorldExample": steps[-1],
        "analogy": "A structured analogy can be added when it improves understanding.",
        "technicalDetails": [],
        "commonConfusions": [],
        "interviewAngle": "Explain the core structure and one practical example.",
        "summary": summary,
        "takeaways": [summary],
    }


def run_benchmark(dataset_path: Path) -> dict:
    dataset = json.loads(dataset_path.read_text())
    results = []

    for case in dataset["cases"]:
        explanation = build_explanation(case)
        build_result = create_storyboard(
            question=case["question"],
            explanation=explanation,
            requested_scene_count=4,
        )
        storyboard = build_result.storyboard
        Storyboard.model_validate(storyboard)
        profile = storyboard["planningProfile"]
        quality = build_result.quality_report or {}
        result = {
            "id": case["id"],
            "question": case["question"],
            "expectedDomain": case["expectedDomain"],
            "actualDomain": profile["subjectDomain"],
            "domainMatch": profile["subjectDomain"] == case["expectedDomain"],
            "expectedArchetypes": case["expectedArchetypes"],
            "actualArchetype": profile["primaryArchetype"],
            "archetypeMatch": profile["primaryArchetype"] in case["expectedArchetypes"],
            "exactSceneCount": len(storyboard["scenes"]) == 4,
            "qualityStatus": quality.get("status"),
            "qualityScore": quality.get("overallScore", 0),
            "technicalRiskScore": quality.get("metrics", {}).get("technicalRiskScore", 100),
            "issueCodes": [issue.get("code") for issue in quality.get("issues", [])],
        }
        results.append(result)

    total = len(results)
    summary = {
        "schemaVersion": "1.0",
        "totalCases": total,
        "domainAccuracy": round(sum(item["domainMatch"] for item in results) / total, 3),
        "archetypeAccuracy": round(sum(item["archetypeMatch"] for item in results) / total, 3),
        "exactSceneCountRate": round(sum(item["exactSceneCount"] for item in results) / total, 3),
        "schemaPassRate": 1.0,
        "qualityPassOrWarnRate": round(
            sum(item["qualityStatus"] in {"pass", "warn"} for item in results) / total,
            3,
        ),
        "averageQualityScore": round(
            sum(item["qualityScore"] for item in results) / total,
            1,
        ),
        "failedCaseIds": [
            item["id"]
            for item in results
            if not item["exactSceneCount"] or item["qualityStatus"] == "fail"
        ],
        "domainMismatchIds": [item["id"] for item in results if not item["domainMatch"]],
        "archetypeMismatchIds": [
            item["id"] for item in results if not item["archetypeMatch"]
        ],
    }
    return {"summary": summary, "results": results}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ConceptCanvas 50-topic quality benchmark.")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=SERVER_ROOT / "benchmarks" / "quality_benchmark.json",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = run_benchmark(args.dataset)
    rendered = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    print(rendered)


if __name__ == "__main__":
    main()
