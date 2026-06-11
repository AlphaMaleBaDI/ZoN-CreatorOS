# ZoN CreatorOS

An **Adaptive Creator Operating System** designed as the intelligence layer for creative workspaces. 

Unlike traditional chat-only assistants, ZoN CreatorOS combines persistent scoped memories, active creator style profiles, and unified multi-agent orchestrations to translate scattered creator logs directly into structured plans, timelines, and calendars.

---

## 🚀 The Product Vision
* **Context over Prompts:** Instead of starting every session cold, CreatorOS aggregates project scopes, user style vectors, and past vector histories before running reasoning cycles.
* **Separation of Behavior & Storage:** By introducing a dedicated **Services Layer** (`profile`, `memory`, `artifact`, `workspace` services), reasoning agents remain decoupled from underlying database states (FAISS/Knowledge Graphs).

---

## 🏗️ Layered Architecture Layout

```text
ZoN CreatorOS
│
├── Experience Layer
│   ├── Creator Dashboard (Streamlit UI)
│   ├── Workspace Studio (Project dashboard)
│   ├── Memory Explorer (FAISS search & graph visualizer)
│   ├── Workflow Builder (Interactive tasks/goals)
│   └── Artifact Review Center (Structured deliverables view)
│
├── Application Layer
│   ├── API Gateway (FastAPI)
│   ├── Context Assembly Engine (State + profile + memory assembly)
│   ├── Session Manager (Cross-session context retention)
│   └── Security Layer (Local NPU data boundary)
│
├── Intelligence Layer (LangGraph Agents)
│   ├── Orchestrator Agent (Task coordinator)
│   ├── Research Agent (Memory & web lookup)
│   ├── Planning Agent (Timeline & milestone generation)
│   ├── Memory Agent (Knowledge graph consolidation)
│   └── Workflow Agent (Action execution helper)
│
├── Artifacts Layer (Output Deliverables)
│   ├── Launch Plans (Release strategies & timelines)
│   ├── Marketing Campaigns (Angles & copy draft templates)
│   ├── Content Calendars (Multi-channel posting schedules)
│   ├── Project Roadmaps (Milestones & requirements)
│   └── Execution Reports (Session outcomes & citation maps)
│
├── Memory Layer
│   ├── FAISS Vector Store (Raw semantic storage)
│   ├── Knowledge Graph (Linked metadata JSON-LD)
│   ├── Project Memory (Scoped via Workspace ID, Project ID, and Memory Scope)
│   ├── Creator Profile Engine (Style, brand voice, preferences, long-term goals)
│   └── Vibra State Engine (Adaptive creative state tracker)
│
├── Services Layer (Business Logic Glue)
│   ├── Profile Service (Identity configuration & retrieval)
│   ├── Memory Service (Vector/graph orchestration)
│   ├── Artifact Service (JSON payload save/load operations)
│   └── Workspace Service (Isolated scope creator)
│
├── Compute Layer
│   ├── Local Ryzen AI NPU (On-device ONNX/PyTorch runs)
│   ├── AMD Instinct GPUs (Cloud-based cluster inference)
│   ├── Prefill Pool (Optimized for context processing)
│   └── Decode Pool (Optimized for token generation)
│
└── Infrastructure Layer
    ├── FastAPI (API framework)
    ├── LangGraph (Agent state orchestration)
    ├── LangChain (LLM wrappers & utilities)
    ├── vLLM / SGLang (AMD-optimized serving engines)
    └── ROCm 7 / "The Rock" (GPU compute stack)
```

---

## 🎯 The Sacred Demo Scenario
The platform is built to validate a single, high-fidelity demo pipeline:
1. **Inputs:** Artist uploads voice notes, raw lyrics, and a release goal.
2. **Aggregations:** The **Context Assembly Engine** combines these with the active **Creator Profile** (writing styles, goals) and retrieves relevant historical vectors.
3. **Execution:** The **Orchestrator Agent** assigns tasks to routing blocks.
4. **Outputs:** A structured release strategy, content calendar, reference citations, Vibra state tracking visual, and a system `confidence_score`.

---

## ⚡ AMD Hardware Strategy
* **Local Ryzen AI NPU Offloading:** Local notes summarization and vector indexing are handled locally on-device, preserving privacy and saving cloud API costs.
* **Cloud Instinct GPU Prefill/Decode:** Large planning routines are run on AMD Instinct Cloud GPUs using vLLM/SGLang with a disaggregated prefill/decode pipeline architecture to reduce token generation overhead by 10x-30x.

---

## 🧪 Quick Start & Verification
To verify the environment, make sure Python 3.12 is active and run:
```bash
# Setup virtual environment and dependencies
.venv\Scripts\pip install -r requirements-foundation.txt
.venv\Scripts\pip install -r requirements-dev.txt

# Run verification test suites
.venv\Scripts\python -m pytest
```
All system milestones and design specifications are logged in `docs/` and tracked in our task files.
