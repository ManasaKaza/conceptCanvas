from app.explanation_service import create_title_from_question


def ensure_string(value, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()

    return fallback


def ensure_string_list(value, fallback: list[str], max_items: int = 8) -> list[str]:
    if not isinstance(value, list):
        return fallback

    cleaned_items = []

    for item in value:
        if isinstance(item, str) and item.strip():
            cleaned_items.append(item.strip())

    if not cleaned_items:
        return fallback

    return cleaned_items[:max_items]


def normalize_explanation(raw_explanation: dict, question: str) -> dict:
    if not isinstance(raw_explanation, dict):
        raw_explanation = {}

    title = ensure_string(
        raw_explanation.get("title"),
        create_title_from_question(question),
    )

    quick_meaning = ensure_string(
        raw_explanation.get("quickMeaning"),
        "This concept can be understood by breaking it into smaller parts.",
    )

    deep_explanation = ensure_string(
        raw_explanation.get("deepExplanation"),
        (
            "This concept needs a deeper explanation because it connects multiple "
            "small ideas. Start with the basic meaning, then understand how each "
            "part works together in a real situation."
        ),
    )

    step_by_step = ensure_string_list(
        raw_explanation.get("stepByStep"),
        [
            "Start with the basic meaning of the concept.",
            "Identify the main parts involved.",
            "Understand how those parts interact with each other.",
            "Connect the concept to a real-world example.",
            "Review the key takeaway in simple words.",
        ],
        max_items=8,
    )

    real_world_example = ensure_string(
        raw_explanation.get("realWorldExample"),
        "A real-world example helps connect the concept to something practical.",
    )

    analogy = ensure_string(
        raw_explanation.get("analogy"),
        (
            "Think of it like understanding a machine: first learn each part, "
            "then see how the parts work together."
        ),
    )

    technical_details = ensure_string_list(
        raw_explanation.get("technicalDetails"),
        [
            "The concept has multiple parts that work together.",
            "Each part has a specific role in the overall flow.",
            "Understanding the flow makes the concept easier to remember.",
        ],
        max_items=8,
    )

    common_confusions = ensure_string_list(
        raw_explanation.get("commonConfusions"),
        [
            "Learners often confuse the definition with the full working flow.",
            "The concept becomes clearer when explained with an example.",
        ],
        max_items=6,
    )

    interview_angle = ensure_string(
        raw_explanation.get("interviewAngle"),
        (
            "In interviews, explain the concept with a simple definition, "
            "a practical flow, tradeoffs if any, and one real-world example."
        ),
    )

    summary = ensure_string(
        raw_explanation.get("summary"),
        "In short, this concept becomes easier when broken into simple steps.",
    )

    takeaways = ensure_string_list(
        raw_explanation.get("takeaways"),
        [
            "Break complex ideas into smaller parts.",
            "Understand the flow, not just the definition.",
            "Use examples to make the concept easier to remember.",
        ],
        max_items=6,
    )

    follow_ups = ensure_string_list(
        raw_explanation.get("followUps"),
        [
            "Explain this with a real-world example",
            "Explain this visually",
            "Explain this from an interview perspective",
        ],
        max_items=4,
    )

    normalized = {
        "title": title,
        "quickMeaning": quick_meaning,
        "deepExplanation": deep_explanation,
        "stepByStep": step_by_step,
        "realWorldExample": real_world_example,
        "analogy": analogy,
        "technicalDetails": technical_details,
        "commonConfusions": common_confusions,
        "interviewAngle": interview_angle,
        "summary": summary,
        "takeaways": takeaways,
        "followUps": follow_ups,
    }

    visual_storyboard = raw_explanation.get("visualStoryboard")

    if isinstance(visual_storyboard, dict):
        normalized["_visualStoryboard"] = visual_storyboard

    if "_modelUsed" in raw_explanation:
        normalized["_modelUsed"] = raw_explanation["_modelUsed"]

    return normalized