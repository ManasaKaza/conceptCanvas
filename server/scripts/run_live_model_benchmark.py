from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from evaluation.live_benchmark import evaluate_live_response, summarize_live_results


def run_live_benchmark(
    *,
    base_url: str,
    dataset_path: Path,
    output_path: Path | None,
    case_limit: int | None,
    grounding_mode: str,
) -> dict:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    cases = dataset.get("cases", [])
    if case_limit:
        cases = cases[:case_limit]

    results = []
    with httpx.Client(base_url=base_url.rstrip("/"), timeout=90.0) as client:
        for case in cases:
            scene_count = int(case.get("sceneCount", 4))
            started = time.perf_counter()
            response = client.post(
                "/api/explain",
                json={
                    "question": case["question"],
                    "mode": "visual",
                    "audienceLevel": case.get("audienceLevel", "beginner"),
                    "explanationDepth": case.get("explanationDepth", "standard"),
                    "requestedSceneCount": scene_count,
                    "groundingMode": grounding_mode,
                },
            )
            elapsed_ms = round((time.perf_counter() - started) * 1000)
            response.raise_for_status()
            normalized_case = {**case, "sceneCount": scene_count}
            results.append(evaluate_live_response(normalized_case, response.json(), elapsed_ms))

    report = {
        "summary": summarize_live_results(results),
        "results": results,
    }
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 50-topic benchmark against a live ConceptCanvas API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--dataset",
        type=Path,
        default=SERVER_ROOT / "benchmarks" / "quality_benchmark.json",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--grounding-mode", choices=("off", "preferred", "required"), default="preferred")
    args = parser.parse_args()

    report = run_live_benchmark(
        base_url=args.base_url,
        dataset_path=args.dataset,
        output_path=args.output,
        case_limit=args.limit,
        grounding_mode=args.grounding_mode,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
