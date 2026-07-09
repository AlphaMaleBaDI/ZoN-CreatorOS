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

---

## ✅ ADR-012: Artifact Lineage

### Context
By Mission 007 and Mission 008, CreatorOS evolved from single-artifact generation to multi-artifact production pipelines (Launch Plan → Campaign Plan → Content Calendar). Each new artifact was generated with access to its predecessors through Context Assembly, but this behavior was implicit — not enforced by the architecture. Nothing prevented a new artifact from being generated in isolation, ignoring the production history already accumulated.

### Decision
Every production artifact inherits the complete validated production context generated by its predecessors. No artifact is generated from an empty state if production history exists.

This principle is codified as **Artifact Lineage** — a permanent architectural invariant:

> **Epoch II, Invariant P-001 (Production Dependency):**
> An artifact must never be generated in isolation if its required predecessors already exist. Every artifact stands on the shoulders of the previous one through automatic context enrichment.

### Implementation (already in place)
1. **Context Assembly enrichment** (`core/context_assembly.py`): Every `ContextObject` receives `recent_artifacts` (prior artifacts) and `active_projects` as standard fields — no opt-in required.
2. **Agent prompt construction** (`agents/campaign_agent.py`, `agents/content_agent.py`): Each agent's `_build_prompt()` method iterates over `context.recent_artifacts`, extracts relevant data from predecessor artifact envelopes, and injects it into the LLM prompt automatically.
3. **Production Knowledge Graph** (`core/pie.py`): The PKG defines valid production paths. PIE will not recommend an artifact whose prerequisites are missing.
4. **Intent routing** (`core/orchestration.py`): The Orchestrator maps artifact types to agents, ensuring the correct agent handles each production step.

### Rationale
- **Prevents context loss:** Without lineage, each generation starts from scratch, discarding the strategic decisions made in prior artifacts.
- **Enables accumulated intelligence:** The Content Calendar should reflect campaign strategy; the campaign should reflect launch positioning. Lineage makes this automatic.
- **Aligns with Epoch II principle:** "Protect the creator's momentum." If every artifact requires re-explaining the context, momentum is destroyed.

### Consequences
- All future domain agents must follow the lineage pattern: iterate over `context.recent_artifacts` and inject predecessor data into prompts.
- The artifact metadata envelope (`artifact_type` field) becomes the primary key for lineage queries — agents filter `recent_artifacts` by type.
- Invariant P-001 joins K-001 (No model executes before context assembly) as a permanent architectural rule.
- Domain Packs (future) will inherit lineage behavior automatically through the Context Assembly Engine — no per-pack implementation required.

---

## ✅ ADR-013: Workspace is the Primary Interface

### Context
By Mission 009, CreatorOS components operate as a coherent system: Context Assembly, Orchestration, Agents, Artifacts, PIE, Evaluation, and Production State Awareness. However, the creator experiences these through isolated endpoints (`/generate-launch-plan`, `/workspaces/{id}/state`). There is no single surface that presents the workspace as a unified creative environment.

The system has the data. It lacks the interface.

### Decision
The primary unit of interaction in CreatorOS is the **Workspace**. Agents, artifacts, memory, production state, evaluation, and identity are all viewed through the active workspace rather than existing as isolated systems.

This means:
1. **Every request starts from the workspace** — not from a blank prompt. The workspace knows the creator, the active project, the production phase, and the recent work.
2. **The workspace surface is the default view** — before any generation, the creator sees where they are. The dashboard is the landing page, not a sidebar.
3. **Generation happens inside the workspace** — generating a Launch Plan is not "calling an API." It is "continuing production from the workspace."
4. **State is inherent, not queried** — the workspace always shows the production phase, evidence, and next requirements. No separate `/state` call needed.

### Implementation
The workspace surface is a **read-only dashboard** assembled from existing data sources:

```
Workspace Dashboard
  ├── OS identity (name + version)
  ├── Workspace name
  ├── Creator profile (name, brand, vibra)
  ├── Active project
  ├── Production phase (visual indicator + progress bar)
  ├── Recent artifacts (completed work, checkmarked)
  └── Recommended next steps (from PIE)
```

No new data sources. No new services. The dashboard is a presentation layer on top of:
- `ProfileService` → creator identity
- `WorkspaceService` → workspace + project
- `ArtifactService` → recent artifacts
- `PIE` → production state assessment + recommendations

### Rationale
- **Aligns with Epoch II principle:** "Protect the creator's momentum." A workspace landing page prevents context loss between sessions.
- **Matches the Mission 009 philosophy:** State is derived, not stored. The workspace demonstrates this by assembling the view from live data.
- **Supports demo psychology:** Judges experience "I'm inside a creative OS" rather than "I'm talking to an AI."
- **Architecture-neutral:** No new services, no new schemas, no new data flows. Pure presentation.

