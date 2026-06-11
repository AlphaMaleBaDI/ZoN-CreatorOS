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
