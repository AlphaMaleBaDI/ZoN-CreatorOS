# Production State Awareness v0 — Design Proposal

## Status: IMPLEMENTED (Mission 009)

## Problem

CreatorOS can generate artifacts and reason about production completeness (PIE). But the concept of "where is this project in its lifecycle" is implicit — derived from a progress float (0.0–1.0) mapped to a label.

The creator experiences:

```
Progress: 50%
```

Not:

```
Planning → Production (in progress)

Evidence:
  ✓ Launch Plan
  ✓ Campaign Plan

To move forward:
  ✓ Create Content Calendar
  ✓ Score eval >= 0.6
```

Without formal state awareness:

- PIE cannot make phase-appropriate recommendations
- The Workspace cannot display a meaningful project dashboard
- Evaluation cannot weight checks differently by phase
- The system has no vocabulary for project lifecycle, only artifact generation

## Design Principles

1. **State is derived, never stored** — State is computed from evidence (artifacts + eval + PIE) every time it's requested. Stored state drifts; derived state stays truthful. No `state` column, no independent state mutations.

2. **State tracks creative maturity, not artifact production** — The question is "What commitment has the creator made?" not "What artifact exists?" A creator who has approved a Launch Plan has made a strategic commitment, even if the eval score is 0.4. Artifacts are evidence of commitment, not the commitment itself.

3. **Domain-agnostic lifecycle** — The six states (Ideation → Planning → Production → Publishing → Released → Archived) are kernel concepts. Domain Packs map their artifact types to these states. Music, Film, Podcast, Publishing, Games all share the same lifecycle — only the artifact types change.

4. **Deterministic transitions** — No LLM decides the phase. The state machine uses rules based on artifact existence, eval scores, and PIE assessment.

5. **Acknowledge reversibility** — Creators iterate, pivot, and backtrack. The design supports backward transitions even if v1 only implements forward movement. The architecture never assumes a linear path.

6. **Three-question output** — Every state query returns: Current Phase → Evidence → Next Requirement. The system coaches, not just labels.

## Architecture

### Lifecycle States (Kernel Concept)

```
    ┌─────────────────────────────────────────────────────┐
    │                                                     │
    ▼                                                     │
┌──────────┐    ┌──────────┐    ┌────────────┐           │
│ Ideation │───▶│ Planning │───▶│ Production │           │
└──────────┘    └──────────┘    └────────────┘           │
    ▲                │                │                   │
    │                │                ▼                   │
    │                │         ┌────────────┐             │
    │                │         │ Publishing │             │
    │                │         └────────────┘             │
    │                │                │                   │
    │                │                ▼                   │
    │                │         ┌──────────┐               │
    │                └────────▶│ Released │───────────────┘
    │                          └──────────┘
    │                                │
    │                                ▼
    │                         ┌──────────┐
    └─────────────────────────│ Archived │
                              └──────────┘
```

Dashed lines = acknowledged but not implemented in v1.

| State | Definition | Knowable by |
|-------|-----------|-------------|
| **Ideation** | Project exists, intent declared. No strategic commitment yet. | Workspace created, no artifacts. |
| **Planning** | Creator has committed to a direction. Strategic choices made. | Launch Plan + Campaign Plan exist. Creator has approved direction. |
| **Production** | Creator has committed to execution. Tactical work underway. | Content Calendar exists. Eval scores >= 0.6 on strategic artifacts. |
| **Publishing** | Creator has committed to release. Distribution imminent. | Publishing Checklist exists. Content Calendar eval >= 0.6. |
| **Released** | Creator has launched. Project is live. | Release Complete artifact exists. |
| **Archived** | Creator has closed the project. Read-only. | Manual creator action. |

### Domain Agnostic — Verified

| Domain | Ideation | Planning | Production | Publishing |
|--------|----------|----------|------------|------------|
| **Music** | Workspace created | Launch Plan + Campaign Plan | Content Calendar + Asset Checklist | Release Checklist + Distribution |
| **Film** | Workspace created | Script + Storyboard + Budget | Shot List + Call Sheets | DCP + Festival Submissions |
| **Podcast** | Workspace created | Format + Guest List + Season Arc | Episode Scripts + Recording Log | Distribution + Show Notes |
| **Publishing** | Workspace created | Outline + Chapter Map | Draft Chapters + Edits | Proof + ISBN + Distribution |
| **Games** | Workspace created | GDD + Concept Art + Milestones | Asset Pipeline + Builds | Store Page + Press Kit |

