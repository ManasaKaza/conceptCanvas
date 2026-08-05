from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

from pydantic import ValidationError

from app.models import Storyboard


GENERIC_LABELS = {
    "concept",
    "idea",
    "main idea",
    "part",
    "step",
    "result",
    "key point",
    "important part",
    "input",
    "output",
    "summary",
    "takeaway",
}

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "being",
    "by", "for", "from", "has", "have", "how", "in", "into", "is", "it",
    "its", "of", "on", "or", "that", "the", "their", "then", "this", "through",
    "to", "was", "were", "when", "which", "while", "with", "you", "your",
}

COMMAND_OPENERS = (
    "show ",
    "display ",
    "highlight ",
    "connect ",
    "move ",
    "reveal ",
    "animate ",
    "draw ",
)

ABSOLUTE_PATTERNS = (
    (r"\balways\b", "absolute_always"),
    (r"\bnever\b", "absolute_never"),
    (r"\bguarantee(?:s|d)?\b", "unsupported_guarantee"),
    (r"\bcompletely eliminates?\b", "unsupported_elimination"),
    (r"\b100\s*%\b", "absolute_percentage"),
    (r"\bimpossible\b", "absolute_impossibility"),
)

NUMERIC_PERFORMANCE_PATTERN = re.compile(
    r"(?:\d+(?:\.\d+)?\s*%|\d+(?:\.\d+)?\s*(?:x|times)).{0,35}"
    r"\b(?:faster|slower|better|improvement|reduction|increase|decrease)\b",
    flags=re.IGNORECASE,
)

DIRECTION_PATTERN = re.compile(
    r"(?P<subject>[A-Za-z0-9][A-Za-z0-9 _\-/]{1,60}?)\s+"
    r"(?P<verb>increases|raises|improves|grows|decreases|lowers|reduces|shrinks)\s+"
    r"(?P<object>[A-Za-z0-9][A-Za-z0-9 _\-/]{1,80}?)(?:[.;]|$)",
    flags=re.IGNORECASE,
)

POSITIVE_DIRECTION = {"increases", "raises", "improves", "grows"}
NEGATIVE_DIRECTION = {"decreases", "lowers", "reduces", "shrinks"}


def _issue(
    code: str,
    severity: str,
    scope: str,
    message: str,
    *,
    scene_id: str | None = None,
    segment_id: str | None = None,
    evidence: str | None = None,
) -> dict:
    payload = {
        "code": code,
        "severity": severity,
        "scope": scope,
        "message": message,
    }
    if scene_id:
        payload["sceneId"] = scene_id
    if segment_id:
        payload["segmentId"] = segment_id
    if evidence:
        payload["evidence"] = evidence[:240]
    return payload


def _token_list(text: object) -> list[str]:
    if not isinstance(text, str):
        return []
    return [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2 and token not in STOP_WORDS
    ]


def _tokens(text: object) -> set[str]:
    return set(_token_list(text))


def _normalized_text(text: object) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _claim_texts(explanation: dict) -> list[str]:
    values: list[str] = []
    for key in (
        "quickMeaning",
        "deepExplanation",
        "realWorldExample",
        "analogy",
        "interviewAngle",
        "summary",
    ):
        value = explanation.get(key)
        if isinstance(value, str) and value.strip():
            values.append(value.strip())

    for key in ("stepByStep", "technicalDetails", "commonConfusions", "takeaways"):
        value = explanation.get(key)
        if isinstance(value, list):
            values.extend(
                item.strip()
                for item in value
                if isinstance(item, str) and item.strip()
            )
    return values


def _visual_lookup(scene: dict) -> dict[str, str]:
    lookup: dict[str, str] = {}
    visual = scene.get("visual") if isinstance(scene, dict) else None
    elements = visual.get("elements", []) if isinstance(visual, dict) else []
    for element in elements:
        if not isinstance(element, dict) or not isinstance(element.get("id"), str):
            continue
        label_parts = [element.get("label")]
        if element.get("type") == "edge":
            label_parts.extend([element.get("relation"), element.get("fromId"), element.get("toId")])
        lookup[element["id"]] = " ".join(
            part for part in label_parts if isinstance(part, str) and part.strip()
        )
    return lookup


