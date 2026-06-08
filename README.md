# ZoN CreatorOS

An **Adaptive Creator Intelligence Platform**.

Not a chatbot. Not a productivity tool. Not a creative tool. Not a
general AI operating system. CreatorOS is the intelligence layer that
creators build workflows on top of.

## Status

Repository bootstrap only. Strategy, foundations, and the killer demo
are documented under `docs/`. No implementation code has been written
yet.

## Read first

- `docs/STRATEGY.md` - vision, positioning, stack, success criteria,
  elevation of Vibra, build plan, module migration order
- `docs/FOUNDATIONS.md` - lineage, what is reused, what is new
- `docs/DEMO.md` - the artifact-producing killer demo

## Layout

- `core/` - orchestration, prompt processing, API service
- `memory/` - scoped memory, FAISS, multimodal recall
- `intelligence/` - Adaptive Intelligence (Vibra engine) and model router
- `workspace/` - project scopes, context objects, asset model
- `agents/` - tool-calling agent framework with confirmations
- `api/` - FastAPI surface
- `dashboard/` - Streamlit surface for memory, Vibra, and artifacts
- `benchmarks/` - MI300X inference numbers for the AMD submission

## Quick start

Read `docs/STRATEGY.md` section 8 (Success Criteria) and section 10
(Build Plan) first. They define what "done" looks like and the order
in which we build it.
