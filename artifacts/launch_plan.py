from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ActionItem(BaseModel):
    action: str
    why: str
    citation_id: Optional[str] = None

class LaunchPlan(BaseModel):
    release_strategy: str
    marketing_angles: List[str] = Field(default_factory=list)
    audience_profile: str
    next_actions: List[ActionItem] = Field(default_factory=list)
    memory_citations: List[str] = Field(default_factory=list)
    creative_state_vibra: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: Optional[float] = None
