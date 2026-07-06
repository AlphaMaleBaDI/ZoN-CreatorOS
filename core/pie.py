import logging
from collections import deque
from typing import List, Set

from core.schemas import PIEAssessment

logger = logging.getLogger(__name__)

# Production Knowledge Graph (PKG) v0
# Static adjacency map: artifact_type -> valid next artifact types
# Deterministic, testable, observable. No database, no LLM.
PRODUCTION_KNOWLEDGE_GRAPH: dict[str, list[str]] = {
    "launch_plan":      ["campaign_plan", "content_calendar", "press_release"],
    "campaign_plan":    ["budget_plan", "content_calendar"],
    "content_calendar": ["content_script", "production_schedule"],
    "press_release":    ["media_kit", "press_distribution"],
    "budget_plan":      ["resource_allocation"],
    "content_script":   [],
    "production_schedule": [],
    "media_kit":        [],
    "press_distribution": [],
    "resource_allocation": [],
}


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


class ProductionIntelligenceEngine:
    """
    PIE v0 — stateless decision service owned by the Kernel.

    Inspects an artifact + workspace state and answers:
      1. What already exists?
      2. What's missing?
      3. What should happen next?
      4. How complete is the production path?
    """

    def __init__(self, graph: dict[str, list[str]] | None = None):
        self.graph = graph or PRODUCTION_KNOWLEDGE_GRAPH

    def analyze(
        self,
        artifact_type: str,
        existing_artifact_types: Set[str],
    ) -> PIEAssessment:
        if artifact_type not in self.graph:
            logger.info(f"PIE: unknown artifact type '{artifact_type}' — no recommendations")
            return PIEAssessment(
                production_state=self._derive_state(1.0),
                completed=list(existing_artifact_types),
                missing=[],
                recommended_next=[],
                production_progress=1.0,
                confidence=1.0,
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

        logger.info(
            f"PIE: type={artifact_type} reachable={total} "
            f"completed={len(completed_sorted)} missing={len(missing_sorted)} "
            f"progress={progress:.0%} next={recommended}"
        )

        return PIEAssessment(
            production_state=self._derive_state(progress),
            completed=completed_sorted,
            missing=sorted(missing_set),
            recommended_next=recommended,
            production_progress=round(progress, 2),
            confidence=round(confidence, 2),
        )

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
