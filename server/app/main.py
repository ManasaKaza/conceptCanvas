import json
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from app.db import (
    clear_conversation_turns,
    delete_conversation,
    get_conversation,
    init_db,
    list_conversations,
    save_turn,
)
from app.explanation_service import get_fake_explanation
from app.explanation_validator import normalize_explanation
from app.gemini_service import (
    generate_explanation_with_gemini,
    generate_storyboard_with_gemini,
    repair_storyboard_with_gemini,
)
from app.grounding_service import attach_grounding_to_storyboard, ground_explanation
from app.groq_service import (
    generate_explanation_with_groq,
    generate_visual_storyboard_with_groq,
    repair_visual_storyboard_with_groq,
)
from app.lesson_constraints import resolve_scene_count
from app.models import ExplainRequest, ExplainResponse
from app.storyboard_service import create_storyboard
from app.settings import (
    ALLOWED_ORIGINS,
    APP_ENV,
    HISTORY_ENABLED,
    MAX_REQUEST_BYTES,
    REQUESTS_PER_MINUTE,
)
from app.topic_classifier import classify_question


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if HISTORY_ENABLED:
        init_db()
    yield


app = FastAPI(title="ConceptCanvas API", version="1.5", lifespan=lifespan)

logger = logging.getLogger("conceptcanvas.api")
request_windows: dict[str, deque[float]] = defaultdict(deque)


HUMAN_REVIEW_RUBRIC_PATH = Path(__file__).parents[1] / "evaluation" / "human_review_rubric.json"


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




def get_client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def request_safety_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    started_at = time.perf_counter()

    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > MAX_REQUEST_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body is too large.", "requestId": request_id},
            headers={"X-Request-ID": request_id},
        )

    if request.url.path == "/api/explain":
        now = time.monotonic()
        key = get_client_key(request)
        window = request_windows[key]
        while window and now - window[0] >= 60:
            window.popleft()
        if len(window) >= REQUESTS_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many lesson requests. Please try again shortly.", "requestId": request_id},
                headers={"X-Request-ID": request_id, "Retry-After": "60"},
            )
        window.append(now)

    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request failure", extra={"request_id": request_id, "path": request.url.path})
        raise

    response.headers["X-Request-ID"] = request_id
    duration_ms = round((time.perf_counter() - started_at) * 1000, 1)
    logger.info(
        "request_complete request_id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


class SaveTurnRequest(BaseModel):
    conversationId: Optional[str] = None
    question: str = Field(min_length=3, max_length=2000)
    mode: Literal["text", "visual"]
    result: dict

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Question must contain at least 3 characters")
        return cleaned


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "environment": APP_ENV,
        "historyEnabled": HISTORY_ENABLED,
        "schemaVersion": "1.5",
        "lessonSchemaVersion": "2.1",
        "qualitySchemaVersion": "1.1",
        "groundingSchemaVersion": "1.0",
    }


@app.get("/api/evaluation/human-review-rubric")
def get_human_review_rubric():
    return json.loads(HUMAN_REVIEW_RUBRIC_PATH.read_text(encoding="utf-8"))


