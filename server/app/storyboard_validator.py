ALLOWED_SCENE_TYPES = {
    "flow",
    "stack",
    "compare",
    "timeline",
    "split",
    "highlight",
}


def ensure_string(value, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return fallback


def ensure_string_list(value, fallback: list[str], max_items: int = 5) -> list[str]:
    if not isinstance(value, list):
        return fallback

    cleaned_items = []

    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned_items.append(item.strip())

    if not cleaned_items:
        return fallback

    return cleaned_items[:max_items]


def normalize_scene(raw_scene: dict, index: int) -> dict:
    if not isinstance(raw_scene, dict):
        raw_scene = {}

    scene_type = raw_scene.get("sceneType")

    if scene_type not in ALLOWED_SCENE_TYPES:
        scene_type = "highlight"

    title = ensure_string(
        raw_scene.get("title"),
        f"Scene {index + 1}",
    )

    narration = ensure_string(
        raw_scene.get("narration"),
        "This scene explains one important part of the concept.",
    )

    visual_elements = ensure_string_list(
        raw_scene.get("visualElements"),
        ["main_idea", "supporting_part", "example"],
        max_items=6,
    )

    subtitle_lines = ensure_string_list(
        raw_scene.get("subtitleLines"),
        [narration],
        max_items=3,
    )

    return {
        "id": ensure_string(raw_scene.get("id"), f"scene_{index + 1}"),
        "sceneType": scene_type,
        "title": title,
        "narration": narration,
        "visualElements": visual_elements,
        "subtitleLines": subtitle_lines,
    }


def normalize_storyboard(raw_storyboard: dict) -> dict:
    if not isinstance(raw_storyboard, dict):
        raw_storyboard = {}

    raw_scenes = raw_storyboard.get("scenes")

    if not isinstance(raw_scenes, list) or len(raw_scenes) == 0:
        raw_scenes = [
            {
                "id": "scene_1",
                "sceneType": "flow",
                "title": "Break the concept into parts",
                "narration": "Start by breaking the concept into smaller parts.",
                "visualElements": ["concept_box", "part_1", "part_2"],
                "subtitleLines": ["Break the concept", "into smaller parts"],
            },
            {
                "id": "scene_2",
                "sceneType": "highlight",
                "title": "Focus on the main idea",
                "narration": "Then focus on the main idea that connects everything.",
                "visualElements": ["main_idea", "highlight_ring"],
                "subtitleLines": ["Focus on", "the main idea"],
            },
        ]

    normalized_scenes = []

    for index, scene in enumerate(raw_scenes[:6]):
        normalized_scenes.append(normalize_scene(scene, index))

    return {
        "scenes": normalized_scenes,
    }