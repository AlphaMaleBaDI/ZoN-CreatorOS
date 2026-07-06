# Architectural Decision Records (ADR)

This document records the key architectural decisions for **ZoN CreatorOS**, providing context, rationale, and consequences for future developers and judges.

---

## 📄 ADR-001: Multi-Workspace & Scoped Memory

### Context
A creator typically runs multiple parallel initiatives (e.g., song release campaigns, startup ideas, personal journals, research projects). If all memory is dumped into a single global vector namespace, searches suffer from context collision and memory soup (e.g., mixing song ideas with software code).

### Decision
We will scope all memory nodes, metadata, and vectors using a three-tier hierarchy:
1. `Workspace ID` (The broad category, e.g., AfroVBra vs. Personal Research)
2. `Project ID` (A specific goal, e.g., EP Release Sept)
3. `Memory Scope` (A tag-based classification for context selection)

### Rationale
* **Data Isolation:** Prevents model confusion and context pollution.
* **Granular Context Loading:** Allows the system to retrieve only relevant vectors, optimizing speed and costs.

### Consequences
* All DB indexes and FAISS queries must include workspace filtering.
* The frontend/client must maintain an active workspace state.

---

## 📄 ADR-002: Dedicated Context Assembly Engine

### Context
AI agents often fail because they are handed plain prompts with missing context. Performing ad-hoc searches inside agent logic makes agents complex, hard to test, and expensive to execute.

### Decision
Establish a first-class **Context Assembly Engine** that executes *before* any agent or model is called. It aggregates:
* User request
* Workspace/project state
* Active Creator Profile (voice, tone, preferences)
* Vector memory snapshots
* Persistent Vibra mood history

### Rationale
* **Separation of Concerns:** Agents focus purely on reasoning and planning, not data fetching.
* **Determinism:** The assembled context can be logged, audited, and cached separately.
* **Testability:** You can test the quality of context assembly independently from the LLM outputs.

### Consequences
* Every LLM call pipeline must pass through the `ContextAssemblyEngine` first.

---

## 📄 ADR-003: AMD Hybrid local NPU & Cloud GPU Routing

### Context
Running multi-agent workflows is resource-heavy. Offloading every lightweight task (notes search, spelling check, local summary) to cloud GPUs consumes credits quickly and creates latency. However, large plans and creative roadmaps cannot run on edge hardware.

### Decision
Implement a hybrid routing strategy using:
* **Local Compute:** Ryzen AI NPU via ONNX/PyTorch for local search, note summarization, and private creator profile operations.
* **Cloud Compute:** AMD Instinct GPUs (MI300X via ROCm 7) with a disaggregated prefill/decode pipeline for deep agent planning and creative generation.

### Rationale
* **TCO Reduction:** Drastically slashes cloud GPU spend by offloading routine tasks.
* **Privacy:** Sensitive creator assets stay local on the NPU.
* **Judges Appeal:** Directly showcases the full spectrum of AMD's AI hardware ecosystem.

### Consequences
* Core code must support config-based switching between local and cloud execution paths.

---

## 📄 ADR-004: Production Kernel as Stable Orchestration Core

### Context
As CreatorOS expands from a single-domain (music release plans) to multi-domain production (film, games, podcasts, publishing), the architecture needs a stable core that does not change when new domains are added. The alternative — adding domain-specific logic to the core — would create coupling and prevent independent evolution.

### Decision
Introduce the **Production Kernel** as the explicit stable core of the system. The Kernel owns:
- Context Assembly
- Agent Lifecycle Management
- Production Intelligence Engine (PIE)
- Creative Asset Graph (CAG)
- Model Router
- Artifact Pipeline
- Evaluation Layer

Domain-specific logic is implemented as **Domain Packs** that plug into the Kernel. The Kernel defines the plugin interface (agents, schemas, templates, routing rules, validators, critics, dashboard panels). Packs implement against this interface.

### Rationale
- **Stability:** The Kernel changes rarely; packs evolve independently.
- **Extensibility:** Adding a new domain = writing a new pack, not modifying core infrastructure.
- **Testability:** The Kernel can be tested without any domain pack loaded; packs can be tested against a mock Kernel.
- **Ecosystem readiness:** The pack interface naturally becomes the marketplace API for third-party domain packs.

### Consequences
- All existing code must be refactored to separate Kernel concerns from domain-specific logic.
- The Domain Pack interface must be defined and documented before Phase 2 begins.
- Domain Packs must be loadable at workspace scope (different workspaces can have different packs enabled).

---

## 📄 ADR-005: Artifact Graph over Terminal Outputs

### Context
In most AI systems, generated outputs are terminal — they are delivered to the user and forgotten. In a creative production system, artifacts are interconnected: a release plan feeds a marketing campaign, which feeds a calendar, which feeds a video script. Treating artifacts as independent outputs loses the production chain and prevents iterative improvement.

