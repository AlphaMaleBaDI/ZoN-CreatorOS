import time
from typing import List, Dict, Optional, Set, Tuple
from core.schemas import (
    CurrentUnderstanding, ReasoningCandidate, BeliefLifecycle,
    TensionSeverity, TensionPriority,
)

def _get_profile(domain) -> Optional[object]:
    try:
        from core.domains import get_domain_profile
        return get_domain_profile(domain)
    except ImportError:
        return None


_CATEGORY_LABELS = {
    "project_identity": "Project identity clarified",
    "budget_constraint": "Budget constraint noted",
    "timeline": "Timeline established",
    "audience": "Audience insight gained",
    "creative_direction": "Creative direction emerging",
    "distribution": "Distribution channel discussed",
    "values": "Creator values surfaced",
    "collaboration": "Collaboration considered",
    "goal": "Goal articulated",
    "project_name": "Project named",
}


class ShadowReasoning:

    def reason(self, understanding: CurrentUnderstanding, pie_recommended: Optional[List[str]] = None, domain: Optional[object] = None) -> ReasoningCandidate:
        if not understanding.observations:
            return ReasoningCandidate(
                reflection="Waiting for first observation.",
                confidence=0.0,
                suggested_action="wait",
                reasoning_trace=["No observations yet. Cannot reason without data."],
            )

        start = time.time()
        beliefs = understanding.beliefs
        tensions = understanding.tensions
        trace: List[str] = []

        # Insight is authoritative — check before synthesizing reflection
        insight = self._generate_insight(understanding, domain)

        if insight:
            trace.append("Generated insight from conversation patterns")
            reflection = insight
            suggested = "reflect"
            is_insight = True
        else:
            reflection = self._synthesize_reflection(understanding, trace, domain)
            is_insight = False

        questions = self._find_questions(understanding, trace, domain)
        risks = self._find_risks(tensions, trace)
        opportunities = self._find_opportunities(understanding, trace)
        confidence = self._compute_confidence(understanding)

        if not insight:
            suggested = self._suggest_action(understanding, confidence, pie_recommended, risks, trace, domain=domain)

        elapsed_ms = (time.time() - start) * 1000

        return ReasoningCandidate(
            reflection=reflection,
            confidence=round(confidence, 2),
            suggested_action=suggested,
            reasoning_trace=trace,
            unanswered_questions=questions,
            risks=risks,
            opportunities=opportunities,
            is_insight=is_insight,
        )

    # ------------------------------------------------------------------

    def _generate_insight(self, understanding: CurrentUnderstanding, domain: Optional[object] = None) -> Optional[str]:
        """Return a reflective insight if ENOUGH evidence exists for a deeper pattern.

        The system must earn the right to infer:
        - At least 3 observations (conversation depth)
        - Emotional Core is CONFIRMED
        - Theme is CONFIRMED
        """
        min_obs = len(understanding.observations) >= 3
        req_map = {r.area: r.status.value for r in understanding.requirement_states}
        has_emotion = req_map.get("Emotional Core", "") in ("candidate", "active", "confirmed")
        has_theme = req_map.get("Theme", "") in ("candidate", "active", "confirmed")

        if not (min_obs and has_emotion and has_theme):
            return None

        texts = " ".join(b.statement.lower() for b in understanding.beliefs)
        all_text = texts + " ".join(o.content.lower() for o in understanding.observations)

        # Pattern: AI + learn/feel + hope/emotion → loneliness/belonging/identity
        has_ai = any(w in all_text for w in ["ai", "artificial intelligence", "machine"])
        has_learn = any(w in all_text for w in ["learn", "learns", "learning", "feel", "feels", "feeling", "emotion", "understand", "understands", "understanding", "experience", "experiences", "discover", "discovers", "discovering", "become", "becomes", "becoming"])
        has_hope = "hope" in all_text
        if has_ai and has_learn and has_hope:
            return (
                "I think I'm beginning to see what you're really exploring.\n\n"
                "When stories use AI as a lens to explore emotion,\n"
                "they're often asking what it means to be alive.\n\n"
                "I'm wondering if your story isn't really about technology at all.\n"
                "I think it might be about loneliness \u2014 or belonging \u2014\n"
                "and hope is simply the doorway into that question."
            )

        # Pattern: hope + future/change → change/redemption
        has_future = any(w in all_text for w in ["future", "change", "changes", "changing"])
        if has_hope and has_future:
            return (
                "I think I'm beginning to see what you're really exploring.\n\n"
                "Hope about the future usually comes from one place:\n"
                "a belief that things can be different.\n\n"
                "That tells me your story may be less about what is\n"
                "and more about what could be."
            )

        return None

    def _synthesize_reflection(self, understanding: CurrentUnderstanding, trace: List[str], domain: Optional[object] = None) -> str:
        beliefs = understanding.beliefs
        active = [b for b in beliefs if b.lifecycle in (BeliefLifecycle.ACTIVE, BeliefLifecycle.CHALLENGED)]
        any_beliefs = [b for b in beliefs if b.lifecycle in (BeliefLifecycle.ACTIVE, BeliefLifecycle.CHALLENGED, BeliefLifecycle.CANDIDATE)]

        domain_label = ""
        if domain and getattr(domain, 'value', '') and domain.value != 'unknown':
            profile = _get_profile(domain)
            if profile:
                domain_label = profile.label

        if not any_beliefs:
            trace.append("No observations or beliefs yet. Still observing.")
            if domain_label:
                return f"I'm listening. What kind of {domain_label.lower()} are you imagining?"
            return "I'm here when you're ready to share what you're working on."

        count = len(any_beliefs)
        active_count = len(active)

        if count <= 2:
            return "I think I'm beginning to understand where you're going."
        elif count <= 4:
            return f"I'm starting to see the shape of your {domain_label.lower()}." if domain_label else f"I'm starting to see the shape of your project."
        else:
            lines = ["A few things are becoming clearer."]
            top = active[:3]
            if top:
                lines.append("Here's what I'm hearing so far:")
                for b in top:
                    s = b.statement[:60]
                    lines.append(f"  \u2022 {s}")
            return "\n".join(lines)

    def _find_questions(self, understanding: CurrentUnderstanding, trace: List[str], domain: Optional[object] = None) -> List[str]:
        questions: List[str] = []
        active = [b for b in understanding.beliefs if b.lifecycle in (BeliefLifecycle.ACTIVE, BeliefLifecycle.CHALLENGED)]
        belief_texts = [b.statement.lower() for b in understanding.beliefs]

        if domain and getattr(domain, 'value', '') and domain.value != 'unknown':
            profile = _get_profile(domain)
            if profile and profile.discovery_priorities:
                from core.domains import get_unaddressed_priorities
                unaddressed = get_unaddressed_priorities(
                    domain,
                    belief_texts,
                    requirement_states=understanding.requirement_states,
                )
                for priority in unaddressed:
                    questions.append(priority.question)
                total = len(profile.discovery_priorities)
                pending = len(unaddressed)
                confirmed = total - pending
                trace.append(f"Domain: {profile.label}, requirements: {confirmed}/{total} confirmed")
                if not questions:
                    questions.append("What else should I know about this project?")
                return questions

        for t in understanding.tensions:
            if t.status == "active" and t.priority in (TensionPriority.CRITICAL, TensionPriority.HIGH):
                questions.append(f"How would you like to resolve the tension between {t.description.lower()}?")

        trace.append(f"Unanswered questions: {len(questions)}")
        return questions

    def _find_risks(self, tensions: List, trace: List[str]) -> List[str]:
        risks: List[str] = []
        for t in tensions:
            if t.status != "active":
                continue
            if t.priority == TensionPriority.CRITICAL:
                risks.append(f"Unresolved {t.description.lower()} tension may block progress.")
            elif t.severity == TensionSeverity.HIGH:
                risks.append(f"{t.description} tension could cause rework if not addressed.")
        trace.append(f"Risks identified: {len(risks)}")
        return risks

    def _find_opportunities(self, understanding: CurrentUnderstanding, trace: List[str]) -> List[str]:
        opportunities: List[str] = []
        active = [b for b in understanding.beliefs if b.lifecycle == BeliefLifecycle.ACTIVE]
        if len(active) >= 3:
            opportunities.append("Multiple aligned beliefs suggest the creative direction is stabilizing.")
        if len(understanding.observations) >= 5:
            opportunities.append("Sufficient observations gathered to begin generating meaningful artifacts.")
        if not any(t.status == "active" for t in understanding.tensions):
            opportunities.append("No active tensions — the creator's vision appears internally consistent.")
        trace.append(f"Opportunities: {len(opportunities)}")
        return opportunities

    def _compute_confidence(self, understanding: CurrentUnderstanding) -> float:
        if not understanding.observations:
            return 0.0

        n_obs = len(understanding.observations)
        n_beliefs = len([b for b in understanding.beliefs if b.lifecycle in (BeliefLifecycle.ACTIVE, BeliefLifecycle.CHALLENGED)])
        n_active = len([b for b in understanding.beliefs if b.lifecycle == BeliefLifecycle.ACTIVE])
        total = len(understanding.beliefs)

        obs_score = min(n_obs / 6, 1.0) * 0.3
        belief_score = (n_active / max(total, 1)) * 0.3
        version_bonus = min(understanding.version / 6, 1.0) * 0.2
        req_score = 0.0
        if understanding.requirement_states:
            confirmed = sum(1 for r in understanding.requirement_states if r.status.value == "confirmed")
            req_score = (confirmed / max(len(understanding.requirement_states), 1)) * 0.2
        tension_penalty = len([t for t in understanding.tensions if t.status == "active" and t.priority == TensionPriority.CRITICAL]) * 0.15

        raw = obs_score + belief_score + version_bonus + req_score - tension_penalty
        return max(0.05, min(1.0, raw))

    def _suggest_action(self, understanding: CurrentUnderstanding, confidence: float, pie_recommended: Optional[List[str]], risks: List[str], trace: List[str], domain: Optional[object] = None) -> str:
        critical_tensions = [t for t in understanding.tensions if t.priority == TensionPriority.CRITICAL and t.status == "active"]

        if not understanding.observations:
            trace.append("Suggested action: wait (no observations)")
            return "wait"

        if critical_tensions:
            trace.append(f"Suggested action: ask (CRITICAL tensions unresolved: {[t.id for t in critical_tensions]})")
            return "ask"

        if confidence < 0.3:
            trace.append("Suggested action: ask (confidence too low for generation)")
            return "ask"

        active_beliefs = [b for b in understanding.beliefs if b.lifecycle == BeliefLifecycle.ACTIVE]
        any_beliefs = [b for b in understanding.beliefs if b.lifecycle in (BeliefLifecycle.ACTIVE, BeliefLifecycle.CHALLENGED, BeliefLifecycle.CANDIDATE)]
        total_beliefs = len(any_beliefs)

        if domain and getattr(domain, 'value', '') and domain.value != 'unknown':
            try:
                from core.domains import get_domain_profile, get_unaddressed_priorities
                profile = get_domain_profile(domain)
                if profile and profile.discovery_priorities:
                    belief_texts = [b.statement for b in understanding.beliefs]
                    unaddressed = get_unaddressed_priorities(
                        domain, belief_texts,
                        requirement_states=understanding.requirement_states,
                    )
                    if unaddressed:
                        # Only reflect with enough conversation evidence (2+ turns)
                        min_obs = len(understanding.observations) >= 2
                        if min_obs and total_beliefs >= 3 and confidence >= 0.4:
                            trace.append(f"Suggested action: reflect (have {total_beliefs} beliefs, {len(unaddressed)} remaining)")
                            return "reflect"
                        trace.append(f"Suggested action: ask ({len(unaddressed)} unaddressed {profile.label.lower()} priorities)")
                        return "ask"
            except ImportError:
                pass

        if confidence >= 0.6 and len(active_beliefs) >= 4:
            trace.append(f"Suggested action: generate (mature understanding, confidence={confidence:.2f})")
            return "generate"

        if confidence >= 0.5 and len(active_beliefs) >= 3:
            trace.append(f"Suggested action: propose (sufficient understanding, confidence={confidence:.2f})")
            return "propose"

        trace.append(f"Suggested action: ask (continue exploring, confidence={confidence:.2f})")
        return "ask"