def _deduplicate_issues(issues: Iterable[dict]) -> list[dict]:
    unique: list[dict] = []
    seen: set[tuple] = set()
    for issue in issues:
        key = (
            issue.get("code"),
            issue.get("scope"),
            issue.get("sceneId"),
            issue.get("segmentId"),
            issue.get("evidence"),
        )
        if key not in seen:
            unique.append(issue)
            seen.add(key)
    return unique


def evaluate_claim_risks(explanation: dict, question: str = "") -> list[dict]:
    issues: list[dict] = []
    claims = _claim_texts(explanation)
    question_normalized = _normalized_text(question)

    for claim in claims:
        lowered = claim.lower()
        for pattern, code in ABSOLUTE_PATTERNS:
            if re.search(pattern, lowered, flags=re.IGNORECASE):
                issues.append(
                    _issue(
                        code,
                        "warning",
                        "explanation",
                        "This claim uses absolute wording and should be verified or qualified.",
                        evidence=claim,
                    )
                )
        if NUMERIC_PERFORMANCE_PATTERN.search(claim) and _normalized_text(claim) not in question_normalized:
            issues.append(
                _issue(
                    "unverified_performance_number",
                    "warning",
                    "explanation",
                    "A performance number appears without an attached source or benchmark context.",
                    evidence=claim,
                )
            )

    directions: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for claim in claims:
        for match in DIRECTION_PATTERN.finditer(claim):
            subject = " ".join(_token_list(match.group("subject"))[-5:])
            obj = " ".join(_token_list(match.group("object"))[:8])
            verb = match.group("verb").lower()
            if not subject or not obj:
                continue
            polarity = "positive" if verb in POSITIVE_DIRECTION else "negative"
            directions.setdefault((subject, obj), []).append((polarity, claim))

    for (subject, obj), entries in directions.items():
        polarities = {polarity for polarity, _ in entries}
        if polarities == {"positive", "negative"}:
            evidence = " | ".join(entry[1] for entry in entries[:2])
            issues.append(
                _issue(
                    "possible_direction_contradiction",
                    "warning",
                    "explanation",
                    f"Claims about how {subject} affects {obj} point in opposite directions.",
                    evidence=evidence,
                )
            )

    return _deduplicate_issues(issues)


