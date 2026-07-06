import time
import logging
from uuid import UUID, uuid4
from typing import Optional, Any, List
from core.schemas import ContextObject
from intelligence.vibra import MoodBridge

logger = logging.getLogger(__name__)

class ContextAssemblyEngine:
    def __init__(self, memory_engine_client: Optional[Any] = None):
        self.memory_engine_client = memory_engine_client

    def assemble_context(
        self,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None,
        user_request: str = "",
        creator_profile: Optional[dict] = None,
        recent_artifacts: Optional[List[dict]] = None,
        active_projects: Optional[List[dict]] = None,
        vibra_override: Optional[dict] = None
    ) -> ContextObject:
        vibra = vibra_override or MoodBridge.detect_vibra(user_request)
        profile = creator_profile or {}
        goals = profile.get("goals", [])

        memory_snapshot = []
        if self.memory_engine_client and hasattr(self.memory_engine_client, 'query_workspace_memories'):
            try:
                memory_snapshot = self.memory_engine_client.query_workspace_memories(
                    workspace_id=workspace_id or uuid4(),
                    project_id=project_id,
                    query=user_request
                )
            except Exception as e:
                logger.warning(f"Memory query during context assembly failed: {e}")

        logger.info(f"Context assembled for request: {user_request[:50]}")
        return ContextObject(
            workspace_id=workspace_id or uuid4(),
            project_id=project_id,
            user_request=user_request,
            creator_profile=profile,
            memory_snapshot=memory_snapshot,
            recent_artifacts=recent_artifacts or [],
            active_projects=active_projects or [],
            vibra_state=vibra or {},
            goals=goals,
            timestamp=time.time()
        )