### Consequences
- `demos/demo_workspace.py` becomes the primary demo entry point, replacing the chat-style `demo_kernel.py` for first impressions.
- Future UI development (web, TUI, dashboard) should use the same workspace surface concept.
- The existing API endpoints remain valid — the workspace surface is a consumer, not a replacement.
- Domain Packs (future) will contribute workspace panels without modifying the surface layout.
- This is the last ADR of Epoch II's foundation phase. Subsequent ADRs will focus on experience deployment.

---

## ✅ ADR-014: Understanding is the Kernel

### Context

By Mission 015, CreatorOS had evolved into a hardened production pipeline: Context Assembly → Intent Engine → PIE → Orchestrator → Agents → Artifacts → Evaluation. This workflow generated launch plans, campaign strategies, content calendars, and publishing checklists with deterministic evaluation, artifact lineage, and persistent workspace state. 63 tests passed. The pipeline was reliable.

But reliability exposed a deeper question: *What is CreatorOS optimizing for?*

The pipeline optimized for artifact generation. Each component existed to produce the next output. The architecture was a workflow engine dressed as an operating system — efficient at production, incapable of cognition.

The rigid pipeline felt wrong because **artifacts are outcomes, not cognition.** CreatorOS should not think "We are generating a Campaign Plan." It should think "We currently understand enough to externalize a campaign strategy." The artifact is a consequence, not a destination.

**Everything built to this point is not wasted.** Onboarding, PIE, orchestration, artifact lineage, evaluation, persistence, context assembly, the intent engine, the conversational shell — every component becomes an executor or sensor around a cognitive core instead of being the core itself.

### The Discovery: Three Core Objects

CreatorOS v1.0 has exactly three core objects:

```
CreatorMind (process)
     │
     ▼
Reasoning
     │
     ▼
Executors
```

Everything else is implementation.

- **CreatorMind** is a *process*, not a service. It continuously transforms observations into beliefs, beliefs into understanding, and understanding into reasoning.
- **Reasoning** is a single engine with access to *everything*: beliefs, evidence, tensions, confidence, momentum, project state, artifacts, evaluation, memory.
- **Executors** are the existing production components — PIE, Orchestrator, Agents, Evaluators. They perform work. They do not reason.

### The Six Cognitive Primitives

CreatorOS recognizes exactly six primitives. Nothing more.

```
Observation
     │
     ▼
Beliefs
     │
     ▼
Tensions
     │
     ▼
Understanding (derived, never stored)
     │
     ▼
Reasoning
     │
     ▼
Actions
```

**Observation** — Every input to the system is an observation. Conversation messages, artifacts, research, evaluations, approvals, failures, corrections. Observations are immutable and carry strength (confidence, recency, authority, impact). Evidence implies truth; observations do not. The system stores an **Evidence Ledger** (append-only log), not conversation history.

**Beliefs** — Hypotheses derived from observations, not facts. Every belief has a confidence score, supporting observation IDs, and a lifecycle: `candidate → active → challenged → resolved → superseded`. Beliefs evolve like Git commits — they supersede each other, never overwrite. When a creator says "I have $5,000" and later "I secured a $250,000 grant," the first belief is resolved and superseded, preserving cognitive history.

**Tensions** — Creators live inside tensions: budget vs. ambition, authenticity vs. virality, time vs. quality, exploration vs. shipping. Tensions are richer than contradictions — they include competing priorities, resource constraints, and value conflicts. Each tension has severity, priority, and linked beliefs. Reasoning resolves the highest-priority tension first.

**Understanding** — Understanding is synthesized from beliefs, not stored. It is a materialized view — like a database query result, not a table. When belief #12 changes, understanding updates automatically. No synchronization bugs, no stale cognition, no cached reasoning. Understanding is what enables narrative statements like "The project is creatively mature but commercially immature" — synthesized insight that no single belief contains.

**Reasoning** — Given current understanding, what action creates the most leverage? Sometimes: generate a campaign. Sometimes: research competitors. Sometimes: ask another question. Sometimes: do nothing. Reasoning has no knowledge of specific executors (PlanningAgent, CampaignAgent, PublishingAgent, Fireworks, Ollama, AMD). It outputs an abstract `ActionPlan`.

**Actions** — A `Dispatcher` translates abstract ActionPlans into executor calls. Executors (existing components) perform work and produce artifacts. Reasoning → Dispatcher → Executor is three distinct responsibilities that must not be conflated.

### Architectural Invariants

**U-001 (Explainability)** — Every system response must be explainable by the current Creator State. The OS can always answer: "Why did you recommend this? What evidence supports this? Which belief caused this decision? What would make you decide differently?"

**U-002 (Artifact Modesty)** — Artifacts never become knowledge automatically. An artifact's existence is an observation, not a belief. The system must reason about whether an artifact's content is credible before it influences future decisions.

