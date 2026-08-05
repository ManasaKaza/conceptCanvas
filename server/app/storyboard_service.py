from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable, Literal

from pydantic import ValidationError

from app.models import Storyboard
from app.quality_evaluator import blocking_quality_issues, evaluate_lesson_quality
from app.visual_plan_service import (
    build_fallback_visual_plan,
    create_scene_payload_from_typed_plan,
    validate_typed_scene,
)
from app.visual_strategy_service import plan_lesson


GENERIC_VISUAL_TERMS = {
    "concept",
    "idea",
    "main idea",
    "part",
    "step",
    "result",
    "important part",
    "focus area",
    "core idea",
    "learning goal",
    "main concept",
    "summary",
    "final takeaway",
    "supporting part",
    "related detail",
    "key point",
}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "they", "their", "them",
    "you", "your", "we", "our", "can", "could", "should", "would", "will",
    "when", "while", "how", "why", "what", "which", "who", "into", "through",
    "first", "then", "next", "finally", "start", "understand", "learn",
    "concept", "idea", "basic", "main", "part", "parts", "step",
}


@dataclass
class StoryboardBuildResult:
    storyboard: dict
    source: Literal["gemini", "groq", "hybrid", "rule_based"]
    model_used: str | None = None
    fallback_used: bool = False
    issues: list[str] = field(default_factory=list)
    quality_report: dict | None = None
    repair_summary: dict = field(default_factory=dict)


StoryboardRepairCallback = Callable[[dict, list[str]], dict | None]


