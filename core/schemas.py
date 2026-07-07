from enum import Enum
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

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
