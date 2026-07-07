import time
import logging
from typing import Callable, List

from core.schemas import EvalCheck, EvalAssessment

logger = logging.getLogger(__name__)

CheckFunc = Callable[[dict], EvalCheck]


# -- Individual check implementations ----------------------------------------

def _check_has_strategy(data: dict) -> EvalCheck:
    val = data.get("release_strategy") or data.get("strategy") or ""
    return EvalCheck(
        name="Has Strategy",
        passed=isinstance(val, str) and len(val) > 50,
        detail=f"Strategy length: {len(val)} chars" if val else "No strategy found",
    )

def _check_has_audience(data: dict) -> EvalCheck:
    val = data.get("audience_profile") or ""
    return EvalCheck(
        name="Has Audience",
        passed=isinstance(val, str) and len(val) > 20,
        detail=f"Audience length: {len(val)} chars" if val else "No audience defined",
    )

def _check_has_next_actions(data: dict) -> EvalCheck:
    actions = data.get("next_actions") or []
    return EvalCheck(
        name="Has Next Actions",
        passed=isinstance(actions, list) and len(actions) > 0,
        detail=f"{len(actions)} action(s) found",
    )

def _check_has_marketing_angles(data: dict) -> EvalCheck:
    angles = data.get("marketing_angles") or []
    return EvalCheck(
        name="Has Marketing Angles",
        passed=isinstance(angles, list) and len(angles) > 0,
        detail=f"{len(angles)} angle(s) found",
    )

def _check_has_confidence(data: dict) -> EvalCheck:
    score = data.get("confidence_score")
    valid = isinstance(score, (int, float)) and 0 <= score <= 1
    return EvalCheck(
        name="Has Confidence Score",
        passed=valid,
        detail=f"Score: {score}" if valid else f"Invalid score: {score}",
    )

def _check_action_details(data: dict) -> EvalCheck:
    actions = data.get("next_actions") or []
    if not actions:
        return EvalCheck(name="Action Details", passed=False, detail="No actions to check")
    all_have_fields = all(
        isinstance(a, dict) and a.get("action") and a.get("why")
        for a in actions
    )
    return EvalCheck(
        name="Action Details",
        passed=all_have_fields,
        detail=f"{len(actions)} action(s)" + (" all have fields" if all_have_fields else " missing action/why fields"),
    )

def _check_angle_details(data: dict) -> EvalCheck:
    angles = data.get("marketing_angles") or []
    if not angles:
        return EvalCheck(name="Angle Details", passed=False, detail="No angles to check")
    all_long_enough = all(isinstance(a, str) and len(a) > 20 for a in angles)
    return EvalCheck(
        name="Angle Details",
        passed=all_long_enough,
        detail=f"{len(angles)} angle(s)" + (" all have substance" if all_long_enough else " some too short"),
    )


# -- Campaign plan checks ----------------------------------------------------

def _check_has_campaign_name(data: dict) -> EvalCheck:
    name = data.get("campaign_name") or ""
    return EvalCheck(
        name="Has Campaign Name",
        passed=isinstance(name, str) and len(name) > 3,
        detail=f"Name: '{name}'" if name else "No campaign name",
    )

def _check_has_objectives(data: dict) -> EvalCheck:
    objs = data.get("campaign_objectives") or []
    return EvalCheck(
        name="Has Objectives",
        passed=isinstance(objs, list) and len(objs) > 0,
        detail=f"{len(objs)} objective(s)" if objs else "No objectives defined",
    )

def _check_has_target_segments(data: dict) -> EvalCheck:
    segs = data.get("target_segments") or []
    return EvalCheck(
        name="Has Target Segments",
        passed=isinstance(segs, list) and len(segs) > 0,
        detail=f"{len(segs)} segment(s)" if segs else "No target segments",
    )

