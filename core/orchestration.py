import time
import logging
from typing import Any, Optional, Dict
from uuid import UUID
from core.schemas import ContextObject
from core.context_assembly import ContextAssemblyEngine
from services.artifact_service import ArtifactService
from services.memory_service import MemoryService

logger = logging.getLogger(__name__)


# ARTIFACT_METADATA — maps artifact type (noun) to agent routing + display info.
# The orchestrator uses this to decide which agent handles a given artifact.
ARTIFACT_METADATA: Dict[str, Dict] = {
    "launch_plan": {
        "agent_attr": "planning_agent",
        "agent_name": "PlanningAgent",
        "label": "Launch Plan",
    },
    "campaign_plan": {
        "agent_attr": "campaign_agent",
        "agent_name": "CampaignAgent",
        "label": "Campaign Plan",
    },
    "content_calendar": {
        "agent_attr": "content_agent",
        "agent_name": "ContentPlanningAgent",
        "label": "Content Calendar",
    },
    "publishing_checklist": {
        "agent_attr": "content_agent",
        "agent_name": "ContentPlanningAgent",
        "label": "Publishing Checklist",
    },
    "release_complete": {
        "agent_attr": "planning_agent",
        "agent_name": "PlanningAgent",
        "label": "Release Complete",
    },
}

# INTENT_KEYWORDS — maps user language to artifact types (Intent Engine only).
# The orchestrator never uses this. Only the shell uses it to decide what the
# creator is asking for.
INTENT_KEYWORDS: Dict[str, list[str]] = {
    "launch_plan":          ["launch", "release", "drop", "roadmap"],
    "campaign_plan":        ["campaign", "marketing", "promotion", "strategy"],
    "content_calendar":     ["content", "calendar", "schedule", "post", "social",
                             "instagram", "twitter", "youtube", "tiktok",
                             "newsletter", "publish", "posting"],
    "publishing_checklist": ["publish", "publication", "publishing", "checklist", "deploy"],
    "release_complete":     ["release", "ship", "complete", "finish"],
}


def _resolve(artifact_type: str, key: str) -> Any:
    """Look up a field from ARTIFACT_METADATA by artifact type key.
    Falls back to launch_plan defaults if the type is unknown."""
    entry = ARTIFACT_METADATA.get(artifact_type)
    if entry:
        return entry[key]
    return ARTIFACT_METADATA["launch_plan"][key]


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
        from agents.orchestrator_agent import OrchestratorAgent
        self.agent_router = agent_router
        self.context_engine = ContextAssemblyEngine(memory_engine_client=MemoryService())
        self.orchestrator_agent = OrchestratorAgent()
        self.artifact_service = artifact_service or ArtifactService()
        self.memory_service = MemoryService()

        self._last_artifact_id: Optional[str] = None
        self._last_artifact_type: Optional[str] = None
        self._last_artifact_envelope: Optional[dict] = None
        self._last_provider: Optional[str] = None

    def run_flow(self, context: ContextObject, artifact_type: str = "launch_plan") -> Any:
        logger.info(f"Orchestrator running flow for: {context.user_request[:50]}")
        if not artifact_type:
            artifact_type = "launch_plan"

        result = self.orchestrator_agent.plan_execution(context, artifact_type=artifact_type)

        metadata = ARTIFACT_METADATA.get(artifact_type, ARTIFACT_METADATA["launch_plan"])
        agent_attr = metadata["agent_attr"]
        agent_name = metadata["agent_name"]

        agent = getattr(self.orchestrator_agent, agent_attr, self.orchestrator_agent.planning_agent)
        provider = getattr(agent, "_last_provider", None)
        self._last_provider = provider

        artifact_id = f"{artifact_type}_{int(time.time())}"
        self._last_artifact_id = artifact_id
        self._last_artifact_type = artifact_type

        data = result.model_dump() if hasattr(result, "model_dump") else result
        envelope = _build_artifact_envelope(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            workspace_id=context.workspace_id,
            project_id=context.project_id,
            created_by=agent_name,
            provider=provider,
            confidence=data.get("confidence_score"),
            data=data,
        )

        if envelope["artifact_type"] != artifact_type:
            raise RuntimeError(
                f"Artifact type mismatch: "
                f"expected={artifact_type}, "
                f"got={envelope['artifact_type']}"
            )

        self._last_artifact_envelope = envelope
        self.artifact_service.save_artifact(
            workspace_id=context.workspace_id,
            artifact_id=artifact_id,
            artifact_data=envelope,
        )

        self._ingest_session_memory(context, result, artifact_id, artifact_type)

        logger.info(f"Orchestrator flow complete, artifact: {artifact_id} ({artifact_type})")
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
