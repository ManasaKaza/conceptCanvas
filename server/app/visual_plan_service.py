from __future__ import annotations

import re
from typing import Iterable

from pydantic import TypeAdapter, ValidationError

from app.models import NarrationSegment, VisualEdge, VisualNode, VisualSpec
from app.visual_strategy_service import extract_comparison_subjects, extract_formula, select_scene_archetype


SEGMENT_LIST_ADAPTER = TypeAdapter(list[NarrationSegment])

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
}

DIAGRAM_TO_LEGACY_SCENE_TYPE = {
    "flow": "flow",
    "sequence": "flow",
    "hierarchy": "stack",
    "stack": "stack",
    "tree": "stack",
    "comparison": "compare",
    "timeline": "timeline",
    "architecture": "split",
    "state_transition": "flow",
    "cycle": "timeline",
    "cause_effect": "flow",
    "concept_map": "split",
    "formula": "highlight",
    "code_execution": "timeline",
    "spatial": "split",
    "fallback": "flow",
}


def normalize_id(value: str, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    words = re.findall(r"[a-zA-Z0-9]+", value.lower())
    if not words:
        return fallback
    candidate = "_".join(words[:6])
    if not candidate[0].isalpha():
        candidate = f"node_{candidate}"
    return candidate[:64]


def clean_label(value: str, fallback: str) -> str:
    if not isinstance(value, str) or not value.strip():
        return fallback
    return value.strip()[:80]


def estimate_duration_ms(text: str) -> int:
    word_count = max(1, len(text.split()))
    return min(12000, max(1800, int(word_count / 2.4 * 1000)))


def get_visual_spec_issues(raw_visual: object) -> list[str]:
    if not isinstance(raw_visual, dict):
        return ["Scene did not contain a typed visual object."]

    try:
        visual = VisualSpec.model_validate(raw_visual)
    except ValidationError as error:
        return [
            "Typed visual schema error: " + issue["msg"]
            for issue in error.errors(include_url=False)
        ]

    issues: list[str] = []
    node_labels = [
        element.label.strip().lower()
        for element in visual.elements
        if isinstance(element, VisualNode)
    ]
    generic_count = sum(label in GENERIC_LABELS for label in node_labels)
    if node_labels and generic_count / len(node_labels) > 0.34:
        issues.append("Typed visual used too many generic node labels.")

    return issues


def get_narration_segment_issues(
    raw_segments: object,
    visual_ids: set[str],
) -> list[str]:
    if not isinstance(raw_segments, list) or not raw_segments:
        return ["Scene did not contain narration segments."]

    try:
        segments = SEGMENT_LIST_ADAPTER.validate_python(raw_segments)
    except ValidationError as error:
        return [
            "Narration timeline schema error: " + issue["msg"]
            for issue in error.errors(include_url=False)
        ]

    issues: list[str] = []
    expected_ids = [f"segment_{index}" for index in range(1, len(segments) + 1)]
    actual_ids = [segment.id for segment in segments]
    if actual_ids != expected_ids:
        issues.append("Narration segment IDs must be segment_1, segment_2, and so on.")

    expected_orders = list(range(1, len(segments) + 1))
    actual_orders = [segment.order for segment in segments]
    if actual_orders != expected_orders:
        issues.append("Narration segment order must be canonical.")

    for index, segment in enumerate(segments, start=1):
        missing_targets = [
            target_id
            for target_id in segment.targetElementIds
            if target_id not in visual_ids
        ]
        if missing_targets:
            issues.append(
                f"Narration segment {index} referenced undeclared visual elements."
            )

        if len(segment.spokenText.split()) < 6:
            issues.append(
                f"Narration segment {index} was too short to explain the visual naturally."
            )

    return issues


def validate_typed_scene(raw_scene: object) -> list[str]:
    if not isinstance(raw_scene, dict):
        return ["Scene was not a JSON object."]

    visual_issues = get_visual_spec_issues(raw_scene.get("visual"))
    visual_ids: set[str] = set()
    if not visual_issues:
        visual = VisualSpec.model_validate(raw_scene["visual"])
        visual_ids = {element.id for element in visual.elements}

    narration_issues = get_narration_segment_issues(
        raw_scene.get("narrationSegments"),
        visual_ids,
    )
    return visual_issues + narration_issues


def parse_visual_spec(raw_visual: dict) -> dict:
    return VisualSpec.model_validate(raw_visual).model_dump()


def parse_narration_segments(raw_segments: list[dict]) -> list[dict]:
    return [segment.model_dump() for segment in SEGMENT_LIST_ADAPTER.validate_python(raw_segments)]


def get_node_ids(visual: dict) -> list[str]:
    return [
        element["id"]
        for element in visual.get("elements", [])
        if element.get("type") == "node"
    ]


def get_edge_by_id(visual: dict) -> dict[str, dict]:
    return {
        element["id"]: element
        for element in visual.get("elements", [])
        if element.get("type") == "edge"
    }


def derive_legacy_contract(
    visual: dict,
    narration_segments: list[dict],
    fallback_narration: str,
) -> tuple[list[str], list[str], list[dict]]:
    """Create temporary fields consumed by the Phase 1 player.

    These fields are derived from LessonV2 and must not become a second source of truth.
    """

    node_ids = get_node_ids(visual)
    edge_by_id = get_edge_by_id(visual)
    subtitle_lines = [
        segment["subtitleText"] for segment in narration_segments[:3]
    ] or [fallback_narration]

    actions: list[dict] = []
    for segment in narration_segments:
        target_ids = segment.get("targetElementIds", [])
        target_id = target_ids[0] if target_ids else None
        action = segment.get("action")
        label = segment.get("spokenText") or fallback_narration

        if target_id in edge_by_id:
            edge = edge_by_id[target_id]
            actions.append(
                {
                    "type": "connect",
                    "fromElement": edge["fromId"],
                    "toElement": edge["toId"],
                    "label": label,
                }
            )
        elif action in {"reveal", "deemphasize"} and target_id in node_ids:
            actions.append({"type": "show", "target": target_id, "label": label})
        elif action == "highlight" and target_id in node_ids:
            actions.append({"type": "highlight", "target": target_id, "label": label})
        elif action == "trace" and len(target_ids) >= 2:
            from_id, to_id = target_ids[:2]
            if from_id in node_ids and to_id in node_ids:
                actions.append(
                    {
                        "type": "connect",
                        "fromElement": from_id,
                        "toElement": to_id,
                        "label": label,
                    }
                )
        elif action == "pause":
            actions.append({"type": "wait", "label": label})

    if not actions and node_ids:
        actions.append(
            {
                "type": "show",
                "target": node_ids[0],
                "label": fallback_narration,
            }
        )

    return node_ids, subtitle_lines, actions


def _node(
    element_id: str,
    label: str,
    node_kind: str,
    detail: str | None = None,
) -> dict:
    payload = {
        "type": "node",
        "id": element_id,
        "label": label,
        "nodeKind": node_kind,
    }
    if detail:
        payload["detail"] = detail
    return payload


def _edge(
    element_id: str,
    from_id: str,
    to_id: str,
    relation: str,
    label: str | None = None,
) -> dict:
    payload = {
        "type": "edge",
        "id": element_id,
        "fromId": from_id,
        "toId": to_id,
        "relation": relation,
        "directed": True,
    }
    if label:
        payload["label"] = label
    return payload


def _segment(
    order: int,
    spoken_text: str,
    subtitle_text: str,
    target_ids: Iterable[str],
    action: str,
) -> dict:
    return {
        "id": f"segment_{order}",
        "order": order,
        "spokenText": spoken_text,
        "subtitleText": subtitle_text,
        "targetElementIds": list(target_ids),
        "action": action,
        "estimatedDurationMs": estimate_duration_ms(spoken_text),
    }


def _phrase_label(text: str, fallback: str, max_words: int = 7) -> str:
    if not isinstance(text, str) or not text.strip():
        return fallback
    cleaned = re.sub(r"^(?:first|then|next|finally|step\s*\d+)\s*[:,.-]?\s*", "", text.strip(), flags=re.IGNORECASE)
    cleaned = re.split(r"[.;:]", cleaned, maxsplit=1)[0].strip()
    words = cleaned.split()
    if len(words) > max_words:
        cleaned = " ".join(words[:max_words])
    return clean_label(cleaned.rstrip(" ,;-"), fallback)


def _lesson_units(explanation: dict, scene_title: str, narration: str) -> list[str]:
    raw: list[str] = []
    steps = explanation.get("stepByStep")
    if isinstance(steps, list):
        raw.extend(item for item in steps if isinstance(item, str))
    details = explanation.get("technicalDetails")
    if isinstance(details, list):
        raw.extend(item for item in details if isinstance(item, str))
    raw.extend([scene_title, narration])

    units: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(raw, start=1):
        label = _phrase_label(item, f"Lesson idea {index}")
        key = label.lower()
        if key not in seen:
            seen.add(key)
            units.append(label)
        if len(units) >= 7:
            break
    return units


def _deduplicate_element_ids(labels: list[str], prefix: str = "node") -> list[str]:
    ids: list[str] = []
    for index, label in enumerate(labels, start=1):
        base = normalize_id(label, f"{prefix}_{index}")
        candidate = base
        suffix = 2
        while candidate in ids:
            candidate = f"{base}_{suffix}"[:64]
            suffix += 1
        ids.append(candidate)
    return ids


def _linear_visual(
    labels: list[str],
    *,
    diagram_type: str,
    node_kind: str,
    relation: str,
    orientation: str,
    scene_index: int,
    narration: str,
) -> tuple[dict, list[dict]]:
    all_labels = labels[:7]
    while len(all_labels) < 2:
        all_labels.append(f"Related idea {len(all_labels) + 1}")

    max_visible = 5 if diagram_type == "cycle" else 4
    global_focus = min(len(all_labels) - 1, max(0, scene_index - 1))
    window_start = min(
        max(0, global_focus - 1),
        max(0, len(all_labels) - max_visible),
    )
    labels = all_labels[window_start:window_start + max_visible]
    local_focus = global_focus - window_start
    node_ids = _deduplicate_element_ids(labels)
    elements = [_node(node_id, label, node_kind) for node_id, label in zip(node_ids, labels)]
    edge_ids: list[str] = []
    for index in range(len(node_ids) - 1):
        edge_id = normalize_id(f"edge_{index + 1}_{node_ids[index]}_to_{node_ids[index + 1]}", f"edge_{index + 1}")
        edge_ids.append(edge_id)
        elements.append(_edge(edge_id, node_ids[index], node_ids[index + 1], relation))
    if diagram_type == "cycle" and len(node_ids) > 2:
        edge_id = normalize_id(f"edge_cycle_{node_ids[-1]}_to_{node_ids[0]}", "cycle_close")
        edge_ids.append(edge_id)
        elements.append(_edge(edge_id, node_ids[-1], node_ids[0], "changes_into", "Cycle repeats"))

    focus_index = min(len(node_ids) - 1, max(0, local_focus))
    targets = [node_ids[focus_index]]
    if focus_index > 0:
        targets = [node_ids[focus_index - 1], edge_ids[focus_index - 1], node_ids[focus_index]]
    elif edge_ids:
        targets.extend([edge_ids[0], node_ids[1]])
    return (
        {
            "schemaVersion": "2.0",
            "diagramType": diagram_type,
            "orientation": orientation,
            "elements": elements,
        },
        [_segment(1, narration, _phrase_label(narration, labels[focus_index], 14), targets, "trace")],
    )


def build_universal_visual_plan(
    *,
    question: str,
    explanation: dict,
    planning_profile: dict,
    scene_title: str,
    narration: str,
    scene_index: int,
    scene_count: int,
) -> tuple[dict, list[dict]]:
    archetype = select_scene_archetype(planning_profile, scene_title, narration)
    units = _lesson_units(explanation, scene_title, narration)
    lesson_title = clean_label(explanation.get("title"), "Lesson concept")

    if archetype == "comparison":
        subjects = extract_comparison_subjects(question)
        labels = list(subjects) if subjects else units[:2]
        while len(labels) < 2:
            labels.append(f"Alternative {len(labels) + 1}")
        ids = _deduplicate_element_ids(labels, "option")
        edge_id = normalize_id(f"edge_compare_{ids[0]}_{ids[1]}", "comparison_edge")
        elements = [
            _node(ids[0], labels[0], "category"),
            _node(ids[1], labels[1], "category"),
            _edge(edge_id, ids[0], ids[1], "contrasts", "Compare"),
        ]
        return (
            {"schemaVersion": "2.0", "diagramType": "comparison", "orientation": "two_column", "elements": elements},
            [_segment(1, narration, _phrase_label(narration, "Compare the two ideas", 14), [ids[0], edge_id, ids[1]], "highlight")],
        )

    if archetype in {"architecture", "concept_map", "hierarchy", "tree", "spatial"}:
        child_labels = units[:4]
        if lesson_title.lower() in {label.lower() for label in child_labels}:
            child_labels = child_labels[1:]
        while len(child_labels) < 2:
            child_labels.append(f"{lesson_title} part {len(child_labels) + 1}")
        labels = [lesson_title, *child_labels[:4]]
        ids = _deduplicate_element_ids(labels)
        root_id = ids[0]
        elements = [_node(root_id, lesson_title, "entity")]
        relation = "contains"
        for child_index, (child_id, child_label) in enumerate(zip(ids[1:], labels[1:]), start=1):
            kind = "place" if archetype == "spatial" else ("category" if archetype in {"hierarchy", "tree"} else "component")
            elements.append(_node(child_id, child_label, kind))
            edge_id = normalize_id(
                f"edge_{child_index}_contains_{root_id}_to_{child_id}",
                f"part_edge_{child_index}",
            )
            elements.append(_edge(edge_id, root_id, child_id, relation))
        focus = ids[1 + ((scene_index - 1) % (len(ids) - 1))]
        focus_edge = next(element["id"] for element in elements if element.get("type") == "edge" and element["toId"] == focus)
        diagram_type = archetype
        orientation = "radial" if archetype in {"architecture", "concept_map", "spatial"} else "top_to_bottom"
        return (
            {"schemaVersion": "2.0", "diagramType": diagram_type, "orientation": orientation, "elements": elements},
            [_segment(1, narration, _phrase_label(narration, focus, 14), [root_id, focus_edge, focus], "highlight")],
        )

    if archetype == "cause_effect":
        causes = units[:4]
        effect = _phrase_label(explanation.get("summary", ""), lesson_title)
        labels = [*causes, effect]
        ids = _deduplicate_element_ids(labels)
        effect_id = ids[-1]
        elements = [_node(node_id, label, "event" if node_id != effect_id else "output") for node_id, label in zip(ids, labels)]
        edge_ids = []
        for cause_id in ids[:-1]:
            edge_id = normalize_id(f"edge_cause_{cause_id}_to_{effect_id}", "cause_edge")
            edge_ids.append(edge_id)
            elements.append(_edge(edge_id, cause_id, effect_id, "causes"))
        focus_index = min(len(ids) - 2, max(0, scene_index - 1))
        return (
            {"schemaVersion": "2.0", "diagramType": "cause_effect", "orientation": "left_to_right", "elements": elements},
            [_segment(1, narration, _phrase_label(narration, "Cause and effect", 14), [ids[focus_index], edge_ids[focus_index], effect_id], "trace")],
        )

    if archetype == "formula":
        combined = " ".join(str(explanation.get(key, "")) for key in ("quickMeaning", "deepExplanation", "summary"))
        formula = extract_formula(question) or extract_formula(combined) or lesson_title
        variable_labels = units[:3]
        labels = [formula, *variable_labels]
        ids = _deduplicate_element_ids(labels, "quantity")
        formula_id = ids[0]
        elements = [_node(formula_id, formula, "formula", "Quantitative relationship")]
        edge_ids = []
        for variable_id, variable_label in zip(ids[1:], labels[1:]):
            elements.append(_node(variable_id, variable_label, "quantity"))
            edge_id = normalize_id(f"edge_formula_{variable_id}_to_{formula_id}", "formula_edge")
            edge_ids.append(edge_id)
            elements.append(_edge(edge_id, variable_id, formula_id, "depends_on"))
        focus_index = (scene_index - 1) % max(1, len(ids) - 1)
        variable_id = ids[1 + focus_index]
        return (
            {"schemaVersion": "2.0", "diagramType": "formula", "orientation": "radial", "elements": elements},
            [_segment(1, narration, _phrase_label(narration, "Understand the relationship", 14), [variable_id, edge_ids[focus_index], formula_id], "highlight")],
        )

    relation_by_archetype = {
        "timeline": "precedes",
        "state_transition": "changes_into",
        "code_execution": "transforms",
        "sequence": "flows_to",
        "cycle": "changes_into",
        "flow": "flows_to",
        "stack": "calls",
    }
    node_kind_by_archetype = {
        "timeline": "event",
        "state_transition": "state",
        "code_execution": "code",
        "sequence": "process",
        "cycle": "process",
        "flow": "process",
        "stack": "stack_frame",
    }
    return _linear_visual(
        units,
        diagram_type=archetype if archetype in relation_by_archetype else "concept_map",
        node_kind=node_kind_by_archetype.get(archetype, "entity"),
        relation=relation_by_archetype.get(archetype, "depends_on"),
        orientation="stacked" if archetype == "stack" else ("top_to_bottom" if archetype in {"timeline", "code_execution"} else "left_to_right"),
        scene_index=scene_index,
        narration=narration,
    )


def build_fallback_visual_plan(
    *,
    question: str,
    explanation: dict,
    planning_profile: dict,
    lesson_title: str,
    scene_title: str,
    narration: str,
    source_labels: list[str],
    scene_type: str,
    scene_index: int,
    scene_count: int,
) -> tuple[dict, list[dict]]:
    del lesson_title, source_labels, scene_type  # Kept temporarily for call compatibility.
    return build_universal_visual_plan(
        question=question,
        explanation=explanation,
        planning_profile=planning_profile,
        scene_title=scene_title,
        narration=narration,
        scene_index=scene_index,
        scene_count=scene_count,
    )

def create_scene_payload_from_typed_plan(
    *,
    scene_id: str,
    order: int,
    title: str,
    narration: str,
    visual: dict,
    narration_segments: list[dict],
) -> dict:
    parsed_visual = parse_visual_spec(visual)
    parsed_segments = parse_narration_segments(narration_segments)
    visual_elements, subtitle_lines, actions = derive_legacy_contract(
        parsed_visual,
        parsed_segments,
        narration,
    )

    return {
        "id": scene_id,
        "order": order,
        "sceneType": DIAGRAM_TO_LEGACY_SCENE_TYPE[parsed_visual["diagramType"]],
        "title": title,
        "narration": narration,
        "visual": parsed_visual,
        "narrationSegments": parsed_segments,
        "visualElements": visual_elements,
        "subtitleLines": subtitle_lines,
        "actions": actions,
    }