@app.post("/api/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest):
    classification = classify_question(request.question)

    if classification["topicType"] == "declined":
        return {
            "schemaVersion": "1.1",
            "status": "success",
            "topicType": "declined",
            "declineType": classification["declineType"],
            "message": classification["message"],
            "suggestions": classification["suggestions"],
        }

    resolved_scene_count = request.requestedSceneCount or 5
    if request.mode == "visual":
        try:
            resolved_scene_count = resolve_scene_count(
                request.question,
                request.requestedSceneCount,
            )
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    source: Literal["gemini", "groq", "fallback"] = "fallback"
    model_used = None
    use_ai = os.getenv("USE_AI", "true").lower() == "true"
    ai_provider = os.getenv("AI_PROVIDER", "groq").lower()

    if use_ai:
        try:
            conversation_history = [
                message.model_dump() for message in request.conversationHistory
            ]

            if ai_provider == "groq":
                raw_explanation = generate_explanation_with_groq(
                    request.question,
                    conversation_history,
                    request.audienceLevel,
                    request.explanationDepth,
                    request.requestedStructure,
                )
                source = "groq"
            elif ai_provider == "gemini":
                raw_explanation = generate_explanation_with_gemini(
                    request.question,
                    conversation_history,
                    request.audienceLevel,
                    request.explanationDepth,
                    request.requestedStructure,
                )
                source = "gemini"
            else:
                raise RuntimeError(f"Unsupported AI provider: {ai_provider}")

            model_used = raw_explanation.get("_modelUsed")
        except Exception as error:
            print("AI explanation failed. Using deterministic fallback:", error)
            raw_explanation = get_fake_explanation(request.question)
            source = "fallback"
    else:
        raw_explanation = get_fake_explanation(request.question)

    explanation = normalize_explanation(raw_explanation, request.question)
    grounding_report = ground_explanation(
        question=request.question,
        explanation=explanation,
        mode=request.groundingMode,
    )

    storyboard = None
    storyboard_source = None
    storyboard_model_used = None
    storyboard_validation = None

    if request.mode == "visual":
        raw_storyboard = None
        candidate_source = None
        candidate_model = None
        storyboard_issues: list[str] = []

        if source == "groq":
            try:
                raw_storyboard = generate_visual_storyboard_with_groq(
                    request.question,
                    explanation,
                    resolved_scene_count,
                    request.audienceLevel,
                )
                candidate_source = "groq"
                candidate_model = raw_storyboard.get("_modelUsed")
            except Exception as error:
                print("Groq storyboard generation failed:", error)
                storyboard_issues.append(
                    "Groq storyboard generation failed; used the deterministic fallback."
                )
        elif source == "gemini":
            try:
                raw_storyboard = generate_storyboard_with_gemini(
                    request.question,
                    explanation,
                    resolved_scene_count,
                    request.audienceLevel,
                )
                candidate_source = "gemini"
                candidate_model = raw_storyboard.get("_modelUsed")
            except Exception as error:
                print("Gemini storyboard generation failed:", error)
                storyboard_issues.append(
                    "Gemini storyboard generation failed; used the deterministic fallback."
                )
        else:
            storyboard_issues.append(
                "The explanation used a fallback, so the visual lesson used the deterministic storyboard."
            )

        repair_callback = None
        repair_enabled = os.getenv("AI_REPAIR_ENABLED", "true").lower() == "true"
        if raw_storyboard and candidate_source and repair_enabled:
            if candidate_source == "groq":
                repair_callback = lambda candidate, issues: repair_visual_storyboard_with_groq(
                    request.question,
                    explanation,
                    resolved_scene_count,
                    request.audienceLevel,
                    candidate,
                    issues,
                )
            elif candidate_source == "gemini":
                repair_callback = lambda candidate, issues: repair_storyboard_with_gemini(
                    request.question,
                    explanation,
                    resolved_scene_count,
                    request.audienceLevel,
                    candidate,
                    issues,
                )

        build_result = create_storyboard(
            question=request.question,
            explanation=explanation,
            requested_scene_count=resolved_scene_count,
            ai_storyboard=raw_storyboard,
            ai_source=candidate_source,
            ai_model_used=candidate_model,
            initial_issues=storyboard_issues,
            repair_callback=repair_callback,
            grounding_report=grounding_report,
        )

        storyboard = attach_grounding_to_storyboard(
            build_result.storyboard,
            grounding_report,
        )
        storyboard_source = build_result.source
        storyboard_model_used = build_result.model_used
        generated_scene_count = len(storyboard.get("scenes", []))
        storyboard_validation = {
            "requestedSceneCount": resolved_scene_count,
            "generatedSceneCount": generated_scene_count,
            "exactSceneCount": generated_scene_count == resolved_scene_count,
            "typedVisualSchemaValid": all(
                isinstance(scene.get("visual"), dict)
                and scene["visual"].get("schemaVersion") == "2.0"
                for scene in storyboard.get("scenes", [])
            ),
            "narrationTimelineValid": all(
                isinstance(scene.get("narrationSegments"), list)
                and len(scene["narrationSegments"]) > 0
                for scene in storyboard.get("scenes", [])
            ),
            "fallbackUsed": build_result.fallback_used,
            "repairAttempted": build_result.repair_summary.get("attempted", False),
            "repairedSceneCount": (
                len(build_result.repair_summary.get("repairedSceneIds", []))
                + len(build_result.repair_summary.get("replacedSceneIds", []))
                if build_result.repair_summary.get("attempted", False)
                else 0
            ),
            "preservedAiSceneCount": len(build_result.repair_summary.get("preservedSceneIds", [])),
            "qualityStatus": (build_result.quality_report or {}).get("status"),
            "issues": build_result.issues,
        }

    return {
        "schemaVersion": "1.1",
        "lessonSchemaVersion": "2.1",
        "status": "success",
        "topicType": "concept_explanation",
        "title": explanation["title"],
        "audienceLevel": request.audienceLevel,
        "explanationDepth": request.explanationDepth,
        "source": source,
        "modelUsed": model_used,
        "storyboardSource": storyboard_source,
        "storyboardModelUsed": storyboard_model_used,
        "storyboardValidation": storyboard_validation,
        "qualityReport": build_result.quality_report if request.mode == "visual" else None,
        "groundingReport": grounding_report,
        "explanation": {
            "title": explanation["title"],
            "quickMeaning": explanation["quickMeaning"],
            "deepExplanation": explanation["deepExplanation"],
            "stepByStep": explanation["stepByStep"],
            "realWorldExample": explanation["realWorldExample"],
            "analogy": explanation["analogy"],
            "technicalDetails": explanation["technicalDetails"],
            "commonConfusions": explanation["commonConfusions"],
            "interviewAngle": explanation["interviewAngle"],
            "summary": explanation["summary"],
            "takeaways": explanation["takeaways"],
        },
        "storyboard": storyboard,
        "followUps": explanation["followUps"],
    }


@app.get("/api/conversations")
def get_conversations():
    if not HISTORY_ENABLED:
        return {"status": "success", "historyEnabled": False, "conversations": []}
    return {"status": "success", "historyEnabled": True, "conversations": list_conversations()}


@app.get("/api/conversations/{conversation_id}")
def read_conversation(conversation_id: str):
    if not HISTORY_ENABLED:
        return {"status": "not_found", "historyEnabled": False, "message": "Lesson history is disabled."}
    conversation = get_conversation(conversation_id)
    if not conversation:
        return {"status": "not_found", "message": "Conversation not found"}
    return {"status": "success", "conversation": conversation}


@app.post("/api/conversations/turns")
def save_conversation_turn(request: SaveTurnRequest):
    if not HISTORY_ENABLED:
        return {
            "status": "success",
            "historyEnabled": False,
            "conversationId": None,
            "turnId": f"ephemeral-{uuid.uuid4()}",
        }
    saved_turn = save_turn(
        conversation_id=request.conversationId,
        question=request.question,
        mode=request.mode,
        result=request.result,
    )
    return {"status": "success", **saved_turn}


@app.delete("/api/conversations/{conversation_id}")
def remove_conversation(conversation_id: str):
    if not HISTORY_ENABLED:
        return {"status": "success", "historyEnabled": False, "deleted": False}
    deleted = delete_conversation(conversation_id)
    return {"status": "success" if deleted else "not_found", "deleted": deleted}


@app.delete("/api/conversations/{conversation_id}/turns")
def clear_conversation(conversation_id: str):
    if not HISTORY_ENABLED:
        return {"status": "success", "historyEnabled": False, "cleared": False}
    cleared = clear_conversation_turns(conversation_id)
    return {"status": "success" if cleared else "not_found", "cleared": cleared}