def evaluate_lesson_quality(
    *,
    question: str,
    explanation: dict,
    storyboard: dict | None,
    requested_scene_count: int,
    repair_summary: dict | None = None,
    grounding_report: dict | None = None,
) -> dict:
    issues: list[dict] = []
    structure_score = 100
    visual_specificity_score = 100
    narration_alignment_score = 100

    scenes = storyboard.get("scenes", []) if isinstance(storyboard, dict) else []
    if len(scenes) != requested_scene_count:
        issues.append(
            _issue(
                "scene_count_mismatch",
                "error",
                "lesson",
                f"Expected {requested_scene_count} scenes but received {len(scenes)}.",
            )
        )
        structure_score -= 35

    if storyboard:
        try:
            Storyboard.model_validate(storyboard)
        except ValidationError as error:
            structure_score -= 45
            for item in error.errors(include_url=False)[:8]:
                issues.append(
                    _issue(
                        "lesson_schema_invalid",
                        "error",
                        "lesson",
                        "LessonV2 schema validation failed.",
                        evidence=item.get("msg"),
                    )
                )
    else:
        structure_score = 0
        issues.append(
            _issue(
                "storyboard_missing",
                "error",
                "lesson",
                "The lesson did not contain a storyboard.",
            )
        )

    title_counts = Counter(
        _normalized_text(scene.get("title"))
        for scene in scenes
        if isinstance(scene, dict) and _normalized_text(scene.get("title"))
    )
    for title, count in title_counts.items():
        if count > 1:
            issues.append(
                _issue(
                    "duplicate_scene_title",
                    "warning",
                    "lesson",
                    "Multiple scenes use the same title, which weakens lesson progression.",
                    evidence=title,
                )
            )
            structure_score -= min(15, 5 * (count - 1))

    narration_counts = Counter(
        _normalized_text(scene.get("narration"))
        for scene in scenes
        if isinstance(scene, dict) and _normalized_text(scene.get("narration"))
    )
    for narration, count in narration_counts.items():
        if count > 1:
            issues.append(
                _issue(
                    "duplicate_scene_narration",
                    "warning",
                    "lesson",
                    "Multiple scenes repeat the same narration instead of advancing the explanation.",
                    evidence=narration,
                )
            )
            structure_score -= min(20, 7 * (count - 1))

    total_nodes = 0
    generic_nodes = 0
    total_segments = 0
    aligned_segments = 0
    command_segments = 0

    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        scene_id = scene.get("id") if isinstance(scene.get("id"), str) else None
        visual = scene.get("visual") if isinstance(scene.get("visual"), dict) else {}
        elements = visual.get("elements", []) if isinstance(visual, dict) else []
        nodes = [element for element in elements if isinstance(element, dict) and element.get("type") == "node"]
        total_nodes += len(nodes)
        generic_nodes += sum(
            _normalized_text(node.get("label")) in GENERIC_LABELS
            or node.get("nodeKind") == "generic"
            for node in nodes
        )

        if visual.get("diagramType") == "fallback":
            visual_specificity_score -= 20
            issues.append(
                _issue(
                    "fallback_visual_used",
                    "warning",
                    "scene",
                    "This scene uses the simplified visual fallback.",
                    scene_id=scene_id,
                )
            )

        lookup = _visual_lookup(scene)
        segments = scene.get("narrationSegments", [])
        if not isinstance(segments, list):
            continue

        for segment in segments:
            if not isinstance(segment, dict):
                continue
            total_segments += 1
            segment_id = segment.get("id") if isinstance(segment.get("id"), str) else None
            spoken_text = segment.get("spokenText", "")
            subtitle_text = segment.get("subtitleText", "")
            combined_text = f"{spoken_text} {subtitle_text}"
            targets = segment.get("targetElementIds", [])
            target_text = " ".join(
                lookup.get(target_id, "")
                for target_id in targets
                if isinstance(target_id, str)
            )
            narration_tokens = _tokens(spoken_text)
            target_tokens = _tokens(target_text)

            if target_tokens and narration_tokens.intersection(target_tokens):
                aligned_segments += 1
            else:
                issues.append(
                    _issue(
                        "narration_visual_mismatch",
                        "warning",
                        "segment",
                        "The narration does not clearly name or describe its highlighted visual targets.",
                        scene_id=scene_id,
                        segment_id=segment_id,
                        evidence=combined_text,
                    )
                )

            if isinstance(spoken_text, str) and spoken_text.strip().lower().startswith(COMMAND_OPENERS):
                command_segments += 1
                issues.append(
                    _issue(
                        "command_like_narration",
                        "warning",
                        "segment",
                        "Narration sounds like an animation command instead of a teaching explanation.",
                        scene_id=scene_id,
                        segment_id=segment_id,
                        evidence=spoken_text,
                    )
                )

    if total_nodes == 0:
        visual_specificity_score = 0
    elif generic_nodes:
        generic_ratio = generic_nodes / total_nodes
        visual_specificity_score -= round(generic_ratio * 70)
        issues.append(
            _issue(
                "generic_visual_nodes",
                "warning",
                "lesson",
                "Some visual nodes use generic labels instead of concept-specific entities.",
                evidence=f"{generic_nodes} of {total_nodes} nodes",
            )
        )

    if total_segments:
        mismatch_ratio = 1 - (aligned_segments / total_segments)
        narration_alignment_score -= round(mismatch_ratio * 70)
        narration_alignment_score -= min(25, command_segments * 8)
    else:
        narration_alignment_score = 0

    claim_issues = evaluate_claim_risks(explanation, question)
    issues.extend(claim_issues)

    grounding_coverage_score = None
    grounding_risk = 0
    if isinstance(grounding_report, dict):
        grounding_metrics = grounding_report.get("metrics", {})
        grounding_coverage_score = grounding_metrics.get("coverageScore")
        contradicted_claims = int(grounding_metrics.get("contradictedClaims", 0) or 0)
        unverified_claims = int(grounding_metrics.get("unverifiedClaims", 0) or 0)
        verifiable_claims = int(grounding_metrics.get("verifiableClaims", 0) or 0)
        grounding_mode = grounding_report.get("mode", "preferred")
        grounding_status = grounding_report.get("status")

        for claim in grounding_report.get("claims", []):
            if claim.get("status") != "contradicted":
                continue
            issues.append(
                _issue(
                    "source_contradicted_claim",
                    "error",
                    "explanation",
                    "A factual claim conflicts with evidence from the grounding provider.",
                    evidence=claim.get("text"),
                )
            )

        if grounding_status == "unavailable":
            issues.append(
                _issue(
                    "grounding_provider_unavailable",
                    "error" if grounding_mode == "required" else "warning",
                    "lesson",
                    "Source grounding was requested, but no trusted evidence provider was available.",
                )
            )
        elif unverified_claims:
            severity = "error" if grounding_mode == "required" and (grounding_coverage_score or 0) < 80 else "warning"
            issues.append(
                _issue(
                    "unverified_grounded_claims",
                    severity,
                    "explanation",
                    f"{unverified_claims} factual claim(s) remain unverified by the configured sources.",
                    evidence=f"coverage={grounding_coverage_score or 0}%",
                )
            )

        unverified_ratio = unverified_claims / max(1, verifiable_claims)
        grounding_risk = min(80, (contradicted_claims * 35) + round(unverified_ratio * 30))

    technical_risk_score = min(100, (len(claim_issues) * 18) + grounding_risk)

    structure_score = max(0, min(100, structure_score))
    visual_specificity_score = max(0, min(100, visual_specificity_score))
    narration_alignment_score = max(0, min(100, narration_alignment_score))
    overall_score = round(
        (
            structure_score
            + visual_specificity_score
            + narration_alignment_score
            + (100 - technical_risk_score)
        )
        / 4
    )

    issues = _deduplicate_issues(issues)
    has_errors = any(issue["severity"] == "error" for issue in issues)
    has_warnings = any(issue["severity"] == "warning" for issue in issues)
    if has_errors or overall_score < 60:
        status = "fail"
    elif has_warnings or overall_score < 88:
        status = "warn"
    else:
        status = "pass"

    return {
        "schemaVersion": "1.1",
        "status": status,
        "overallScore": overall_score,
        "metrics": {
            "structureScore": structure_score,
            "visualSpecificityScore": visual_specificity_score,
            "narrationAlignmentScore": narration_alignment_score,
            "technicalRiskScore": technical_risk_score,
            "groundingCoverageScore": grounding_coverage_score,
        },
        "repair": repair_summary or {
            "attempted": False,
            "strategy": "none",
            "modelRepairAttempted": False,
            "modelRepairSucceeded": False,
            "repairedSceneIds": [],
            "replacedSceneIds": [],
            "preservedSceneIds": [],
            "notes": [],
        },
        "issues": issues,
    }


NON_STORYBOARD_BLOCKING_CODES = {
    "source_contradicted_claim",
    "unverified_grounded_claims",
    "grounding_provider_unavailable",
}


def blocking_quality_issues(report: dict) -> list[dict]:
    """Return only errors that can be fixed by rebuilding the storyboard.

    Grounding and factual errors remain release-blocking in the quality report,
    but they must not cause a valid visual plan to be replaced.
    """
    return [
        issue
        for issue in report.get("issues", [])
        if issue.get("severity") == "error"
        and issue.get("code") not in NON_STORYBOARD_BLOCKING_CODES
    ]
