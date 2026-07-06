import time
import logging
from typing import Any, Optional
from uuid import UUID
from core.schemas import ContextObject
from core.context_assembly import ContextAssemblyEngine
from agents.orchestrator_agent import OrchestratorAgent
from services.artifact_service import ArtifactService
from services.memory_service import MemoryService

logger = logging.getLogger(__name__)


def _build_artifact_envelope(
    artifact_id: str,
    artifact_type: str,
    workspace_id: UUID,
    project_id: Optional[UUID],
    created_by: str,
    provider: Optional[str],
    confidence: Optional[float],
    data: dict,
) -> dict:
    return {
        "artifact_id": artifact_id,
        "artifact_type": artifact_type,
        "workspace_id": str(workspace_id),
        "project_id": str(project_id) if project_id else None,
        "created_at": time.time(),
        "created_by": created_by,
        "provider": provider,
        "confidence": confidence,
        "version": 1,
        "data": data,
    }


class Orchestrator:
    def __init__(
        self,
        agent_router: Optional[Any] = None,
        artifact_service: Optional[ArtifactService] = None,
    ):
        self.agent_router = agent_router
        self.context_engine = ContextAssemblyEngine(memory_engine_client=MemoryService())
        self.orchestrator_agent = OrchestratorAgent()
        self.artifact_service = artifact_service or ArtifactService()
        self.memory_service = MemoryService()

        self._last_artifact_id: Optional[str] = None
        self._last_artifact_type: Optional[str] = None
        self._last_artifact_envelope: Optional[dict] = None
        self._last_provider: Optional[str] = None

    def run_flow(self, context: ContextObject) -> Any:
        logger.info(f"Orchestrator running flow for: {context.user_request[:50]}")
        result = self.orchestrator_agent.plan_execution(context)

        provider = getattr(self.orchestrator_agent.planning_agent, "_last_provider", None)
        self._last_provider = provider

        artifact_id = f"launch_plan_{int(time.time())}"
        artifact_type = "launch_plan"
        self._last_artifact_id = artifact_id
        self._last_artifact_type = artifact_type

        data = result.model_dump() if hasattr(result, "model_dump") else result
        envelope = _build_artifact_envelope(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            created_by="PlanningAgent",
            provider=provider,
            confidence=data.get("confidence_score"),
            data=data,
        )
        self._last_artifact_envelope = envelope
        self.artifact_service.save_artifact(
            workspace_id=context.workspace_id,
            artifact_id=artifact_id,
            artifact_data=envelope,
        )

        self._ingest_session_memory(context, result, artifact_id)

        logger.info(f"Orchestrator flow complete, artifact: {artifact_id}")
        return result

    def _ingest_session_memory(self, context: ContextObject, result: Any, artifact_id: str) -> None:
        try:
            tags = ["launch_plan", "session"]
            if context.goals:
                tags.append("goal:" + context.goals[0][:30])
            self.memory_service.ingest_session_memory(
                workspace_id=context.workspace_id,
                project_id=context.project_id,
                content=f"Generated {artifact_id}: {context.user_request[:100]}",
                tags=tags,
            )
            logger.info(f"Session memory ingested for {artifact_id}")
        except Exception as e:
            logger.warning(f"Session memory ingestion failed: {e}")
