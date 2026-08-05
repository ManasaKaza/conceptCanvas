from typing import Annotated, Literal, Optional, Union

from pydantic import AnyHttpUrl, BaseModel, Field, field_validator, model_validator


AudienceLevel = Literal["beginner", "intermediate", "advanced"]
ExplanationDepth = Literal["focused", "standard", "deep"]
DiagramType = Literal[
    "flow",
    "sequence",
    "hierarchy",
    "stack",
    "tree",
    "comparison",
    "timeline",
    "architecture",
    "state_transition",
    "cycle",
    "cause_effect",
    "concept_map",
    "formula",
    "code_execution",
    "spatial",
    "fallback",
]
VisualOrientation = Literal[
    "left_to_right",
    "top_to_bottom",
    "stacked",
    "two_column",
    "radial",
]
NodeKind = Literal[
    "actor",
    "client",
    "server",
    "service",
    "cache",
    "database",
    "process",
    "decision",
    "data",
    "packet",
    "stack_frame",
    "tree_node",
    "bucket",
    "queue",
    "code",
    "output",
    "entity",
    "event",
    "state",
    "component",
    "category",
    "organism",
    "place",
    "quantity",
    "formula",
    "example",
    "generic",
]
EdgeRelation = Literal[
    "flows_to",
    "request",
    "response",
    "calls",
    "returns",
    "reads",
    "writes",
    "contains",
    "routes_to",
    "transforms",
    "compares",
    "depends_on",
    "causes",
    "precedes",
    "part_of",
    "changes_into",
    "activates",
    "inhibits",
    "supports",
    "contrasts",
    "located_in",
    "increases",
    "decreases",
]
NarrationAction = Literal["reveal", "highlight", "trace", "deemphasize", "pause"]



SubjectDomain = Literal[
    "computing",
    "mathematics",
    "natural_science",
    "social_science",
    "humanities",
    "business",
    "everyday",
    "interdisciplinary",
    "unknown",
]
KnowledgeShape = Literal[
    "process",
    "interaction",
    "hierarchy",
    "structure",
    "comparison",
    "chronology",
    "cycle",
    "state_change",
    "cause_effect",
    "quantitative",
    "spatial",
    "code_execution",
    "stack",
    "classification",
    "concept_relationship",
]
RendererSupport = Literal["specialized", "schematic", "fallback"]
QualityStatus = Literal["pass", "warn", "fail"]
QualitySeverity = Literal["info", "warning", "error"]
RepairStrategy = Literal["none", "canonicalization", "model_repair", "partial_hybrid", "full_fallback"]
GroundingMode = Literal["off", "preferred", "required"]
GroundingStatus = Literal["off", "unavailable", "pass", "warn", "fail"]
ClaimKind = Literal[
    "definition",
    "mechanism",
    "causal",
    "quantitative",
    "historical",
    "comparative",
    "example",
    "instructional",
    "analogy",
    "other",
]
ClaimVerificationStatus = Literal["supported", "contradicted", "unverified", "not_applicable"]
EvidenceStance = Literal["supports", "contradicts"]
SourceAuthority = Literal["primary", "official", "academic", "reference", "curated"]
ExplanationSection = Literal[
    "quickMeaning",
    "deepExplanation",
    "stepByStep",
    "realWorldExample",
    "analogy",
    "technicalDetails",
    "commonConfusions",
    "interviewAngle",
    "summary",
    "takeaways",
]


class LessonPlanningProfile(BaseModel):
    schemaVersion: Literal["1.0"] = "1.0"
    subjectDomain: SubjectDomain
    knowledgeShapes: list[KnowledgeShape] = Field(min_length=1, max_length=4)
    primaryArchetype: DiagramType
    secondaryArchetypes: list[DiagramType] = Field(default_factory=list, max_length=4)
    rationale: str = Field(min_length=12, max_length=400)
    confidence: float = Field(ge=0, le=1)
    rendererSupport: RendererSupport
    limitations: list[str] = Field(default_factory=list, max_length=5)


