# ZoN CreatorOS Sprint Build Rules

These build rules serve as the project constitution during the execution phase starting July 6. They prevent architectural drift and ensure focus on the core hackathon deliverables.

## Core Rules

1. **No Architecture Changes During Sprint**
   The architecture layer boundaries, namespace structure, and component boundaries frozen in the preseason are final.
2. **No New Features Unless They Support [DEMO_SCENARIO.md](file:///d:/my%20programming/ZoN-CreatorOS/docs/DEMO_SCENARIO.md)**
   Avoid scope creep. Every new code path or utility must directly support the primary demo pathway (Launch Plan, Calendar, Report generation).
3. **Every Module Requires Tests**
   No component is complete without corresponding unit tests verifying its interfaces. Keep tests green.
4. **Every Memory Query Must Respect WorkspaceScope**
   Queries to vector databases, graph storage, or profiles must accept and enforce the correct workspace boundary (e.g., `WorkspaceScope`, `ProjectScope`, `MemoryScope`) defined in `core/schemas.py`.
5. **Context Assembly Must Execute Before Agents**
   Context collection (profile + memories + Vibra mood history) must happen deterministically inside the Context Assembly Engine prior to routing to orchestrator/agents.
6. **No AMD Cloud Credits Used for Experimentation**
   Do not run speculative experiments or heavy scratch workloads on the AMD Instinct GPU resources.
7. **Credits Only Used for Sprint Deliverables**
   Reserve AMD Instinct Cloud compute strictly for running final agent logic, deep reasoning tasks, and executing/validating the primary demo flow.
