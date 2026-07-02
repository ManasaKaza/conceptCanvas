import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.explanation_service import get_fake_explanation
from app.explanation_validator import normalize_explanation
from app.gemini_service import (
    generate_explanation_with_gemini,
    generate_storyboard_with_gemini,
)
from app.groq_service import (
    generate_explanation_with_groq,
    generate_visual_storyboard_with_groq,
)
from app.models import ExplainRequest, ExplainResponse
from app.storyboard_service import create_storyboard
from app.storyboard_validator import normalize_storyboard
from app.topic_classifier import classify_question

from typing import Optional

from pydantic import BaseModel

from app.db import (
    clear_conversation_turns,
    delete_conversation,
    get_conversation,
    init_db,
    list_conversations,
    save_turn,
)

app = FastAPI(title="ConceptCanvas API")

@app.on_event("startup")
def startup_event():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SaveTurnRequest(BaseModel):
    conversationId: Optional[str] = None
    question: str
    mode: str
    result: dict


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/explain", response_model=ExplainResponse)
def explain(request: ExplainRequest):
    classification = classify_question(request.question)

    if classification["topicType"] == "declined":
        return {
            "status": "success",
            "topicType": "declined",
            "declineType": classification["declineType"],
            "message": classification["message"],
            "suggestions": classification["suggestions"],
        }

    model_used = None
    source = "fallback"

    use_ai = os.getenv("USE_AI", "true").lower() == "true"
    ai_provider = os.getenv("AI_PROVIDER", "groq").lower()

    if use_ai:
        try:
            conversation_history = [
                message.model_dump() for message in request.conversationHistory
            ]

            if ai_provider == "groq":
                explanation = generate_explanation_with_groq(
                    request.question,
                    conversation_history,
                )
                source = "groq"
            elif ai_provider == "gemini":
                explanation = generate_explanation_with_gemini(
                    request.question,
                    conversation_history,
                )
                source = "gemini"
            else:
                raise RuntimeError(f"Unsupported AI provider: {ai_provider}")

            model_used = explanation.get("_modelUsed")

        except Exception as error:
            print("AI failed. Falling back to fake explanation:", error)
            explanation = get_fake_explanation(request.question)
            source = "fallback"
    else:
        explanation = get_fake_explanation(request.question)
        source = "fallback"

    explanation = normalize_explanation(explanation, request.question)

    storyboard = None
    storyboard_source = None
    storyboard_model_used = None

    use_gemini_storyboard = (
        os.getenv("USE_GEMINI_STORYBOARD", "false").lower() == "true"
    )

    storyboard = None
    storyboard_source = None
    storyboard_model_used = None

    use_gemini_storyboard = (
        os.getenv("USE_GEMINI_STORYBOARD", "false").lower() == "true"
    )

    if request.mode == "visual":
        if source == "groq":
            try:
                raw_storyboard = generate_visual_storyboard_with_groq(
                    request.question,
                    explanation,
                )
                storyboard_model_used = raw_storyboard.get("_modelUsed")
                explanation["_visualStoryboard"] = raw_storyboard
                storyboard = create_storyboard(request.question, explanation)
                storyboard_source = "groq"
            except Exception as error:
                print("Groq storyboard failed. Falling back to explanation-based storyboard:", error)
                storyboard = create_storyboard(request.question, explanation)
                storyboard_source = "rule_based"

        elif use_gemini_storyboard:
            try:
                raw_storyboard = generate_storyboard_with_gemini(
                    request.question,
                    explanation,
                )
                storyboard_model_used = raw_storyboard.get("_modelUsed")
                explanation["_visualStoryboard"] = raw_storyboard
                storyboard = create_storyboard(request.question, explanation)
                storyboard_source = "gemini"
            except Exception as error:
                print(
                    "Gemini storyboard failed. Falling back to rule-based storyboard:",
                    error,
                )
                storyboard = create_storyboard(request.question, explanation)
                storyboard_source = "rule_based"

        else:
            storyboard = create_storyboard(request.question, explanation)
            storyboard_source = "rule_based"

    return {
        "status": "success",
        "topicType": "concept_explanation",
        "title": explanation["title"],
        "source": source,
        "modelUsed": model_used,
        "storyboardSource": storyboard_source,
        "storyboardModelUsed": storyboard_model_used,
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
    return {
        "status": "success",
        "conversations": list_conversations(),
    }


@app.get("/api/conversations/{conversation_id}")
def read_conversation(conversation_id: str):
    conversation = get_conversation(conversation_id)

    if not conversation:
        return {
            "status": "not_found",
            "message": "Conversation not found",
        }

    return {
        "status": "success",
        "conversation": conversation,
    }


@app.post("/api/conversations/turns")
def save_conversation_turn(request: SaveTurnRequest):
    saved_turn = save_turn(
        conversation_id=request.conversationId,
        question=request.question,
        mode=request.mode,
        result=request.result,
    )

    return {
        "status": "success",
        **saved_turn,
    }


@app.delete("/api/conversations/{conversation_id}")
def remove_conversation(conversation_id: str):
    deleted = delete_conversation(conversation_id)

    return {
        "status": "success" if deleted else "not_found",
        "deleted": deleted,
    }


@app.delete("/api/conversations/{conversation_id}/turns")
def clear_conversation(conversation_id: str):
    cleared = clear_conversation_turns(conversation_id)

    return {
        "status": "success" if cleared else "not_found",
        "cleared": cleared,
    }