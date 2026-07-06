import time
import logging
from typing import Optional, Any, List, Set
from uuid import UUID

from core.schemas import ContextObject, PIEAssessment
from core.context_assembly import ContextAssemblyEngine
from core.orchestration import Orchestrator
from core.pie import ProductionIntelligenceEngine
from services.workspace_service import WorkspaceService
from services.profile_service import ProfileService
from services.artifact_service import ArtifactService
from services.snapshot_service import SnapshotService

logger = logging.getLogger(__name__)


class Kernel:
    """
    CreatorOS Kernel — enforces the core invariant:
    No model executes before Context Assembly completes.

    Initialization flow:
        Load Workspace → Load Profile → Load Projects
        → Load Artifacts → Assemble Context → Execute Agents
    """

    def __init__(self):
        self.workspace_service = WorkspaceService()
        self.profile_service = ProfileService()
        self.artifact_service = ArtifactService()
        self.snapshot_service = SnapshotService()
        self.context_engine = ContextAssemblyEngine()
        self.orchestrator = Orchestrator(artifact_service=self.artifact_service)
        self.pie = ProductionIntelligenceEngine()

        self.initialized = False
        self.current_workspace = None
        self.current_profile = None
        self.current_profile_dict: dict = {}
        self.current_projects: List[dict] = []
        self.recent_artifacts: List[dict] = []

    def initialize(
        self,
        workspace_id: Optional[UUID] = None,
        creator_name: Optional[str] = None
    ) -> "Kernel":
        logger.info("Kernel initializing...")

        ws = None
        if workspace_id:
            ws = self.workspace_service.get_workspace(workspace_id)
        if not ws:
            workspaces = self.workspace_service.list_workspaces()
            if workspaces:
                ws = workspaces[0]
            else:
                ws = self.workspace_service.create_workspace("Default Workspace")
        self.current_workspace = ws
        logger.info(f"  Workspace loaded: '{ws.name}' ({str(ws.workspace_id)[:8]}...)")

        profile = None
        if creator_name:
            profile = self.profile_service.get_creator_profile(creator_name)
        self.current_profile = profile
        self.current_profile_dict = profile.model_dump() if profile else {}
        if profile:
            logger.info(f"  Profile loaded: '{profile.creator_name}'")
        else:
            logger.info(f"  Profile: none (creator_name={creator_name})")

        projects = self.workspace_service.list_projects(ws.workspace_id)
        self.current_projects = [p.model_dump() for p in projects]
        logger.info(f"  Projects loaded: {len(projects)} active")

        artifact_ids = self.artifact_service.list_artifacts(ws.workspace_id)
        recent = []
        for aid in artifact_ids[-5:]:
            art = self.artifact_service.retrieve_artifact(aid, ws.workspace_id)
            if art:
                recent.append(art)
        self.recent_artifacts = recent
        logger.info(f"  Recent artifacts loaded: {len(recent)}")

        self.initialized = True
        logger.info("Kernel initialized. Ready for context assembly.")
        return self

    def assemble_context(
        self,
        user_request: str,
        project_id: Optional[UUID] = None,
    ) -> ContextObject:
        if not self.initialized:
            raise RuntimeError(
                "Kernel invariant violated: "
                "initialize() must be called before assemble_context(). "
                "No model executes before Context Assembly completes."
            )
        return self.context_engine.assemble_context(
            workspace_id=self.current_workspace.workspace_id,
            project_id=project_id,
            user_request=user_request,
            creator_profile=self.current_profile_dict,
            recent_artifacts=self.recent_artifacts,
            active_projects=self.current_projects,
        )

    def execute(self, context: ContextObject) -> Any:
        if not self.initialized:
            raise RuntimeError(
                "Kernel invariant violated: "
                "initialize() must be called before execute()."
            )
        result = self.orchestrator.run_flow(context)

        self.snapshot_service.record(
            workspace_id=context.workspace_id,
            creator_name=self.current_profile_dict.get("creator_name"),
            project_id=context.project_id,
            artifact_id=self.orchestrator._last_artifact_id,
            artifact_type="launch_plan",
            provider=self.orchestrator._last_provider,
            intent="launch_plan",
            confidence=getattr(result, "confidence_score", None),
        )

        pie_assessment = self.pie.analyze(
            artifact_type=self.orchestrator._last_artifact_type or "launch_plan",
            existing_artifact_types=self._get_existing_types(),
        )
        result._pie_assessment = pie_assessment

        return result

    def _get_existing_types(self) -> Set[str]:
        types = set()
        for art in self.recent_artifacts:
            atype = art.get("artifact_type") if isinstance(art, dict) else None
            if atype:
                types.add(atype)
        if self.orchestrator._last_artifact_type:
            types.add(self.orchestrator._last_artifact_type)
        return types
