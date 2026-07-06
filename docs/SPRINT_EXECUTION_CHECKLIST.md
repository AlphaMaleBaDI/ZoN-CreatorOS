# ZoN CreatorOS - Sprint Execution Checklist

This document serves as the absolute target list of deliverables for the build sprint starting July 6. Every phase delivers one complete **vertical slice** — a working end-to-end flow that crosses all architecture layers.

**Build rule:** Never spend 8 hours perfecting one module in isolation. Complete the vertical slice first, then add depth.

---

## 📦 Phase 1.2: Vertical Slice 1 — Memory & Profile Foundation

*Slice scope: Schema → Service → Storage → API → Test*

**Schemas (Layer 1 — Core)**
- [ ] Implement isolated workspace scoping (`WorkspaceScope`, `ProjectScope`, `MemoryScope` filters)

**Services (Layer 5 — Services)**
- [ ] Profile Service: save, load, update creator profile
- [ ] Memory Service: scoped vector query + session ingestion

**Memory (Layer 4 — Memory)**
- [ ] Implement FAISS vector storage (embedding indexing & search retrieval)
- [ ] Implement CreatorProfileEngine (persistence CRUD)
- [ ] Implement VibraStateEngine with per-scope history

**API (Layer 2 — Application)**
- [ ] Expose profile endpoints in `api/memory_routes.py`

**Tests**
- [ ] Profile retrieval & update tests
- [ ] Workspace memory query insulation tests
- [ ] Scope hierarchy tests

---

## 🧠 Phase 1.3: Vertical Slice 2 — Context Assembly Pipeline

*Slice scope: Context Assembly → Vibra → Router → API → Display*

**Context Assembly (Layer 1 — Core)**
- [ ] Implement `ContextObject` instantiation from profile + memory + vibra
- [ ] Aggregate vector search memories based on tags & relations
- [ ] Aggregate profile settings (brand voice, style preferences)
- [ ] Integrate Vibra state history calculations

**Intelligence (Layer 3 — Intelligence)**
- [ ] Single `intelligence.adapt(context) -> VibraShift` API surface
- [ ] Context-sensitive Vibra computation (not just keyword-based)

**Model Router (Layer 3 — Intelligence)**
- [ ] Implement `route_request()` with simple rules:
  - Lightweight semantic lookups → local NPU / Ollama
  - Heavy reasoning & planning → AMD Instinct Cloud

**API (Layer 2 — Application)**
- [ ] Expose context assembly endpoint
- [ ] Expose Vibra state endpoint

**Tests**
- [ ] Context output fidelity tests
- [ ] Vibra computation tests with mocked memory snapshots
- [ ] Router decision-path tests

---

## 🤖 Phase 1.4: Vertical Slice 3 — Agent Execution & Artifact Generation

*Slice scope: Orchestrator → Agents → Artifacts → Display*

**Orchestrator (Layer 1 — Core)**
- [ ] Implement master router mapping intent to specialized execution logic
  ```
  if intent == "launch": PlannerAgent()
  elif intent == "research": ResearchAgent()
  ```

**Agents (Layer 3 — Intelligence)**
- [ ] **Planner Agent:** Generate roadmaps, timelines from context
- [ ] **Research Agent:** Memory & web lookups
- [ ] **Memory Agent:** Consolidate session → Knowledge Graph
- [ ] **Workflow Agent:** Execute tool calls with `dryRun`/`confirmApply` flow
- [ ] **Orchestrator Agent:** Parse assembled context and coordinate sub-agent routing

**Artifacts (Layer 4 — Artifacts)**
- [ ] Launch Plan generation from agent output
- [ ] Content Calendar generation
- [ ] Project Roadmap generation
- [ ] Execution Report with citation map + Vibra metrics

**Dashboard (Layer 6 — Experience)**
- [ ] Streamlit UI: memory nodes, Vibra meter, agent status, artifact review
- [ ] Artifact Review Center: clickable memory references
- [ ] Vibra history chart (line/area chart across sessions)

**Integration Tests**
- [ ] End-to-end demo pipeline:
  Upload Notes → Upload Lyrics → Release Objective → Context Assembly → Orchestrator → Artifact → Confidence Score

---

## 🎯 Demo Scenario Validation

- [ ] Upload notes file successfully
- [ ] Upload lyrics file successfully
- [ ] Accept release objective text inputs
- [ ] Generate parsed JSON deliverables (Artifacts Layer)
- [ ] Display references to original memory nodes
- [ ] Chart creative state (Vibra) history shifts
- [ ] Verify confidence score outputs
- [ ] Config-based switching: local Ryzen AI NPU ↔ AMD Instinct Cloud (no code change)

---

---

## 🧭 Post-MVP: Validation-Focused Execution Roadmap

Once the hackathon MVP vertical slices (Phases 1.2–1.4) are complete, the architecture is frozen per ADR-008. All subsequent work follows validation phases — prove it works before expanding it.

### Phase 0 — Architecture Freeze (Current)
The architecture is frozen at the current abstraction level. Only bug fixes, clarifications, and implementation-driven discoveries are permitted. No new architectural layers, agent types, or conceptual components without implementation evidence.

### Phase 1 — Kernel Validation
Prove the Production Kernel can successfully execute:
```
Intent → Context Assembly → Agent Orchestrator → Planning Agent → Artifact → Evaluation → Approval
```
If this one flow works end-to-end, the architecture is validated.

### Phase 2 — Memory Validation
Demonstrate persistent creative context across sessions:
```
Session 1 → Memory Stored → Close App → Open Tomorrow → Project Continues
```
This is one of the hardest problems in AI applications and the most persuasive evidence for judges.

### Phase 3 — Artifact Validation
Show connected artifacts, not isolated outputs:
```
Release Plan → Content Calendar → Campaign → Execution Checklist
```
Every artifact references its predecessor. This demonstrates the Artifact Graph philosophy without requiring the full graph implementation.

### Phase 4 — Domain Pack Validation
Extract the Music domain into a formal Domain Pack:
```
packs/music/ (agents, schemas, templates, routing, validators, critics, panels)
```
Only after Music successfully operates as a pack should new domains (Film, etc.) be implemented. One validated pack proves the abstraction.

### Phase 5 — Production Engine
Only after the Kernel has survived real use: Story Architect, Continuity Director, Budget Director, Video Router. These should emerge from implementation needs, not architectural ambition.

### Phase 6 — Ecosystem
Marketplace, Production Cloud, Shared Packs, Community Templates, Third-party Agents. Platform concerns, not operating system concerns. Deferred until the OS is proven.

---

## 📓 Builder's Journal Template

After each day's work, copy this into `docs/journal/YYYY-MM-DD.md`:

```markdown
# Day N — YYYY-MM-DD

## What worked
-

## What broke
-

## Why I changed something
-

## What I learned
-

## Next focused step
-
```
