# ZoN CreatorOS - Sacred Demo Scenario

This document defines the single, official demo scenario for the ZoN CreatorOS submission. Every feature, module, and layer built during the hackathon sprint must directly support and refine this end-to-end user experience.

---

## 🎯 The Demo Goal
Deliver a structured release strategy and content plan for a music artist, proving that ZoN CreatorOS acts as an operating system layer that **remembers context**, **retrieves relevant knowledge**, **tracks Vibra shifts**, and **executes specialized agent planning** to generate concrete deliverables (artifacts).

---

## 🚀 The Sacred Demo Pipeline (High-Level)

This is the story the judge experiences. Every component exists to serve this flow:

```
Creator opens workspace
        ↓
Creator describes a goal
        ↓
Context Assembly builds understanding
        ↓
Agents collaborate
        ↓
Memory enriches the response
        ↓
Artifacts are generated
        ↓
Creator leaves with a concrete plan
```

---

## 🔄 Vertical Slice Architecture

Each phase builds one end-to-end vertical slice. Every slice crosses all layers of the stack:

```
Phase 1.2         Phase 1.3            Phase 1.4
─────────         ─────────            ─────────
UI                UI                   UI
│                 │                    │
API               API                  API
│                 │                    │
Context Assembly  Context Assembly     Context Assembly
│                 │                    │
Orchestrator      Orchestrator         Orchestrator
│                 │                    │
Planner Agent     Planner Agent        Planner Agent
│                 │                    │
Launch Plan       Content Calendar     Execution Report
│                 │                    │
Display Result    Display Result       Display Result
```

**Rule:** Never build a layer in isolation. Complete the vertical slice first, then add depth.

---

## 🚀 The Sacred User Flow

### 1. Inputs Upload
The creator uploads three items to their active workspace (e.g., the `AfroVBra` scope):
1. **Artist Notes / Audio Transcript:** Raw transcripts of their session explaining the song idea.
2. **Song Lyrics:** Raw lyrics of the track.
3. **Release Objective:** A text input (e.g., *"I want to launch my next Afrobeat EP in September with a focus on TikTok viral growth"*).

---

## 🔄 Under the Hood: The Processing Pipeline

```
[User Action: Upload Files]
       ↓
[Context Assembly Engine]
  ├── Loads Workspace ID & Scope (AfroVBra)
  ├── Pulls Creator Profile (Preferences, brand voice, past release style)
  └── Query FAISS/Graph (Past session memory & previous EP references)
       ↓
[Vibra State Engine]
  └── Analyzes creator's mood & active goals to compute current creative state (VibraShift)
       ↓
[Orchestrator Agent]
  ├── Determines required sub-tasks
  └── Delegates to Planner and Research Agents
       ↓
[Artifact Generator]
  └── Produces structured JSON-LD outputs
```

---

## 📦 The Deliverable Artifact
The user receives a single, high-fidelity JSON object parsed into the **Artifact Review Center** in the Dashboard:

1. **`release_strategy`:** Structured EP release timeline, marketing angles, and target audiences.
2. **`content_calendar`:** A concrete schedule showing content distribution milestones.
3. **`memory_references`:** Clickable source citations referencing past sessions or files that shaped this plan.
4. **`creative_state`:** The active Vibra state showing how their creative trajectory evolved across this session.
5. **`confidence_score`:** A system confidence metric representing context match fidelity.

---

## 🛠️ Verification Criteria
The demo is complete when:
- The user can run the pipeline with config-based switching between **local Ryzen AI NPU** (summarization, search) and **AMD Instinct Cloud GPUs** (heavy agent routing).
- The dashboard charts the creator's persistent Vibra history.
- Clickable citation links open raw memory nodes accurately.
