from __future__ import annotations

import concurrent.futures
import json
import os
import time

from dotenv import load_dotenv
from app.storyboard_repair_service import build_storyboard_repair_prompt
try:
    from groq import Groq
except ImportError:  # Provider dependency is optional when AI is disabled.
    Groq = None

load_dotenv()


def build_conversation_context(conversation_history: list[dict] | None) -> str:
    if not conversation_history:
        return "No previous conversation."

    recent_messages = conversation_history[-6:]
    lines = []
    for message in recent_messages:
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
    conversation_context = build_conversation_context(conversation_history)
    structure_text = ", ".join(requested_structure or []) or "No extra structure requested"

    return f"""
You are ConceptCanvas, an AI visual learning tutor.

Previous conversation context:
{conversation_context}

The user now asked:
{question}

Lesson settings:
- Audience level: {audience_level}
- Explanation depth: {explanation_depth}
- Additional requested structure: {structure_text}

Return ONLY valid JSON. Do not include markdown or text outside JSON.

Use this exact JSON shape:
{{
  "title": "Learner-friendly title, not just one word",
  "quickMeaning": "Simple meaning in 2-3 sentences.",
  "deepExplanation": "Detailed explanation with depth appropriate for the selected audience.",
  "stepByStep": [
    "Clear explanatory step 1",
    "Clear explanatory step 2",
    "Clear explanatory step 3",
    "Clear explanatory step 4",
    "Clear explanatory step 5"
  ],
  "realWorldExample": "A practical example explained clearly.",
  "analogy": "A simple and accurate analogy.",
  "technicalDetails": [
    "Technical detail 1",
    "Technical detail 2",
    "Technical detail 3"
  ],
  "commonConfusions": [
    "Common confusion and clarification 1",
    "Common confusion and clarification 2"
  ],
  "interviewAngle": "How to explain this concept in an interview.",
  "summary": "Clear final summary in 2-3 sentences.",
  "takeaways": ["Takeaway 1", "Takeaway 2", "Takeaway 3"],
  "followUps": ["Follow-up 1", "Follow-up 2", "Follow-up 3"]
}}

Rules:
- Follow the selected audience level and explanation depth.
- Respect additional requested structure when it is relevant.
- Begin simply, then add technical depth.
- Do not invent benefits, guarantees, or causal claims.
- Distinguish normal behaviour, tradeoffs, and limitations.
- Include practical flow, real-world use, and interview relevance for technical topics.
- Keep JSON valid and use escaped newlines inside strings when needed.
"""


def build_visual_storyboard_prompt(
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


def get_timeout_seconds() -> int:
    return int(os.getenv("AI_TIMEOUT_SECONDS", "20"))


def get_retry_attempts() -> int:
    return int(os.getenv("AI_RETRY_ATTEMPTS", "1"))


def get_retry_delay_seconds() -> float:
    return float(os.getenv("AI_RETRY_DELAY_SECONDS", "1"))


def call_with_timeout(callable_function, timeout_seconds: int):
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(callable_function)
    try:
        return future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError as error:
        future.cancel()
        raise TimeoutError(
            f"Groq request timed out after {timeout_seconds} seconds"
        ) from error
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def call_groq_model(client: Groq, model_name: str, prompt: str):
    return client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are ConceptCanvas. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )


def generate_json_with_groq(prompt: str, output_label: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    if Groq is None:
        raise RuntimeError("The groq package is not installed")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing")

    client = Groq(api_key=api_key)
    last_error = None

    for attempt in range(1, get_retry_attempts() + 1):
        try:
            print(f"Calling Groq for {output_label}. Model={model_name}, attempt={attempt}")
            completion = call_with_timeout(
                lambda: call_groq_model(client, model_name, prompt),
                get_timeout_seconds(),
            )
            parsed_response = parse_json_response(completion.choices[0].message.content)
            parsed_response["_modelUsed"] = model_name
            return parsed_response
        except Exception as error:
            print(
                f"Groq {output_label} failed. Model={model_name}, "
                f"attempt={attempt}. Error: {error}"
            )
            last_error = error
            if attempt < get_retry_attempts():
                time.sleep(get_retry_delay_seconds() * attempt)

    raise RuntimeError(f"Groq {output_label} failed. Last error: {last_error}")


def generate_explanation_with_groq(
    question: str,
    conversation_history: list[dict] | None = None,
    audience_level: str = "beginner",
    explanation_depth: str = "standard",
    requested_structure: list[str] | None = None,
) -> dict:
    return generate_json_with_groq(
        prompt=build_explanation_prompt(
            question,
            conversation_history,
            audience_level,
            explanation_depth,
            requested_structure,
        ),
        output_label="explanation",
    )


def generate_visual_storyboard_with_groq(
    question: str,
    explanation: dict,
    requested_scene_count: int,
    audience_level: str = "beginner",
) -> dict:
    return generate_json_with_groq(
        prompt=build_visual_storyboard_prompt(
            question,
            explanation,
            requested_scene_count,
            audience_level,
        ),
        output_label="visual storyboard",
    )


def repair_visual_storyboard_with_groq(
    question: str,
    explanation: dict,
    requested_scene_count: int,
    audience_level: str,
    candidate_storyboard: dict,
    issues: list[str],
) -> dict:
    return generate_json_with_groq(
        prompt=build_storyboard_repair_prompt(
            question=question,
            explanation=explanation,
            requested_scene_count=requested_scene_count,
            audience_level=audience_level,
            candidate_storyboard=candidate_storyboard,
            issues=issues,
        ),
        output_label="visual storyboard repair",
    )