### Decision
Artifacts are first-class persistent nodes in an **Artifact Graph**. Each artifact:
- Stores its provenance (which context, agents, and prior artifacts produced it)
- Links to successor artifacts (what it feeds into)
- Maintains version history
- Is queryable by relationship, not just by ID
- Is part of the project's persistent state, not a session export

The generation model shifts from `Prompt → Artifact` to `Intent → Artifact Graph`.

### Rationale
- **Traceability:** Every output can be traced back to its inputs and forward to its dependents.
- **Iteration:** Modifying one artifact automatically surfaces which downstream artifacts are affected.
- **Self-evolving projects:** The artifact graph grows organically across sessions, rather than resetting each time.
- **Alignment with CAG:** The Artifact Graph is a specialization of the Creative Asset Graph — both use the same property graph infrastructure.

### Consequences
- Artifact schemas must include `predecessor_ids`, `provenance`, and `version` fields.
- The Artifact Service (`services/artifact_service.py`) must support graph traversal queries, not just CRUD.
- The Dashboard must render artifact relationship views (dependency trees, production chains).

---

## 📄 ADR-006: Evaluation Layer with Specialized Critics

### Context
AI-generated creative work has no natural quality feedback loop. The model generates, and the creator either accepts or regenerates blindly. Without structured evaluation, errors in planning, brand alignment, memory consistency, and domain-specific correctness propagate through the production pipeline undetected.

### Decision
Introduce a dedicated **Evaluation Layer** within the Production Kernel. Every artifact passes through a chain of specialized critics before delivery:

```
Generate → Evaluate → Improve → Approve
```

Each critic:
- Checks a single quality dimension
- Assigns a score or pass/fail
- Optionally generates structured improvement suggestions
- Passes to the next critic or back for revision

Critics are registered by Domain Packs and can be chained conditionally. The Evaluation Layer also produces an audit trail for every artifact.

### Rationale
- **Catch errors early:** A planning critic catches structural issues before generation compute is spent.
- **Transparency:** Creators see exactly which checks passed and failed, reducing blind trust in model output.
- **Continuous improvement:** Critic feedback can be logged and used to fine-tune prompt templates and routing rules.
- **Domain-specific:** Each Domain Pack registers its own critics; the Kernel does not need to know about every domain.

### Consequences
- Critics must be stateless and deterministic for a given input (no randomness in evaluation).
- Critics must be fast — they should not require LLM calls for every check (lightweight heuristics first, LLM-assisted checks second).
- The Dashboard must display critic scores per artifact (pass/fail visualization, improvement suggestions).

---

## 📄 ADR-007: Domain Packs as Pluggable Production Modules

### Context
Hardcoding production domains (Music, Film, Games, Podcast) into the core architecture would create a monolith. Each domain has different agents, schemas, prompt templates, routing rules, validators, and quality criteria. Adding a new domain would require modifying multiple core modules.

### Decision
Domains are implemented as **Domain Packs** — self-contained directories that plug into the Production Kernel. Each pack provides:

| Component | Description |
|---|---|
| `agents/` | Domain-specific agent implementations |
| `schemas/` | Pydantic artifact models |
| `templates/` | Reusable prompt library |
| `routing.py` | Model routing rules for the domain |
| `validators.py` | Domain-specific output validators |
| `critics.py` | Evaluation layer critics |
| `dashboard.py` | Streamlit dashboard panels |

The Kernel loads packs based on workspace configuration. Multiple packs can be active simultaneously (a music project and a film project in different workspaces).

### Rationale
- **Modularity:** Each pack is independently developed, tested, and versioned.
- **Extensibility:** Third-party developers can create and publish Domain Packs.
- **Marketplace readiness:** The pack structure naturally becomes the unit of distribution in the CreatorOS Marketplace.
- **Kernel stability:** The Kernel defines the interface but never imports domain-specific code directly.

### Consequences
- The Domain Pack plugin interface must be defined in the Kernel before Phase 2.
- A pack registry must manage loading, dependency resolution, and version conflicts.
- The MVP Music domain must be refactored into a Domain Pack to validate the interface before adding new domains.

---

## 📄 ADR-008: Architecture Freeze — Implementation over Abstraction

### Context
Complex systems face a recurring risk: **architecture drift** — the tendency to add abstractions, layers, and components because they seem necessary in theory, rather than because implementation has proven they are needed. Each new abstraction increases cognitive load, documentation surface, and the risk of building infrastructure that never gets used.

After the preseason architecture definition (ADR-001 through ADR-007), the system has reached a coherent architectural language. Continuing to add abstractions before implementation will produce diminishing returns.

### Decision
Effective immediately, the architecture is **frozen** at the current abstraction level. Only three categories of changes are permitted:

1. **Bug fixes** — corrections to existing implementations that do not introduce new concepts.
2. **Clarifications** — changes to documentation that improve understanding without adding new abstractions.
3. **Implementation discoveries** — new abstractions are only permitted if they emerge from implementation necessity (i.e., code is duplicated three times across independent modules, proving a missing abstraction).

New architectural layers, new agent types, and new conceptual components require **implementation evidence** rather than theoretical benefit. The burden of proof lies with the proposer to demonstrate that the architecture cannot express a required behavior without the new abstraction.

### Rationale
- **Diminishing returns:** Each additional abstraction explains less about the system than the one before it. The core patterns are established.
- **Increasing returns from implementation:** Every hour spent building and validating the current architecture produces more evidence than an hour spent refining it on paper.
- **Hackathon constraint:** With a fixed deadline, implementation velocity matters more than architectural completeness.
- **Evidence-first design:** Abstractions that emerge from real usage are more likely to be correct than abstractions designed in advance.

### Consequences
- The sprint checklist (`docs/SPRINT_EXECUTION_CHECKLIST.md`) is the sole source of truth for what gets built. No work outside the checklist is permitted.
- Architectural discussions during the sprint are limited to: "Does this belong in the existing architecture?" If no, it waits. If yes, it is implemented as simply as possible.
- After the hackathon, the freeze may be lifted by reviewing each proposed new abstraction against actual implementation pain points.

---

## ✅ ADR-009: Kernel Validation Complete

### Context
Since ADR-008 (Architecture Freeze), the team implemented the MVP vertical slice (Workspace → Context Assembly → Orchestrator → Planning Agent → Launch Plan). Before expanding into Phase 1.2 (Memory & Profile Foundation), the Kernel required structured validation to confirm the architecture survives implementation.

### Decision
The CreatorOS Kernel has been validated through a structured demo (`demos/demo_kernel.py`) confirming all five kernel criteria:

| Criterion | Result | Evidence |
|---|---|---|
| Context Assembly | PASS | Profile (name, brand, personality), 3 goals, vibra state all present in ContextObject |
| Genuine Orchestration | PASS | OrchestratorAgent scans intent keywords, matched "launch" + "campaign", routed to PlanningAgent |
| Artifact Persistence | PASS | LaunchPlan saved as JSON to `zon_memory/artifacts/{ws_id}/` and successfully reloaded from disk |
| Determinism | PASS | Two runs both produced structurally coherent LaunchPlans with valid scores and action items |
| Observability | PASS | 28 structured log lines tracking every pipeline stage |

### Rationale
- **Architecture survived first contact with reality.** The theoretical design (ADR-001 through ADR-008) was exercised end-to-end without needing structural changes.
- **Intent-based orchestration is demonstrated.** The OrchestratorAgent performs genuine routing (5 keywords scanned, 2 matched, sub-agent selected) rather than calling a single LLM directly.
- **Provider abstraction is verified.** The provider chain (Ollama Cloud → NVIDIA → static fallback) resolves without modifications to the Kernel.
- **Artifact durability is proven.** Generated launch plans persist to disk as JSON under workspace scope and reload correctly.

### Consequences
- The Kernel transitions from **architecture validation** to **platform evolution**.
- Memory & Identity becomes the next implementation priority.
- Future contributors see a validated foundation, not just documented intent.
- The architecture freeze (ADR-008) remains in effect — no new abstractions without implementation evidence.
- All subsequent work builds on a proven Core, not an assumed one.

---

## ✅ ADR-010: Identity Foundation Complete

### Context
After Kernel Validation (ADR-009), the system required a persistent identity layer so that every interaction begins with a rich understanding of the creator, workspace, projects, and prior artifacts. Without this, Context Assembly was limited to the current request — it could not reason across sessions.

### Decision
The **Creator Continuity Layer** is now operational, comprising six integrated subsystems:

| Subsystem | File | Role |
|---|---|---|
| Kernel | `core/kernel.py` | Enforces invariant K-001: initialize → assemble context → execute agents. Runtime error if violated. |
| Context Enrichment | `core/context_assembly.py` | Injects `recent_artifacts` + `active_projects` into every ContextObject alongside profile, goals, vibra |
| Artifact Envelope | `core/orchestration.py` | Every artifact saved with `{artifact_id, type, workspace_id, project_id, created_by, provider, confidence, version, data}` |
| Snapshot Service | `services/snapshot_service.py` | Independent execution trace (provider, intent, confidence, timestamp) — separate from artifacts and memory |
| Session Memory | `core/orchestration.py` | Auto-ingests request + artifact ID as memory nodes after each successful pipeline execution |
| Retrieval API | `main.py` | `GET /workspaces/{id}/artifacts`, `GET /workspaces/{id}/artifacts/{aid}`, `GET /workspaces/{id}/snapshots` |

