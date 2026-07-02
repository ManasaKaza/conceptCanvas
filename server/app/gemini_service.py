import concurrent.futures
import json
import os
import time

from dotenv import load_dotenv
from google import genai

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
  "title": "Short concept title",
  "quickMeaning": "Simple beginner-friendly meaning in 1-2 sentences.",
  "steps": [
    "Step 1",
    "Step 2",
    "Step 3",
    "Step 4"
  ],
  "analogy": "Simple analogy.",
  "example": "Simple example.",
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
- Keep it focused.
- Do not make it too long.
- Explain like a helpful teacher.
- Prefer clarity over complexity.
- Use beginner-friendly language.
- If the user asks a follow-up, use the previous conversation context.
"""


def build_storyboard_prompt(question: str, explanation: dict) -> str:
    return f"""
You are ConceptCanvas, an AI visual learning tutor.

The user asked:
{question}

The text explanation is:
Title: {explanation.get("title")}
Quick meaning: {explanation.get("quickMeaning")}
Steps: {explanation.get("steps")}
Analogy: {explanation.get("analogy")}
Example: {explanation.get("example")}
Takeaways: {explanation.get("takeaways")}

Create a visual storyboard for an in-browser whiteboard-style explanation.

Return ONLY valid JSON.
Do not include markdown.
Do not include ```json.
Do not include explanations outside JSON.

Use ONLY these sceneType values:
- flow
- stack
- compare
- timeline
- split
- highlight

Use this exact JSON shape:
{{
  "scenes": [
    {{
      "id": "scene_1",
      "sceneType": "flow",
      "title": "Short scene title",
      "narration": "One clear narration sentence.",
      "visualElements": ["element_one", "element_two", "element_three"],
      "subtitleLines": ["Subtitle line 1", "Subtitle line 2"]
    }}
  ]
}}

Rules:
- Create 3 to 6 scenes only.
- Every scene should teach one idea.
- Use simple visualElements with snake_case names.
- Do not create decorative/random elements.
- The storyboard must match the text explanation.
- Narration should be short and beginner-friendly.
- subtitleLines should be 1 to 3 short lines.
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
    models = os.getenv(
        "GEMINI_MODELS",
        "gemini-3.5-flash,gemini-2.5-flash,gemini-2.5-flash-lite",
    )

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
    return client.interactions.create(
        model=model_name,
        input=prompt,
    )


def generate_json_with_gemini(prompt: str, output_label: str) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")

    client = genai.Client(api_key=api_key)

    timeout_seconds = get_timeout_seconds()
    retry_attempts = get_retry_attempts()
    retry_delay_seconds = get_retry_delay_seconds()

    last_error = None

    for model_name in get_model_fallbacks():
        for attempt in range(1, retry_attempts + 1):
            try:
                print(
                    f"Calling Gemini for {output_label}. "
                    f"Model={model_name}, attempt={attempt}"
                )

                interaction = call_with_timeout(
                    lambda: call_gemini_model(client, model_name, prompt),
                    timeout_seconds,
                )

                response_text = interaction.output_text
                parsed_response = parse_json_response(response_text)
                parsed_response["_modelUsed"] = model_name

                return parsed_response

            except Exception as error:
                print(
                    f"Gemini {output_label} failed. "
                    f"Model={model_name}, attempt={attempt}. Error: {error}"
                )

                last_error = error

                if attempt < retry_attempts:
                    time.sleep(retry_delay_seconds * attempt)

    raise RuntimeError(
        f"All Gemini models failed for {output_label}. Last error: {last_error}"
    )


def generate_explanation_with_gemini(
    question: str,
    conversation_history: list[dict] | None = None,
) -> dict:
    prompt = build_explanation_prompt(question, conversation_history)

    return generate_json_with_gemini(
        prompt=prompt,
        output_label="explanation",
    )


def generate_storyboard_with_gemini(question: str, explanation: dict) -> dict:
    prompt = build_storyboard_prompt(question, explanation)

    return generate_json_with_gemini(
        prompt=prompt,
        output_label="storyboard",
    )