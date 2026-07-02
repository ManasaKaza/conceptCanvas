BLOCKED_PATTERNS = [
    {
        "type": "prediction",
        "keywords": ["who will win", "predict", "future", "tomorrow", "next election"],
        "message": "ConceptCanvas works best for explaining concepts, not predicting future events.",
        "suggestions": [
            "How do elections work?",
            "What is probability?",
            "How does forecasting work?",
        ],
    },
    {
        "type": "current_news",
        "keywords": ["latest news", "today's news", "current news", "breaking news"],
        "message": "ConceptCanvas is focused on explaining concepts, not live or current news.",
        "suggestions": [
            "How does journalism work?",
            "What is media literacy?",
            "How does information spread online?",
        ],
    },
    {
        "type": "financial_advice",
        "keywords": ["what stock should i buy", "which stock to buy", "should i invest"],
        "message": "ConceptCanvas can explain financial concepts, but it does not give personal investment advice.",
        "suggestions": [
            "What is stock market?",
            "How does compounding work?",
            "What is risk diversification?",
        ],
    },
    {
        "type": "opinion",
        "keywords": ["what do you think about", "is this person good", "who is better"],
        "message": "ConceptCanvas works best for learning concepts, not judging people or giving subjective opinions.",
        "suggestions": [
            "What is critical thinking?",
            "How do comparisons work?",
            "What is bias?",
        ],
    },
]


def classify_question(question: str) -> dict:
    normalized_question = question.lower().strip()

    for pattern in BLOCKED_PATTERNS:
        for keyword in pattern["keywords"]:
            if keyword in normalized_question:
                return {
                    "topicType": "declined",
                    "declineType": pattern["type"],
                    "message": pattern["message"],
                    "suggestions": pattern["suggestions"],
                }

    return {
        "topicType": "concept_explanation",
        "declineType": None,
        "message": None,
        "suggestions": [],
    }