from __future__ import annotations

import re
from collections import Counter

from app.models import LessonPlanningProfile


DOMAIN_KEYWORDS = {
    "computing": {
        "algorithm", "api", "cache", "cloud", "code", "computer", "cpu", "database", "dns",
        "docker", "http", "internet", "java", "javascript", "kubernetes", "memory",
        "network", "operating system", "python", "server", "software", "sql", "web",
        "recursion", "recursive", "binary search", "merge sort", "sorting", "stack frame",
        "data structure", "program execution", "data", "dashboard", "wearable",
    },
    "mathematics": {
        "algebra", "calculus", "derivative", "equation", "formula", "function", "geometry",
        "integral", "matrix", "probability", "statistics", "theorem", "vector",
        "mean", "median", "average", "number", "polynomial",
    },
    "natural_science": {
        "atom", "biology", "blood", "cell", "chemical", "chemistry", "circulation", "dna", "ecology", "electricity",
        "energy", "force", "gene", "heart", "lung", "molecule", "organ", "physics", "planet", "reaction",
        "water cycle", "ecosystem", "habitat", "solar system", "climate", "health", "sensor",
    },
    "social_science": {
        "economics", "government", "inflation", "market", "policy", "psychology", "society",
        "sociology", "supply", "demand", "economic", "election", "voter", "ballot",
        "conditioning", "public policy", "civic",
    },
    "humanities": {
        "art", "culture", "empire", "history", "language", "literature", "philosophy",
        "revolution", "war", "story", "narrative", "rationalism", "empiricism",
    },
    "business": {
        "business", "customer", "finance", "marketing", "operations", "product", "revenue",
        "sales", "startup", "strategy", "supply chain", "manufacturer", "distributor",
        "subscription", "transaction revenue",
    },
    "everyday": {
        "cooking", "habit", "home", "money", "sleep", "travel", "weather",
        "household", "budget", "expense", "bread",
    },
}

SHAPE_CUES = {
    "comparison": ("compare", "comparison", "difference between", "versus", " vs ", "better than"),
    "chronology": ("history", "timeline", "evolution", "over time", "century", "year", "revolution"),
    "cycle": ("cycle", "repeats", "loop", "circulation", "recycle", "season"),
    "cause_effect": ("cause", "effect", "impact", "why does", "leads to", "results in", "because"),
    "hierarchy": ("hierarchy", "levels", "tree", "parent", "child", "rank", "taxonomy"),
    "classification": ("types of", "categories", "classify", "classification", "kinds of"),
    "structure": ("structure", "anatomy", "parts of", "components", "architecture", "inside"),
    "state_change": ("state", "transition", "lifecycle", "life cycle", "phase", "status"),
    "quantitative": ("formula", "equation", "calculate", "graph", "rate", "slope"),
    "spatial": ("geographic map", "map of", "location", "geography", "region", "country", "route"),
    "stack": ("call stack", "stack frame", "push", "pop", "nested call", "unwind"),
    "code_execution": ("code", "program", "algorithm", "execute", "trace", "debug", "function call"),
    "interaction": ("communicate", "interaction", "request", "response", "between", "exchange", "sequence"),
    "process": ("how does", "how do", "process", "steps", "work", "flow", "from start to finish", "transform"),
    "concept_relationship": ("relationship", "relate", "connects", "maps"),
}

ARCHETYPE_BY_SHAPE = {
    "process": "flow",
    "interaction": "sequence",
    "hierarchy": "hierarchy",
    "structure": "architecture",
    "comparison": "comparison",
    "chronology": "timeline",
    "cycle": "cycle",
    "state_change": "state_transition",
    "cause_effect": "cause_effect",
    "quantitative": "formula",
    "spatial": "spatial",
    "code_execution": "code_execution",
    "stack": "stack",
    "classification": "tree",
    "concept_relationship": "concept_map",
}

# These renderers are reusable archetypes, not topic-specific templates.
SPECIALIZED_RENDERERS = {
    "flow", "sequence", "hierarchy", "stack", "tree", "comparison", "timeline",
    "architecture", "state_transition", "cycle", "cause_effect", "concept_map",
    "formula", "code_execution",
}


def _normalize_text(question: str, explanation: dict) -> str:
    values = [question]
    for key in (
        "title", "quickMeaning", "deepExplanation", "realWorldExample", "analogy", "summary",
    ):
        value = explanation.get(key)
        if isinstance(value, str):
            values.append(value)
    for key in ("stepByStep", "technicalDetails", "commonConfusions", "takeaways"):
        value = explanation.get(key)
        if isinstance(value, list):
            values.extend(item for item in value if isinstance(item, str))
    return " ".join(values).lower()


def _contains_keyword(text: str, keyword: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def _contains_cue(text: str, cue: str) -> bool:
    if _contains_keyword(text, cue):
        return True
    if " " in cue or not cue.isalpha() or len(cue) < 4:
        return False
    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(cue)
        + r"(?:s|es|ed|ing)?(?![a-z0-9])"
    )
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def classify_subject_domain(question: str, explanation: dict) -> tuple[str, float]:
    text = _normalize_text(question, explanation)
    question_text = question.lower()
    title_text = str(explanation.get("title", "")).lower()
    scores = Counter()
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            phrase_bonus = 2 if " " in keyword else 0
            if _contains_keyword(question_text, keyword):
                score += 4 + phrase_bonus
            elif _contains_keyword(title_text, keyword):
                score += 2 + phrase_bonus
            elif _contains_keyword(text, keyword):
                score += 1 + (1 if " " in keyword else 0)
        scores[domain] = score

    if not scores or max(scores.values(), default=0) == 0:
        return "unknown", 0.35

    ranked = scores.most_common(2)
    best_domain, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0
    if (
        (best_score == second_score and best_score >= 4)
        or (best_score >= 8 and second_score >= 4 and second_score / best_score >= 0.45)
    ):
        return "interdisciplinary", 0.7
    return best_domain, min(0.95, 0.55 + best_score * 0.08)


