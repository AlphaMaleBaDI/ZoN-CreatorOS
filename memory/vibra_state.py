import logging
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from uuid import UUID
from intelligence.vibra import MoodBridge

logger = logging.getLogger(__name__)

class VibraShift(BaseModel):
    mood_vector: List[float] = Field(default_factory=list)
    signals: Dict[str, Any] = Field(default_factory=dict)
    active_vibe: str
    energy_level: float

class VibraStateEngine:
    def __init__(self):
        self.state_history: Dict[UUID, List[VibraShift]] = {}

    def compute_vibra(
        self,
        user_prompt: str,
        system_state: Dict[str, Any],
        memory_snapshot: List[Dict[str, Any]]
    ) -> VibraShift:
        vibe = MoodBridge.detect_vibra(user_prompt)
        mood = vibe.get("mood", "neutral")
        known = {"energetic": 0.9, "reflective": 0.4, "hopeful": 0.7,
                 "melancholy": 0.3, "technological": 0.6, "spiritual": 0.8}
        energy = known.get(mood, 0.5)
        logger.info(f"Vibra computed: {mood} (energy={energy})")
        return VibraShift(
            active_vibe=vibe.get("name", "Steady Harmonic"),
            energy_level=energy,
            signals=vibe
        )

    def record_shift(self, project_id: UUID, shift: VibraShift) -> None:
        self.state_history.setdefault(project_id, []).append(shift)
        logger.info(f"Vibra shift recorded for project {project_id}")
