from __future__ import annotations

import concurrent.futures
import json
import os
import time

from dotenv import load_dotenv
from app.storyboard_repair_service import build_storyboard_repair_prompt
try:
    from google import genai
except ImportError:  # Provider dependency is optional when AI is disabled.
    genai = None

load_dotenv()


def build_conversation_context(conversation_history: list[dict] | None) -> str:
    if not conversation_history:
        return "No previous conversation."

    lines = []
    for message in conversation_history[-6:]:
        role = message.get("role", "user")
        content = message.get("content", "")
        if isinstance(content, str) and content.strip():
            lines.append(f"{role}: {content.strip()}")
    return "\n".join(lines) or "No previous conversation."


def build_explanation_prompt(
    question: str,
    conversation_history: list[dict] | None = None,
    audience_level: str = "beginner",
    explanation_depth: str = "standard",
    requested_structure: list[str] | None = None,
) -> str:
    context = build_conversation_context(conversation_history)
    structure_text = ", ".join(requested_structure or []) or "No extra structure requested"

    return f"""
You are ConceptCanvas, an AI visual learning tutor.

Previous conversation context:
{context}

Question: {question}
Audience level: {audience_level}
Explanation depth: {explanation_depth}
Additional requested structure: {structure_text}

Return ONLY valid JSON with this exact shape:
{{
  "title": "Learner-friendly title",
  "quickMeaning": "Simple meaning in 2-3 sentences.",
  "deepExplanation": "Detailed explanation appropriate for the settings.",
  "stepByStep": ["Step 1", "Step 2", "Step 3", "Step 4", "Step 5"],
  "realWorldExample": "Practical example.",
  "analogy": "Simple accurate analogy.",
  "technicalDetails": ["Detail 1", "Detail 2", "Detail 3"],
  "commonConfusions": ["Confusion and clarification 1", "Confusion and clarification 2"],
  "interviewAngle": "Interview explanation.",
  "summary": "Final summary.",
  "takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],
  "followUps": ["Follow-up 1", "Follow-up 2", "Follow-up 3"]
}}

Do not include markdown or text outside JSON. Do not invent technical benefits or guarantees.
"""


def build_storyboard_prompt(
    question: str,
    explanation: dict,
    requested_scene_count: int,
    audience_level: str = "beginner",
) -> str:
    return f"""
You are ConceptCanvas, an AI visual lesson planner.

The user asked:
{question}

Audience level: {audience_level}
Required scene count: exactly {requested_scene_count}

Explanation context:
Title: {explanation.get("title")}
Quick meaning: {explanation.get("quickMeaning")}
Step by step: {explanation.get("stepByStep")}
Technical details: {explanation.get("technicalDetails")}
Example: {explanation.get("realWorldExample")}
Summary: {explanation.get("summary")}

Create a scene-by-scene lesson using the ConceptCanvas LessonV2 visual grammar.
First identify the knowledge shape: process, interaction, hierarchy, structure,
comparison, chronology, cycle, state change, cause-effect, quantitative relationship,
spatial relationship, code execution, classification, or concept relationship.
Then choose the reusable visual archetype that teaches that structure most clearly.
Do not choose a diagram because of the subject name alone, and do not return generic
labels arranged as decorative boxes.

Return ONLY valid JSON. Do not include markdown or text outside JSON.

Use this exact shape:
{{
  "scenes": [
    {{
      "id": "scene_1",
      "title": "Descriptive title without Step 1 or Scene 1",
      "narration": "A clear scene-level explanation matching the visual.",
      "visual": {{
        "schemaVersion": "2.0",
        "diagramType": "hierarchy",
        "orientation": "top_to_bottom",
        "elements": [
          {{
            "type": "node",
            "id": "recursive_resolver",
            "label": "Recursive resolver",
            "nodeKind": "service",
            "detail": "Finds the DNS answer for the browser"
          }},
          {{
            "type": "node",
            "id": "root_server",
            "label": "Root DNS server",
            "nodeKind": "server"
          }},
          {{
            "type": "edge",
            "id": "resolver_to_root",
            "fromId": "recursive_resolver",
            "toId": "root_server",
            "relation": "request",
            "label": "Where is .com?",
            "directed": true
          }}
        ]
      }},
      "narrationSegments": [
        {{
          "id": "segment_1",
          "order": 1,
          "spokenText": "The recursive resolver asks a root server where dot com domains are managed.",
          "subtitleText": "The resolver asks the DNS root",
          "targetElementIds": ["recursive_resolver", "root_server", "resolver_to_root"],
          "action": "trace",
          "estimatedDurationMs": 4200
        }}
      ]
    }}
  ]
}}

Allowed diagramType values:
flow, sequence, hierarchy, stack, tree, comparison, timeline, architecture,
state_transition, cycle, cause_effect, concept_map, formula, code_execution, spatial.

Allowed orientation values:
left_to_right, top_to_bottom, stacked, two_column, radial.

Allowed nodeKind values:
actor, client, server, service, cache, database, process, decision, data,
packet, stack_frame, tree_node, bucket, queue, code, output, entity, event, state,
component, category, organism, place, quantity, formula, example, generic.

Allowed edge relation values:
flows_to, request, response, calls, returns, reads, writes, contains, routes_to,
transforms, compares, depends_on, causes, precedes, part_of, changes_into, activates,
inhibits, supports, contrasts, located_in, increases, decreases.

Allowed narration action values:
reveal, highlight, trace, deemphasize, pause.

Rules:
- Return exactly {requested_scene_count} scenes, no more and no fewer.
- Use IDs scene_1 through scene_{requested_scene_count} in order.
- Do not put numbering inside scene titles.
- Each scene needs at least two typed nodes.
- Use stable lowercase snake_case IDs unique within each scene.
- Every edge must reference node IDs declared in the same scene.
- Every narration target must reference a declared node, edge, group, or annotation.
- Use segment_1, segment_2, and so on in exact order within every scene.
- Narration must explain the visible relationship, not issue UI commands.
- Prefer one coherent diagram that progresses across scenes when the knowledge structure is continuous.
- Use timeline for chronology, comparison for contrasting alternatives, formula for quantitative relationships,
  architecture or concept_map for parts and relationships, and spatial only for schematic spatial relationships.
- Never invent geographic shapes, quantitative values, or scientific mechanisms that are absent from the explanation.
- Do not generate visualElements, subtitleLines, actions, or sceneType; the backend derives temporary compatibility fields.
- Do not use fallback as a diagram type.
- Keep JSON valid.
"""