def ensure_string(value, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def ensure_string_list(value, fallback: list[str], max_items: int = 6) -> list[str]:
    if not isinstance(value, list):
        return fallback

    cleaned_items = [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]
    return cleaned_items[:max_items] or fallback


def strip_generated_numbering(value: str) -> str:
    cleaned = re.sub(
        r"^(?:scene|step)\s*\d+\s*[:.\-–—]?\s*",
        "",
        value.strip(),
        flags=re.IGNORECASE,
    )
    return cleaned or value.strip()


def sentence_to_title(text: str, fallback: str) -> str:
    cleaned = strip_generated_numbering(ensure_string(text, fallback))
    cleaned = cleaned.split(".", 1)[0].strip()
    words = cleaned.split()
    if len(words) > 9:
        cleaned = " ".join(words[:9])
    return cleaned[:72].rstrip(" ,;:-") or fallback


def extract_meaningful_words(text: str, max_words: int = 6) -> list[str]:
    if not isinstance(text, str):
        return []

    words: list[str] = []
    for word in re.findall(r"[a-zA-Z0-9]+", text.lower()):
        if len(word) < 3 or word in STOP_WORDS:
            continue
        if word not in words:
            words.append(word)
        if len(words) >= max_words:
            break
    return words


def create_visual_labels_from_text(
    text: str,
    lesson_title: str,
    question: str,
) -> list[str]:
    labels: list[str] = []
    for source in (text, lesson_title, question):
        words = extract_meaningful_words(source, max_words=6)
        for index in range(0, len(words), 2):
            label = " ".join(words[index:index + 2])
            if label and label not in labels:
                labels.append(label)
            if len(labels) >= 4:
                return labels
    return labels


def choose_scene_type_from_text(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("difference", "compare", "versus", " vs ")):
        return "compare"
    if any(token in lowered for token in ("if ", "condition", "decision", "check")):
        return "split"
    if any(token in lowered for token in ("before", "after", "then", "sequence")):
        return "timeline"
    if any(token in lowered for token in ("layer", "stack", "level")):
        return "stack"
    if any(token in lowered for token in ("important", "key", "focus", "summary")):
        return "highlight"
    return "flow"


def deduplicate_issues(issues: list[str]) -> list[str]:
    unique: list[str] = []
    for issue in issues:
        if issue and issue not in unique:
            unique.append(issue)
    return unique


def get_raw_storyboard_contract_issues(
    raw_storyboard: dict,
    requested_scene_count: int,
) -> list[str]:
    raw_scenes = raw_storyboard.get("scenes") if isinstance(raw_storyboard, dict) else None
    if not isinstance(raw_scenes, list):
        return ["Storyboard did not contain a valid scenes array."]

    issues: list[str] = []
    if len(raw_scenes) != requested_scene_count:
        issues.append(
            f"Expected exactly {requested_scene_count} scenes, received {len(raw_scenes)}."
        )

    for index, raw_scene in enumerate(raw_scenes, start=1):
        if not isinstance(raw_scene, dict):
            issues.append(f"Scene {index} was not a JSON object.")
            continue

        expected_id = f"scene_{index}"
        if raw_scene.get("id") != expected_id:
            issues.append(f"Scene {index} must use the canonical ID {expected_id}.")

        title = raw_scene.get("title", "")
        if not isinstance(title, str) or not title.strip():
            issues.append(f"Scene {index} needs a descriptive title.")
        elif re.match(r"^(?:scene|step)\s*\d+", title.strip(), flags=re.IGNORECASE):
            issues.append(f"Scene {index} title duplicated generated numbering.")

        narration = raw_scene.get("narration", "")
        if not isinstance(narration, str) or len(narration.split()) < 6:
            issues.append(f"Scene {index} narration was too short or missing.")

        for issue in validate_typed_scene(raw_scene):
            issues.append(f"Scene {index}: {issue}")

    return deduplicate_issues(issues)


def normalize_ai_storyboard(raw_storyboard: dict, planning_profile: dict) -> dict:
    scenes = []
    for index, raw_scene in enumerate(raw_storyboard["scenes"], start=1):
        title = sentence_to_title(raw_scene.get("title"), f"Scene {index}")
        narration = ensure_string(
            raw_scene.get("narration"),
            "This scene explains one important part of the concept.",
        )
        scenes.append(
            create_scene_payload_from_typed_plan(
                scene_id=f"scene_{index}",
                order=index,
                title=title,
                narration=narration,
                visual=raw_scene["visual"],
                narration_segments=raw_scene["narrationSegments"],
            )
        )

    return {"schemaVersion": "2.1", "planningProfile": planning_profile, "scenes": scenes}


def get_storyboard_quality_issues(
    storyboard: dict | None,
    requested_scene_count: int,
) -> list[str]:
    if not storyboard or not isinstance(storyboard.get("scenes"), list):
        return ["Storyboard did not contain a valid scenes array."]

    issues: list[str] = []
    scenes = storyboard["scenes"]
    if len(scenes) != requested_scene_count:
        issues.append(
            f"Expected exactly {requested_scene_count} scenes, received {len(scenes)}."
        )

    try:
        Storyboard.model_validate(storyboard)
    except ValidationError as error:
        issues.extend(
            "LessonV2 validation error: " + item["msg"]
            for item in error.errors(include_url=False)
        )
        return deduplicate_issues(issues)

    total_nodes = 0
    generic_nodes = 0
    scenes_with_visual_focus = 0

    for scene in scenes:
        visual = scene["visual"]
        nodes = [
            element
            for element in visual["elements"]
            if element["type"] == "node"
        ]
        total_nodes += len(nodes)
        generic_nodes += sum(
            node["label"].strip().lower() in GENERIC_VISUAL_TERMS
            for node in nodes
        )

        segments = scene["narrationSegments"]
        if any(segment["targetElementIds"] for segment in segments):
            scenes_with_visual_focus += 1

        if visual["diagramType"] == "fallback":
            issues.append(
                f"Scene {scene['order']} used the unsupported-visual fallback diagram."
            )

    if total_nodes == 0:
        issues.append("Storyboard did not contain typed visual nodes.")
    elif generic_nodes / total_nodes > 0.34:
        issues.append("Storyboard used too many generic typed visual nodes.")

    if scenes_with_visual_focus < len(scenes):
        issues.append("Every scene narration must focus on declared visual elements.")

    return deduplicate_issues(issues)


def make_fallback_scene(
    *,
    question: str,
    lesson_title: str,
    title: str,
    narration: str,
    scene_type: str,
    index: int,
    scene_count: int,
    explanation: dict,
    planning_profile: dict,
) -> dict:
    source_labels = create_visual_labels_from_text(
        narration,
        lesson_title,
        question,
    )
    visual, narration_segments = build_fallback_visual_plan(
        question=question,
        explanation=explanation,
        planning_profile=planning_profile,
        lesson_title=lesson_title,
        scene_title=title,
        narration=narration,
        source_labels=source_labels,
        scene_type=scene_type,
        scene_index=index,
        scene_count=scene_count,
    )
    return create_scene_payload_from_typed_plan(
        scene_id=f"scene_{index}",
        order=index,
        title=sentence_to_title(title, f"Scene {index}"),
        narration=narration,
        visual=visual,
        narration_segments=narration_segments,
    )


def create_explanation_based_storyboard(
    question: str,
    explanation: dict,
    requested_scene_count: int,
) -> dict:
    lesson_title = ensure_string(explanation.get("title"), "Concept explanation")
    planning_profile = plan_lesson(question, explanation)
    quick_meaning = ensure_string(
        explanation.get("quickMeaning"),
        f"This lesson introduces {lesson_title}.",
    )
    summary = ensure_string(
        explanation.get("summary"),
        f"This completes the main flow of {lesson_title}.",
    )

    middle_candidates: list[tuple[str, str, str]] = []
    for step in ensure_string_list(explanation.get("stepByStep"), [], max_items=8):
        middle_candidates.append(
            (
                sentence_to_title(step, "How the process works"),
                step,
                choose_scene_type_from_text(step),
            )
        )

    example = explanation.get("realWorldExample")
    if isinstance(example, str) and example.strip():
        middle_candidates.append(("A practical example", example.strip(), "timeline"))

    for detail in ensure_string_list(explanation.get("technicalDetails"), [], max_items=4):
        middle_candidates.append(
            (
                sentence_to_title(detail, "Technical detail"),
                detail,
                choose_scene_type_from_text(detail),
            )
        )

    for takeaway in ensure_string_list(explanation.get("takeaways"), [], max_items=4):
        middle_candidates.append(
            (sentence_to_title(takeaway, "Key takeaway"), takeaway, "highlight")
        )

    required_middle_count = requested_scene_count - 2
    while len(middle_candidates) < required_middle_count:
        number = len(middle_candidates) + 1
        middle_candidates.append(
            (
                f"Understanding the flow {number}",
                f"This part connects the earlier explanation of {lesson_title} to its final outcome.",
                "flow",
            )
        )

    scene_specs = [
        (f"Understanding {lesson_title}", quick_meaning, "highlight"),
        *middle_candidates[:required_middle_count],
        ("Putting the concept together", summary, "highlight"),
    ]

    scenes = [
        make_fallback_scene(
            question=question,
            lesson_title=lesson_title,
            title=title,
            narration=narration,
            scene_type=scene_type,
            index=index,
            scene_count=requested_scene_count,
            explanation=explanation,
            planning_profile=planning_profile,
        )
        for index, (title, narration, scene_type) in enumerate(scene_specs, start=1)
    ]

    storyboard = {
        "schemaVersion": "2.1",
        "planningProfile": planning_profile,
        "scenes": scenes,
    }
    Storyboard.model_validate(storyboard)
    return storyboard


def _default_repair_summary() -> dict:
    return {
        "attempted": False,
        "strategy": "none",
        "modelRepairAttempted": False,
        "modelRepairSucceeded": False,
        "repairedSceneIds": [],
        "replacedSceneIds": [],
        "preservedSceneIds": [],
        "notes": [],
    }


def _canonicalize_raw_scene(raw_scene: dict, index: int) -> tuple[dict, bool]:
    canonical = deepcopy(raw_scene)
    changed = False
    expected_scene_id = f"scene_{index}"
    if canonical.get("id") != expected_scene_id:
        canonical["id"] = expected_scene_id
        changed = True

    normalized_title = sentence_to_title(canonical.get("title"), f"Scene {index}")
    if canonical.get("title") != normalized_title:
        canonical["title"] = normalized_title
        changed = True

    normalized_narration = ensure_string(
        canonical.get("narration"),
        "This scene explains one important part of the concept.",
    )
    if canonical.get("narration") != normalized_narration:
        canonical["narration"] = normalized_narration
        changed = True

    segments = canonical.get("narrationSegments")
    if isinstance(segments, list):
        normalized_segments = []
        for segment_index, raw_segment in enumerate(segments, start=1):
            if not isinstance(raw_segment, dict):
                normalized_segments.append(raw_segment)
                continue
            segment = deepcopy(raw_segment)
            expected_segment_id = f"segment_{segment_index}"
            if segment.get("id") != expected_segment_id:
                segment["id"] = expected_segment_id
                changed = True
            if segment.get("order") != segment_index:
                segment["order"] = segment_index
                changed = True
            normalized_segments.append(segment)
        canonical["narrationSegments"] = normalized_segments

    return canonical, changed


def _normalize_single_scene(raw_scene: dict, index: int) -> dict:
    return create_scene_payload_from_typed_plan(
        scene_id=f"scene_{index}",
        order=index,
        title=sentence_to_title(raw_scene.get("title"), f"Scene {index}"),
        narration=ensure_string(
            raw_scene.get("narration"),
            "This scene explains one important part of the concept.",
        ),
        visual=raw_scene["visual"],
        narration_segments=raw_scene["narrationSegments"],
    )


def _partially_repair_storyboard(
    *,
    raw_storyboard: dict,
    fallback_storyboard: dict,
    planning_profile: dict,
    requested_scene_count: int,
    model_repair_attempted: bool,
    model_repair_succeeded: bool,
) -> tuple[dict, dict, list[str]]:
    raw_scenes = raw_storyboard.get("scenes") if isinstance(raw_storyboard, dict) else None
    if not isinstance(raw_scenes, list):
        raw_scenes = []

    scenes: list[dict] = []
    preserved_ids: list[str] = []
    repaired_ids: list[str] = []
    replaced_ids: list[str] = []
    notes: list[str] = []
    repair_issues: list[str] = []

    if len(raw_scenes) > requested_scene_count:
        notes.append(
            f"Trimmed {len(raw_scenes) - requested_scene_count} extra scene(s) to match the request."
        )
    if len(raw_scenes) < requested_scene_count:
        notes.append(
            f"Filled {requested_scene_count - len(raw_scenes)} missing scene(s) from the deterministic plan."
        )

    for index in range(1, requested_scene_count + 1):
        scene_id = f"scene_{index}"
        raw_scene = raw_scenes[index - 1] if index - 1 < len(raw_scenes) else None
        fallback_scene = fallback_storyboard["scenes"][index - 1]

        if isinstance(raw_scene, dict):
            canonical_scene, changed = _canonicalize_raw_scene(raw_scene, index)
            scene_issues = validate_typed_scene(canonical_scene)
            narration = canonical_scene.get("narration")
            if not isinstance(narration, str) or len(narration.split()) < 6:
                scene_issues.append("Scene narration was too short or missing.")

            if not scene_issues:
                try:
                    scenes.append(_normalize_single_scene(canonical_scene, index))
                    preserved_ids.append(scene_id)
                    if changed:
                        repaired_ids.append(scene_id)
                    continue
                except (ValidationError, KeyError, TypeError) as error:
                    scene_issues.append(f"Scene normalization failed: {error}")

            repair_issues.extend(
                f"{scene_id}: {issue}" for issue in deduplicate_issues(scene_issues)
            )

        scenes.append(deepcopy(fallback_scene))
        replaced_ids.append(scene_id)

    storyboard = {
        "schemaVersion": "2.1",
        "planningProfile": planning_profile,
        "scenes": scenes,
    }
    Storyboard.model_validate(storyboard)

    if replaced_ids and preserved_ids:
        strategy = "partial_hybrid"
    elif replaced_ids:
        strategy = "full_fallback"
    elif model_repair_attempted:
        strategy = "model_repair"
    elif repaired_ids:
        strategy = "canonicalization"
    else:
        strategy = "none"

    summary = {
        "attempted": bool(replaced_ids or repaired_ids or model_repair_attempted),
        "strategy": strategy,
        "modelRepairAttempted": model_repair_attempted,
        "modelRepairSucceeded": model_repair_succeeded,
        "repairedSceneIds": repaired_ids,
        "replacedSceneIds": replaced_ids,
        "preservedSceneIds": preserved_ids,
        "notes": notes,
    }
    return storyboard, summary, repair_issues


def _quality_issue_messages(report: dict, *, include_explanation: bool = False) -> list[str]:
    messages: list[str] = []
    for issue in report.get("issues", []):
        if not include_explanation and issue.get("scope") == "explanation":
            continue
        if issue.get("code") in {
            "grounding_provider_unavailable",
            "unverified_grounded_claims",
            "source_contradicted_claim",
        }:
            continue
        if issue.get("severity") not in {"warning", "error"}:
            continue
        location = issue.get("sceneId") or issue.get("segmentId")
        prefix = f"{location}: " if location else ""
        messages.append(prefix + issue.get("message", "Lesson quality issue."))
    return deduplicate_issues(messages)


def create_storyboard(
    *,
    question: str,
    explanation: dict,
    requested_scene_count: int,
    ai_storyboard: dict | None = None,
    ai_source: Literal["gemini", "groq"] | None = None,
    ai_model_used: str | None = None,
    initial_issues: list[str] | None = None,
    repair_callback: StoryboardRepairCallback | None = None,
    grounding_report: dict | None = None,
) -> StoryboardBuildResult:
    issues = list(initial_issues or [])
    model_repair_attempted = False
    model_repair_succeeded = False
    planning_profile = plan_lesson(question, explanation)
    fallback_storyboard = create_explanation_based_storyboard(
        question,
        explanation,
        requested_scene_count,
    )

    if ai_storyboard and ai_source:
        contract_issues = get_raw_storyboard_contract_issues(
            ai_storyboard,
            requested_scene_count,
        )
        normalized_storyboard = None
        if not contract_issues:
            normalized_storyboard = normalize_ai_storyboard(ai_storyboard, planning_profile)

        legacy_quality_issues = (
            get_storyboard_quality_issues(normalized_storyboard, requested_scene_count)
            if normalized_storyboard
            else []
        )
        candidate_report = (
            evaluate_lesson_quality(
                question=question,
                explanation=explanation,
                storyboard=normalized_storyboard,
                requested_scene_count=requested_scene_count,
                repair_summary=_default_repair_summary(),
                grounding_report=grounding_report,
            )
            if normalized_storyboard
            else None
        )
        candidate_quality_messages = (
            _quality_issue_messages(candidate_report) if candidate_report else []
        )
        candidate_issues = deduplicate_issues(
            contract_issues + legacy_quality_issues + candidate_quality_messages
        )

        if (
            normalized_storyboard
            and not contract_issues
            and not legacy_quality_issues
            and not blocking_quality_issues(candidate_report)
            and (not candidate_quality_messages or repair_callback is None)
        ):
            return StoryboardBuildResult(
                storyboard=normalized_storyboard,
                source=ai_source,
                model_used=ai_model_used,
                fallback_used=False,
                issues=issues,
                quality_report=candidate_report,
                repair_summary=_default_repair_summary(),
            )

        issues.extend(candidate_issues)
        repair_candidate = ai_storyboard
        if repair_callback and candidate_issues:
            model_repair_attempted = True
            try:
                repaired_by_model = repair_callback(ai_storyboard, candidate_issues)
                if isinstance(repaired_by_model, dict):
                    repair_candidate = repaired_by_model
                    repaired_contract_issues = get_raw_storyboard_contract_issues(
                        repaired_by_model,
                        requested_scene_count,
                    )
                    repaired_normalized = None
                    if not repaired_contract_issues:
                        repaired_normalized = normalize_ai_storyboard(
                            repaired_by_model,
                            planning_profile,
                        )
                    repaired_quality_issues = (
                        get_storyboard_quality_issues(
                            repaired_normalized,
                            requested_scene_count,
                        )
                        if repaired_normalized
                        else []
                    )
                    model_summary = {
                        "attempted": True,
                        "strategy": "model_repair",
                        "modelRepairAttempted": True,
                        "modelRepairSucceeded": False,
                        "repairedSceneIds": [],
                        "replacedSceneIds": [],
                        "preservedSceneIds": [
                            f"scene_{index}"
                            for index in range(1, requested_scene_count + 1)
                        ],
                        "notes": ["The AI provider returned a repaired full storyboard."],
                    }
                    repaired_report = (
                        evaluate_lesson_quality(
                            question=question,
                            explanation=explanation,
                            storyboard=repaired_normalized,
                            requested_scene_count=requested_scene_count,
                            repair_summary=model_summary,
                            grounding_report=grounding_report,
                        )
                        if repaired_normalized
                        else None
                    )
                    repaired_messages = (
                        _quality_issue_messages(repaired_report)
                        if repaired_report
                        else []
                    )
                    if (
                        repaired_normalized
                        and not repaired_contract_issues
                        and not repaired_quality_issues
                        and not blocking_quality_issues(repaired_report)
                        and not repaired_messages
                    ):
                        model_repair_succeeded = True
                        model_summary["modelRepairSucceeded"] = True
                        repaired_report["repair"] = model_summary
                        return StoryboardBuildResult(
                            storyboard=repaired_normalized,
                            source=ai_source,
                            model_used=repaired_by_model.get("_modelUsed") or ai_model_used,
                            fallback_used=False,
                            issues=deduplicate_issues(issues),
                            quality_report=repaired_report,
                            repair_summary=model_summary,
                        )
                    issues.extend(
                        deduplicate_issues(
                            repaired_contract_issues
                            + repaired_quality_issues
                            + repaired_messages
                        )
                    )
            except Exception as error:
                issues.append(f"AI storyboard repair failed: {error}")

        hybrid_storyboard, repair_summary, repair_issues = _partially_repair_storyboard(
            raw_storyboard=repair_candidate,
            fallback_storyboard=fallback_storyboard,
            planning_profile=planning_profile,
            requested_scene_count=requested_scene_count,
            model_repair_attempted=model_repair_attempted,
            model_repair_succeeded=model_repair_succeeded,
        )
        issues.extend(repair_issues)
        hybrid_report = evaluate_lesson_quality(
            question=question,
            explanation=explanation,
            storyboard=hybrid_storyboard,
            requested_scene_count=requested_scene_count,
            repair_summary=repair_summary,
            grounding_report=grounding_report,
        )

        if repair_summary["preservedSceneIds"] and not blocking_quality_issues(hybrid_report):
            used_scene_fallback = bool(repair_summary["replacedSceneIds"])
            return StoryboardBuildResult(
                storyboard=hybrid_storyboard,
                source="hybrid" if used_scene_fallback else ai_source,
                model_used=ai_model_used,
                fallback_used=used_scene_fallback,
                issues=deduplicate_issues(issues),
                quality_report=hybrid_report,
                repair_summary=repair_summary,
            )
    elif not issues:
        issues.append("No AI storyboard was available; used the deterministic fallback.")

    fallback_summary = {
        "attempted": bool(ai_storyboard),
        "strategy": "full_fallback",
        "modelRepairAttempted": model_repair_attempted,
        "modelRepairSucceeded": model_repair_succeeded,
        "repairedSceneIds": [],
        "replacedSceneIds": [
            f"scene_{index}" for index in range(1, requested_scene_count + 1)
        ],
        "preservedSceneIds": [],
        "notes": ["The deterministic visual planner supplied the complete lesson."],
    }
    fallback_report = evaluate_lesson_quality(
        question=question,
        explanation=explanation,
        storyboard=fallback_storyboard,
        requested_scene_count=requested_scene_count,
        repair_summary=fallback_summary,
        grounding_report=grounding_report,
    )

    contains_generic_nodes = any(
        element.get("type") == "node" and element.get("nodeKind") == "generic"
        for scene in fallback_storyboard["scenes"]
        for element in scene["visual"]["elements"]
    )
    if contains_generic_nodes:
        issues.append(
            "No concept-specific deterministic visual template was available; "
            "used a typed generic flow that should be replaced by an AI visual plan."
        )

    return StoryboardBuildResult(
        storyboard=fallback_storyboard,
        source="rule_based",
        model_used=None,
        fallback_used=True,
        issues=deduplicate_issues(issues),
        quality_report=fallback_report,
        repair_summary=fallback_summary,
    )
