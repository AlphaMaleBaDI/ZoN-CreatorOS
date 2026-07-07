import logging
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from core.schemas import (
    PIEAssessment,
    ProductionState,
    StateAssessment,
    StateEvidence,
)

logger = logging.getLogger(__name__)

# Production Knowledge Graph (PKG) v0
# Static adjacency map: artifact_type -> valid next artifact types
# Deterministic, testable, observable. No database, no LLM.
PRODUCTION_KNOWLEDGE_GRAPH: dict[str, list[str]] = {
    "launch_plan":            ["campaign_plan", "content_calendar", "press_release"],
    "campaign_plan":          ["budget_plan", "content_calendar"],
    "content_calendar":       ["content_script", "production_schedule"],
    "press_release":          ["media_kit", "press_distribution"],
    "budget_plan":            ["resource_allocation"],
    "content_script":         [],
    "production_schedule":    [],
    "media_kit":              [],
    "press_distribution":     [],
    "resource_allocation":    [],
}

# -- Production State Machine (Mission 009) --------------------------------

# Kernel-level: state definitions (domain-agnostic)
STATE_DEFINITIONS: dict[str, dict] = {
    "ideation":    {"display": "Ideation",    "progress_range": (0.0, 0.15)},
    "planning":    {"display": "Planning",    "progress_range": (0.15, 0.45)},
    "production":  {"display": "Production",  "progress_range": (0.45, 0.75)},
    "publishing":  {"display": "Publishing",  "progress_range": (0.75, 0.90)},
    "released":    {"display": "Released",    "progress_range": (0.90, 1.0)},
    "archived":    {"display": "Archived",    "progress_range": (1.0, 1.0)},
}

# Domain-level: artifact-to-state mapping for Music domain
# Each artifact type maps to a production state. Some are required for
# state transitions; others are optional enrichments.
MUSIC_ARTIFACT_STATE_MAP: dict[str, dict] = {
    "launch_plan":            {"state": "planning",    "required_for_transition": True},
    "campaign_plan":          {"state": "planning",    "required_for_transition": True},
    "content_calendar":       {"state": "production",  "required_for_transition": True},
    "asset_checklist":        {"state": "production",  "required_for_transition": False},
    "publishing_checklist":   {"state": "publishing",  "required_for_transition": True},
    "release_complete":       {"state": "released",    "required_for_transition": True},
    "press_release":          {"state": "publishing",  "required_for_transition": False},
    "budget_plan":            {"state": "planning",    "required_for_transition": False},
    "content_script":         {"state": "production",  "required_for_transition": False},
    "production_schedule":    {"state": "production",  "required_for_transition": False},
    "media_kit":              {"state": "publishing",  "required_for_transition": False},
    "press_distribution":     {"state": "publishing",  "required_for_transition": False},
    "resource_allocation":    {"state": "production",  "required_for_transition": False},
}

# Ordered state list for transition logic
STATE_ORDER = ["ideation", "planning", "production", "publishing", "released", "archived"]


def _reachable_types(root: str, graph: dict[str, list[str]]) -> Set[str]:
    """BFS from root to find all reachable artifact types."""
    visited = set()
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for child in graph.get(node, []):
            if child not in visited:
                queue.append(child)
    return visited


def _existing_types(existing_artifacts: list[dict]) -> Set[str]:
    types = set()
    for art in existing_artifacts:
        atype = art.get("artifact_type") if isinstance(art, dict) else None
        if atype:
            types.add(atype)
    return types


NARRATIVE_MAP: dict[str, str] = {
    "launch_plan": "Launch strategy established. The creative vision is now documented with a structured release approach.",
    "campaign_plan": "Campaign strategy completed. Audience messaging and channel positioning are defined.",
    "content_calendar": "Content calendar ready. Scheduled posts and platform cadence aligned with the campaign.",
    "press_release": "Press materials prepared. Media outreach and announcement messaging are ready.",
    "budget_plan": "Budget planned. Resource allocation and cost structure are documented.",
    "content_script": "Content scripts written. Video, audio, and written materials are drafted.",
    "production_schedule": "Production timeline set. Milestones and deliverables are scheduled.",
    "media_kit": "Media kit assembled. Brand assets, bios, and press materials are packaged.",
    "press_distribution": "Press distribution configured. Media contacts and submission deadlines are set.",
    "resource_allocation": "Resources allocated. Team, tools, and budget assignments are finalized.",
}