class QualityIssue(BaseModel):
    code: str = Field(min_length=3, max_length=80)
    severity: QualitySeverity
    scope: Literal["lesson", "explanation", "scene", "segment"]
    message: str = Field(min_length=8, max_length=400)
    sceneId: Optional[str] = None
    segmentId: Optional[str] = None
    evidence: Optional[str] = Field(default=None, max_length=240)


class LessonQualityMetrics(BaseModel):
    structureScore: int = Field(ge=0, le=100)
    visualSpecificityScore: int = Field(ge=0, le=100)
    narrationAlignmentScore: int = Field(ge=0, le=100)
    technicalRiskScore: int = Field(ge=0, le=100)
    groundingCoverageScore: Optional[int] = Field(default=None, ge=0, le=100)


class RepairSummary(BaseModel):
    attempted: bool = False
    strategy: RepairStrategy = "none"
    modelRepairAttempted: bool = False
    modelRepairSucceeded: bool = False
    repairedSceneIds: list[str] = Field(default_factory=list, max_length=7)
    replacedSceneIds: list[str] = Field(default_factory=list, max_length=7)
    preservedSceneIds: list[str] = Field(default_factory=list, max_length=7)
    notes: list[str] = Field(default_factory=list, max_length=12)


class LessonQualityReport(BaseModel):
    schemaVersion: Literal["1.1"] = "1.1"
    status: QualityStatus
    overallScore: int = Field(ge=0, le=100)
    metrics: LessonQualityMetrics
    repair: RepairSummary
    issues: list[QualityIssue] = Field(default_factory=list, max_length=80)



class SourceReference(BaseModel):
    sourceId: str = Field(pattern=r"^source_[a-z0-9_]{3,80}$")
    title: str = Field(min_length=3, max_length=240)
    publisher: str = Field(min_length=2, max_length=160)
    url: AnyHttpUrl
    authority: SourceAuthority
    publishedAt: Optional[str] = Field(default=None, max_length=40)
    locator: Optional[str] = Field(default=None, max_length=160)


class GroundingEvidence(BaseModel):
    evidenceId: str = Field(pattern=r"^evidence_[1-9][0-9]*$")
    claimId: str = Field(pattern=r"^claim_[1-9][0-9]*$")
    sourceId: str = Field(pattern=r"^source_[a-z0-9_]{3,80}$")
    stance: EvidenceStance
    excerpt: str = Field(min_length=8, max_length=600)
    locator: Optional[str] = Field(default=None, max_length=160)
    confidence: float = Field(ge=0, le=1)


class GroundedClaim(BaseModel):
    claimId: str = Field(pattern=r"^claim_[1-9][0-9]*$")
    section: ExplanationSection
    itemIndex: Optional[int] = Field(default=None, ge=0, le=20)
    text: str = Field(min_length=8, max_length=700)
    kind: ClaimKind
    status: ClaimVerificationStatus
    confidence: float = Field(ge=0, le=1)
    sourceIds: list[str] = Field(default_factory=list, max_length=6)
    evidenceIds: list[str] = Field(default_factory=list, max_length=8)


class GroundingMetrics(BaseModel):
    totalClaims: int = Field(ge=0, le=40)
    verifiableClaims: int = Field(ge=0, le=40)
    supportedClaims: int = Field(ge=0, le=40)
    contradictedClaims: int = Field(ge=0, le=40)
    unverifiedClaims: int = Field(ge=0, le=40)
    notApplicableClaims: int = Field(ge=0, le=40)
    coverageScore: int = Field(ge=0, le=100)