def parse_json_response(text: str) -> dict:
    cleaned_text = text.strip()
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text.replace("```json", "", 1).strip()
    if cleaned_text.startswith("```"):
        cleaned_text = cleaned_text.replace("```", "", 1).strip()
    if cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[:-3].strip()
    return json.loads(cleaned_text)


def get_model_fallbacks() -> list[str]:
    models = os.getenv("GEMINI_MODELS", "gemini-2.5-flash,gemini-2.5-flash-lite")
    return [model.strip() for model in models.split(",") if model.strip()]


def get_timeout_seconds() -> int:
    return int(os.getenv("GEMINI_TIMEOUT_SECONDS", "25"))


def get_retry_attempts() -> int:
    return int(os.getenv("GEMINI_RETRY_ATTEMPTS", "2"))


def get_retry_delay_seconds() -> float:
    return float(os.getenv("GEMINI_RETRY_DELAY_SECONDS", "1"))


def call_with_timeout(callable_function, timeout_seconds: int):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(callable_function)
    try:
        return future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError as error:
        future.cancel()
        raise TimeoutError(
            f"Gemini request timed out after {timeout_seconds} seconds"
        ) from error
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def call_gemini_model(client, model_name: str, prompt: str):
    return client.interactions.create(model=model_name, input=prompt)


def generate_json_with_gemini(prompt: str, output_label: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if genai is None:
        raise RuntimeError("The google-genai package is not installed")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")

    client = genai.Client(api_key=api_key)
    last_error = None

    for model_name in get_model_fallbacks():
        for attempt in range(1, get_retry_attempts() + 1):
            try:
                print(
                    f"Calling Gemini for {output_label}. "
                    f"Model={model_name}, attempt={attempt}"
                )
                interaction = call_with_timeout(
                    lambda: call_gemini_model(client, model_name, prompt),
                    get_timeout_seconds(),
                )
                parsed_response = parse_json_response(interaction.output_text)
                parsed_response["_modelUsed"] = model_name
                return parsed_response
            except Exception as error:
                print(
                    f"Gemini {output_label} failed. Model={model_name}, "
                    f"attempt={attempt}. Error: {error}"
                )
                last_error = error
                if attempt < get_retry_attempts():
                    time.sleep(get_retry_delay_seconds() * attempt)

    raise RuntimeError(
        f"All Gemini models failed for {output_label}. Last error: {last_error}"
    )


def generate_explanation_with_gemini(
    question: str,
    conversation_history: list[dict] | None = None,
    audience_level: str = "beginner",
    explanation_depth: str = "standard",
    requested_structure: list[str] | None = None,
) -> dict:
    return generate_json_with_gemini(
        build_explanation_prompt(
            question,
            conversation_history,
            audience_level,
            explanation_depth,
            requested_structure,
        ),
        "explanation",
    )


def generate_storyboard_with_gemini(
    question: str,
    explanation: dict,
    requested_scene_count: int,
    audience_level: str = "beginner",
) -> dict:
    return generate_json_with_gemini(
        build_storyboard_prompt(
            question,
            explanation,
            requested_scene_count,
            audience_level,
        ),
        "storyboard",
    )


def repair_storyboard_with_gemini(
    question: str,
    explanation: dict,
    requested_scene_count: int,
    audience_level: str,
    candidate_storyboard: dict,
    issues: list[str],
) -> dict:
    return generate_json_with_gemini(
        build_storyboard_repair_prompt(
            question=question,
            explanation=explanation,
            requested_scene_count=requested_scene_count,
            audience_level=audience_level,
            candidate_storyboard=candidate_storyboard,
            issues=issues,
        ),
        "storyboard repair",
    )
