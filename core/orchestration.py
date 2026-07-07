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


def _detect_intent(user_request: str) -> str:
    lowered = user_request.lower()
    if any(kw in lowered for kw in ["campaign", "marketing", "promotion"]):
        return "campaign"
    return "launch"


def _agent_name_for(intent: str) -> str:
    return "CampaignAgent" if intent == "campaign" else "PlanningAgent"


def _artifact_type_for(intent: str) -> str:
    return "campaign_plan" if intent == "campaign" else "launch_plan"


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

    def run_flow(self, context: ContextObject, intent: str = "") -> Any:
        logger.info(f"Orchestrator running flow for: {context.user_request[:50]}")
        if not intent:
            intent = _detect_intent(context.user_request)

        result = self.orchestrator_agent.plan_execution(context, intent=intent)

        agent = self.orchestrator_agent.campaign_agent if intent == "campaign" else self.orchestrator_agent.planning_agent
        provider = getattr(agent, "_last_provider", None)
        self._last_provider = provider

        artifact_type = _artifact_type_for(intent)
        artifact_id = f"{artifact_type}_{int(time.time())}"
        self._last_artifact_id = artifact_id
        self._last_artifact_type = artifact_type

        created_by = _agent_name_for(intent)
        data = result.model_dump() if hasattr(result, "model_dump") else result
        envelope = _build_artifact_envelope(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            created_by=created_by,
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

        self._ingest_session_memory(context, result, artifact_id, artifact_type)

        logger.info(f"Orchestrator flow complete, artifact: {artifact_id}")
        return result

    def _ingest_session_memory(
        self, context: ContextObject, result: Any, artifact_id: str, artifact_type: str = "launch_plan"
    ) -> None:
        try:
            tags = [artifact_type, "session"]
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