def _check_has_channel_strategy(data: dict) -> EvalCheck:
    channels = data.get("channel_strategy") or []
    return EvalCheck(
        name="Has Channel Strategy",
        passed=isinstance(channels, list) and len(channels) > 0,
        detail=f"{len(channels)} channel(s)" if channels else "No channel strategy",
    )

def _check_has_content_themes(data: dict) -> EvalCheck:
    themes = data.get("content_themes") or []
    return EvalCheck(
        name="Has Content Themes",
        passed=isinstance(themes, list) and len(themes) > 0,
        detail=f"{len(themes)} theme(s)" if themes else "No content themes",
    )

def _check_has_kpis(data: dict) -> EvalCheck:
    kpis = data.get("kpis") or []
    return EvalCheck(
        name="Has KPIs",
        passed=isinstance(kpis, list) and len(kpis) > 0,
        detail=f"{len(kpis)} KPI(s)" if kpis else "No KPIs defined",
    )

def _check_has_timeline(data: dict) -> EvalCheck:
    weeks = data.get("timeline_weeks")
    return EvalCheck(
        name="Has Timeline",
        passed=isinstance(weeks, (int, float)) and weeks > 0,
        detail=f"{weeks} week(s)" if weeks else "No timeline defined",
    )

def _check_campaign_next_actions(data: dict) -> EvalCheck:
    actions = data.get("next_actions") or []
    return EvalCheck(
        name="Has Next Actions",
        passed=isinstance(actions, list) and len(actions) > 0,
        detail=f"{len(actions)} action(s)" if actions else "No next actions",
    )


# -- Rule registry -----------------------------------------------------------

EVAL_RULES: dict[str, List[CheckFunc]] = {
    "launch_plan": [
        _check_has_strategy,
        _check_has_audience,
        _check_has_next_actions,
        _check_has_marketing_angles,
        _check_has_confidence,
        _check_action_details,
        _check_angle_details,
    ],
    "campaign_plan": [
        _check_has_campaign_name,
        _check_has_objectives,
        _check_has_target_segments,
        _check_has_channel_strategy,
        _check_has_content_themes,
        _check_has_kpis,
        _check_has_timeline,
        _check_campaign_next_actions,
    ],
}


class EvaluationEngine:
    """
    Evaluation Engine v0 — stateless artifact quality assessment.

    Answers four questions:
      1. Is the artifact structurally complete?
      2. Is it internally consistent?
      3. What is missing?
      4. Should the creator continue?

    No LLM calls. No side effects. Deterministic and testable.
    """

    def __init__(self, rules: dict | None = None):
        self.rules = rules or EVAL_RULES

    def evaluate(self, artifact: dict, artifact_type: str = "launch_plan") -> EvalAssessment:
        t0 = time.perf_counter()
        checks = self.rules.get(artifact_type, [])
        results: list[EvalCheck] = []
        for check_fn in checks:
            try:
                results.append(check_fn(artifact))
            except Exception as exc:
                results.append(EvalCheck(
                    name=check_fn.__name__,
                    passed=False,
                    detail=f"Error: {exc}",
                ))

        total = len(results)
        passed = sum(1 for c in results if c.passed)
        score = passed / total if total > 0 else 1.0

        recommendations = [
            c.detail for c in results if not c.passed
        ]

        status = self._derive_status(score)
        confidence = min(1.0, total / 6.0)

        elapsed = round((time.perf_counter() - t0) * 1000, 2)

        logger.info(
            f"Eval: type={artifact_type} score={score:.0%} "
            f"status={status} passed={passed}/{total} in {elapsed}ms"
        )

        return EvalAssessment(
            artifact_type=artifact_type,
            status=status,
            score=round(score, 2),
            checks=results,
            recommendations=recommendations,
            eval_time_ms=elapsed,
            confidence=round(confidence, 2),
        )

    @staticmethod
    def _derive_status(score: float) -> str:
        if score >= 0.8:
            return "ready"
        if score >= 0.5:
            return "needs_revision"
        return "incomplete"
