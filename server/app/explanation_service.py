from app.fake_data import FAKE_EXPLANATIONS, GENERIC_EXPLANATION


def normalize_question(question: str) -> str:
    return question.lower().strip()


def get_fake_explanation(question: str) -> dict:
    title = create_title_from_question(question)

    return {
        "title": title,
        "quickMeaning": (
            f"{title} is a concept that becomes easier to understand when "
            "we break it into smaller parts and connect it with an example."
        ),
        "deepExplanation": (
            f"{title} can be understood by first learning what it means, "
            "then understanding the main parts involved, and finally seeing "
            "how those parts work together in a real situation.\n\n"
            "This fallback explanation is used when AI is unavailable, but it "
            "still keeps the learning structure clear."
        ),
        "stepByStep": [
            "Start with the basic meaning of the concept.",
            "Identify the main parts involved.",
            "Understand how the parts interact with each other.",
            "Connect the idea with a simple example.",
            "Review the key takeaway.",
        ],
        "realWorldExample": (
            "For example, when learning a technical concept, it helps to connect "
            "it to something you have seen in real applications or daily usage."
        ),
        "analogy": (
            "Think of it like learning how a machine works: first understand each "
            "part, then understand how the parts work together."
        ),
        "technicalDetails": [
            "The concept usually has multiple parts working together.",
            "The flow between these parts is important.",
            "Understanding the flow makes the concept easier to apply.",
        ],
        "commonConfusions": [
            "Learners may remember only the definition but miss the working flow.",
            "Learners may confuse similar concepts if examples are not used.",
        ],
        "interviewAngle": (
            "In interviews, explain the definition, the flow, a real-world example, "
            "and any tradeoffs if relevant."
        ),
        "summary": (
            f"In short, {title} becomes easier when explained through meaning, "
            "steps, examples, and visuals."
        ),
        "takeaways": [
            "Understand the basic meaning first.",
            "Focus on the flow of how it works.",
            "Use examples to remember it better.",
        ],
        "followUps": [
            "Explain this with a practical example",
            "Explain this visually",
            "Explain this from an interview perspective",
        ],
    }
    
def create_title_from_question(question: str) -> str:
    cleaned_question = question.strip().rstrip("?")

    prefixes = [
        "explain ",
        "what is ",
        "what are ",
        "how does ",
        "how do ",
    ]

    lowered = cleaned_question.lower()

    for prefix in prefixes:
        if lowered.startswith(prefix):
            cleaned_question = cleaned_question[len(prefix):]
            break

    if not cleaned_question:
        return "Concept Explanation"

    return cleaned_question[:1].upper() + cleaned_question[1:]