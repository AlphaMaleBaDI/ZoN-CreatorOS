from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CalendarEntry(BaseModel):
    title: str
    scheduled_time: datetime
    channels: List[str] = Field(default_factory=list)
    description: str
    citation_id: Optional[str] = None

class ContentCalendar(BaseModel):
    calendar_id: str
    entries: List[CalendarEntry] = Field(default_factory=list)
