from pydantic import BaseModel, Field
from typing import List, Optional


class CalendarWeek(BaseModel):
    week: int
    theme: str = ""
    actions: List[str] = Field(default_factory=list)


class CalendarAction(BaseModel):
    action: str
    why: str


class ContentCalendar(BaseModel):
    campaign_name: str
    content_strategy: str = ""
    weeks: List[CalendarWeek] = Field(default_factory=list)
    platform_schedule: List[str] = Field(default_factory=list)
    post_cadence: str = ""
    key_announcements: List[str] = Field(default_factory=list)
    milestones: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    success_metrics: List[str] = Field(default_factory=list)
    next_actions: List[CalendarAction] = Field(default_factory=list)
    confidence_score: Optional[float] = None
