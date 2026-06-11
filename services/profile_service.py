from typing import Optional, Any
from memory.creator_profile import CreatorProfile, CreatorProfileEngine

class ProfileService:
    def __init__(self, profile_engine: Optional[CreatorProfileEngine] = None):
        self.profile_engine = profile_engine or CreatorProfileEngine()

    def get_creator_profile(self, creator_name: str) -> Optional[CreatorProfile]:
        """Fetches and processes creator profile metrics."""
        return self.profile_engine.load_profile(creator_name)

    def update_creator_profile(self, profile: CreatorProfile) -> bool:
        """Saves updates to a creator profile."""
        return self.profile_engine.save_profile(profile)
