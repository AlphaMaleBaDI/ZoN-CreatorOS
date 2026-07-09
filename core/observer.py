import os
import json
import re
from typing import List, Dict, Optional, Tuple
from core.schemas import (
    Observation, ObservationSource, Belief, BeliefLifecycle,
    Tension, TensionSeverity, TensionPriority, CurrentUnderstanding,
    Requirement, RequirementStatus,
)

MIND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "zon_memory", "mind")

_TENSION_PATTERNS: List[Tuple[str, List[str], List[str], TensionSeverity, TensionPriority]] = [
    ("budget_ambition", ["budget", "cost", "limited", "tight", "cheap"], ["ambitious", "vision", "epic", "large", "premium", "high-end", "grand"], TensionSeverity.HIGH, TensionPriority.CRITICAL),
    ("time_quality", ["deadline", "timeline", "soon", "rush", "due", "hurry"], ["perfect", "quality", "polish", "refine", "meticulous"], TensionSeverity.HIGH, TensionPriority.CRITICAL),
    ("authenticity_virality", ["authentic", "real", "genuine", "organic", "raw"], ["viral", "trend", "popular", "mainstream", "algorithm"], TensionSeverity.HIGH, TensionPriority.HIGH),
    ("exploration_shipping", ["explore", "experiment", "discover", "iterate"], ["release", "launch", "ship", "finish", "complete"], TensionSeverity.MEDIUM, TensionPriority.MEDIUM),
    ("scope_resources", ["feature", "collab", "guest", "feature"], ["alone", "solo", "minimal", "simple"], TensionSeverity.MEDIUM, TensionPriority.MEDIUM),
]

_KEYWORD_MAP: List[Tuple[str, str, str]] = [
    (r"(?:making|creating|working\s+on|building|writing|producing)\s+(?:an|a|the|my)?\s*(.+)", "project_identity", "high"),
    (r"(?:budget|cost|spend|price)\s+(?:is|around|about|under|below|limited|tight)\s*(.+)", "budget_constraint", "medium"),
    (r"(?:deadline|timeline|release|launch|due)\s+(?:is|by|in|for)\s*(.+)", "timeline", "medium"),
    (r"(?:audience|target|fans|listeners|viewers)\s+(?:is|are|include|love|enjoy)\s*(.+)", "audience", "high"),
    (r"(?:style|genre|vibe|aesthetic|theme|concept)\s+(?:is|feels|explores|blends)\s*(.+)", "creative_direction", "high"),
    (r"((?:non\s*fiction|fiction|non-fiction|fantasy|sci-fi|science\s*fiction|mystery|thriller|romance|horror|drama|memoir|biography|comedy|satire|magical\s+realism|historical)\s+\w+)", "creative_direction", "high"),
    (r"(?:platform|distribute|post\s+on|upload\s+to|release\s+on)\s*(.+)", "distribution", "medium"),
    (r"(?:authentic|\breal\b|genuine|true\s+to)\s*(.+)", "values", "high"),
    (r"(?:collaborat|partner|feature|work\s+with)\s*(.+)", "collaboration", "medium"),
    (r"(?:goal|aim|objective|vision|mission)\s+(?:is|to)\s*(.+)", "goal", "high"),
    (r"(?:name|call(?:ed)?)\s+(?:it|the\s+(?:project|album|ep|song|track))\s*(.+)", "project_name", "high"),
    (r"(?:protagonist|main\s+character|hero|lead)\s+(?:is|named|called)\s*(.+)", "main_character", "high"),
    (r"(?:character|protagonist)\s+(?:is|named|called)\s*['\"]?(\w+)", "main_character", "high"),
    (r"\b(?:it's|this is|the story is|the protagonist is)\s+(?:about\s+)?(?:a\s+)?(?:young\s+)?(?:teenager|character|protagonist|person|girl|boy)\s+(?:named|called)\s+(\w+)", "main_character", "high"),
    (r"\b(?:I'm|I am|we're|we are|it'?s|this is)\s+(?:a|an|the)?\s*(.+)", "project_identity", "high"),
]


