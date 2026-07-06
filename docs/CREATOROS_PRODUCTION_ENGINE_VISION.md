# CreatorOS Production Engine Vision

This document defines the long-term architecture beyond the hackathon MVP. It maps multi-model orchestration (validated by *Computer Village* by Ogini Studios) onto the existing CreatorOS architecture, widening from film to a general **Creative Production Engine** supporting any creative domain.

**Key insight validated by research:** The innovation in modern AI production is not in any single model — it is in the orchestration layer connecting specialized models. That orchestration is exactly what CreatorOS is designed to provide.

Design principles guiding this architecture are codified in `docs/PRINCIPLES.md`.

---

## 1. The Production Pipeline (Current State of Art)

*Computer Village* was produced using a multi-tool orchestration pipeline:

```
Story & Script ──► ChatGPT
                        │
            Character Design ──► NanoBanana Pro
                        │
        ┌───────────────┼───────────────┐
  Google Veo 3     Kling AI 3.0    Kling AI 2.6
  (cinematic,     (action,        (character
   establishing,   locomotion,     animation,
   drone shots)    dialogue)       secondary)
                        │
                  Voices ──► ElevenLabs
                        │
                   Music ──► Suno AI
                        │
              Editing ──► DaVinci Resolve
                        │
                   Final Film
```

This pipeline is a *specialization* of a general pattern. Replace the video engines with music generators or game engines, and the orchestration problem is identical.

---

## 2. Architecture: The Production Kernel

The architecture centers on a **Production Kernel** — the stable core that owns all production orchestration. Everything else is a plugin.

```
                         CreatorOS
                              │
              ┌────────────────┼────────────────┐
              │                │                │
        Agent Orchestrator  Memory System  Production Kernel
                                              │
                      ┌───────────────────────┼───────────────────────┐
                      │                       │                       │
              Context Assembly          PIE (Production        Creative Asset
                                        Intelligence            Graph (CAG)
                                        Engine)
                      │                       │                       │
                      └───────────────────────┼───────────────────────┘
                                              │
                              ┌───────────────┴───────────────┐
                              │                               │
                        Model Router                   Evaluation Layer
                        Compute Director               (Critics + Feedback)
                        Continuity Director
                              │
                              │
                    ┌─────────┴─────────┐
                    │                   │
              Artifact Pipeline   Export Pipeline
                              │
                  ┌───────────┼───────────┐
                  │           │           │
            Domain Pack   Domain Pack  Domain Pack
              Music        Film        Games
```

The kernel owns:
- Context Assembly
- Agent Lifecycle
- Production Intelligence Engine (PIE)
- Creative Asset Graph (CAG)
- Model Router
- Artifact Pipeline
- Evaluation Layer

Domain Packs plug into the kernel. The kernel remains stable while packs evolve.

---

## 3. Creative Asset Graph (CAG)

The CAG elevates CreatorOS from "prompt + memory" to true creative reasoning. It is a labeled property graph of every creative object and its relationships.

### Music Domain Example

```
Song
├── belongs_to ──► Album
├── written_by ──► Artist
├── has_theme ──► VisualTheme
├── appears_in ──► MusicVideo
├── promoted_by ──► MarketingCampaign
│   ├── includes ──► SocialPosts
│   └── includes ──► Merchandise
└── inspires ──► FanArt
```

### Film Domain Example

```
Character
├── owns ──► Voice
├── appears_in ──► Scene
│   └── belongs_to ──► Episode
│       └── belongs_to ──► Season
│           └── belongs_to ──► Franchise
├── wears ──► Wardrobe
├── has_emotion ──► EmotionalArc
└── relates_to ──► Character (relationship)
```

### Why CAG Is Not Just Memory

| Feature | Current Memory Layer | CAG |
|---|---|---|
| Storage | Vector embeddings + JSON-LD | Labeled property graph |
| Queries | Similarity search | Traversal + filter + join |
| Relationships | Implicit (tags) | Explicit (typed edges) |
| Consistency | Best-effort | Enforced by graph constraints |
| Impact analysis | Manual | Automated cascade |

**Example — cascade from a single change:**

> "Ada appears sad."

The CAG immediately surfaces what this affects:
- Facial expression in all active scenes
- Dialogue tone for current episode
- Music BPM and key for the scene
- Camera lighting temperature
- Continuity with previous emotional state
- Wardrobe color palette (if grieving)

Without CAG, each of these requires a separate prompt. With CAG, they are automatic traversals.

### Implementation Strategy

The CAG sits **above** the existing memory stack:

```
Knowledge Graph (JSON-LD) ──► CAG (Property Graph)
        │                              │
   Lightweight,                  Rich relationships,
   schema-less                   typed edges,
   good for retrieval            good for reasoning
```

- Phase 1 (MVP): Use existing `KnowledgeGraph` in `memory/knowledge_graph.py` with tagged edges
- Phase 2: Add typed relationship schemas and traversal queries
- Phase 3: Full property graph with automated cascade resolution

---