class GroundingReport(BaseModel):
    schemaVersion: Literal["1.0"] = "1.0"
    mode: GroundingMode
    status: GroundingStatus
    provider: str = Field(min_length=2, max_length=80)
    metrics: GroundingMetrics
    claims: list[GroundedClaim] = Field(default_factory=list, max_length=40)
    sources: list[SourceReference] = Field(default_factory=list, max_length=30)
    evidence: list[GroundingEvidence] = Field(default_factory=list, max_length=80)
    warnings: list[str] = Field(default_factory=list, max_length=20)


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=6000)

    @field_validator("content")
    @classmethod
    def strip_content(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Message content cannot be blank")
        return cleaned


class ExplainRequest(BaseModel):
    schemaVersion: Literal["1.1"] = "1.1"
    question: str = Field(min_length=3, max_length=2000)
    mode: Literal["text", "visual"] = "text"
    audienceLevel: AudienceLevel = "beginner"
    explanationDepth: ExplanationDepth = "standard"
    requestedSceneCount: Optional[int] = Field(default=None, ge=3, le=7)
    requestedStructure: list[str] = Field(default_factory=list, max_length=8)
    narrationEnabled: bool = True
    groundingMode: GroundingMode = "preferred"
    conversationHistory: list[ConversationMessage] = Field(
        default_factory=list,
        max_length=12,
    )

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Question must contain at least 3 characters")
        return cleaned

    @field_validator("requestedStructure")
    @classmethod
    def normalize_requested_structure(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                continue
            cleaned = item.strip()
            if cleaned and cleaned not in normalized:
                normalized.append(cleaned)
        return normalized


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


class VisualNode(BaseModel):
    type: Literal["node"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    label: str = Field(min_length=1, max_length=80)
    nodeKind: NodeKind
    detail: Optional[str] = Field(default=None, max_length=180)
    groupId: Optional[str] = Field(default=None, pattern=r"^[a-z][a-z0-9_]{1,63}$")

    @field_validator("label", "detail")
    @classmethod
    def strip_optional_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class VisualEdge(BaseModel):
    type: Literal["edge"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    fromId: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    toId: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    relation: EdgeRelation = "flows_to"
    label: Optional[str] = Field(default=None, max_length=80)
    directed: bool = True

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class VisualGroup(BaseModel):
    type: Literal["group"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    label: str = Field(min_length=1, max_length=80)
    childIds: list[str] = Field(min_length=1, max_length=12)
    groupKind: Literal["system", "layer", "lane", "cluster"] = "cluster"


class VisualAnnotation(BaseModel):
    type: Literal["annotation"]
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")
    label: str = Field(min_length=1, max_length=120)
    targetId: str = Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")


VisualElement = Annotated[
    Union[VisualNode, VisualEdge, VisualGroup, VisualAnnotation],
    Field(discriminator="type"),
]


class VisualSpec(BaseModel):
    schemaVersion: Literal["2.0"] = "2.0"
    diagramType: DiagramType
    orientation: VisualOrientation = "left_to_right"
    elements: list[VisualElement] = Field(min_length=2, max_length=24)

    @model_validator(mode="after")
    def validate_references(self):
        element_ids = [element.id for element in self.elements]
        if len(element_ids) != len(set(element_ids)):
            raise ValueError("Visual element IDs must be unique within a scene")

        id_set = set(element_ids)
        node_ids = {
            element.id for element in self.elements if isinstance(element, VisualNode)
        }
        group_ids = {
            element.id for element in self.elements if isinstance(element, VisualGroup)
        }

        if len(node_ids) < 2:
            raise ValueError("A visual scene needs at least two typed nodes")

        for element in self.elements:
            if isinstance(element, VisualEdge):
                if element.fromId not in node_ids or element.toId not in node_ids:
                    raise ValueError("Visual edges must reference declared node IDs")
                if element.fromId == element.toId:
                    raise ValueError("Visual edges cannot connect a node to itself")
            elif isinstance(element, VisualGroup):
                if any(child_id not in node_ids for child_id in element.childIds):
                    raise ValueError("Visual groups must contain declared node IDs")
            elif isinstance(element, VisualAnnotation):
                if element.targetId not in id_set:
                    raise ValueError("Annotations must reference declared visual elements")
            elif isinstance(element, VisualNode):
                if element.groupId and element.groupId not in group_ids:
                    raise ValueError("Node groupId must reference a declared group")

        return self


class NarrationSegment(BaseModel):
    id: str = Field(pattern=r"^segment_[1-9][0-9]*$")
    order: int = Field(ge=1, le=20)
    spokenText: str = Field(min_length=8, max_length=500)
    subtitleText: str = Field(min_length=3, max_length=180)
    targetElementIds: list[str] = Field(default_factory=list, max_length=8)
    action: NarrationAction
    estimatedDurationMs: int = Field(default=3500, ge=700, le=20000)
    claimIds: list[str] = Field(default_factory=list, max_length=6)
    sourceIds: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("spokenText", "subtitleText")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class AnimationAction(BaseModel):
    """Temporary compatibility contract for the Phase 1 player.

    Phase 3 will remove this once the typed renderer consumes VisualSpec and
    NarrationSegment directly.
    """

    type: Literal["show", "connect", "highlight", "move", "wait"]
    target: Optional[str] = None
    fromElement: Optional[str] = None
    toElement: Optional[str] = None
    label: Optional[str] = None


class Scene(BaseModel):
    id: str
    order: int = Field(ge=1)
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
    visual: VisualSpec
    narrationSegments: list[NarrationSegment] = Field(min_length=1, max_length=12)
    visualElements: list[str]
    subtitleLines: list[str]
    actions: list[AnimationAction] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_scene_timeline(self):
        expected_segment_ids = [
            f"segment_{index}" for index in range(1, len(self.narrationSegments) + 1)
        ]
        actual_segment_ids = [segment.id for segment in self.narrationSegments]
        actual_orders = [segment.order for segment in self.narrationSegments]

        if actual_segment_ids != expected_segment_ids:
            raise ValueError("Narration segment IDs must be canonical and ordered")
        if actual_orders != list(range(1, len(self.narrationSegments) + 1)):
            raise ValueError("Narration segment order must be canonical")

        visual_ids = {element.id for element in self.visual.elements}
        for segment in self.narrationSegments:
            if any(target_id not in visual_ids for target_id in segment.targetElementIds):
                raise ValueError(
                    "Narration segments must reference declared visual element IDs"
                )

        return self


class Storyboard(BaseModel):
    schemaVersion: Literal["2.1"] = "2.1"
    planningProfile: LessonPlanningProfile
    scenes: list[Scene]


class StoryboardValidation(BaseModel):
    requestedSceneCount: int = Field(ge=3, le=7)
    generatedSceneCount: int = Field(ge=0, le=7)
    exactSceneCount: bool
    typedVisualSchemaValid: bool
    narrationTimelineValid: bool
    fallbackUsed: bool
    repairAttempted: bool = False
    repairedSceneCount: int = Field(default=0, ge=0, le=7)
    preservedAiSceneCount: int = Field(default=0, ge=0, le=7)
    qualityStatus: Optional[QualityStatus] = None
    issues: list[str] = Field(default_factory=list)


class ConceptExplanationResponse(BaseModel):
    schemaVersion: Literal["1.1"] = "1.1"
    lessonSchemaVersion: Literal["2.1"] = "2.1"
    status: Literal["success"]
    topicType: Literal["concept_explanation"]
    title: str
    audienceLevel: AudienceLevel
    explanationDepth: ExplanationDepth
    source: Literal["gemini", "groq", "fallback"]
    modelUsed: Optional[str] = None
    storyboardSource: Optional[Literal["gemini", "groq", "hybrid", "rule_based"]] = None
    storyboardModelUsed: Optional[str] = None
    storyboardValidation: Optional[StoryboardValidation] = None
    qualityReport: Optional[LessonQualityReport] = None
    groundingReport: Optional[GroundingReport] = None
    explanation: Explanation
    storyboard: Optional[Storyboard] = None
    followUps: list[str]


class DeclinedResponse(BaseModel):
    schemaVersion: Literal["1.1"] = "1.1"
    status: Literal["success"]
    topicType: Literal["declined"]
    declineType: str
    message: str
    suggestions: list[str]


ExplainResponse = Union[ConceptExplanationResponse, DeclinedResponse]