class CreatorMindObserver:

    def __init__(self):
        self._loaded: Dict[str, CurrentUnderstanding] = {}

    def _mind_path(self, workspace_id: str) -> str:
        return os.path.join(MIND_DIR, str(workspace_id), "creator_state.json")

    def load(self, workspace_id: str) -> CurrentUnderstanding:
        path = self._mind_path(workspace_id)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return CurrentUnderstanding(**data)
        return CurrentUnderstanding()

    def _save(self, workspace_id: str, state: CurrentUnderstanding) -> None:
        path = self._mind_path(workspace_id)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(state.model_dump_json(indent=2))

    def observe(self, message: str, workspace_id: str,
                source: ObservationSource = ObservationSource.CONVERSATION,
                domain=None, activity=None) -> CurrentUnderstanding:
        state = self.load(workspace_id)

        old_belief_snapshot = [(b.id, b.lifecycle.value, b.confidence) for b in state.beliefs]
        old_tension_count = len(state.tensions)

        observations = self._extract_observations(message, source, state)
        state.observations.extend(observations)

        self._update_beliefs(state, observations)

        self._detect_tensions(state)

        # Mission 021A: evaluate requirement satisfaction after every observe()
        self._evaluate_requirements(state, domain, message)

        if domain:
            state.domain = domain.value if hasattr(domain, 'value') else str(domain)
        if activity:
            state.activity = activity.value if hasattr(activity, 'value') else str(activity)

        if self._understanding_changed(state, old_belief_snapshot, old_tension_count):
            state.version += 1

        self._update_derived_trace(state)
        self._save(workspace_id, state)
        return state

    def get_state(self, workspace_id: str) -> CurrentUnderstanding:
        return self.load(workspace_id)

    # ------------------------------------------------------------------
    def _next_obs_id(self, state: CurrentUnderstanding) -> str:
        return f"obs_{len(state.observations) + 1:03d}"

    def _next_belief_id(self, state: CurrentUnderstanding) -> str:
        return f"belief_{len(state.beliefs) + 1:03d}"

    def _extract_observations(self, message: str, source: ObservationSource, state: CurrentUnderstanding) -> List[Observation]:
        results: List[Observation] = []

        for pattern, category, impact in _KEYWORD_MAP:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                extracted = match.group(1).strip().rstrip(".,!?;:")
                if len(extracted) > 3:
                    results.append(Observation(
                        id=self._next_obs_id(state) if not results else f"obs_{len(state.observations) + len(results) + 1:03d}",
                        content=category + ": " + extracted,
                        confidence=0.75,
                        source=source,
                        impact=impact,
                    ))

        if not results:
            results.append(Observation(
                id=self._next_obs_id(state),
                content=message.strip(),
                confidence=0.6,
                source=source,
                impact="low",
            ))

        return results

    def _update_beliefs(self, state: CurrentUnderstanding, observations: List[Observation]) -> None:
        for obs in observations:
            obs_words = set(w.lower() for w in re.findall(r'\w+', obs.content) if len(w) > 3)
            # Mission 021B: extract named entities (capitalised words ≥ 3 chars)
            obs_entities = set(re.findall(r'\b[A-Z][a-z]{2,}\b', obs.content))

            matched: Optional[Belief] = None
            for belief in state.beliefs:
                if belief.lifecycle not in (BeliefLifecycle.ACTIVE, BeliefLifecycle.CHALLENGED, BeliefLifecycle.CANDIDATE):
                    continue
                belief_words = set(w.lower() for w in re.findall(r'\w+', belief.statement) if len(w) > 3)
                belief_entities = set(re.findall(r'\b[A-Z][a-z]{2,}\b', belief.statement))

                # Merge on: shared named entity (e.g. "Sarah") OR word overlap ≥ 2
                entity_match = bool(obs_entities & belief_entities)
                word_overlap = len(obs_words & belief_words)
                if entity_match or word_overlap >= 2:
                    matched = belief
                    break

            if matched:
                if obs.confidence >= 0.7:
                    # Refresh statement to the latest description (living belief)
                    # Strip category prefix so we don't overwrite rich text with "main_character: sarah"
                    clean_content = re.sub(
                        r'^(project_identity|budget_constraint|timeline|audience|creative_direction'
                        r'|distribution|values|collaboration|goal|project_name|main_character):\s*',
                        '', obs.content,
                    ).strip()
                    # Only refresh if new content is meaningfully longer (richer)
                    if len(clean_content) > len(matched.statement):
                        matched.statement = clean_content[:120]
                    matched.lifecycle = BeliefLifecycle.ACTIVE
                    matched.confidence = min(1.0, matched.confidence + 0.08)
                else:
                    matched.lifecycle = BeliefLifecycle.CHALLENGED
                    matched.confidence = max(0.1, matched.confidence - 0.05)
                if obs.id not in matched.observation_ids:
                    matched.observation_ids.append(obs.id)
            else:
                raw = obs.content
                clean = re.sub(r'^(project_identity|budget_constraint|timeline|audience|creative_direction|distribution|values|collaboration|goal|project_name|main_character):\s*', '', raw)
                state.beliefs.append(Belief(
                    id=self._next_belief_id(state),
                    statement=clean[:120],
                    confidence=obs.confidence * 0.8,
                    lifecycle=BeliefLifecycle.ACTIVE if obs.confidence >= 0.7 else BeliefLifecycle.CANDIDATE,
                    observation_ids=[obs.id],
                    source="deterministic",
                ))

    def _evaluate_requirements(self, state: CurrentUnderstanding, domain, raw_message: str) -> None:
        """Mission 021A — Evaluate domain requirements after every observe() call.

        Strategy (beliefs are primary; raw message is fallback):
        1. For each DiscoveryPriority in the domain profile:
           a. If already CONFIRMED or RESOLVED — skip (invariant: only moves forward).
           b. Search active/candidate beliefs for keyword match → CONFIRMED.
           c. If no belief match, search raw_message for keyword match → SUSPECTED.
        2. Challenged requirements (user contradiction) remain challengeable
           but are not overwritten here — that's the Observer's interruption path.
        """
        if not domain or getattr(domain, 'value', '') == 'unknown':
            return

        try:
            from core.domains import get_domain_profile
            profile = get_domain_profile(domain)
        except ImportError:
            return

        if not profile or not profile.discovery_priorities:
            return

        # Build requirement lookup keyed by area
        req_map: Dict[str, Requirement] = {r.area: r for r in state.requirement_states}

        raw_lower = raw_message.lower()
        active_statuses = (BeliefLifecycle.ACTIVE, BeliefLifecycle.CHALLENGED, BeliefLifecycle.CANDIDATE)

        for priority in profile.discovery_priorities:
            existing = req_map.get(priority.area)

            # Initialise if first time we've seen this requirement
            if not existing:
                existing = Requirement(area=priority.area, question=priority.question)
                state.requirement_states.append(existing)
                req_map[priority.area] = existing

            # CONFIRMED / RESOLVED are final — never downgrade
            if existing.status in (RequirementStatus.CONFIRMED, RequirementStatus.RESOLVED):
                continue

            keywords = priority.keywords or []
            evaluator = getattr(priority, 'evaluator', None)

            # EVALUATOR takes priority — understands what satisfies a requirement
            if evaluator and evaluator(state.beliefs, raw_message):
                existing.status = RequirementStatus.CONFIRMED
                existing.confidence = max(existing.confidence, 0.7)
                if state.observations:
                    last_obs_id = state.observations[-1].id
                    if last_obs_id not in existing.evidence_ids:
                        existing.evidence_ids.append(last_obs_id)
                continue

            # PRIMARY: check beliefs via keyword matching
            belief_satisfied = False
            for belief in state.beliefs:
                if belief.lifecycle not in active_statuses:
                    continue
                belief_lower = belief.statement.lower()
                if keywords and any(kw in belief_lower for kw in keywords):
                    existing.status = RequirementStatus.CONFIRMED
                    existing.confidence = max(existing.confidence, round(belief.confidence, 2))
                    if belief.id not in existing.evidence_ids:
                        existing.evidence_ids.append(belief.id)
                    belief_satisfied = True
                    break

            if belief_satisfied:
                continue

            # FALLBACK: check raw message (weaker signal; does not override belief-based CONFIRMED)
            if keywords and any(kw in raw_lower for kw in keywords):
                if existing.status == RequirementStatus.UNKNOWN:
                    existing.status = RequirementStatus.SUSPECTED
                existing.confidence = max(existing.confidence, 0.55)
                if state.observations:
                    last_obs_id = state.observations[-1].id
                    if last_obs_id not in existing.evidence_ids:
                        existing.evidence_ids.append(last_obs_id)


    def _detect_tensions(self, state: CurrentUnderstanding) -> None:
        active = [b for b in state.beliefs if b.lifecycle in (BeliefLifecycle.ACTIVE, BeliefLifecycle.CHALLENGED)]

        for tension_id, left_terms, right_terms, default_severity, default_priority in _TENSION_PATTERNS:
            left = [b for b in active if any(t in b.statement.lower() for t in left_terms)]
            right = [b for b in active if any(t in b.statement.lower() for t in right_terms)]

            if not left or not right:
                continue

            all_ids = list(set(b.id for b in left + right))

            existing = [t for t in state.tensions if t.id.startswith(tension_id) and t.status == "active"]
            if existing:
                existing[0].belief_ids = list(set(existing[0].belief_ids + all_ids))
            else:
                label = left_terms[0].capitalize()
                label2 = right_terms[0].capitalize()
                state.tensions.append(Tension(
                    id=f"{tension_id}_{len(state.tensions) + 1:02d}",
                    description=f"{label} vs {label2}",
                    belief_ids=all_ids,
                    severity=default_severity,
                    priority=default_priority,
                ))

    def _understanding_changed(self, state: CurrentUnderstanding, old_snapshot: List[Tuple[str, str, float]], old_tension_count: int) -> bool:
        if len(state.tensions) != old_tension_count:
            return True
        for i, belief in enumerate(state.beliefs):
            if i < len(old_snapshot):
                old_id, old_lifecycle, old_conf = old_snapshot[i]
                if belief.id == old_id and (belief.lifecycle.value != old_lifecycle or abs(belief.confidence - old_conf) > 0.05):
                    return True
        if len(state.beliefs) != len(old_snapshot):
            return True
        return False

    def _update_derived_trace(self, state: CurrentUnderstanding) -> None:
        if state.observations:
            state.derived_from_observation = state.observations[-1].id
        active = [b.id for b in state.beliefs if b.lifecycle in (BeliefLifecycle.ACTIVE, BeliefLifecycle.CHALLENGED)]
        if active:
            state.derived_from_beliefs = active[-1]
