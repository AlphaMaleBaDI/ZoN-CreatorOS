from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from time import time

class WorkspaceScope(BaseModel):
    workspace_id: UUID = Field(default_factory=uuid4)
    name: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProjectScope(BaseModel):
    project_id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    name: str
    active: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MemoryScope(BaseModel):
    scope_id: UUID = Field(default_factory=uuid4)
    workspace_id: UUID
    project_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)


class ProductionState(str, Enum):
    IDEATION = "ideation"
    PLANNING = "planning"
    PRODUCTION = "production"
    PUBLISHING = "publishing"
    RELEASED = "released"
    ARCHIVED = "archived"


class StateEvidence(BaseModel):
    artifact_type: str
    exists: bool
    eval_score: Optional[float] = None
    eval_passed: Optional[bool] = None


class StateAssessment(BaseModel):
    current_state: ProductionState
    evidence: List[StateEvidence] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    next_state: Optional[ProductionState] = None
    can_transition: bool = False
    blockers: List[str] = Field(default_factory=list)


class PIEAssessment(BaseModel):
    production_state: str = "planning"
    completed: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    recommended_next: List[str] = Field(default_factory=list)
    production_progress: float = 0.0
    confidence: float = 0.0
    narrative: str = ""
    state_assessment: Optional[StateAssessment] = None


class EvalCheck(BaseModel):
    name: str
    passed: bool
    detail: str = ""

class EvalAssessment(BaseModel):
    artifact_type: str
    status: str = "incomplete"
    score: float = 0.0
    checks: List[EvalCheck] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    eval_time_ms: float = 0.0
    confidence: float = 0.0


class PipelineMetrics(BaseModel):
    kernel_boot_ms: float = 0.0
    context_assembly_ms: float = 0.0
    orchestration_ms: float = 0.0
    snapshot_ms: float = 0.0
    pie_ms: float = 0.0
    eval_ms: float = 0.0
    total_ms: float = 0.0
    provider: str = ""
    pipeline_version: str = "0.5.0"


class ContextObject(BaseModel):
    workspace_id: UUID
    project_id: Optional[UUID] = None
    user_request: str
    creator_profile: Dict[str, Any] = Field(default_factory=dict)
    memory_snapshot: List[Dict[str, Any]] = Field(default_factory=list)
    recent_artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    active_projects: List[Dict[str, Any]] = Field(default_factory=list)
    vibra_state: Dict[str, Any] = Field(default_factory=dict)
    goals: List[str] = Field(default_factory=list)
    timestamp: float


class ObservationSource(str, Enum):
    CONVERSATION = "conversation"
    ARTIFACT = "artifact"
    RESEARCH = "research"
    EVALUATION = "evaluation"
    PROFILE = "profile"
    ONBOARDING = "onboarding"
    APPROVAL = "approval"
    CORRECTION = "correction"
    EXTERNAL = "external"


class Observation(BaseModel):
    id: str
    content: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: ObservationSource = ObservationSource.CONVERSATION
    impact: str = "medium"
    timestamp: float = Field(default_factory=time)


class BeliefLifecycle(str, Enum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    CHALLENGED = "challenged"
    RESOLVED = "resolved"
    SUPERSEDED = "superseded"


class Belief(BaseModel):
    id: str
    statement: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    lifecycle: BeliefLifecycle = BeliefLifecycle.CANDIDATE
    observation_ids: List[str] = Field(default_factory=list)
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    source: str = "deterministic"
    created_at: float = Field(default_factory=time)


class TensionSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TensionPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# --- Mission 021: Requirement satisfaction model ---

class RequirementStatus(str, Enum):
    UNKNOWN    = "unknown"     # Not yet discussed
    SUSPECTED  = "suspected"   # Raw message matched; no confirmed belief yet
    CONFIRMED  = "confirmed"   # Belief evidence supports this requirement
    CHALLENGED = "challenged"  # Creator contradicted a previously confirmed requirement
    RESOLVED   = "resolved"    # Confirmed after being challenged


class Requirement(BaseModel):
    """A single cognitive requirement the OS must satisfy before it truly understands
    a creator's project. Lifecycle mirrors BeliefLifecycle for symmetry."""
    area:         str
    question:     str
    status:       RequirementStatus = RequirementStatus.UNKNOWN
    confidence:   float             = 0.0
    evidence_ids: List[str]         = Field(default_factory=list)  # observation / belief IDs


class Tension(BaseModel):
    id: str
    description: str
    belief_ids: List[str] = Field(default_factory=list)
    severity: TensionSeverity = TensionSeverity.MEDIUM
    priority: TensionPriority = TensionPriority.MEDIUM
    status: str = "active"
    created_at: float = Field(default_factory=time)


class Reflection(BaseModel):
    id: str
    narrative: str
    belief_ids: List[str] = Field(default_factory=list)
    tension_ids: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: float = Field(default_factory=time)


class ReasoningResult(BaseModel):
    reflections: List[Reflection] = Field(default_factory=list)
    priorities: List[str] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    decision_narrative: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning_time_ms: float = 0.0
    provider: str = "deterministic"


class ReasoningCandidate(BaseModel):
    reflection: str = ""
    confidence: float = 0.0
    suggested_action: str = ""
    reasoning_trace: List[str] = Field(default_factory=list)
    unanswered_questions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    is_insight: bool = False
    generated_at: float = Field(default_factory=time)


class CurrentUnderstanding(BaseModel):
    version: int = 1
    derived_from_observation: str = ""
    derived_from_beliefs: str = ""
    observations: List[Observation] = Field(default_factory=list)
    beliefs: List[Belief] = Field(default_factory=list)
    tensions: List[Tension] = Field(default_factory=list)
    reasoning: Optional[ReasoningResult] = None
    requirement_states: List[Requirement] = Field(default_factory=list)
    domain: str = "unknown"
    activity: str = "unknown"