**Philosophical Invariant** — Nothing in CreatorOS is ever forgotten. It is either observed, believed, questioned, challenged, resolved, or superseded.

### The First Principle

> **CreatorOS does not optimize for generating artifacts. It optimizes for maintaining the most coherent understanding of a creator's evolving work. Artifacts are externalizations of that understanding, not the objective itself.**

### What Changes

The current architecture:

```
Shell → Intent Engine → PIE → Orchestrator → Agents → Artifacts
```

Becomes:

```
Shell → CreatorMind → Reasoning → Dispatcher → Executors → Artifacts
```

**Intent Engine disappears.** Not because it was wrong — because intent is a single belief among many. Intent becomes part of the belief graph, not a separate component.

**PIE is renamed philosophically.** Not Production Intelligence Engine — **Practical** Intelligence Engine. Its job is no longer "What's the next artifact?" but "Given everything we understand, what action creates the most leverage?"

**Conversation history becomes the Evidence Ledger.** History is passive. The Evidence Ledger is an append-only log of everything the OS has observed, with confidence, impact, and source metadata.

**The architecture shifts from artifact-centered to cognition-centered.**

```
Old: Artifacts → State
New: Observations → Beliefs → Understanding → Reasoning → Artifacts
```

Artifacts move from the center to the edge — exactly where they belong.

### Consequences

- The existing production pipeline (PIE, Orchestrator, Agents, Evaluation, Artifact Lineage) is not replaced — it becomes an executor subsystem around the cognitive core.
- Mission 016 is split into 016A (Architectural Constitution — this ADR + data schemas only) and 016B (Observer Mode — evidence ingestion, belief extraction, tension detection, no pipeline driving).
- CreatorMind is a process, not a service. It does not get its own API endpoint initially. It observes.
- Understanding is never stored — always derived from current beliefs when Reasoning runs.
- Beliefs use `lifecycle` (not `status`) with states: candidate, active, challenged, resolved, superseded.
- Tensions use `severity` and `priority` as separate dimensions; Reasoning resolves highest-priority first.
- CurrentUnderstanding carries `version`, `derived_from_observation`, and `derived_from_beliefs` for full explainability.
- All future components must pass the ADR-014 test: "Does this deepen understanding or just produce an artifact?" If the latter, it is an executor/renderer, not part of the kernel.
- ADR-008's architecture freeze is implicitly superseded for the cognitive core — but remains in effect for executors. New executor abstractions still require implementation evidence.
- The invariant "Every action must be explainable by the current understanding" becomes the system's most important correctness criterion.

---

## ✅ ADR-015: Observer Before Actor

### Context

ADR-014 established Understanding as the Kernel — the principle that CreatorOS optimizes for maintaining the most coherent understanding of a creator's evolving work. But understanding requires witnessing before acting. A system that acts before it observes will produce confident but incorrect decisions.

The architecture freeze (ADR-008) and the existing production pipeline (PIE, Orchestrator, Agents, Artifacts) are hardened and tested. Any new component that touches the production path risks destabilizing the demo. The cognitive core must be introduced without modifying any executor.

### Decision

CreatorOS adopts the **Observer Before Actor** principle:

> **CreatorMind must observe the creator successfully before it is ever permitted to influence the creator.**

This is enforced by splitting Mission 016 into two phases:

**Mission 016A (Architectural Constitution)** — ADR-014 + data schemas only. No executable code. The laws of the operating system.

**Mission 016B (Observer Mode)** — A `CreatorMindObserver` that witnesses every shell message and builds a cognitive picture without influencing any outcome. Zero feedback to the production pipeline.

### Observer Mode Contract

The `CreatorMindObserver` is not an engine. It does not:

- Call LLMs
- Generate artifacts
- Modify PIE state
- Route or reroute requests
- Recommend or block actions
- Change any executor behavior

It only:

1. **Observes** — Every shell message produces one or more `Observation` objects appended to the Evidence Ledger.
2. **Believes** — Observations update `Belief` lifecycles (candidate → active → challenged → resolved → superseded).
3. **Detects tensions** — Conflicting beliefs become `Tension` objects with severity and priority.
4. **Derives understanding** — `CurrentUnderstanding.version` increments only when understanding changes (new active beliefs, new tensions, resolved contradictions).
5. **Reports** — The dashboard renders the current CurrentUnderstanding in a "Creator State" panel showing live cognitive evolution.

### Architectural Position

```
Conversation
     │
     ├──────────────► Existing System (unchanged)
     │                    │
     │                    ▼
     │               Launch Plan, Campaign Plan, etc.
     │
     ▼
CreatorMindObserver
     │
     ▼
Observation Ledger
     │
     ▼
Belief Graph
     │
     ▼
Tension Detection
     │
     ▼
Creator State (reported to dashboard, never to pipeline)
```

### Acceptance Criteria for Mission 016B

