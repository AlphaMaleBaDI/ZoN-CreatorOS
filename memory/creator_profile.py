import os
import json
import logging
from pydantic import BaseModel, Field
from typing import List, Optional

logger = logging.getLogger(__name__)

class CreatorProfile(BaseModel):
    creator_name: str
    brand_voice: str
    writing_style: str
    goals: List[str] = Field(default_factory=list)
    preferred_platforms: List[str] = Field(default_factory=list)
    personality: str
    preferred_tools: List[str] = Field(default_factory=list)
    working_habits: List[str] = Field(default_factory=list)

class CreatorProfileEngine:
    def __init__(self, storage_path: Optional[str] = None):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_path = storage_path or os.path.join(base, "zon_memory", "profiles")
        os.makedirs(self.storage_path, exist_ok=True)

    def load_profile(self, creator_name: str) -> Optional[CreatorProfile]:
        filepath = os.path.join(self.storage_path, f"{creator_name.lower()}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return CreatorProfile(**json.load(f))
        except Exception as e:
            logger.warning(f"Failed to load profile '{creator_name}': {e}")
            return None

    def save_profile(self, profile: CreatorProfile) -> bool:
        filepath = os.path.join(self.storage_path, f"{profile.creator_name.lower()}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(profile.model_dump(), f, indent=4)
            logger.info(f"Profile saved for '{profile.creator_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to save profile '{profile.creator_name}': {e}")
            return False

    def list_profiles(self) -> List[str]:
        if not os.path.exists(self.storage_path):
            return []
        return [f.replace(".json", "") for f in os.listdir(self.storage_path) if f.endswith(".json")]
