import pytest
from memory.creator_profile import CreatorProfile, CreatorProfileEngine

def test_creator_profile_schema():
    profile = CreatorProfile(
        creator_name="OdiB\u00e0",
        brand_voice="Afrofuturist",
        writing_style="Vibrant and technical",
        goals=["Launch CreatorOS", "Win Hackathon"],
        preferred_platforms=["Twitter", "Discord"],
        personality="Bold and analytical",
        preferred_tools=["Python", "Ryzen AI"],
        working_habits=["Fast iteration"]
    )
    assert profile.creator_name == "OdiB\u00e0"
    assert profile.brand_voice == "Afrofuturist"

def test_profile_engine_placeholders():
    engine = CreatorProfileEngine()
    # Placeholder assertions for validation structure
    assert engine.load_profile("NonExistent") is None
