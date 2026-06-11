from pydantic import BaseModel, Field
from typing import List, Dict, Any

class ExecutionReport(BaseModel):
    report_id: str
    session_outcome: str
    citation_map: Dict[str, str] = Field(default_factory=dict)
    vibra_shift_metrics: Dict[str, Any] = Field(default_factory=dict)
