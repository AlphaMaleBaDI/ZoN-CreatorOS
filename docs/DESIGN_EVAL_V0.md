# Evaluation Engine v0 — Design Proposal

## Status: DRAFT (pre-implementation)

## Problem

CreatorOS can generate artifacts (Launch Plans) and reason about production completeness (PIE). But it cannot assess artifact *quality*. Every artifact is accepted as-is — no structured feedback, no quality score, no improvement guidance.

Without evaluation, the pipeline is open-loop:

```
Generate → PIE → Creator Approval (subjective)
```

A creator has no signal beyond their own intuition about whether an artifact is complete, coherent, or aligned with their goals.

## Design Principles

1. **Deterministic first** — No LLM calls in evaluation. All checks are static rules applied to the artifact's structured data.
2. **Stateless** — The Evaluation Engine receives an artifact and returns a score. No side effects, no internal state.
3. **Composable** — Each check is independent. Checks can be added, removed, or reordered without changing the engine.
4. **Transparent** — Every check reports pass/fail + a human-readable reason. The score is the ratio of passes to total checks.
5. **Domain-agnostic** — The engine evaluates any artifact type. Domain-specific checks are registered by name, not hardcoded.

## Architecture

### Schema

```python
class EvalCheck(BaseModel):
    name: str
    passed: bool
    detail: str = ""

class EvalAssessment(BaseModel):
    artifact_type: str
    score: float              # 0.0 — 1.0
    checks: list[EvalCheck]
    recommendations: list[str]
    eval_time_ms: float
    confidence: float         # based on check coverage
```

### Evaluation Rules Registry

A static mapping of `artifact_type → list[check_functions]`. Each check function is a pure callable that inspects the artifact dict and returns `EvalCheck`.

```
EVAL_RULES: dict[str, list[Callable[[dict], EvalCheck]]] = {
    "launch_plan": [check_has_objectives, check_has_timeline, check_has_milestones,
                    check_has_kpis, check_has_risks, check_has_audience,
                    check_strategy_min_length],
    "campaign_plan": [...],
    ...
}
```

### Check Examples

#### `check_has_timeline`
- **Input:** Artifact data dict
- **Logic:** `"timeline" in data or "next_actions" in data`
- **Pass:** If timeline or next_actions exist and contain at least one entry
- **Fail:** If missing

#### `check_has_kpis`
- **Input:** Artifact data dict
- **Logic:** `"kpis" in data or "metrics" in data or "success_criteria" in data`
- **Pass:** If any KPI-like field exists with content
- **Fail:** If missing

#### `check_has_risks`
- **Input:** Artifact data dict
- **Logic:** `"risks" in data or "risk_factors" in data`
- **Pass:** If risk section exists
- **Fail:** If no risk assessment

#### `check_strategy_min_length`
- **Input:** Artifact data dict
- **Logic:** `len(data.get("release_strategy", "")) > 100`
- **Pass:** Strategy has substance
- **Fail:** Strategy is too short to be actionable

### Scoring

```python
score = sum(1 for c in checks if c.passed) / len(checks) if checks else 1.0
```

### Confidence

```python
# Based on what fraction of the target checks were actually run
# (some artifact types may have fewer registered checks)
confidence = min(1.0, len(checks_registered) / 6)  # 6 is the target minimum
```

## Integration

The Evaluation Engine sits between PIE and the API response, inside `Kernel.execute()`:

```
Orchestrator → result
  ↓
Snapshot Service
  ↓
PIE Assessment
  ↓
EVALUATION ENGINE ← NEW
  ↓
result._eval_assessment = eval_result
  ↓
Return result
```

The API serializes it alongside `pie`:

```json
{
  "artifact": {...},
  "pie": {...},
  "eval": {
    "artifact_type": "launch_plan",
    "score": 0.83,
    "checks": [
      {"name": "Has Strategy", "passed": true, "detail": "Strategy length: 342 chars"},
      {"name": "Has Timeline", "passed": true, "detail": "7 next_actions found"},
      {"name": "Has KPIs", "passed": false, "detail": "No KPIs or metrics found"}
    ],
    "recommendations": ["Add measurable KPIs to track launch success"],
    "eval_time_ms": 0.4,
    "confidence": 1.0
  }
}
```

## Launch Plan Checks (v0)

| # | Check | Description |
|---|---|---|
| 1 | has_strategy | `release_strategy` exists and has length > 50 |
| 2 | has_audience | `audience_profile` exists and has length > 20 |
| 3 | has_next_actions | `next_actions` is a non-empty list |
| 4 | has_marketing_angles | `marketing_angles` is a non-empty list |
| 5 | has_confidence | `confidence_score` is in [0, 1] and > 0 |
| 6 | has_kpis_or_metrics | At least one KPI/metric/success_criteria field exists |
| 7 | action_details | All next_actions have both `action` and `why` fields |
| 8 | angle_details | All marketing_angles have length > 20 |

## Expansion Path

- **v0:** Static rule registry — all checks are Python functions. Deterministic, no LLM.
- **v1:** Domain Packs register their own checks via the Kernel plugin interface.
- **v2:** LLM-assisted checks for subjective quality (brand alignment, tone consistency) — but always alongside deterministic checks, never replacing them.

## What This Enables Later

- **Creator Dashboard** — show a quality score per artifact, highlight weak areas
- **Improvement Loop** — low-scoring artifacts trigger automatic revision prompts
- **Hackathon Demo** — "CreatorOS gives your launch plan an 83/100. Here's what's missing."
- **ADR-006 alignment** — The Evaluation Layer with specialized critics begins here

## Non-Goals (v0)

- No LLM-assisted checks
- No domain pack registration (hardcoded rules for launch_plan only)
- No auto-improvement (evaluate only, don't revise)
- No persistent evaluation history (score is computed on-the-fly)
