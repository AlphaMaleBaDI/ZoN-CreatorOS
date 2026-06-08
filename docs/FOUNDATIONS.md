# Foundations & Lineage

ZoN CreatorOS is a fresh repository. It contains no prior commit history
and is intended to be evaluated as new work for the AMD AI Developer
Hackathon.

Architectural ideas and several subsystem designs - including the
memory engine, the model router, the Vibra state model, and the
FastAPI service layout - were prototyped in the AfroVBra project''s
`zon_mcp` module, a sibling repository maintained by the same author.
The relevant AfroVBra module is referenced here for transparency and
reviewer convenience.

The code in this repository was written for this hackathon. Patterns
and designs are re-implemented to fit CreatorOS''s goals, the Adaptive
Creator Intelligence Platform positioning, and the AMD submission
requirements.

## What is reused (designs only)

- Memory: scoped topic storage with semantic + multimodal recall
- Routing: multi-source model abstraction (OpenAI, OpenRouter, local)
- Vibra: a six-state creative-state model with color and name metadata
- Service layout: FastAPI app with CORS, router mounts, and a memory
  API surface

## What is new in CreatorOS

- **Adaptive Intelligence layer** - Vibra becomes a context-aware
  interpretation engine with a single `adapt(context) -> VibraShift`
  API, first-class persistence, and per-scope history.
- **Workspace layer** - project scopes, goals, milestones, knowledge,
  and artifacts as first-class objects.
- **Agents layer** - a tool-calling agent framework with `dryRun` and
  `confirmApply` confirmation flow.
- **Dashboard** - a Streamlit surface for memory, Vibra (current and
  history), projects, and artifacts.
- **AMD MI300X benchmarks** - latency and throughput numbers for the
  hot paths, run on AMD Cloud credits.

## Mapping (for reviewer convenience)

| CreatorOS path        | Lineage in `zon_mcp`                          |
|-----------------------|------------------------------------------------|
| `core/`               | `zon_mcp/zon_core.py`, `schemas.py`            |
| `memory/`             | `zon_mcp/memory_engine.py`, `memory_vector.py` |
| `intelligence/vibra.py` | `zon_mcp/mood_bridge.py` (elevated)          |
| `intelligence/router.py` | `zon_mcp/flex_model.py`, `utils/model_registry.py` |
| `api/`                | `zon_mcp/api/memory_routes.py`                 |
| `agents/`             | new                                            |
| `workspace/`          | new                                            |
| `dashboard/`          | new                                            |
| `benchmarks/`         | new                                            |

Reviewers wishing to trace the lineage can inspect `zon_mcp` in the
AfroVBra project. No code is copied verbatim; patterns and designs
are re-implemented to fit CreatorOS''s positioning and goals.