## 4. Production Intelligence Engine (PIE)

An explicit decision-making layer within the Kernel. PIE evaluates production choices and recommends:
- Which model to use for this task
- Whether existing assets can be reused
- Expected quality and estimated cost
- Anticipated runtime and parallelization feasibility
- Where human review adds most value

PIE is **not** a general AI reasoning engine. It is a specialized production planner that understands creative workflows, compute costs, and quality trade-offs.

---

## 5. The Artifact Graph

Artifacts are not terminal outputs. They are **persistent state** that feeds the next artifact in the graph.

```
Intent
  │
  ▼
Release Plan ──► Marketing Campaign ──► Calendar ──► Video Script ──► Storyboard ──► Thumbnail ──► Published Content
```

Each artifact is a node in the Artifact Graph. The system does not generate in isolation — it builds on previous artifacts, tracks provenance, and surfaces the chain of decisions that produced each output.

This replaces the "prompt → output" model with an "intent → artifact graph" model.

---

## 6. Evaluation Layer

Every generation passes through a feedback loop:

```
Generate
   │
   ▼
Evaluate ──► Improve ──► Approve
```

Instead of:

```
LLM → Done
```

CreatorOS evaluates its own work through specialized critics:

```
Release Plan
   │
   ▼
Planning Critic
   │
   ▼
Marketing Critic
   │
   ▼
Brand Critic
   │
   ▼
Memory Consistency Check
   │
   ▼
Final Artifact
```

Each critic:
- Checks a specific dimension of quality
- Assigns a score or pass/fail
- Optionally generates improvement suggestions
- Passes to the next critic or back for revision

The Evaluation Layer is part of the Production Kernel. Domain Packs register their own critics.

---

## 7. Domain Packs

Domains are not hardcoded modules. They are **Production Packs** that plug into the Kernel.

Each pack supplies:

| Component | Purpose |
|---|---|
| Agents | Domain-specific agent implementations |
| Artifact Schemas | Pydantic models for domain outputs |
| Prompt Templates | Reusable prompt library for the domain |
| Model Routing Rules | Which engines handle which tasks |
| Validators | Domain-specific output validation |
| Critics | Evaluation layer checkers for the domain |
| Dashboard Panels | Streamlit panels for the domain |

Example pack structure:

```
packs/
├── music/
│   ├── agents/
│   ├── schemas/
│   ├── templates/
│   ├── routing.py
│   ├── validators.py
│   ├── critics.py
│   └── dashboard.py
├── film/
│   ├── agents/
│   ├── schemas/
│   ├── templates/
│   ├── routing.py
│   ├── validators.py
│   ├── critics.py
│   └── dashboard.py
└── podcast/
    └── ...
```

The Kernel loads whichever packs are enabled for a workspace. This makes CreatorOS extensible without architectural changes.

---

## 8. New Agent Types

### Story Architect Agent
- Generates screenplay, story arcs, scene breakdowns
- Estimates runtime and pacing
- Produces: script, scene list, character arcs

### Casting Agent
- Creates character identity packages
- Generates front/side/back views, expressions, wardrobe
- Produces: character bible, reference images, identity embeddings

### Scene Director Agent
- Converts screenplay scenes into structured production data
- Specifies camera, lighting, mood, location per scene
- Produces: shot list, camera script, storyboard prompts

### Video Engine Router
- Routes each scene to optimal video model by scene type
- Dialogue → Veo, Action → Kling, Stylized → Runway/Hailuo
- Manages prompt templates per engine

### Voice Director Agent
- Manages dialogue and emotional delivery
- Routes to ElevenLabs or equivalent TTS
- Handles multilingual speech and lip-sync alignment

### Music Composer Agent
- Generates adaptive score per scene mood
- Routes to Suno AI or equivalent
- Manages soundtrack metadata (BPM, key, mood tags)

### Editor Agent
- Assembles scenes into sequence
- Adds transitions, subtitles, color grading
- Exports final film with multiple format options

### Continuity Director Agent
- Prevents continuity errors before generation
- Tracks wardrobe, props, weather, emotional arcs, relationships, lore
- Cross-references every new generation against the Creative Asset Graph
- Flags inconsistencies before compute is wasted

### Budget & Compute Director Agent
- Estimates compute cost per generation decision
- Recommends cheaper alternatives when quality loss is negligible
- Example reasoning:
  ```
  This dialogue scene does not require Veo.
  Kling is sufficient.
  Estimated savings: $4.72
  No noticeable quality loss.
  ```

---

## 9. New Artifact Types

| Artifact | Schema | Purpose |
|---|---|---|
| `Script` | scenes, acts, dialogue, action lines | Screenplay for any narrative work |
| `CharacterBible` | character_id, name, appearance, personality, wardrobe, expressions, relationships | Canonical character identity |
| `Storyboard` | scene_id, shot_number, camera_angle, composition_prompt, engine | Visual plan per shot |
| `ShotList` | scene_id, shots[], preferred_engine, prompt_template, cost_estimate | Production-ready shot instructions |
| `FilmRender` | asset_id, format, duration, resolution, codec | Final film output |
| `Soundtrack` | track_id, BPM, mood, duration, scenes_used[], key, instrumentation | Generated music metadata |
| `Campaign` | channels[], assets[], timeline, budget, kpis | Multi-channel marketing campaign |
| `AssetPack` | asset_ids[], category, license, tags | Reusable character/location/prop collection |