- Every shell message produces one or more `Observation` objects.
- Observations update `Belief` lifecycles.
- Contradictions become `Tension` objects.
- `CurrentUnderstanding.version` increments only when understanding changes.
- Nothing in the production pipeline behaves differently.
- All existing tests still pass.
- A new "Creator State" panel appears in the UI showing live cognitive evolution.

### Rationale

- **Safety first:** An actor that hasn't observed is dangerous. Observer mode proves the observation layer before any reasoning or acting layer is added.
- **Zero regression risk:** The observer is a pure side effect — it reads messages, never modifies execution. All 77 existing tests continue to pass unchanged.
- **Incremental adoption:** The observer can be verified independently of the pipeline. The dashboard panel provides immediate visible feedback without architectural risk.
- **Philosophical alignment:** "Nothing in CreatorOS is ever forgotten. It is either observed, believed, questioned, challenged, resolved, or superseded." The observer is the first implementation of this invariant.
- **Fireworks reservation:** Frontier model calls are reserved for belief synthesis in a future phase. The observer begins deterministically (keyword extraction, heuristic tension detection), proving the data model before adding expensive reasoning.

### Consequences

- The `CreatorMindObserver` is instantiated once in `main.py` and called after every shell message processed by the intent endpoint.
- A new API endpoint `GET /workspaces/{id}/mind` exposes the current `CurrentUnderstanding` for dashboard consumption.
- The observer persists `CurrentUnderstanding` to `zon_memory/mind/{workspace_id}/creator_state.json` — separate from artifacts, snapshots, and memory.
- No existing service, route, agent, or evaluation layer is modified.
- Belief extraction begins deterministically (keyword patterns). LLM-assisted extraction is deferred to a future phase.
- The observer's `CurrentUnderstanding` is readable by the dashboard but never fed into the production pipeline.

---

## ✅ ADR-016: The Reasoning Layer

### Context

Mission 016 established Observer Mode — a `CreatorMindObserver` that witnesses every shell message, extracts observations, builds beliefs, detects tensions, and derives a `CurrentUnderstanding`. The observer is deterministic, pure, and has zero influence on the production pipeline.

But the architecture now has a gap. Between the observer and the executors, there is no **reasoning** — no capability to synthesize across time, prioritize what matters, ask questions, form hypotheses, or decide what action creates the most leverage.

The observer produces:

```
Observations → Beliefs → Tensions → CurrentUnderstanding
```

But the pipeline still expects:

```
Intent → PIE → Orchestrator → Agent → Artifact
```

The cognitive core is richer than the intent engine. But it has no way to influence decisions yet — and more importantly, no way to **justify** decisions.

Mission 017 introduces the layer that bridges this gap.

### Decision

The **Reasoning Layer** is introduced as the second cognitive capability (after Observation). It sits between the observer and the dispatcher:

```
Observation
     │
     ▼
Beliefs
     │
     ▼
Tensions
     │
     ▼
Reasoning
  ├── Reflection
  ├── Prioritization
  ├── Hypothesis
  ├── Questioning
  ├── Planning
  └── Decision
     │
     ▼
CurrentUnderstanding
     │
     ▼
Dispatcher
     │
     ▼
Executors
```

**Reasoning creates Understanding.** Understanding is not a store that reasoning reads — it is the output that reasoning produces. Every time reasoning runs, it synthesizes all available evidence, beliefs, and tensions into a fresh understanding. That is why understanding is never persisted as truth — it is always a synthesis of the present cognitive state.

### Reasoning Capabilities (defined by contract)

The Reasoning Layer defines six capabilities, each with a clear input/output contract:

| Capability | Input | Output | Provider |
|---|---|---|---|
| **Reflection** | Belief history, tension trajectory | Narrative synthesis across time | Fireworks (premium) |
| **Prioritization** | Active tensions, momentum, project state | Ordered list of what matters most | Deterministic first |
| **Hypothesis** | New observations, unresolved questions | Candidate beliefs with confidence | Deterministic + optional LLM |
| **Questioning** | Understanding gaps, low-confidence beliefs | Questions to ask the creator | Deterministic |
| **Planning** | Priorities + artifact state | Recommended action sequence | Existing PIE |
| **Decision** | All of the above | ActionPlan with reasoning trace | Deterministic |

### The First Capability: Reflection

Reflection is the first reasoning capability for the same reason that Observation was the first cognitive primitive: it must be proven before it is trusted.

Reflection answers:

> "Over time, how has my understanding changed?"

A reflection is a synthesis across time — not a belief, not an observation, but a pattern detected across multiple observations and beliefs. For example:

```
"Over the last three conversations, my understanding has shifted
from 'the creator wants an EP' to 'the creator is building a
creative brand around Afrofuturism.'"
```

This sentence cannot be extracted from a single observation. It requires reasoning across the full evidence ledger.

### Separation from Executors

The Reasoning Layer:

