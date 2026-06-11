# M1.4-B — Lazy Import Refactor (core/orchestration)

## Purpose
Remove the **import-time AI/ML dependency chain** caused by `core/orchestration.py` importing `memory.memory_vector` at module load time.

This keeps CreatorOS **Foundation** imports isolated until `process_prompt()` actually needs vector/visual memory.

---

## Before (import-time dependency)
### Before import location (module level)
In `core/orchestration.py`, the following import existed at the top level:

```python
from memory.memory_vector import query_memory, query_visual_memory
```

### Impact
When Python evaluates `from core.orchestration import *`, it imports the module, which imports `memory.memory_vector` immediately, which in turn imports AI/ML dependencies (e.g., `numpy`, `torch`, `transformers`, `langchain-community`, FAISS, CLIP stack, etc.).

---

## After (runtime dependency / lazy import)
### After import location (inside `process_prompt`)
The import is now moved into the function:

```python
# Lazy import to avoid AI-stack dependency at module import time
from memory.memory_vector import query_memory, query_visual_memory
```

### Exact function modified
- `process_prompt(prompt: str) -> dict`

### What was NOT changed
- No change to OpenRouter `.env` loading
- No change to OpenAI client initialization
- No change to `from memory.memory_engine import recall`
- No change to `from intelligence.vibra import get_vibra_shift`
- No logic changes to how `query_memory(...)` / `query_visual_memory(...)` are called

---

## Dependency chain removed / isolated

### Previously (at foundation import time)
`core.orchestration` (module import)
→ `memory.memory_vector` (import-time)
→ AI stack (numpy / torch / transformers / langchain-community / faiss / CLIP components, etc.)

### Now
`core.orchestration` (module import)
→ (no `memory.memory_vector` import)
→ foundation can import without numpy/torch/etc

`core.orchestration.process_prompt(...)` (runtime)
→ lazy import `memory.memory_vector`
→ AI stack is required only when `process_prompt()` runs and vector/visual search executes

---

## Expected impact
### Foundation import should succeed without AI stack
- `from core.orchestration import *` should no longer require `numpy/torch/transformers/langchain-community/faiss`.

### Runtime behavior
- When `process_prompt()` executes, it still imports and uses `query_memory` and `query_visual_memory`, so behavior should remain consistent.

---

## Verification instructions (Python 3.12 critical-path)
Run the following in an environment where only `requirements-foundation.txt` is installed:

1) **Orchestration import**
```powershell
py -3.12 -c "from core.orchestration import *; print('orchestration ok')"
```

2) **API memory routes import**
```powershell
py -3.12 -c "from api.memory_routes import *; print('memory routes ok')"
```

3) **Optional: runtime smoke test**
Only after the above imports succeed:
- execute the app flow or call `process_prompt()` to confirm lazy import triggers correctly.

---

## Refactor Risk
- **Low**: This is a single import relocation (module-level → function-level) with identical call sites.
