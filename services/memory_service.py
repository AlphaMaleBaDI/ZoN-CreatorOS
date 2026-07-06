import logging
from typing import Optional, Any, List, Dict
from uuid import UUID
from memory import memory_engine as me

logger = logging.getLogger(__name__)

class MemoryService:
    def __init__(self, memory_engine: Optional[Any] = None):
        self.memory_engine = memory_engine

    def _scope_name(self, workspace_id: UUID, project_id: Optional[UUID] = None) -> str:
        return f"ws_{workspace_id}" if not project_id else f"ws_{workspace_id}_proj_{project_id}"

    def query_workspace_memories(
        self,
        workspace_id: UUID,
        project_id: Optional[UUID],
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        me.set_scope(self._scope_name(workspace_id, project_id))
        results = me.recall(query)
        return results[:limit]

    def ingest_session_memory(
        self,
        workspace_id: UUID,
        project_id: Optional[UUID],
        content: str,
        tags: List[str]
    ) -> bool:
        me.set_scope(self._scope_name(workspace_id, project_id))
        for tag in tags:
            me.remember(tag, content)
        logger.info(f"Ingested {len(tags)} memory tags for workspace {workspace_id}")
        return True