- **Never** calls executors directly.
- **Never** generates artifacts.
- **Never** modifies the production pipeline.
- **Never** knows about PlanningAgent, CampaignAgent, ContentAgent, Ollama, Fireworks, or AMD.

It outputs an abstract `ReasoningResult` containing reflections, priorities, questions, and a decision narrative. A `Dispatcher` (Mission 018) translates those into executor calls.

### Mission 017 Phases

Following the same discipline as Mission 016:

**17A (Architectural Contract)** — This ADR + ReasoningResult + Reflection schemas. No runtime behavior changes.

**17B (Shadow Mode)** — The Reasoning Layer runs after every observer update, producing reflections and an updated CurrentUnderstanding with reasoning attached. The Dispatcher ignores it. The UI displays the reasoning output for demonstration while the production pipeline runs untouched.

**17C (Promotion to Driver)** — Only after observing consistent high-quality reasoning does the Dispatcher begin executing actions based on its recommendations.

### Invariants

**R-001 (Evidence Purity)** — Reasoning never creates evidence. Only observations create evidence. Reasoning only interprets evidence. This prevents hallucinated beliefs, circular reasoning, and the OS convincing itself something is true. Everything must ultimately trace back to an observation.

**R-002 (Reasoning never executes alone)** — Reasoning must not run unless the observer has produced a current understanding. If no observations exist, reasoning returns empty.

**R-003 (Reasoning is explainable)** — Every ReasoningResult must trace back to the beliefs, tensions, and observations that produced it. No opaque decisions.

**R-004 (Fireworks is reserved for Reflection)** — The premium provider is called only for synthesis across time. Prioritization, hypothesis, questioning, and decision remain deterministic. This prevents credit waste and keeps the architecture auditable.

**R-005 (Understanding is created by Reasoning)** — CurrentUnderstanding is the output of reasoning, not a store that reasoning reads. Version increments when reasoning produces a materially different understanding.

### Rationale

- **Reflection first, planning last** — The system should understand how its understanding has changed before it tries to act on that understanding. Planning is a downstream consumer of reflective insight.
- **Fireworks at the right level** — Premium reasoning tokens are spent on synthesis (Reflection), not content generation. This is the most efficient use of the provider budget and aligns with the principle that firepower belongs at the cognitive layer, not the executor layer.
- **Shadow mode protects the demo** — 17B allows the Reflection output to be displayed in the dashboard without any risk to the working production pipeline. The judges see cognition without destabilization.
- **No new engines** — The Reasoning Layer is not an engine. It is a capability set with a contract. Each capability is a function, not a service. This prevents architecture bloat.
- **Clean progression across missions** — 016 (observe) → 017 (reason) → 018 (act) forms a natural evolution that maps directly to how cognition develops: witness, understand, then influence.

### Consequences

- Mission 017 is split into 17A (this ADR + schemas), 17B (shadow mode reasoning), and 17C (promotion to driver).
- `Reflection` and `ReasoningResult` are added to `core/schemas.py` as data shapes only — no runtime code in 17A.
- `CurrentUnderstanding` gains an optional `reasoning` field to hold the most recent `ReasoningResult` for traceability.
- The Fireworks provider is not called in 17A or 17B — reflection begins deterministically (keyword-pattern synthesis) to prove the contract before spending premium credits.
- The dashboard gains a "Reasoning" section in 17B, showing recent reflections, priorities, and the decision narrative alongside the existing cognitive state.
- The intent engine (`core/intent_engine.py`) is not removed but is demoted from architectural centerpiece to a transitional bridge. Its keyword-based routing becomes a fallback for the deterministic Reasoning Layer.
- The "Understanding creates the narrative" flow from ADR-014 is now architecturally realized: reasoning produces understanding, and understanding drives the narrative presented to the creator.

---

## ✅ ADR-017: Collaborative Reasoning

### Context

Mission 019-020 conversations revealed a critical gap. The system could observe, reason, and ask questions — but it could not **collaborate**.

When the creator replied to "What themes are you hoping to explore?" with:

```
theme?
```

The system re-asked its question. A human creative partner would have recognized this as a **request for explanation** and answered:

> *"Theme is the underlying idea your story explores. From what you've told me, I see social media influence, education, and identity as possibilities. Which feels closest?"*

When the creator asked "what do you want to know?" the system answered "what else should I know?" — a conversational deadlock.

These failures are not observer bugs or requirement-matching errors. They are **reasoning failures**. The system had the right understanding but didn't know what conversational move to make.

The architecture today:

```
Observation → Beliefs → Understanding → Reasoning → Dispatcher → Executors
```

Reasoning produces questions, but it asks them the same way every time — by cycling through unanswered requirements. It never explains, suggests, reflects back, challenges, or celebrates.

This ADR extends ADR-016. It does not create a new layer.

### Decision

Collaborative Reasoning is an **evolution of ADR-016's Reasoning capability set**, not a new architectural layer. The pipeline remains:

