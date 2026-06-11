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

class ContextObject(BaseModel):
    workspace_id: UUID
    project_id: Optional[UUID] = None
    user_request: str
    creator_profile: Dict[str, Any] = Field(default_factory=dict)
    memory_snapshot: List[Dict[str, Any]] = Field(default_factory=list)
    vibra_state: Dict[str, Any] = Field(default_factory=dict)
    goals: List[str] = Field(default_factory=list)
    timestamp: float
