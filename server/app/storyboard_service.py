ALLOWED_SCENE_TYPES = {
    "flow",
    "stack",
    "compare",
    "timeline",
    "split",
    "highlight",
}

ALLOWED_ACTION_TYPES = {
    "show",
    "connect",
    "highlight",
    "move",
    "wait",
}

GENERIC_VISUAL_TERMS = {
    "concept_box",
    "part_1",
    "part_2",
    "part_3",
    "action",
    "result",
    "important_part",
    "focus_area",
    "core_idea",
    "learning_goal",
    "main_concept",
    "summary",
    "final_takeaway",
}

def is_generic_visual_element(element: str) -> bool:
    if not isinstance(element, str):
        return True

    cleaned = element.strip().lower()

    if cleaned in GENERIC_VISUAL_TERMS:
        return True

    if cleaned.startswith("part_"):
        return True

    if cleaned.startswith("element_"):
        return True

    return False


def has_teacher_like_action_labels(scene: dict) -> bool:
    actions = scene.get("actions", [])

    if not isinstance(actions, list) or not actions:
        return False

    good_labels = 0

    for action in actions:
        if not isinstance(action, dict):
            continue

        label = action.get("label", "")

        if not isinstance(label, str):
            continue

        words = label.strip().split()

        if len(words) >= 6:
            good_labels += 1

    return good_labels >= max(1, len(actions) // 2)


def is_storyboard_quality_good(storyboard: dict) -> bool:
    if not isinstance(storyboard, dict):
        return False

    scenes = storyboard.get("scenes", [])

    if not isinstance(scenes, list) or len(scenes) < 3:
        return False

    total_elements = 0
    generic_elements = 0
    teacher_like_scenes = 0

    for scene in scenes:
        if not isinstance(scene, dict):
            continue

        visual_elements = scene.get("visualElements", [])

        if not isinstance(visual_elements, list):
            continue

        for element in visual_elements:
            total_elements += 1

            if is_generic_visual_element(element):
                generic_elements += 1

        if has_teacher_like_action_labels(scene):
            teacher_like_scenes += 1

    if total_elements == 0:
        return False

    generic_ratio = generic_elements / total_elements

    if generic_ratio > 0.4:
        return False

    if teacher_like_scenes < max(1, len(scenes) // 2):
        return False

    return True

def make_subtitles(text: str) -> list[str]:
    if not isinstance(text, str) or not text.strip():
        return ["Understand the idea step by step"]

    parts = [part.strip() for part in text.replace(".", ".|").split("|") if part.strip()]

    if len(parts) >= 2:
        return parts[:2]

    words = text.split()

    if len(words) <= 8:
        return [text]

    midpoint = len(words) // 2

    return [
        " ".join(words[:midpoint]),
        " ".join(words[midpoint:]),
    ]


def ensure_string(value, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return fallback


def ensure_string_list(value, fallback: list[str], max_items: int = 6) -> list[str]:
    if not isinstance(value, list):
        return fallback

    cleaned_items = []

    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned_items.append(item.strip())

    if not cleaned_items:
        return fallback

    return cleaned_items[:max_items]


def normalize_visual_name(text: str, fallback: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return fallback

    cleaned = (
        text.lower()
        .replace(":", "")
        .replace(",", "")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
        .replace("/", " ")
        .replace("-", " ")
    )

    words = [word for word in cleaned.split() if word.isalnum()]

    if not words:
        return fallback

    return "_".join(words[:4])


def create_actions_from_elements(elements: list[str]) -> list[dict]:
    actions = []

    for element in elements:
        actions.append(
            {
                "type": "show",
                "target": element,
                "label": f"Show {element.replace('_', ' ')}",
            }
        )

    for index in range(len(elements) - 1):
        actions.append(
            {
                "type": "connect",
                "fromElement": elements[index],
                "toElement": elements[index + 1],
                "label": "connects to",
            }
        )

    if elements:
        actions.append(
            {
                "type": "highlight",
                "target": elements[-1],
                "label": "Key result",
            }
        )

    return actions


def normalize_action(raw_action: dict, visual_elements: list[str]) -> dict | None:
    if not isinstance(raw_action, dict):
        return None

    action_type = raw_action.get("type")

    if action_type not in ALLOWED_ACTION_TYPES:
        action_type = "show"

    target = raw_action.get("target")
    from_element = raw_action.get("fromElement")
    to_element = raw_action.get("toElement")

    action = {
        "type": action_type,
        "label": ensure_string(raw_action.get("label"), ""),
    }

    if isinstance(target, str) and target.strip():
        action["target"] = normalize_visual_name(target, target)

    if isinstance(from_element, str) and from_element.strip():
        action["fromElement"] = normalize_visual_name(from_element, from_element)

    if isinstance(to_element, str) and to_element.strip():
        action["toElement"] = normalize_visual_name(to_element, to_element)

    if action_type in {"show", "highlight"} and "target" not in action:
        if visual_elements:
            action["target"] = visual_elements[0]
        else:
            return None

    if action_type in {"connect", "move"}:
        if "fromElement" not in action or "toElement" not in action:
            if len(visual_elements) >= 2:
                action["fromElement"] = visual_elements[0]
                action["toElement"] = visual_elements[1]
            else:
                return None

    return action


def normalize_scene(raw_scene: dict, index: int) -> dict:
    if not isinstance(raw_scene, dict):
        raw_scene = {}

    scene_type = raw_scene.get("sceneType")

    if scene_type not in ALLOWED_SCENE_TYPES:
        scene_type = "flow"

    title = ensure_string(raw_scene.get("title"), f"Scene {index + 1}")
    narration = ensure_string(
        raw_scene.get("narration"),
        "This scene explains one important part of the concept.",
    )

    raw_visual_elements = raw_scene.get("visualElements")

    visual_elements = ensure_string_list(
        raw_visual_elements,
        [
            normalize_visual_name(title, f"scene_{index + 1}_idea"),
            "important_part",
            "result",
        ],
        max_items=6,
    )

    visual_elements = [
        normalize_visual_name(element, f"element_{element_index + 1}")
        for element_index, element in enumerate(visual_elements)
    ]

    subtitle_lines = ensure_string_list(
        raw_scene.get("subtitleLines"),
        make_subtitles(narration),
        max_items=3,
    )

    raw_actions = raw_scene.get("actions")
    actions = []

    if isinstance(raw_actions, list):
        for raw_action in raw_actions[:10]:
            normalized_action = normalize_action(raw_action, visual_elements)

            if normalized_action:
                actions.append(normalized_action)

    if not actions:
        actions = create_actions_from_elements(visual_elements)

    return {
        "id": ensure_string(raw_scene.get("id"), f"scene_{index + 1}"),
        "sceneType": scene_type,
        "title": title,
        "narration": narration,
        "visualElements": visual_elements,
        "subtitleLines": subtitle_lines,
        "actions": actions,
    }


def normalize_ai_storyboard(raw_storyboard: dict) -> dict | None:
    if not isinstance(raw_storyboard, dict):
        return None

    raw_scenes = raw_storyboard.get("scenes")

    if not isinstance(raw_scenes, list) or len(raw_scenes) == 0:
        return None

    scenes = []

    for index, raw_scene in enumerate(raw_scenes[:7]):
        scenes.append(normalize_scene(raw_scene, index))

    return {"scenes": scenes}

STOP_WORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "being",
    "this", "that", "these", "those", "it", "its", "they", "their", "them",
    "you", "your", "we", "our", "can", "could", "should", "would", "will",
    "when", "while", "how", "why", "what", "which", "who", "into", "through",
    "first", "then", "next", "finally", "start", "understand", "learn",
    "concept", "idea", "basic", "main", "part", "parts", "step",
}


def extract_meaningful_words(text: str, max_words: int = 4) -> list[str]:
    if not isinstance(text, str):
        return []

    cleaned = (
        text.lower()
        .replace(".", " ")
        .replace(",", " ")
        .replace(":", " ")
        .replace(";", " ")
        .replace("(", " ")
        .replace(")", " ")
        .replace("/", " ")
        .replace("-", " ")
    )

    words = []

    for word in cleaned.split():
        if len(word) < 3:
            continue

        if word in STOP_WORDS:
            continue

        if not word.isalnum():
            continue

        if word not in words:
            words.append(word)

    return words[:max_words]


def create_visual_elements_from_text(text: str, title: str, index: int) -> list[str]:
    words = extract_meaningful_words(text, max_words=4)

    if len(words) >= 3:
        return [
            "_".join(words[:2]),
            words[2],
            words[3] if len(words) > 3 else "outcome",
        ]

    title_words = extract_meaningful_words(title, max_words=3)

    combined_words = words + title_words

    cleaned_words = []

    for word in combined_words:
        if word not in cleaned_words:
            cleaned_words.append(word)

    if len(cleaned_words) >= 3:
        return [
            "_".join(cleaned_words[:2]),
            cleaned_words[2],
            "key_point",
        ]

    return [
        f"concept_step_{index}",
        "related_detail",
        "key_point",
    ]


def create_teacher_actions_from_text(elements: list[str], narration: str) -> list[dict]:
    first = elements[0]
    second = elements[1] if len(elements) > 1 else elements[0]
    third = elements[2] if len(elements) > 2 else elements[-1]

    return [
        {
            "type": "show",
            "target": first,
            "label": narration,
        },
        {
            "type": "connect",
            "fromElement": first,
            "toElement": second,
            "label": f"This connects {first.replace('_', ' ')} with {second.replace('_', ' ')} in the explanation.",
        },
        {
            "type": "highlight",
            "target": third,
            "label": f"The key takeaway here is {third.replace('_', ' ')}.",
        },
    ]


def choose_scene_type_from_text(text: str) -> str:
    lowered = text.lower()

    if "difference" in lowered or "compare" in lowered or "versus" in lowered:
        return "compare"

    if "if" in lowered or "condition" in lowered or "check" in lowered:
        return "split"

    if "before" in lowered or "after" in lowered or "then" in lowered:
        return "timeline"

    if "layer" in lowered or "stack" in lowered:
        return "stack"

    if "important" in lowered or "key" in lowered or "focus" in lowered:
        return "highlight"

    return "flow"

def create_explanation_based_storyboard(question: str, explanation: dict) -> dict:
    title = explanation.get("title", "Concept Explanation")
    quick_meaning = explanation.get("quickMeaning", "")
    step_by_step = explanation.get("stepByStep", [])
    technical_details = explanation.get("technicalDetails", [])
    summary = explanation.get("summary", "")

    scenes = []

    intro_elements = create_visual_elements_from_text(
        quick_meaning,
        title,
        1,
    )

    scenes.append(
        {
            "id": "scene_1",
            "sceneType": "highlight",
            "title": f"Understanding {title}",
            "narration": quick_meaning
            or f"This lesson explains {title} step by step.",
            "visualElements": intro_elements,
            "subtitleLines": make_subtitles(
                quick_meaning or f"This lesson explains {title}."
            ),
            "actions": create_teacher_actions_from_text(
                intro_elements,
                quick_meaning or f"Let us understand {title} step by step.",
            ),
        }
    )

    if isinstance(step_by_step, list) and step_by_step:
        for index, step in enumerate(step_by_step[:4], start=2):
            step_elements = create_visual_elements_from_text(
                step,
                title,
                index,
            )

            scenes.append(
                {
                    "id": f"scene_{index}",
                    "sceneType": choose_scene_type_from_text(step),
                    "title": f"Step {index - 1}",
                    "narration": step,
                    "visualElements": step_elements,
                    "subtitleLines": make_subtitles(step),
                    "actions": create_teacher_actions_from_text(
                        step_elements,
                        step,
                    ),
                }
            )

    if isinstance(technical_details, list) and technical_details:
        detail_text = technical_details[0]
        detail_elements = create_visual_elements_from_text(
            detail_text,
            title,
            len(scenes) + 1,
        )

        scenes.append(
            {
                "id": f"scene_{len(scenes) + 1}",
                "sceneType": "highlight",
                "title": "Technical detail",
                "narration": detail_text,
                "visualElements": detail_elements,
                "subtitleLines": make_subtitles(detail_text),
                "actions": create_teacher_actions_from_text(
                    detail_elements,
                    detail_text,
                ),
            }
        )

    if summary:
        summary_elements = create_visual_elements_from_text(
            summary,
            title,
            len(scenes) + 1,
        )

        scenes.append(
            {
                "id": f"scene_{len(scenes) + 1}",
                "sceneType": "highlight",
                "title": "Summary",
                "narration": summary,
                "visualElements": summary_elements,
                "subtitleLines": make_subtitles(summary),
                "actions": create_teacher_actions_from_text(
                    summary_elements,
                    summary,
                ),
            }
        )

    return {"scenes": scenes[:6]}
    
def create_storyboard(question: str, explanation: dict) -> dict:
    ai_storyboard = explanation.get("_visualStoryboard")

    if not ai_storyboard:
        print("No AI storyboard available. Using explanation-based storyboard.")
        return create_explanation_based_storyboard(question, explanation)

    normalized_ai_storyboard = normalize_ai_storyboard(ai_storyboard)

    if not normalized_ai_storyboard:
        print("AI storyboard format was invalid. Using explanation-based storyboard.")
        return create_explanation_based_storyboard(question, explanation)

    if is_storyboard_quality_good(normalized_ai_storyboard):
        return normalized_ai_storyboard

    print("AI storyboard quality was weak. Using explanation-based storyboard.")
    return create_explanation_based_storyboard(question, explanation)