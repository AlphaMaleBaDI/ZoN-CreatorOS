# ZoN CreatorOS Risk Register

This document tracks identified technical and execution risks, their impact, and mitigation strategies.

| Risk ID | Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **RSK-001** | AMD Instinct Cloud credits expire or fail to activate | **High** | Delay cloud activation; ensure local cpu/gpu fallback configuration is operational inside `compute/`. |
| **RSK-002** | LangGraph instability or orchestrator routing loop | **Medium** | Use deterministic routing inside `orchestrator_agent.py` before moving to complex agentic graphs. |
| **RSK-003** | Large model latency / timeouts on Local AI NPU | **Medium** | Route low-level/semantic lookups to lightweight models on local Ollama, and reserve cloud for heavy reasoning. |
| **RSK-004** | Sprint scope creep (running out of time) | **Critical** | Strictly follow [DEMO_SCENARIO.md](file:///d:/my%20programming/ZoN-CreatorOS/docs/DEMO_SCENARIO.md) and implement only components marked in the sprint checklist. |
| **RSK-005** | API schema updates break core schema bindings | **High** | Rely on Pydantic schemas in `core/schemas.py` to decouple outer API logic from core services. |
| **RSK-006** | Local workspace state sync issues | **Medium** | Keep workspaces isolated by folder directories, using absolute paths linked to specific WorkspaceScopes. |