```
Observation
     │
     ▼
Beliefs
     │
     ▼
Tensions
     │
     ▼
CurrentUnderstanding
     │
     ▼
Reasoning
  ├── Reflection
  ├── Prioritization
  ├── Hypothesis
  ├── Questioning
  ├── Planning
  ├── Decision
  └── **Conversational Move Selection**  ← NEW
     │
     ▼
ReasoningResult (with mode, message, hypotheses, unanswered)
     │
     ▼
Dispatcher
     │
     ▼
Executors
```

Reasoning still holds single decision authority. It just has a richer vocabulary.

#### Conversational Action Modes

ReasoningResult gains a `mode` field from the following vocabulary:

| Mode | When | Example |
|---|---|---|
| **ASK** | System needs information it doesn't have | "What themes are you hoping to explore?" |
| **EXPLAIN** | Creator asked what a question means, or system detected confusion | "Theme is the underlying idea your story explores. Here are some I'm already noticing..." |
| **SUGGEST** | System has enough context to propose directions | "These are the themes I'm beginning to see. Which feels closest?" |
| **REFLECT** | System summarizes understanding back to creator | "I think we've found the heart of your story." |
| **CHALLENGE** | System detects conflicting goals or inconsistencies | "You said Sarah leaves school to become an influencer, but also that education is important to her. Is that tension intentional?" |
| **GENERATE** | System judges understanding sufficient for an artifact | "I think I understand well enough to draft something." |
| **CELEBRATE** | System acknowledges a breakthrough or decision | "I think we've found the heart of your story." |

These are not separate executors. They are modes of a single `ReasoningResult.message` — different rhetorical intentions for how Reasoning presents its understanding to the creator.

#### Meta-Questions

The ConversationClassifier evolves to recognize a new intent:

```
MetaQuestion
```

Messages like:

- "theme?"
- "what do you mean?"
- "explain that"
- "why?"
- "can you clarify?"
- "what is conflict?"
- "i don't understand"

These are **not project evidence**. They never enter the cognitive graph as observations. They route directly to Reasoning with mode=EXPLAIN, passing the original question as context so Reasoning can explain what it meant and why.

Classification hierarchy:

```
                input
                  │
          ┌───────┴───────┐
          │               │
   MetaQuestion      ConversationClassifier
          │          ├── greeting
          │          ├── small_talk
          │          ├── project
          │          ├── correction
          │          ├── approval
          │          ├── rejection
          │          └── unknown
          │
          ▼
     Reasoning
     mode=EXPLAIN
```

Meta-question detection happens before the main classifier gate — alongside greeting/small_talk — so no evidence is created from "what do you mean?"

#### General Hypotheses (Not Requirement-Bound)

Reasoning forms hypotheses about **anything** — the project's tone, the creator's preferences, the likely audience, the unspoken conflict, even the creator's skill level. A Hypothesis is not bound to a requirement:

```python
Hypothesis(
    subject="theme",                               # What this is about
    statement="Social media influence on identity", # The inferred content
    confidence=0.82,                                # How sure reasoning is
    supported_by=["observation_id_3", "belief_id_7"]
)
```

When the creator says "a young teenager named sarah who was influenced by some social media influencers that she decided going to school was no longer important," Reasoning forms:

```python
[
    Hypothesis(subject="theme", statement="Social media influence on identity", confidence=0.82, ...),
    Hypothesis(subject="theme", statement="The value of education", confidence=0.71, ...),
    Hypothesis(subject="theme", statement="Identity and belonging", confidence=0.63, ...),
    Hypothesis(subject="tone", statement="Serious, dramatic", confidence=0.55, ...),
    Hypothesis(subject="genre", statement="Contemporary coming-of-age", confidence=0.78, ...),
]
```

A hypothesis:
- **Does not change any requirement status.** Only Observation can confirm a requirement.
- **Is presented to the creator via SUGGEST.** The system offers its inference for confirmation or correction.
- **Raises the confidence of the originating observation** when confirmed.
- **Informs which question gets asked next.** If Theme hypothesis confidence is 0.82, the system doesn't need to ask "what themes?" — it asks "does social media influence feel like the right theme?"

When multiple hypotheses exist for the same subject, Reasoning includes them all in a suggestion: "I'm seeing social media influence (0.82), education (0.71), and identity (0.63). Which feels closest?"

#### Confidence Bands

Confidence is not just a number — it selects **behavior**. Five bands, each mapping to a conversational mode:

| Band | Confidence | Mode | Behavior |
|---|---|---|---|
| Unknown | 0.00–0.35 | ASK | No basis to infer. Need information. |
| Vague | 0.35–0.60 | EXPLAIN | Weak signal detected. Explain the question so creator can answer. |
| Plausible | 0.60–0.80 | SUGGEST | Strong enough to propose. Offer hypothesis for confirmation. |
| Strong | 0.80–0.95 | REFLECT | High confidence. Summarize understanding back to creator. |
| Certain | >0.95 | GENERATE candidate | Sufficient understanding. Ready to produce. |

