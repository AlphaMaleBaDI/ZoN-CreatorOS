# CreatorOS Design Principles

These principles are the architectural laws of CreatorOS. Every decision — from sprint task selection to long-term architecture planning — is evaluated against them.

---

## 1. Context before Generation

Never generate before assembling context.

Most AI systems: `Prompt → LLM`

CreatorOS: `Workspace → Project → Profile → Memory → Knowledge Graph → Context Assembly → LLM`

The quality of the output is bounded by the quality of the context. Spending effort on context assembly returns more value than optimizing the model.

---

## 2. Artifacts over Conversations

The product is what the creator leaves with.

Conversations are ephemeral. Artifacts — launch plans, content calendars, roadmaps, reports, films, albums, games — are durable. CreatorOS optimizes for the artifact, not the chat.

This means:
- Every session should produce a reviewable deliverable
- Artifacts become part of the project's persistent state (see Artifact Graph)
- The dashboard centers on artifact review, not chat history

---

## 3. Memory before Repetition

Never ask the creator for information the system already knows.

If a creator has set their brand voice, preferred platforms, or long-term goals, every subsequent session should use that context without re-asking. If a character's appearance was defined in Scene 1, Scene 97 should reference the same identity package.

This is enforced by:
- Scoped memory hierarchy (`WorkspaceScope`, `ProjectScope`, `MemoryScope`)
- Creator Profile Engine
- Creative Asset Graph (CAG)
- Continuity Director Agent

---

## 4. Deterministic before Autonomous

Simple routing before dynamic planning.

```
if intent == "launch":  PlannerAgent()
elif intent == "research":  ResearchAgent()
```

Predictable flows are debuggable, testable, and explainable. Evolve to dynamic orchestration only after the deterministic path is proven in production.

This applies to:
- Agent routing (intent → agent mapping)
- Model selection (scene type → engine rules)
- Evaluation (critic chain before learned scoring)

---

## 5. Human Approval before Execution

CreatorOS proposes. The creator decides.

Every generation should be reviewable before it becomes final. The `dryRun` / `confirmApply` pattern ensures:
- The creator sees what will be generated
- The creator can modify or reject
- The system learns from the creator's choice

This is not a limitation. It is a trust-building mechanism.

---

## 6. Services Layer Discipline

Never allow `API → Database`. Always `API → Service → Memory → Database`.

The Services Layer decouples reasoning from storage. This makes the architecture:
- Testable (mock services, not databases)
- Portable (swap storage backends without changing agent logic)
- Observable (instrument the service boundary, not the database)

---

## 7. Domains Extend. The Kernel Remains Stable.

The Production Kernel — Context Assembly, Agent Lifecycle, PIE, CAG, Model Router, Artifact Pipeline, Evaluation Layer — does not change when a new domain is added.

Domain Packs (agents, schemas, templates, routing rules, validators, critics, panels) plug into the Kernel. This ensures that adding Music, Film, Games, or any future domain never requires rewriting core infrastructure.

---

## 8. Evaluate before Deliver

Every artifact passes through a feedback loop before reaching the creator.

```
Generate → Evaluate → Improve → Approve
```

Critics check planning quality, brand alignment, memory consistency, and domain-specific correctness. The Evaluation Layer catches errors the model would miss and provides an audit trail for every output.

---

## 9. Architect for the Ecosystem

Design every component as if it will be shared.

- Agents should be reusable across domains
- Artifact schemas should be composable into larger graphs
- Prompt templates should be publishable in a marketplace
- Model routing rules should be adjustable per workspace

This principle guides the transition from production platform to production ecosystem (Phase 5).

---

## 10. The North Star

Every decision answers one question:

> **Does this make the Creator's work easier?**

Not:
- Does it use more AI?
- Does it have more features?
- Does it look impressive?

CreatorOS is an operating system for creators. Not a chatbot. Not a demo. Not a feature collection. A system that transforms fragmented ideas, memories, and goals into production-ready artifacts through persistent context, intelligent orchestration, and domain-specific production engines.