def infer_knowledge_shapes(question: str, explanation: dict) -> list[str]:
    text = _normalize_text(question, explanation)
    scored: list[tuple[int, str]] = []
    if extract_formula(f"{question} {text}") or re.search(r"[A-Za-z]\s*=\s*[^,.;]+", question):
        scored.append((8, "quantitative"))
    for shape, cues in SHAPE_CUES.items():
        score = 0
        for cue in cues:
            if _contains_cue(question.lower(), cue):
                score += 2
            elif _contains_cue(text, cue):
                score += 1
        if score:
            if shape == "classification" and any(
                _contains_cue(question.lower(), cue) for cue in cues
            ):
                score += 1
            scored.append((score, shape))

    scored.sort(key=lambda item: (-item[0], list(SHAPE_CUES).index(item[1])))
    shapes: list[str] = []
    for _, shape in scored:
        if shape not in shapes:
            shapes.append(shape)
        if len(shapes) >= 4:
            break
    if not shapes:
        shapes = ["concept_relationship"]
    elif "process" not in shapes and isinstance(explanation.get("stepByStep"), list) and len(explanation["stepByStep"]) >= 3:
        shapes.append("process")
    return shapes[:4]


def plan_lesson(question: str, explanation: dict) -> dict:
    domain, domain_confidence = classify_subject_domain(question, explanation)
    shapes = infer_knowledge_shapes(question, explanation)
    primary = ARCHETYPE_BY_SHAPE[shapes[0]]
    secondary = []
    for shape in shapes[1:]:
        archetype = ARCHETYPE_BY_SHAPE[shape]
        if archetype != primary and archetype not in secondary:
            secondary.append(archetype)

    support = "specialized" if primary in SPECIALIZED_RENDERERS else "schematic"
    limitations: list[str] = []
    if primary == "spatial":
        support = "schematic"
        limitations.append(
            "Spatial lessons currently use a relationship schematic; geographic maps require verified map data."
        )
    if domain == "unknown":
        limitations.append(
            "The subject domain was uncertain, so the planner prioritised the detected knowledge structure."
        )

    confidence = min(0.96, max(0.4, domain_confidence + (0.08 if len(shapes) > 1 else 0)))
    rationale = (
        f"The lesson is treated as {', '.join(shape.replace('_', ' ') for shape in shapes)} "
        f"knowledge, so {primary.replace('_', ' ')} is the primary reusable visual archetype."
    )
    profile = LessonPlanningProfile(
        subjectDomain=domain,
        knowledgeShapes=shapes,
        primaryArchetype=primary,
        secondaryArchetypes=secondary,
        rationale=rationale,
        confidence=round(confidence, 2),
        rendererSupport=support,
        limitations=limitations,
    )
    return profile.model_dump()


def select_scene_archetype(profile: dict, scene_title: str, narration: str) -> str:
    primary = profile["primaryArchetype"]
    if primary in {
        "comparison", "timeline", "cycle", "formula", "code_execution",
        "stack", "spatial", "hierarchy", "tree",
    }:
        return primary

    local_text = f"{scene_title} {narration}".lower()
    local_candidates: list[tuple[str, tuple[str, ...]]] = [
        ("comparison", SHAPE_CUES["comparison"]),
        ("cause_effect", SHAPE_CUES["cause_effect"]),
        ("timeline", SHAPE_CUES["chronology"]),
        ("cycle", SHAPE_CUES["cycle"]),
        ("state_transition", SHAPE_CUES["state_change"]),
        ("formula", SHAPE_CUES["quantitative"]),
        ("stack", SHAPE_CUES["stack"]),
        ("code_execution", SHAPE_CUES["code_execution"]),
        ("hierarchy", SHAPE_CUES["hierarchy"] + SHAPE_CUES["classification"]),
        ("architecture", SHAPE_CUES["structure"]),
        ("sequence", SHAPE_CUES["interaction"]),
    ]
    for archetype, cues in local_candidates:
        if any(cue in local_text for cue in cues):
            return archetype
    return primary


def extract_comparison_subjects(question: str) -> tuple[str, str] | None:
    patterns = [
        r"difference between\s+(.+?)\s+and\s+(.+?)(?:\?|$)",
        r"compare\s+(.+?)\s+(?:vs\.?|versus)\s+(.+?)(?:\?|$)",
        r"compare\s+(.+?)\s+(?:and|with|to)\s+(.+?)(?:\?|$)",
        r"(.+?)\s+(?:vs\.?|versus)\s+(.+?)(?:\?|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, question, flags=re.IGNORECASE)
        if match:
            left = re.sub(r"^compare\s+", "", match.group(1), flags=re.IGNORECASE).strip(" .,-")[:70]
            right = match.group(2).strip(" .,-")[:70]
            if left and right:
                return left, right
    return None


def extract_formula(text: str) -> str | None:
    candidates = re.findall(
        r"(?:[A-Za-z][A-Za-z0-9_]*(?:\([^)]*\))?\s*=\s*[^.;\n]{1,80})",
        text,
    )
    if candidates:
        return candidates[0].strip()
    return None
