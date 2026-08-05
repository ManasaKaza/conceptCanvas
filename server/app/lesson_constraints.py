import re


NUMBER_WORDS = {
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
}


def extract_scene_count(question: str) -> int | None:
    lowered = question.lower()

    numeric_match = re.search(
        r"\b(?:exactly\s+|in\s+|using\s+|with\s+)?(\d{1,2})\s+(?:[a-z-]+\s+){0,3}scenes?\b",
        lowered,
    )
    if numeric_match:
        count = int(numeric_match.group(1))
        if count < 3 or count > 7:
            raise ValueError("Visual lessons currently support between 3 and 7 scenes.")
        return count

    word_pattern = "|".join(NUMBER_WORDS)
    word_match = re.search(
        rf"\b(?:exactly\s+|in\s+|using\s+|with\s+)?({word_pattern})\s+(?:[a-z-]+\s+){{0,3}}scenes?\b",
        lowered,
    )
    if word_match:
        return NUMBER_WORDS[word_match.group(1)]

    return None


def resolve_scene_count(question: str, requested_scene_count: int | None) -> int:
    if requested_scene_count is not None:
        return requested_scene_count

    return extract_scene_count(question) or 5
