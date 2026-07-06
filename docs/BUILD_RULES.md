# ZoN CreatorOS Sprint Build Rules

These build rules serve as the project constitution during the execution phase starting July 6. They prevent architectural drift and ensure focus on the core hackathon deliverables.

## Core Rules

1. **Protect the North Star**
   Every decision answers: *Does this make the Creator's work easier?* CreatorOS is an operating system for creators, not a chatbot. Never lose that identity.

2. **No Architecture Changes During Sprint**
   The architecture layer boundaries, namespace structure, and component boundaries frozen in the preseason are final. Do not redesign — not on Day 1, not on Day 2, not because someone on Discord suggests it.

3. **Demo-First Feature Gate**
   No new feature is allowed unless it directly supports the Sacred Demo Pipeline defined in `DEMO_SCENARIO.md`. If a feature doesn't improve the story of creator → artifact, it can wait.

4. **Build Vertical Slices, Not Horizontal Layers**
   Complete one end-to-end flow per phase (UI → API → Context Assembly → Orchestrator → Agent → Artifact → Display). A working system beats five unfinished components.

5. **Agent Determinism First**
   Use simple intent routing before dynamic orchestration (`if intent == "launch": PlannerAgent()`). Predictable, debuggable, testable. Evolve only after the deterministic path is proven.

6. **Every Module Requires Tests**
   No component is complete without corresponding unit tests verifying its interfaces. Keep tests green.

7. **Every Memory Query Must Respect WorkspaceScope**
   Queries to vector databases, graph storage, or profiles must accept and enforce the correct workspace boundary (e.g., `WorkspaceScope`, `ProjectScope`, `MemoryScope`) defined in `core/schemas.py`.

8. **Context Assembly Must Execute Before Agents**
   Context collection (profile + memories + Vibra mood history) must happen deterministically inside the Context Assembly Engine prior to routing to orchestrator/agents.

9. **Services Layer Discipline**
   Never allow `API → Database`. Always `API → Service → Memory → Database`. This decoupling is what makes the architecture testable and portable.

10. **No AMD Cloud Credits Used for Experimentation**
    Do not run speculative experiments or heavy scratch workloads on the AMD Instinct GPU resources.

11. **Credits Only Used for Sprint Deliverables**
    Reserve AMD Instinct Cloud compute strictly for running final agent logic, deep reasoning tasks, and executing/validating the primary demo flow.
