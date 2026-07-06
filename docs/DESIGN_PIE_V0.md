# PIE v0 — Production Intelligence Engine (Design Proposal)

## Status: APPROVED for implementation

---

## 1. What PIE Is

PIE is a **stateless decision service** owned by the Kernel. Its sole purpose is to inspect an artifact and workspace state, then answer three questions:

1. **What already exists?** — completed artifact types
2. **What's missing?** — valid next types not yet produced
3. **What should happen next?** — the single highest-impact missing artifact

It does not generate, execute, or store anything.

```
[Artifact] → PIE → [Assessment] → [Human] → [Orchestrator]
```

---

## 2. What PIE Is Not

| Role | Not PIE's job |
|---|---|
| Generation | ❌ No LLM calls, no content creation |
| Execution | ❌ No agent invocation, no side effects |
| Storage | ❌ No memory, no snapshots, no artifacts |
| Routing | ❌ The Orchestrator routes; PIE only recommends |
| Approval | ❌ The human decides |

PIE is pure reasoning. No inputs are mutated. No outputs are persisted by PIE itself.

---

## 3. Where PIE Lives

```
core/           (Kernel layer)
├── kernel.py           — orchestrates init → context → execute → evaluate
├── orchestration.py    — agent routing + artifact persistence
├── context_assembly.py — context assembly
├── schemas.py          — shared schemas
└── pie.py              ← NEW — Production Intelligence Engine
```

No new architectural layer. PIE is a single class in the Kernel's directory, called by the Kernel after `execute()` completes.

---

## 4. Output Schema

```python
@dataclass
class PIEAssessment:
    completed: list[str]              # Artifact types already produced
    missing: list[str]                # Valid next types not yet produced
    recommended_next: list[str]       # Ordered by priority (1-3 items)
    production_progress: float        # 0.0 - 1.0 (percentage complete)
    confidence: float                 # 0.0 - 1.0 (how sure PIE is of the path)
```

### No LLM

PIE returns recommendations, not generated content. The caller (Kernel) surfaces them to the human.

---

## 5. Production Knowledge Graph (PKG)

PIE v0 uses a **Production Knowledge Graph** — a static adjacency map defining which artifact types lead to which:

```python
PRODUCTION_KNOWLEDGE_GRAPH = {
    "launch_plan":      ["campaign_plan", "content_calendar", "press_release"],
    "campaign_plan":    ["budget_plan", "content_calendar"],
    "content_calendar": ["content_script", "production_schedule"],
    "press_release":    ["media_kit", "press_distribution"],
    "budget_plan":      ["resource_allocation"],
}
```

This is defined as a module-level `dict[str, list[str]]`. No database, no configuration file. Deterministic, testable, observable.

### Algorithm

PIE works by:

1. Determine the **root** node — the just-produced artifact's type
2. Walk the PKG to find all reachable types from the root
3. For each reachable type, check if an artifact of that type exists in `existing_artifacts`
4. Categorize into `completed` (exists) or `missing` (not yet exists)
5. `recommended_next` = the first missing artifact that has all its dependencies met
6. `production_progress` = `len(completed) / len(all_reachable)` for the current root path

### Determinism Guarantee

Same workspace state + same artifact → same assessment. No randomness, no LLM temperature, no stochasticity.

---

## 6. Integration with Kernel

```python
class Kernel:
    def execute(self, context):
        result = self.orchestrator.run_flow(context)

        pie = ProductionIntelligenceEngine()
        assessment = pie.analyze(
            artifact_type=self.orchestrator._last_artifact_type,
            existing_artifact_types=self._get_existing_types(),
        )

        result._pie_assessment = assessment
        return result
```

---

## 7. API Surface

The existing `POST /generate-launch-plan` returns PIE assessment inline:

```json
{
  "release_strategy": "...",
  "confidence_score": 0.85,
  "pie": {
    "completed": ["launch_plan"],
    "missing": ["campaign_plan", "content_calendar", "press_release"],
    "recommended_next": ["campaign_plan"],
    "production_progress": 0.18,
    "confidence": 0.91
  }
}
```

No separate endpoint for v0. The assessment rides with the artifact.

---

## 8. Progress Visualization (Demo)

```
Launch Plan:    ████░░░░░░  18%
Campaign:       ██████████  100%
Calendar:       ██████░░░░  52%
```

Each artifact type's progress = `(artifacts_of_this_type_exist ? 100% : progress_of_its_upstream)`.

---

## 9. ADR Check

| ADR | Compliance |
|---|---|
| ADR-008 (Architecture Freeze) | ✅ Single class in `core/`, not a new layer |
| ADR-004 (Production Kernel) | ✅ Owned by Kernel, not agents |
| ADR-002 (Context Assembly first) | ✅ Runs after context assembly + execution |
| Invariant K-001 | ✅ Runs after `Kernel.execute()`, never before context |

---

## 10. Files Changed

| File | Change |
|---|---|
| `core/pie.py` | **NEW** — `ProductionIntelligenceEngine` + `PRODUCTION_KNOWLEDGE_GRAPH` |
| `core/kernel.py` | Call `pie.analyze()` after `orchestrator.run_flow()` |
| `core/schemas.py` | Add `PIEAssessment` schema |
| `core/orchestration.py` | Track `_last_artifact_type` |
| `tests/test_pie.py` | **NEW** — Graph traversal, completion detection, progress calc |

No changes to agents, services, or memory layer.

---

## 11. Implementation Order

1. `core/schemas.py` — add `PIEAssessment`
2. `core/pie.py` — `ProductionIntelligenceEngine` with PKG
3. `core/orchestration.py` — track `_last_artifact_type`
4. `core/kernel.py` — wire PIE after `execute()`
5. `tests/test_pie.py` — verify all paths
6. Update `/generate-launch-plan` response to include `pie`

No agents. No LLM. No new services. One class, one graph, one integration point.