class ProductionIntelligenceEngine:
    """
    PIE v0 — stateless decision service owned by the Kernel.

    Inspects an artifact + workspace state and answers:
      1. What already exists?
      2. What's missing?
      3. What should happen next?
      4. How complete is the production path?

    Mission 009 adds:
      5. What phase is this project in?
      6. What evidence supports that phase?
      7. What is required to reach the next phase?
    """

    def __init__(
        self,
        graph: dict[str, list[str]] | None = None,
        state_map: dict[str, dict] | None = None,
    ):
        self.graph = graph or PRODUCTION_KNOWLEDGE_GRAPH
        self.state_map = state_map or MUSIC_ARTIFACT_STATE_MAP

    def analyze(
        self,
        artifact_type: str,
        existing_artifact_types: Set[str],
        eval_scores: Dict[str, float] | None = None,
    ) -> PIEAssessment:
        eval_scores = eval_scores or {}
        state_assessment = self.determine_state(
            existing_artifact_types=existing_artifact_types,
            eval_scores=eval_scores,
        )

        if artifact_type not in self.graph:
            logger.info(f"PIE: unknown artifact type '{artifact_type}' — no recommendations")
            return PIEAssessment(
                production_state=state_assessment.current_state.value,
                completed=list(existing_artifact_types),
                missing=[],
                recommended_next=[],
                production_progress=1.0,
                confidence=1.0,
                narrative="Artifact type not recognized. Production assessment is unavailable.",
                state_assessment=state_assessment,
            )

        reachable = _reachable_types(artifact_type, self.graph)
        completed_set = {t for t in reachable if t in existing_artifact_types}
        missing_set = reachable - completed_set

        completed_sorted = sorted(completed_set)
        missing_sorted = sorted(missing_set, key=self._priority_key)

        total = len(reachable)
        progress = len(completed_sorted) / total if total > 0 else 1.0

        recommended = self._rank_next(missing_sorted, artifact_type)[:3]

        total_graph = sum(len(v) for v in self.graph.values())
        graph_density = total_graph / max(len(self.graph), 1)
        confidence = min(1.0, 0.7 + (progress * 0.2) + (graph_density * 0.1))

        narrative = self._build_narrative(artifact_type, completed_sorted, recommended)

        state_assessment = self.determine_state(
            existing_artifact_types=existing_artifact_types,
            eval_scores=eval_scores or {},
        )

        logger.info(
            f"PIE: type={artifact_type} reachable={total} "
            f"completed={len(completed_sorted)} missing={len(missing_sorted)} "
            f"progress={progress:.0%} next={recommended} "
            f"state={state_assessment.current_state.value}"
        )

        return PIEAssessment(
            production_state=state_assessment.current_state.value,
            completed=completed_sorted,
            missing=sorted(missing_set),
            recommended_next=recommended,
            production_progress=round(progress, 2),
            confidence=round(confidence, 2),
            narrative=narrative,
            state_assessment=state_assessment,
        )

    @staticmethod
    def _build_narrative(artifact_type: str, completed: list[str], recommended: list[str]) -> str:
        parts = []
        last_completed = completed[-1] if completed else artifact_type
        line = NARRATIVE_MAP.get(last_completed, "")
        if line:
            parts.append(line)
        state = ProductionIntelligenceEngine._derive_state(len(completed) / max(len(completed) + len(recommended), 1))
        if state == "planning":
            parts.append("Production is in early stages. Core foundation is being established.")
        elif state == "production":
            parts.append("Production has advanced. Momentum is building toward completion.")
        elif state == "review":
            parts.append("Most deliverables are complete. Focus is shifting to quality review.")
        elif state == "publishing":
            parts.append("Production is nearly complete. Final deliverables are being prepared.")
        elif state == "completed":
            parts.append("All production deliverables are complete. The project is ready.")
        if recommended:
            parts.append(f"Recommended next step: {recommended[0].replace('_', ' ').title()}.")
        return " ".join(parts)

    def determine_state(
        self,
        existing_artifact_types: Set[str],
        eval_scores: Dict[str, float],
    ) -> StateAssessment:
        """Derive the current production state from evidence (artifacts + eval scores).

        State is always derived, never stored. This guarantees truthfulness
        and prevents drift between stored state and actual evidence.
        """
        evidence = self._build_evidence(existing_artifact_types, eval_scores)
        current = self._compute_current_state(existing_artifact_types, eval_scores)
        next_state, can_transition, blockers = self._evaluate_transition(
            current, existing_artifact_types, eval_scores
        )
        requirements = self._build_requirements(next_state, blockers)

        return StateAssessment(
            current_state=current,
            evidence=evidence,
            requirements=requirements,
            next_state=next_state,
            can_transition=can_transition,
            blockers=blockers,
        )

    def _build_evidence(
        self,
        existing_types: Set[str],
        eval_scores: Dict[str, float],
    ) -> List[StateEvidence]:
        result = []
        for art_type, mapping in self.state_map.items():
            exists = art_type in existing_types
            score = eval_scores.get(art_type)
            passed = score >= 0.6 if score is not None else None
            result.append(StateEvidence(
                artifact_type=art_type,
                exists=exists,
                eval_score=score,
                eval_passed=passed,
            ))
        result.sort(key=lambda e: (not e.exists, e.artifact_type))
        return result

    def _compute_current_state(
        self,
        existing_types: Set[str],
        eval_scores: Dict[str, float],
    ) -> ProductionState:
        """Determine the current production state based on commitments made.

        The question is 'What commitment has the creator made?'
        not 'What artifact exists?'

        Commitment is evidenced by:
        - Required artifacts exist for a given state
        - Eval scores for those artifacts meet thresholds
        """
        state_scores = self._score_states(existing_types, eval_scores)
        best_score = max(state_scores.values())
        if best_score == 0.0:
            return ProductionState.IDEATION
        best_state = max(state_scores, key=lambda s: (state_scores[s], STATE_ORDER.index(s)))
        return ProductionState(best_state)

    def _score_states(
        self,
        existing_types: Set[str],
        eval_scores: Dict[str, float],
    ) -> Dict[str, float]:
        """Score each state based on commitment evidence.

        The question is: 'What commitment has the creator made?'
        Only required-for-transition artifacts count toward a state's score.
        Optional artifacts are enrichment — they don't affect state derivation.

        A state's score = (fulfilled required artifacts) / (total required artifacts).
        If tied, the later state in the lifecycle wins (deeper commitment).
        """
        scores = {}
        for state in STATE_ORDER:
            artifacts_in_state = [
                (t, m) for t, m in self.state_map.items()
                if m["state"] == state
            ]
            if not artifacts_in_state:
                scores[state] = 0.0
                continue

            required_count = 0
            fulfilled_count = 0.0

            for art_type, mapping in artifacts_in_state:
                if not mapping["required_for_transition"]:
                    continue
                required_count += 1
                if art_type in existing_types:
                    score = eval_scores.get(art_type)
                    if score is not None and score >= 0.6:
                        fulfilled_count += 1.0
                    elif score is not None:
                        fulfilled_count += 0.5
                    else:
                        fulfilled_count += 0.3

            scores[state] = fulfilled_count / max(required_count, 1) if required_count > 0 else 0.0

        return scores

    def _evaluate_transition(
        self,
        current: ProductionState,
        existing_types: Set[str],
        eval_scores: Dict[str, float],
    ) -> Tuple[Optional[ProductionState], bool, List[str]]:
        """Check if the project can transition to the next state.

        A transition requires that the CURRENT state's required-for-transition
        artifacts exist with passing eval scores. This is asymmetric:
        harder to advance than to stay.

        Example: to move from Planning to Production, both Launch Plan and
        Campaign Plan must exist with eval >= 0.6. The Content Calendar
        (a Production artifact) is NOT required — it is produced IN Production.
        """
        current_idx = STATE_ORDER.index(current.value)
        if current_idx >= len(STATE_ORDER) - 1:
            return None, False, ["Project has reached the final state."]

        next_state_str = STATE_ORDER[current_idx + 1]
        next_state = ProductionState(next_state_str)

        blockers = []

        # Special case: Ideation requires at least one artifact to advance
        if current == ProductionState.IDEATION and not existing_types:
            blockers.append("No artifacts exist. Create your first artifact to begin production.")
            return next_state, False, blockers

        for art_type, mapping in self.state_map.items():
            if mapping["state"] != current.value:
                continue
            if not mapping["required_for_transition"]:
                continue
            if art_type not in existing_types:
                blockers.append(f"{art_type.replace('_', ' ').title()} does not exist")
                continue
            score = eval_scores.get(art_type)
            if score is not None and score < 0.6:
                blockers.append(f"{art_type.replace('_', ' ').title()} eval below threshold ({score}/0.6)")

        can_transition = len(blockers) == 0
        return next_state, can_transition, blockers

    def _build_requirements(self, next_state: Optional[ProductionState], blockers: List[str]) -> List[str]:
        """Translate blockers into actionable requirements."""
        if not next_state:
            return ["All phases complete. Project is ready for archival or release."]
        if not blockers:
            return [f"Advance to {next_state.value.title()} phase."]
        return [f"{b}. Resolve to advance to {next_state.value.title()}." for b in blockers]

    @staticmethod
    def _derive_state(progress: float) -> str:
        if progress >= 1.0:
            return "completed"
        if progress >= 0.85:
            return "publishing"
        if progress >= 0.6:
            return "review"
        if progress >= 0.35:
            return "production"
        return "planning"

    def _priority_key(self, artifact_type: str) -> int:
        """Lower number = higher priority. Direct children of root rank first."""
        for depth, children in enumerate(self._layer_map()):
            if artifact_type in children:
                return depth
        return 99

    def _layer_map(self) -> list[set]:
        """Returns adjacency layers for priority scoring."""
        layers = []
        seen: set = set()
        current = set(self.graph.keys()) - seen
        while current:
            layers.append(current)
            seen |= current
            next_set: set = set()
            for node in current:
                next_set |= set(self.graph.get(node, []))
            current = next_set - seen
        return layers

    def _rank_next(self, missing: list[str], root: str) -> list[str]:
        """Prioritize direct children of completed artifacts."""
        direct = self.graph.get(root, [])
        direct_missing = [t for t in missing if t in direct]
        indirect_missing = [t for t in missing if t not in direct]
        return direct_missing + indirect_missing
