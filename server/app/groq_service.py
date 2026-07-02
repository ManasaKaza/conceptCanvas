import concurrent.futures
import json
import os
import time

from dotenv import load_dotenv
from groq import Groq

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

    if not lines:
        return "No previous conversation."

    return "\n".join(lines)


def build_explanation_prompt(
    question: str,
    conversation_history: list[dict] | None = None,
) -> str:
    conversation_context = build_conversation_context(conversation_history)

    return f"""
You are ConceptCanvas, an AI visual learning tutor.

Previous conversation context:
{conversation_context}

The user now asked:
{question}

Return ONLY valid JSON.
Do not include markdown.
Do not include ```json.
Do not include explanations outside JSON.

Use this exact JSON shape:
{{
  "title": "Learner-friendly title, not just one word",
  "quickMeaning": "Simple beginner-friendly meaning in 2-3 sentences.",
  "deepExplanation": "Detailed explanation in 2-4 paragraphs. Use escaped newlines if needed.",
  "stepByStep": [
    "Step 1 with clear detail",
    "Step 2 with clear detail",
    "Step 3 with clear detail",
    "Step 4 with clear detail",
    "Step 5 with clear detail"
  ],
  "realWorldExample": "A practical real-world example explained clearly.",
  "analogy": "Simple analogy that makes the concept easier to understand.",
  "technicalDetails": [
    "Technical detail 1",
    "Technical detail 2",
    "Technical detail 3",
    "Technical detail 4"
  ],
  "commonConfusions": [
    "Common confusion 1 and clarification",
    "Common confusion 2 and clarification"
  ],
  "interviewAngle": "How to explain this concept in an interview.",
  "summary": "Clear final summary in 2-3 sentences.",
  "takeaways": [
    "Takeaway 1",
    "Takeaway 2",
    "Takeaway 3"
  ],
  "followUps": [
    "Follow-up question 1",
    "Follow-up question 2",
    "Follow-up question 3"
  ]
}}

Rules:
- Give a detailed answer, not a very brief answer.
- Explain like ChatGPT would explain to a learner.
- Use beginner-friendly language first, then add technical depth.
- For technical concepts, include practical flow, real-world usage, and interview relevance.
- Do not make the title too short. Prefer "How DNS Works" instead of "DNS".
- Keep JSON valid.
- Do not include markdown.
- Do not include ```json.
- Do not use unescaped raw newlines inside JSON strings.
- If the user asks a follow-up, use the previous conversation context.
"""

def build_visual_storyboard_prompt(question: str, explanation: dict) -> str:
    return f"""
You are ConceptCanvas, an AI visual lesson designer.

The user asked:
{question}

The explanation is:
Title: {explanation.get("title")}
Quick meaning: {explanation.get("quickMeaning")}
Step by step: {explanation.get("stepByStep")}
Technical details: {explanation.get("technicalDetails")}
Summary: {explanation.get("summary")}

Create a visual storyboard for an animated lesson player.

The visual lesson should feel like a teacher explaining with diagrams.
It should not feel like random boxes being shown.
Each action label will be spoken by browser voice and shown as a live subtitle.

Return ONLY valid JSON.
Do not include markdown.
Do not include ```json.
Do not include explanations outside JSON.

Use this exact JSON shape:
{{
  "scenes": [
    {{
      "id": "scene_1",
      "sceneType": "flow",
      "title": "Short scene title",
      "narration": "Short summary of what this scene teaches.",
      "visualElements": ["element_one", "element_two", "element_three"],
      "subtitleLines": [
        "Short subtitle 1",
        "Short subtitle 2"
      ],
      "actions": [
        {{
          "type": "show",
          "target": "element_one",
          "label": "A complete teacher-like sentence explaining this visual step."
        }},
        {{
          "type": "connect",
          "fromElement": "element_one",
          "toElement": "element_two",
          "label": "A complete teacher-like sentence explaining why these two parts connect."
        }},
        {{
          "type": "highlight",
          "target": "element_two",
          "label": "A complete teacher-like sentence explaining why this part matters."
        }}
      ]
    }}
  ]
}}

Allowed sceneType values:
- flow
- stack
- compare
- timeline
- split
- highlight

Allowed action type values:
- show
- connect
- highlight
- move
- wait

Rules:
- Create 4 to 7 scenes.
- The storyboard must be specific to the user's concept.
- Do not create generic elements like "concept_box", "part_1", "part_2", "action", "result" unless truly needed.
- visualElements must be short, concept-specific snake_case names.
- Every scene should have 3 to 5 visualElements.
- Every scene should have 3 to 7 actions.
- Each action label must be a complete sentence.
- Each action label should sound like a teacher explaining, not like a UI command.
- Do not use labels like "Show browser", "Connects to", or "Important part".
- Good label example: "The browser first checks whether it already knows the IP address."
- Good label example: "If the cache does not have the answer, the request moves to the DNS resolver."
- Good label example: "This returned IP address tells the browser where the website server is located."
- Keep each action label between 10 and 24 words.
- subtitleLines should be short readable captions, not long paragraphs.
- Narration should summarize the scene, while action labels explain each animation step.
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
            {
                "role": "system",
                "content": "You are ConceptCanvas. Return only valid JSON.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

def generate_json_with_groq(prompt: str, output_label: str) -> dict:
    api_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing")

    client = Groq(api_key=api_key)

    retry_attempts = get_retry_attempts()
    retry_delay_seconds = get_retry_delay_seconds()
    timeout_seconds = get_timeout_seconds()

    last_error = None

    for attempt in range(1, retry_attempts + 1):
        try:
            print(
                f"Calling Groq for {output_label}. "
                f"Model={model_name}, attempt={attempt}"
            )

            completion = call_with_timeout(
                lambda: call_groq_model(client, model_name, prompt),
                timeout_seconds,
            )

            response_text = completion.choices[0].message.content
            parsed_response = parse_json_response(response_text)
            parsed_response["_modelUsed"] = model_name

            return parsed_response

        except Exception as error:
            print(
                f"Groq {output_label} failed. "
                f"Model={model_name}, attempt={attempt}. Error: {error}"
            )
            last_error = error

            if attempt < retry_attempts:
                time.sleep(retry_delay_seconds * attempt)

    raise RuntimeError(f"Groq {output_label} failed. Last error: {last_error}")

def generate_explanation_with_groq(
    question: str,
    conversation_history: list[dict] | None = None,
) -> dict:
    prompt = build_explanation_prompt(question, conversation_history)

    return generate_json_with_groq(
        prompt=prompt,
        output_label="explanation",
    )

def generate_visual_storyboard_with_groq(
    question: str,
    explanation: dict,
) -> dict:
    prompt = build_visual_storyboard_prompt(question, explanation)

    return generate_json_with_groq(
        prompt=prompt,
        output_label="visual storyboard",
    )