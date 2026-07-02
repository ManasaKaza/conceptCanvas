from typing import Literal, Optional, Union

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ExplainRequest(BaseModel):
    question: str
    mode: Literal["text", "visual"] = "text"
    conversationHistory: list[ConversationMessage] = Field(default_factory=list)


class Explanation(BaseModel):
    title: str
    quickMeaning: str
    deepExplanation: str
    stepByStep: list[str]
    realWorldExample: str
    analogy: str
    technicalDetails: list[str]
    commonConfusions: list[str]
    interviewAngle: str
    summary: str
    takeaways: list[str]


class AnimationAction(BaseModel):
    type: Literal["show", "connect", "highlight", "move", "wait"]
    target: Optional[str] = None
    fromElement: Optional[str] = None
    toElement: Optional[str] = None
    label: Optional[str] = None


class Scene(BaseModel):
    id: str
    sceneType: Literal[
        "flow",
        "stack",
        "compare",
        "timeline",
        "split",
        "highlight",
    ]
    title: str
    narration: str
    visualElements: list[str]
    subtitleLines: list[str]
    actions: Optional[list[AnimationAction]] = None


class Storyboard(BaseModel):
    scenes: list[Scene]


class ConceptExplanationResponse(BaseModel):
    status: Literal["success"]
    topicType: Literal["concept_explanation"]
    title: str
    source: Literal["gemini", "groq", "fallback"]
    modelUsed: Optional[str] = None
    storyboardSource: Optional[Literal["gemini", "groq", "rule_based"]] = None
    storyboardModelUsed: Optional[str] = None
    explanation: Explanation
    storyboard: Optional[Storyboard] = None
    followUps: list[str]


class DeclinedResponse(BaseModel):
    status: Literal["success"]
    topicType: Literal["declined"]
    declineType: str
    message: str
    suggestions: list[str]


ExplainResponse = Union[ConceptExplanationResponse, DeclinedResponse]