### Invariant K-001 (Permanent)
> No intelligence executes before context is assembled. `Kernel.initialize()` must complete before `Kernel.execute()` is called.

### Rationale
- **Continuity over sessions:** Creator identity, workspace state, and prior artifacts load automatically — the system does not reset between requests.
- **Separation of concerns:** Memory, artifacts, and snapshots are deliberately decoupled. Each can evolve independently without creating coupling.
- **Artifact lineage:** The envelope schema creates a foundation for versioning, provider auditing, and provenance tracking without schema redesign.
- **Observability by design:** Every execution produces a snapshot, making evaluation, analytics, and timeline visualization possible without ad-hoc instrumentation.

### Consequences
- All future agent execution must go through `Kernel.execute()` — bypassing the Kernel is an architecture violation.
- The artifact envelope schema (`artifact_id`, `type`, `provider`, `confidence`, `version`) must not be modified without ADR update.
- Snapshot storage format is independent of artifact and memory storage — this separation is deliberate and must be preserved.
- Phase 2 (Workflow Intelligence) builds on the Continuity Layer, not below it.

---

## ✅ ADR-011: Production Intelligence Introduced

### Context
After Kernel Validation (ADR-009) and Identity Foundation (ADR-010), the system could generate artifacts and persist context across sessions, but it could not reason about production completeness. Every artifact was produced in isolation — no subsystem could answer "what exists, what's missing, and what should happen next."

The multi-workspace architecture (ADR-001) and Artifact Graph vision (ADR-005) implied intelligent production awareness, but the architecture freeze (ADR-008) prohibited new abstractions without implementation evidence.

### Decision
The **Production Intelligence Engine (PIE)** is introduced as a stateless decision service owned by the Kernel, operating exclusively on deterministic rules — no LLM calls, no database, no external dependencies.

PIE v0 comprises:

| Component | File | Role |
|---|---|---|
| PKG (Production Knowledge Graph) | `core/pie.py` | Static adjacency map: `artifact_type → [valid next types]` |
| PIE Engine | `core/pie.py` | BFS traversal + priority ranking + progress computation |
| PIEAssessment Schema | `core/schemas.py` | `production_state, completed, missing, recommended_next, production_progress, confidence` |
| Kernel Integration | `core/kernel.py` | PIE runs after `execute()` completes, before returning to caller |
| API Integration | `main.py` | `pie` field included inline in `POST /generate-launch-plan` response |

### Production Knowledge Graph (PKG v0)

```
launch_plan → campaign_plan, content_calendar, press_release
campaign_plan → budget_plan, content_calendar
content_calendar → content_script, production_schedule
press_release → media_kit, press_distribution
budget_plan → resource_allocation
content_script → []  (leaf)
production_schedule → []  (leaf)
media_kit → []  (leaf)
press_distribution → []  (leaf)
resource_allocation → []  (leaf)
```

### Production States

| State | Progress Range | Meaning |
|---|---|---|
| `planning` | < 0.35 | Foundational artifacts only |
| `production` | 0.35 – 0.59 | Core production in progress |
| `review` | 0.60 – 0.84 | Most artifacts exist, quality review phase |
| `publishing` | 0.85 – 0.99 | Near complete, final deliverables pending |
| `completed` | 1.0 | All reachable artifacts produced |

### Rationale
- **Zero LLM dependency:** PIE is fully deterministic — tests pass without API keys, network, or model access. This separation between *generation* (LLM-dependent) and *evaluation* (deterministic) is a core architectural property.
- **Stateless by design:** PIE receives state, computes assessment, returns result. No internal state, no caching, no side effects. Testable in isolation.
- **Kernel-owned:** PIE runs after `execute()` — it does not interfere with generation, does not block the pipeline, and produces advisory output alongside the artifact.
- **Progress as a signal:** `production_progress` (0.0 → 1.0) gives creators and dashboards a single numeric indicator of production completeness, derived from graph reachability.
- **Confidence weighted by graph density:** Confidence combines progress with graph complexity — a small graph with few branches produces lower confidence than a richly connected production path.
- **Vocabulary over functionality:** The `production_state` field adds no new reasoning — it maps `progress` to a human-readable label — but it changes how the system communicates about production maturity.

### Consequences
- PIE must remain stateless and deterministic. Any future version that introduces LLM calls for production reasoning must first demonstrate that the static graph is insufficient.
- The PKG can be extended (new artifact types, new edges) without modifying the PIE engine — the graph is a data dependency, not a code dependency.
- The three-question output (`completed`, `missing`, `recommended_next`) becomes the standard interface for production queries — dashboards, CLIs, and future evaluation agents consume this shape.
- ADR-004's Production Kernel now includes PIE as a confirmed component (alongside Context Assembly, Agent Lifecycle, and Artifact Pipeline).
- The first evolutionary cycle is complete: Architecture → Kernel → Identity → Production Intelligence.
