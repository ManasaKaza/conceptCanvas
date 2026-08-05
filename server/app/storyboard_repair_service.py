from __future__ import annotations

import json


def build_storyboard_repair_prompt(
    *,
    question: str,
    explanation: dict,
    requested_scene_count: int,
    audience_level: str,
    candidate_storyboard: dict,
    issues: list[str],
) -> str:
    issue_text = "\n".join(f"- {issue}" for issue in issues[:20])
    candidate_json = json.dumps(candidate_storyboard, ensure_ascii=False, indent=2)[:18000]
    explanation_json = json.dumps(
        {
            "title": explanation.get("title"),
            "quickMeaning": explanation.get("quickMeaning"),
            "stepByStep": explanation.get("stepByStep"),
            "technicalDetails": explanation.get("technicalDetails"),
            "summary": explanation.get("summary"),
        },
        ensure_ascii=False,
        indent=2,
    )

    return f"""
You are repairing a ConceptCanvas LessonV2 storyboard.

Question: {question}
Audience: {audience_level}
Required scene count: exactly {requested_scene_count}

Explanation context:
{explanation_json}

Validation failures:
{issue_text}

Candidate storyboard:
{candidate_json}

Return ONLY a complete repaired JSON object with one top-level `scenes` array.
Preserve any scene that is already valid and educational. Change only fields or scenes
needed to fix the listed failures. The final response must:
- contain exactly {requested_scene_count} scenes;
- use canonical scene_1 through scene_{requested_scene_count} IDs;
- use the LessonV2 typed visual schemaVersion 2.0;
- use at least two concept-specific nodes in every scene;
- keep every edge and narration target reference valid;
- use canonical segment_1, segment_2 ordering inside each scene;
- make narration explain the highlighted visual instead of giving UI commands;
- avoid unsupported facts, invented values, decorative generic labels, and fallback diagrams.
Do not include markdown or commentary outside JSON.
"""