Same six states. Different artifact types. The state machine is a kernel concept.

### Commitment over Artifacts

The transition rule asks:

> "Has the creator made the commitment this state represents?"

Not:

> "Does the artifact exist?"

Evidence of commitment:

| State | Commitment | Evidence |
|-------|-----------|----------|
| Planning→Production | "I know what I'm building and who it's for" | Launch Plan created, Campaign Plan created, eval >= 0.6 on launch |
| Production→Publishing | "I'm ready to release" | Content Calendar complete, eval >= 0.6, creator has reviewed |
| Publishing→Released | "I have released" | Release Complete artifact, timestamp |

The distinction prevents a state from advancing just because a low-quality artifact was generated. The creator must have made a meaningful commitment.

### State Transition Rules

PIE determines state from three signals:

1. **Artifact existence** — Which artifacts have been produced?
2. **Eval scores** — Do artifacts pass quality thresholds?
3. **Production progress** — Overall completeness (0.0–1.0)

```
Ideation ───────────────▶ Planning
  Any artifact exists       Progress >= 0.1

Planning ────────────────▶ Production
  Launch eval >= 0.6       Campaign eval >= 0.5
  Campaign Plan exists     (asymmetric: harder to enter
                            production than to stay)

Production ──────────────▶ Publishing
  Content Calendar eval    Publishing Checklist exists
  >= 0.6                   PIE recommends publishing

Publishing ──────────────▶ Released
  Publishing eval >= 0.6   ReleaseComplete exists

Released ─────────────────▶ Archived
  Manual creator action
```

Backward transitions (acknowledged, v1 scope):

```
Publishing ──────────────▶ Production
  Creator revises content   PIE detects content-calendar
                            eval drop after revision

Planning ─────────────────▶ Ideation (not in v1)
  Creator deletes all       Manual override only
  artifacts

Released ─────────────────▶ Publishing (not in v1)
  Creator unpublishes       Manual override only
```

v1 only implements forward transitions. But the architecture doesn't forbid backward movement — state is derived, so if evidence changes, the derived state changes naturally.

### Derived State — The Key Insight

State is never stored. It is always computed:

```
def derive_state(workspace_id) -> ProductionState:
    artifacts = ArtifactService.list_artifacts(workspace_id)
    eval_results = {a.artifact_type: EvalService.evaluate(a) for a in artifacts}
    pie_state = PIE.compute_state(artifacts, eval_results)
    return pie_state
```

This means:
- **No drift** — If artifacts are deleted, state reverts automatically
- **No sync** — No state to synchronize across services
- **No migrations** — Add new rules, re-derive, done
- **Truthful** — The state always reflects the actual evidence

### The Three-Question Output

Every state query returns:

```
Current Phase:
  Planning

Evidence:
  ✓ Launch Plan (eval 0.8)
  ✓ Campaign Plan (eval 0.6)
  ✗ Content Calendar (missing)

To reach Production:
  ✓ Create Content Calendar
  ✓ Score Content Calendar eval >= 0.6
  → Then PIE will transition to Production phase
```

The output is coaching, not status.

### Schema Changes

```python
class ProductionState(str, Enum):
    IDEATION = "ideation"
    PLANNING = "planning"
    PRODUCTION = "production"
    PUBLISHING = "publishing"
    RELEASED = "released"
    ARCHIVED = "archived"

class StateEvidence(BaseModel):
    artifact_type: str
    exists: bool
    eval_score: float | None = None
    eval_passed: bool | None = None

class StateAssessment(BaseModel):
    current_state: ProductionState
    evidence: list[StateEvidence]
    requirements: list[str]  # "To move forward..."
    next_state: ProductionState | None = None
    can_transition: bool = False
    blockers: list[str] = []

# PIEAssessment gains state assessment (not stored, derived on access)
class PIEAssessment(BaseModel):
    # existing fields unchanged...
    production_state: str  # maps to ProductionState enum value
    production_progress: float  # unchanged
    state_assessment: StateAssessment | None = None  # new, optional
```

### Seed Data — Domain Pack Mapping

