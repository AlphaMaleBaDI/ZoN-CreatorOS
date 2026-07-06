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

PRODUCTION_STATES = ["planning", "production", "review", "publishing", "completed"]


class PIEAssessment(BaseModel):
    production_state: str = "planning"
    completed: List[str] = Field(default_factory=list)
    missing: List[str] = Field(default_factory=list)
    recommended_next: List[str] = Field(default_factory=list)
    production_progress: float = 0.0
    confidence: float = 0.0


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
