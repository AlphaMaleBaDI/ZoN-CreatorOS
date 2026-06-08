# ZoN CreatorOS - Strategy

## Vision

ZoN CreatorOS is an Adaptive Creator Intelligence Platform that
combines persistent memory, multimodal retrieval, adaptive intelligence,
and agentic workflows into a unified operating system for creators.

Rather than responding to isolated prompts, CreatorOS maintains
continuity across projects, understands creative state, retrieves
relevant knowledge, and generates actionable artifacts that help
creators transform ideas into executable reality.

Adaptive Intelligence is not sentiment analysis. It is a context-aware
interpretation layer that combines project memory, active goals,
creator interaction patterns, and conversational signals to guide
decision support and artifact generation.

## 1. Mission

ZoN CreatorOS is an AI Operating System for creators, builders, and
innovators. Unlike chat-only assistants, it combines persistent memory,
multimodal intelligence, adaptive workflows, project awareness, and AI
agents into a unified creative environment. Its job is to take a
creator from inspiration to a real, reviewable artifact - and to
remember the journey so the next session starts with context, not cold.

## 2. Positioning

ZoN CreatorOS is an **Adaptive Creator Intelligence Platform** - not
a chatbot, not a productivity tool, not a creative tool, not a
general AI operating system. It is the intelligence layer that creators
build workflows on top of.

Three framings hold simultaneously:

- **Creator domain** - the proving ground is real artist work, not
  toy benchmarks.
- **Infrastructure narrative** - AMD, NVIDIA, and platform sponsors
  think in layers. CreatorOS claims the layer.
- **Agent narrative** - the system observes, plans, executes, and
  confirms. It is a workforce, not an assistant.

## 3. Components

| Layer                | Status             | Source / Plan                                 |
|----------------------|--------------------|-----------------------------------------------|
| Core                 | Reused from `zon_mcp` | Orchestration, prompt processing, FastAPI app |
| Memory               | Reused from `zon_mcp` | Scopes, FAISS, multimodal recall             |
| Adaptive Intelligence| Reused + extended     | Vibra state engine, context-aware, persisted  |
| Workspace            | New                   | Project scopes, context objects, asset model |
| Agents               | New                   | Tool-calling agent framework with confirmations |
| Dashboard            | New                   | Memory + Vibra + artifact UI                  |
| Benchmarks           | New                   | MI300X inference numbers for AMD submission   |

## 4. The Stack

```
Layer 6  Dashboard         visualize: memory, state, projects, agents
Layer 5  Agents            observe, plan, execute, confirm, learn
Layer 4  Workspace         projects, goals, milestones, knowledge, artifacts
Layer 3  Adaptive Intel    context-aware interpretation, VibraShift
Layer 2  Memory            scoped topics + FAISS + multimodal recall
Layer 1  Core              reason, plan, generate, respond
```

## 5. Showcase

AfroVBra AI Studio - a creator-facing surface built on ZoN CreatorOS.
Demonstrates a real artist workflow: upload song + lyrics + goal,
receive a single reviewable artifact (release plan, marketing angles,
next actions) grounded in persistent memory and Vibra state.

## 6. AMD Hook

CreatorOS runs locally; hot-path inference (multimodal embeddings,
retrieval, chat, release-plan generation) is benchmarked on AMD
Instinct MI300X via AMD Cloud credits. CreatorOS exposes multiple
distinct workloads:

- **Memory retrieval** - FAISS semantic + topic recall
- **Visual retrieval** - CLIP text-to-image
- **Agent planning** - LLM inference
- **Multimodal processing** - text + image + structured artifacts
- **Benchmarking** - latency and throughput on MI300X

That is a stronger AMD story than "here is my chatbot." It is an
inference-platform story.

## 7. Killer Demo

The artifact, not the chat. Artist uploads three things; CreatorOS
returns one JSON object with audience profile, release strategy,
marketing angles, next actions, Vibra state, and clickable memory
references. Judges see a co-pilot producing work, not a chatbot.

```
Song + Mood References + Release Objective
        |
        v
Memory Retrieval + Adaptive Intelligence + Project Context
        |
        v
Structured Artifact (the product)
```

The artifact contains:

- `release_strategy`
- `marketing_angles`
- `audience_analysis`
- `next_actions` (each with a `why` that cites a memory entry)
- `memory_references`
- `creative_state` (Vibra)

## 8. Success Criteria

### Creator Workflow

1. Upload song
2. Upload mood references
3. Enter release objective
4. Receive structured release strategy
5. View memory references used
6. View Vibra state analysis
7. Save results into project memory
8. Continue project across sessions

### Platform Workflow

9. Switch between local and AMD Cloud inference through configuration
   only - no code change required
10. Display Vibra history visualization for the active project scope

If all 10 are satisfied, ZoN CreatorOS MVP is complete.

## 9. Adaptive Intelligence - Elevation of Vibra

`mood_bridge.py` from `zon_mcp` becomes the Adaptive Intelligence
Engine in CreatorOS. Three concrete changes:

- **Context-sensitive computation.** Vibra is computed from
  `user_prompt + system_state + memory_snapshot + agent_plan`, not
  just keywords in the user message.
- **First-class persistence.** Vibra is stored alongside topics in
  `memory_engine`, with a `vibra_history` array per scope. The
  dashboard can chart it; the agent can condition on it.
- **Single API surface.** `intelligence.adapt(context) -> VibraShift`
  is the only entry point. The chat path, the agent layer, and the
  dashboard all consume it. Nobody calls the underlying detector
  directly.

This is what turns Vibra from a feature into a system.

## 10. Hackathon Build Plan

Day-by-day targets:

- Day 1: Repo bootstrap, `FOUNDATIONS.md`, Core/Memory seeding,
  canonical FastAPI app, smoke test against the OpenRouter router.
- Day 2: Workspace (project scopes, asset model), Intelligence cleanup
  (single source of truth for active model), Vibra API endpoint.
- Day 3: Agents framework - one working tool-calling agent using
  `dryRun` / `confirmApply` from the existing `PromptRequest` schema.
- Day 4: Dashboard - Streamlit app over the API with a Vibra meter
  and Vibra history chart.
- Day 5: AfroVBra AI Studio surface - the artist workflow that
  produces the artifact.
- Day 6: MI300X benchmarks for embedding + retrieval + chat hot paths.
- Day 7: Polish, README, demo video, submission form.

## 11. Module Migration Order

When the strategy is approved, modules migrate from `zon_mcp` in this
order:

1. `schemas.py` - everything imports it
2. `memory_engine.py` - nothing works without it
3. `memory_vector.py` - retrieval layer
4. `mood_bridge.py` -> `intelligence/vibra.py` - elevated, not copied
5. `core_utils.py` - orchestration
6. `flex_model.py` - routing (consolidated)
7. `api/memory_routes.py` - HTTP surface

Nothing else migrates. The three duplicate CLIs, the second FastAPI
app, and the VS Code extension stay in AfroVBra. They are tooling, not
platform.

## 12. Eligibility & Lineage

See `FOUNDATIONS.md`. Architectures and ideas are inherited from the
AfroVBra project''s `zon_mcp` module. The code in this repository was
written for the AMD hackathon.