---

## 10. Evolution Path: Validation-Focused Execution

The architecture is frozen at the current abstraction level (ADR-008). Every subsequent phase is a **validation gate** — prove the current architecture works before expanding it.

### Phase 0 — Architecture Freeze (Current)
The architecture at the abstraction level defined in ADR-001 through ADR-007 is final. Only three changes permitted:
- Bug fixes
- Documentation clarifications
- Implementation-driven discoveries (a pattern appears 3x before extracting it)
- No new layers, agent types, or conceptual components without implementation evidence.

### Phase 1 — Hackathon MVP
**Validation:** Kernel works end-to-end on one domain.
**Focus:** Music artist release plan pipeline.
```
Intent → Context Assembly → Agent Orchestrator → Planning Agent → Artifact → Evaluation → Approval
```
- Single domain (Music), minimal Kernel
- Delivers: Launch Plan artifact with memory citations and Vibra state
- If this works, the architecture is validated.

### Phase 2 — Memory Validation
**Validation:** Persistent creative context survives session boundaries.
```
Session 1 → Memory Stored → Close App → Open Tomorrow → Project Continues
```
- The creator returns to find their workspace, profile, project state, and vibra history intact
- The system does not re-ask for information it already knows

### Phase 3 — Artifact Validation
**Validation:** Artifacts are connected, not isolated.
```
Release Plan → Content Calendar → Campaign → Execution Checklist
```
- Each artifact references its predecessor
- Modifying one artifact surfaces affected downstream artifacts
- Demonstrates Artifact Graph philosophy without requiring full graph implementation

### Phase 4 — Domain Pack Validation
**Validation:** The plugin architecture is correct.
- Extract the Music domain into a formal Domain Pack (`packs/music/`)
- One validated pack proves the abstraction
- Only then implement the Film pack

### Phase 5 — Production Engine (Implementation-Driven)
**Validation:** Production agents emerge from real needs.
- Story Architect, Continuity Director, Budget & Compute Director, Video Router
- These must be driven by implementation necessity, not architectural ambition
- Evaluation Layer with specialized critics

### Phase 6 — Multi-Domain Production
**Domains:** Games, Podcast, Publishing, Animation, Education
**Focus:** Domain expansion without Kernel changes.
- New domains = new Domain Packs only
- All share: Kernel, CAG, PIE, ModelRouter, Evaluation Layer

### Phase 7 — Production Ecosystem
**Focus:** Platform beyond production.
- **CreatorOS Production Cloud:** Managed rendering, shared compute pool
- **CreatorOS Marketplace:** Characters, camera packs, styles, lighting presets, prompt templates, orchestration workflows, voice profiles, Domain Packs
- **CreatorOS Network:** Cross-creator collaboration, version control, review workflows, shared continuity across projects

---

## 11. Architecture Integrity

### No Structural Changes Needed

The Production Engine does not require structural changes to the existing 7-layer architecture. Every agent is an `intelligence` module consuming the same `ContextObject`, respecting the same `WorkspaceScope`, and producing `Artifact` subclasses. Domain Packs extend horizontally, not vertically.

### ModelRouter Expansion

`intelligence/router.py` is the critical expansion point. It currently stubs local-NPU-vs-cloud routing but is designed for rule-based engine selection:

```
if scene.type == "dialogue":
    engine = "veo"
elif scene.type == "action":
    engine = "kling"
elif scene.type == "stylized":
    engine = "runway"
```

This follows Principle #4 from `docs/PRINCIPLES.md` — deterministic before autonomous.

---

## 12. AMD Advantage

This pipeline aligns strongly with AMD's hardware narrative:
- **Local Ryzen AI NPU:** Character identity embedding (CLIP), prompt preprocessing, scene metadata management, CAG traversal queries
- **AMD Instinct Cloud GPU:** Heavy video generation inference (vLLM/SGLang), multi-scene rendering
- **ROCm 7 GPU-to-GPU:** Distributed rendering of multiple scenes in parallel
- **MAX Engine heterogeneous routing:** Route different scene types to different GPU configurations

---

## 13. Reference

- *Computer Village: Season 1* by Ogini Studios — https://youtu.be/4ACCORO1JDE
- Production stack: Google Veo 3, Kling AI 3.0/2.6, NanoBanana Pro, ElevenLabs, Suno AI, DaVinci Resolve, ChatGPT
- Higgsfield contest submission: https://higgsfield.ai/contests/make-your-action-scene/submissions/c64ac92e-ba3f-4760-9786-5fa8680bfed9
- CreatorOS Design Principles: `docs/PRINCIPLES.md`
