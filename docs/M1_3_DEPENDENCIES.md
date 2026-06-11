# M1.3 Dependencies Manifest (Foundation vs AI Stack)

## Why the dependency split exists

CreatorOS is being built in “foundation-first” milestones:

- **Foundation layer** must be importable and runnable with a minimal dependency set.
- **AI / ML stack** is optional and used only when you enable higher-cost features (vector search, CLIP multimodal search, embeddings, FAISS indexing, etc.).

Keeping these stacks isolated prevents ML-heavy packages from breaking core API/schema/model bootstrapping.

## Target Python

- **Python 3.12**
- Minimum-version pins only (`>=`)
- No exact version locks

## `requirements-foundation.txt` — Foundation-only dependencies

### Used by (current extracted modules)
- `core/orchestration.py`
  - `python-dotenv` (`load_dotenv`)
  - `openai` (`OpenAI`)
  - `fastapi` is not used directly here, but is required by `api/memory_routes.py`
- `api/memory_routes.py`
  - `fastapi` (`APIRouter`, `HTTPException`, `Query`)
  - `pydantic` (`BaseModel`)
- `core/schemas.py`
  - `pydantic` (schema base models)
- `memory/memory_engine.py`
  - stdlib only (no external deps)
- `intelligence/router.py`
  - `python-dotenv` (`load_dotenv`)
  - `openai` (`OpenAI`)
- `intelligence/vibra.py`
  - stdlib only

### Why this file intentionally excludes deployment/runtime servers
- **No `uvicorn`** included because:
  - it is a deployment/server concern
  - it is not required for import validation of the foundation modules

## `requirements-ai.txt` — Optional AI / ML dependencies

### Used by
- `memory/memory_vector.py`
  - `numpy`
  - `torch`
  - `transformers` (CLIPProcessor / CLIPModel)
  - `langchain-community` (FAISS + HuggingFaceEmbeddings)
  - `faiss-cpu`
  - `pillow` (PIL Image loader)
  - (sentence-transformers is required for embedding model compatibility)

### Why this file is isolated from the foundation layer
- The AI stack includes large and GPU/CPU-sensitive packages.
- A failure in the ML toolchain should not make:
  - `core/` imports fail
  - FastAPI routes/schema imports fail
  - memory JSON engine features unusable

## Future plan for AMD GPU integration (timeline note)
- Later milestones will experiment with:
  - GPU-accelerated inference paths
  - alternative embedding backends
  - FAISS/CLIP optimizations for AMD environments
- These experiments should remain confined to the **AI stack manifest** so the foundation stays stable.
