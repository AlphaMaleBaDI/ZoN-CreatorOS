from typing import Optional, Any, List, Dict
from uuid import UUID

class MemoryService:
    def __init__(self, memory_engine: Optional[Any] = None):
        self.memory_engine = memory_engine

    def query_workspace_memories(
        self,
        workspace_id: UUID,
        project_id: Optional[UUID],
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Queries scoped vector and knowledge memories for context assembly."""
        pass

    def ingest_session_memory(
        self,
        workspace_id: UUID,
        project_id: Optional[UUID],
        content: str,
        tags: List[str]
    ) -> bool:
        """Stores new content node into vector storage and references knowledge graph."""
        pass
