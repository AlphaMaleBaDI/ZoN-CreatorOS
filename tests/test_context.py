import pytest
from uuid import uuid4
import time
from core.schemas import ContextObject
from memory.creator_profile import CreatorProfile

def test_context_object_instantiation():
    ws_id = uuid4()
    profile = CreatorProfile(
        creator_name="OdiB\u00e0",
        brand_voice="Afrofuturist",
        writing_style="Vibrant",
        goals=[],
        preferred_platforms=[],
        personality="Bold",
        preferred_tools=[],
        working_habits=[]
    )
    
    context = ContextObject(
        workspace_id=ws_id,
        user_request="Launch Campaign",
        creator_profile=profile.model_dump(),
        timestamp=time.time()
    )

    assert context.workspace_id == ws_id
    assert context.creator_profile["creator_name"] == "OdiB\u00e0"
