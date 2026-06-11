import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# --- Vibra Mapping ---
# Maps specific moods to sacred colors and descriptions
VIBRA_MAP = {
    "energetic": {
        "color": "#FF5F1F",  # Neon Orange
        "name": "Ardent Pulse",
        "description": "The sacred flame is high. High energy, rhythmic drive, and creative fire.",
        "keywords": {"dance", "party", "fire", "heat", "build", "fast", "powerful", "bright", "shout", "win"}
    },
    "reflective": {
        "color": "#7DF9FF",  # Electric Blue
        "name": "Indigo Depths",
        "description": "Searching the infinite. Deep thought, soul-searching, and quiet intelligence.",
        "keywords": {"mind", "think", "soul", "truth", "why", "deep", "learn", "question", "quiet", "logic"}
    },
    "hopeful": {
        "color": "#50C878",  # Emerald Green
        "name": "Verdant Dawn",
        "description": "The first light of OdoBa'. Growth, belief, and futuristic optimism.",
        "keywords": {"rise", "light", "dream", "hope", "believe", "shine", "future", "new", "possible", "goal"}
    },
    "melancholy": {
        "color": "#9370DB",  # Medium Purple
        "name": "Twilight Echo",
        "description": "Remembrance of things passed. Rainy-day reflection and emotional resonance.",
        "keywords": {"cry", "alone", "sad", "miss", "lost", "past", "memory", "rain", "heavy", "gone"}
    },
    "technological": {
        "color": "#E6E6FA",  # Lavender
        "name": "Etheric Matrix",
        "description": "Precision and structure. Divine order within the code.",
        "keywords": {"code", "build", "api", "logic", "structure", "data", "fix", "system", "script", "app"}
    },
    "spiritual": {
        "color": "#FFD700",  # Gold
        "name": "Sacred Order",
        "description": "Aligning with the First Intelligence. Harmony, peace, and cosmic alignment.",
        "keywords": {"sacred", "holy", "spirit", "divine", "harmony", "order", "cosmos", "blessing", "peace", "alignment"}
    }
}

DEFAULT_VIBRA = {
    "color": "#C0C0C0",  # Silver
    "name": "Steady Harmonic",
    "description": "Balanced presence. Neutral and ready for any direction.",
    "keywords": set()
}

class MoodBridge:
    """
    Analyzes conversation energy and converts it into 'Vibra Shifts'.
    """
    
    @staticmethod
    def detect_vibra(text: str) -> Dict[str, Any]:
        text = text.lower()
        scores = {}
        
        for mood, data in VIBRA_MAP.items():
            score = sum(1 for word in data["keywords"] if word in text)
            if score > 0:
                scores[mood] = score
        
        if not scores:
            return DEFAULT_VIBRA
        
        # Select the mood with the highest score
        best_mood = max(scores, key=scores.get)
        result = VIBRA_MAP[best_mood].copy()
        result["mood"] = best_mood
        # Remove keywords from the output to keep it clean
        result.pop("keywords", None)
        
        return result

def get_vibra_shift(user_prompt: str, zon_response: str) -> Dict[str, Any]:
    """
    Determines the vibra shift based on the combined energy of user and ZoN.
    """
    # We weight the user's prompt more for the 'shift' direction
    combined_text = f"{user_prompt} {user_prompt} {zon_response}"
    return MoodBridge.detect_vibra(combined_text)