```python
# Kernel-level: state definitions only (no artifact specifics)
STATE_DEFINITIONS = {
    "ideation":    {"display": "Ideation",    "progress_range": (0.0, 0.15)},
    "planning":    {"display": "Planning",    "progress_range": (0.15, 0.45)},
    "production":  {"display": "Production",  "progress_range": (0.45, 0.75)},
    "publishing":  {"display": "Publishing",  "progress_range": (0.75, 0.90)},
    "released":    {"display": "Released",    "progress_range": (0.90, 1.0)},
    "archived":    {"display": "Archived",    "progress_range": (1.0, 1.0)},
}

# Domain Pack-level: artifact-to-state mapping
# (lives in the Domain Pack, not the kernel)
MUSIC_ARTIFACT_STATE_MAP = {
    "launch_plan":       {"state": "planning",    "required_for_transition": True},
    "campaign_plan":     {"state": "planning",    "required_for_transition": True},
    "content_calendar":  {"state": "production",  "required_for_transition": True},
    "asset_checklist":   {"state": "production",  "required_for_transition": False},
    "publishing_checklist": {"state": "publishing", "required_for_transition": True},
    "release_complete":  {"state": "released",    "required_for_transition": True},
}
```

This separation ensures the kernel state machine is domain-agnostic. A Films Domain Pack would define `FILM_ARTIFACT_STATE_MAP` without touching the kernel.

### Evaluation Integration

Eval checks become state-scoped:

```python
EVAL_RULES = {
    "launch_plan":       {"applicable_states": ["planning", "production"]},
    "campaign_plan":     {"applicable_states": ["planning", "production"]},
    "content_calendar":  {"applicable_states": ["production", "publishing"]},
    "publishing_checklist": {"applicable_states": ["publishing"]},
    "release_complete":  {"applicable_states": ["released"]},
}
```

If `launch_plan` eval is requested during `publishing` state, the engine returns the last known score instead of re-running.

### Workspace Integration

```json
GET /workspace/:id/state

{
  "current_state": "planning",
  "progress": 0.32,
  "evidence": [
    {"artifact_type": "launch_plan", "exists": true, "eval_score": 0.8, "eval_passed": true},
    {"artifact_type": "campaign_plan", "exists": false, "eval_score": null, "eval_passed": null}
  ],
  "to_move_forward": [
    "Create Campaign Plan",
    "Score Campaign Plan eval >= 0.5"
  ],
  "blockers": [
    "Campaign Plan does not exist"
  ],
  "can_transition": false,
  "next_state": "production"
}
```

## Open Questions (Answered)

| Question | Answer |
|----------|--------|
| State derived or stored? | **Derived**. Never stored independently. |
| Can projects move backward? | **Acknowledged, v1 forward-only.** Design supports reversal via re-derivation. |
| Is this domain-specific? | **No.** Kernel concept. Domain Packs provide artifact mappings. |
| Who owns state? | **PIE.** It already has the signals. `determine_state()` is a new method. |
| What about the demo? | State is text labels only in v0. Visual phase bar deferred to Mission 010. |

## Migration

No breaking change. The existing `production_state` field already returns a string. Migration path:

1. Add `ProductionState` enum (backward-compatible string values)
2. Add `determine_state()` to PIE (derived, not stored)
3. Add `StateAssessment` schema (optional, only included when requested)
4. Add domain-pack artifact-to-state mapping (kernel + music pack)
5. Update eval to accept optional `state` scope filter
6. Expose `/workspace/:id/state` endpoint in API
7. Add `state_assessment` field to PIEAssessment (optional, None by default)

## Comparison to Co-Captain's Vision

| Co-Captain Said | Design Does |
|----------------|------------|
| "What commitment has the creator made?" | Commitment-based transitions with evidence of intent |
| "Can a project move backwards?" | Design acknowledges reversibility; v1 forward-only but derived-state architecture supports natural reversal |
| "Who owns state? Not stored, derived." | `derive_state()` — computed on every request |
| "Domain-agnostic lifecycle" | Kernel `STATE_DEFINITIONS` + Domain Pack `ARTIFACT_STATE_MAP` |
| "Three-question output: Phase → Evidence → Next" | `StateAssessment` schema with `current_state`, `evidence`, `requirements` |
| "Coaching over production" | Output says "To move forward: ..." instead of "Status: ..." |
| "Every future Domain Pack uses the same machine" | Verified across Music, Film, Podcast, Publishing, Games |

## Out of Scope (v0)

- Backward state transitions (architecture supports, code doesn't)
- Visual phase render in demo (text labels only)
- Multi-project aggregation dashboard
- State expiry / auto-archive
- Creator-triggered transitions via API