The system never hardcodes "ask about theme because it's first." It naturally ASKs because Theme confidence is 0.12. It naturally SUGGESTs because Theme confidence is 0.73 after extracting "influenced by social media influencers."

Confidence bands govern **individual hypotheses**, not the entire ReasoningResult. Reasoning may have multiple hypotheses at different bands simultaneously — a Strong hypothesis about genre (0.88) and a Vague hypothesis about audience (0.42). The mode selected is the one whose band produces the highest-value conversational move; if all hypotheses are Strong or Certain, GENERATE becomes viable.

#### Response Classification, Not Deadlock Counters

Conversational quality degrades when the system treats every creator response as either "answered" or "not answered." A counter that escalates ASK → EXPLAIN → SUGGEST after N retries makes conversation mechanical.

Instead, Reasoning classifies the creator's response into one of six states:

| State | Signal | Example | Next Mode |
|---|---|---|---|
| `answered` | Directly addressed the question | "Social media influence." | Next priority |
| `partial` | Addressed it tangentially | "The story is about identity." | SUGGEST (offer what's missing) |
| `confused` | Asked what the question means | "Theme?" | EXPLAIN |
| `redirected` | Changed the subject | "Actually, let me tell you about the setting." | Follow the redirect |
| `rejected` | Declined to answer | "I'll figure that out later." | Move on |
| `unknown` | Unparseable | "Hmm." | REFLECT (summarize, re-approach) |

No counters. Reasoning evaluates the response, classifies it, and selects the mode that matches the conversational state.

```
Example:

ASK:  "What themes are you hoping to explore?"
      ↓
      "Theme?"
      ↓
ResponseClassification = confused
      ↓
EXPLAIN: "Theme is the underlying idea your story explores. From what you've told me,
          I'm seeing social media influence, education, and identity as possibilities."

Or:

ASK:  "What themes are you hoping to explore?"
      ↓
      "I'd rather figure that out later."
      ↓
ResponseClassification = rejected
      ↓
Move on (no escalation, no repeat)
```

This is deterministic classification, not LLM judgement — keyword patterns detect confusion ("?" on the system's own word), rejection ("will figure out", "later", "don't know yet"), redirect ("actually", "but", "let me tell you about", change of subject), and so on.

#### Information Gain Ordering

When multiple requirements remain unanswered, Reasoning selects the question with the **highest information gain** — the one whose answer would most change CurrentUnderstanding.

Information gain estimation is deterministic:

1. **Hypothesis confidence gap** — If the system has a hypothesis at 0.82, asking for confirmation yields little gain. If all hypotheses are below 0.5, asking yields high gain.
2. **Downstream dependency count** — A question that unlocks 3 other requirements (e.g., genre affects tone, audience, and structure) has higher gain than a leaf requirement.
3. **Conversation flow** — If the creator just provided setting details, the next question should build on setting, not jump to audience.

This prevents the deadlock pattern: "What do you want to know?" → "What else should I know?"

#### Conversation Observations (A Third Evidence Type)

Meta-questions must never become project evidence. But they **are** evidence — they tell Reasoning something about the creator:

- "Theme?" → `{type: conversation, content: "creator asked for clarification of terminology", implication: "prefers examples to abstract questions"}`
- "What do you want to know?" → `{type: conversation, content: "creator expressed confusion about the line of questioning", implication: "current question was too broad"}`
- "I don't know." → `{type: conversation, content: "creator uncertain about a requirement", implication: "should offer suggestions instead of asking"}`

The observation taxonomy expands to three types:

| Type | Becomes project beliefs? | Purpose |
|---|---|---|
| `project` | Yes | Core creative work |
| `creator` | No | The creator's preferences, process, style |
| `conversation` | No | How the conversation is going |

`creator` and `conversation` observations improve Reasoning's collaboration quality over time without polluting the project understanding.

### The Five Behavioral Acceptance Criteria

1. **The system never repeats a question without first acknowledging why it remains unanswered.**
2. **Meta-questions trigger explanations, not evidence collection.**
3. **Reasoning may propose hypotheses before requirements are confirmed.**
4. **Every conversational move is selected by Reasoning using an explicit action mode (ASK, EXPLAIN, SUGGEST, REFLECT, CHALLENGE, GENERATE, CELEBRATE).**
5. **No executor runs unless Reasoning explicitly selects GENERATE.**

These are demonstrable behaviors, not architecture metrics. The hackathon judge can feel them.

### Implementation Plan

**Phase 1 (Meta-Questions + EXPLAIN)**

- Add `MetaQuestion` to ConversationClassifier with keyword/pattern detection
- Route meta-questions to Reasoning with `mode=EXPLAIN`
- Add `message` field to `ReasoningResult`
- `MetaQuestion` creates a `conversation` observation (not `project` observation)
- When mode=ASK and the creator's last message is a meta-question, switch to EXPLAIN

**Phase 2 (Action Modes + Confidence Bands)**

- Add `mode: str` to `ReasoningResult` schema (validated against vocabulary)
- Add `response_classification` field to track creator response state (`answered`, `partial`, `confused`, `redirected`, `rejected`, `unknown`)
- Define confidence bands (0–0.35, 0.35–0.60, 0.60–0.80, 0.80–0.95, >0.95) with corresponding mode defaults
- Wire mode into response builders in `main.py`
- Rename ShadowReasoning → Reasoning (or CollaborativeReasoning)

**Phase 3 (Hypothesis Formation)**

- `Hypothesis` schema: `subject: str`, `statement: str`, `confidence: float`, `supported_by: List[str]`
- Deterministic hypothesis extraction from beliefs + observation content — forms hypotheses about themes, tone, audience, conflict, and any detectable pattern
- Wire into SUGGEST mode — when hypotheses exist with confidence > 0.60, propose them as suggestions
- Response classification: `confused` → EXPLAIN, `rejected` → move on, `partial` → SUGGEST missing piece

**Phase 4 (Response Classification replaces deadlock counters)**

- Implement `classify_response(question: str, response: str) → ResponseState` in Reasoning
- Deterministic keyword patterns detect confusion, rejection, redirect, partial answer
- Mode selection uses response state + hypothesis confidence together, never a retry counter
- Implement information gain ordering to replace first-unanswered loop

### Invariants

**CR-001 (Single conversational authority)** — Reasoning is the sole selector of conversational mode. No Dispatcher, no Executor, no UI code decides whether to ASK, EXPLAIN, or SUGGEST.

**CR-002 (Meta-questions produce no project evidence)** — `MetaQuestion` messages never become `project` observations. They may become `conversation` observations to improve collaboration, but they never enter the project's cognitive graph and never change requirement states.

**CR-003 (Hypotheses change no requirement status)** — Hypothesis formation never sets `RequirementStatus.CONFIRMED`. Only Observation via evaluator or keyword pipeline can confirm a requirement.

**CR-004 (Explainability includes mode selection)** — Every ReasoningResult must trace not only what it concluded but why it chose that conversational mode. The `reasoning_trace` includes mode selection rationale.

**CR-005 (Confidence governs mode)** — Conversational mode is determined by the confidence band of the subject being discussed, not by a question queue or arbitrary priority list. Below 0.35 the system must ASK; above 0.80 it may REFLECT.

### Rationale

- **Guide is not a layer** — Adding a separate Guide layer would create a second decision authority between Reasoning and Dispatcher. This violates the single-decision-authority invariant the last few weeks have carefully established.
- **Richer vocabulary changes the feel** — A system with 7 conversational modes feels radically different from a system with 3, even if the underlying understanding is identical. The hackathon demo impact of EXPLAIN + SUGGEST + CELEBRATE is enormous.
- **Meta-questions are the most common collaboration failure** — In early conversations with creators, "what do you mean?" and "theme?" are the most frequent signals that the system is failing to communicate. Fixing this first has the highest leverage.
- **Hypothesis formation separates competent systems from intelligent ones** — A system that infers before it confirms demonstrates understanding. A system that only confirms demonstrates data collection. The hackathon narrative wins with inference.
- **Deadlock detection is the difference between a collaborator and a form** — Forms repeat questions. Collaborators recognize when they're stuck and try a different approach.

### Consequences

- `ConversationClassifier` gains a new intent category `MetaQuestion` that routes before project evidence collection.
- `ReasoningResult` gains `mode: str`, `message: str`, `hypotheses: List[Hypothesis]`, `response_classification: str`, and `unanswered: List[str]` fields.
- `Hypothesis` dataclass added to `core/schemas.py`: `subject: str`, `statement: str`, `confidence: float`, `supported_by: List[str]`.
- Observation taxonomy expands to three types: `project`, `creator`, `conversation`.
- `ShadowReasoning` renamed to `Reasoning` (or `CollaborativeReasoning`). The "shadow" prefix fit only while reasoning observed without influencing — now it's the sole conversational authority.
- Reasoning gains: response classification (6-state deterministic), general hypothesis formation (not requirement-bound), confidence-band-driven mode selection, and information gain ordering.
- Conversation response builders in `main.py` switch on `mode` to produce different response styles (explanatory vs. suggestive vs. reflective). UI renders mode-specific icons instead of inferring intent from message text.
- The first-unanswered-requirement loop is replaced by: classify response → evaluate hypothesis confidence → select mode by band → determine next question by information gain.
- No new files. No new endpoints. No new engine classes. Changes limited to `core/schemas.py`, `core/conversation.py`, `core/reasoning.py`, and `main.py`.
