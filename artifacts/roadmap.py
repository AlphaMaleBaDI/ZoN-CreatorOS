from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date

class Milestone(BaseModel):
    title: str
    target_date: Optional[date] = None
    description: str
    completed: bool = False

class ProjectRoadmap(BaseModel):
    project_id: str
    roadmap_name: str
    milestones: List[Milestone] = Field(default_factory=list)
