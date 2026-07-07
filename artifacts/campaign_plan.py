from pydantic import BaseModel, Field
from typing import List, Optional


class CampaignAction(BaseModel):
    action: str
    why: str


class CampaignPlan(BaseModel):
    campaign_name: str
    campaign_objectives: List[str] = Field(default_factory=list)
    target_segments: List[str] = Field(default_factory=list)
    channel_strategy: List[str] = Field(default_factory=list)
    content_themes: List[str] = Field(default_factory=list)
    timeline_weeks: int = 12
    budget_notes: str = ""
    kpis: List[str] = Field(default_factory=list)
    next_actions: List[CampaignAction] = Field(default_factory=list)
    confidence_score: Optional[float] = None
