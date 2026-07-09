import time
import logging
from typing import Optional, Any, Dict, List, Set
from uuid import UUID

from core.schemas import ContextObject, PIEAssessment, PipelineMetrics
from core.context_assembly import ContextAssemblyEngine
from core.orchestration import Orchestrator, _resolve
from core.pie import ProductionIntelligenceEngine
from core.eval import EvaluationEngine
from services.workspace_service import WorkspaceService
from services.profile_service import ProfileService
from services.artifact_service import ArtifactService
from services.snapshot_service import SnapshotService
from core.pipeline_progress import update as update_pipeline

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
        self.evaluator = EvaluationEngine()

        self.initialized = False
        self.current_workspace = None
        self.current_profile = None
        self.current_profile_dict: dict = {}
        self.current_projects: List[dict] = []
        self.recent_artifacts: List[dict] = []
        self._metrics = PipelineMetrics()

    def initialize(
        self,
        workspace_id: Optional[UUID] = None,
        creator_name: Optional[str] = None
    ) -> "Kernel":
        t0 = time.perf_counter()
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
        self._metrics.kernel_boot_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(f"Kernel initialized in {self._metrics.kernel_boot_ms}ms.")
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
        t0 = time.perf_counter()
        ctx = self.context_engine.assemble_context(
            workspace_id=self.current_workspace.workspace_id,
            project_id=project_id,
            user_request=user_request,
            creator_profile=self.current_profile_dict,
            recent_artifacts=self.recent_artifacts,
            active_projects=self.current_projects,
        )
        self._metrics.context_assembly_ms = round((time.perf_counter() - t0) * 1000, 1)
        logger.info(f"  Context assembly in {self._metrics.context_assembly_ms}ms.")
        return ctx

    def execute(self, context: ContextObject, artifact_type: str = "launch_plan") -> Any:
        if not self.initialized:
            raise RuntimeError(
                "Kernel invariant violated: "
                "initialize() must be called before execute()."
            )
        t0 = time.perf_counter()
        if not artifact_type:
            artifact_type = "launch_plan"
        agent_label = _resolve(artifact_type, "label")
        update_pipeline("orchestration", 0.2, f"Running {agent_label} Agent...", 0)

        result = self.orchestrator.run_flow(context, artifact_type=artifact_type)
        self._metrics.orchestration_ms = round((time.perf_counter() - t0) * 1000, 1)
        self._metrics.provider = self.orchestrator._last_provider or ""

        t1 = time.perf_counter()
        update_pipeline("snapshot", 0.4, "Recording snapshot...", int((t1 - t0) * 1000))
        last_type = self.orchestrator._last_artifact_type or "launch_plan"
        self.snapshot_service.record(
            workspace_id=context.workspace_id,
            creator_name=self.current_profile_dict.get("creator_name"),
            project_id=context.project_id,
            artifact_id=self.orchestrator._last_artifact_id,
            artifact_type=last_type,
            provider=self.orchestrator._last_provider,
            intent=last_type,
            confidence=getattr(result, "confidence_score", None),
        )
        self._metrics.snapshot_ms = round((time.perf_counter() - t1) * 1000, 1)

        t2 = time.perf_counter()
        update_pipeline("eval", 0.6, "Evaluating artifact quality...", int((t2 - t0) * 1000))
        artifact_data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
        eval_assessment = self.evaluator.evaluate(
            artifact=artifact_data,
            artifact_type=self.orchestrator._last_artifact_type or "launch_plan",
        )
        self._metrics.eval_ms = round((time.perf_counter() - t2) * 1000, 1)
        result._eval_assessment = eval_assessment

        t3 = time.perf_counter()
        update_pipeline("pie", 0.8, "Assessing production state...", int((t3 - t0) * 1000))
        eval_scores = self._extract_eval_scores(eval_assessment)
        pie_assessment = self.pie.analyze(
            artifact_type=self.orchestrator._last_artifact_type or "launch_plan",
            existing_artifact_types=self._get_existing_types(),
            eval_scores=eval_scores,
        )
        self._metrics.pie_ms = round((time.perf_counter() - t3) * 1000, 1)
        result._pie_assessment = pie_assessment

        elapsed = int((time.perf_counter() - t0) * 1000)
        self._metrics.total_ms = round(elapsed, 1)
        result._pipeline_metrics = self._metrics

        update_pipeline("complete", 1.0, "Workspace updated.", elapsed)
        return result

    def continue_production(self, user_request: str, project_id: Optional[UUID] = None) -> Any:
        pie = self.pie.analyze(
            artifact_type=self.orchestrator._last_artifact_type or "launch_plan",
            existing_artifact_types=self._get_existing_types(),
            eval_scores={},
        )
        if not pie.recommended_next:
            logger.info("PIE: no next artifact recommended — production complete or unknown path")
            return None

        context = self.assemble_context(
            user_request=user_request,
            project_id=project_id,
        )
        return self.execute(context, artifact_type=pie.recommended_next[0])

    def _get_existing_types(self) -> Set[str]:
        types = set()
        if self.current_workspace:
            artifact_ids = self.artifact_service.list_artifacts(self.current_workspace.workspace_id)
            for aid in artifact_ids:
                art = self.artifact_service.retrieve_artifact(aid, self.current_workspace.workspace_id)
                if art and isinstance(art, dict):
                    atype = art.get("artifact_type")
                    if atype:
                        types.add(atype)
        for art in self.recent_artifacts:
            atype = art.get("artifact_type") if isinstance(art, dict) else None
            if atype:
                types.add(atype)
        if self.orchestrator._last_artifact_type:
            types.add(self.orchestrator._last_artifact_type)
        return types

    def _extract_eval_scores(self, eval_assessment) -> Dict[str, float]:
        """Extract per-artifact eval scores for state derivation.

        Since the kernel only evaluates the current artifact, we return
        a single-entry dict. Future iterations may aggregate historical scores.
        """
        scores = {}
        if eval_assessment:
            scores[eval_assessment.artifact_type] = eval_assessment.score
        return scores
