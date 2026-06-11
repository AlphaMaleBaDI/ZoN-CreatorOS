# M1.4-A Dependency Isolation Audit (core/orchestration.py only)

## Target file
- `core/orchestration.py`

### Goal
Explain why `from core.orchestration import *` pulls in the AI stack (numpy/torch/transformers/sentence-transformers/langchain-community/faiss), and whether those imports are required at *module import time* vs *runtime*.

---

## Dependency chain (from `core/orchestration.py` import *)

### Import statements that immediately trigger dependency loading
The following lines are present in `core/orchestration.py` and execute during module import (top-level):

1. `from memory.memory_engine import recall`
2. `from memory.memory_vector import query_memory, query_visual_memory`
3. `from intelligence.vibra import get_vibra_shift`

Only **#2** is capable of pulling the heavy AI/ML stack, because `memory.memory_vector` imports numpy/torch/transformers/langchain-community/PIL.

---

## Exact import locations (in `core/orchestration.py`)

### 1) Standard/Foundation + network client (module import time)
- `from dotenv import load_dotenv`
- `from openai import OpenAI`

These do **not** pull numpy/torch/transformers; they pull only foundation deps.

### 2) Internal CreatorOS imports (module import time)
- `from memory.memory_engine import recall`  
  (internal memory module; should be lightweight, but see note in “What actually pulls numpy?”)

- `from memory.memory_vector import query_memory, query_visual_memory`  
  **THIS is the import that triggers numpy/torch/transformers/langchain-community/faiss.**

- `from intelligence.vibra import get_vibra_shift`  
  (internal vibra mapping; lightweight)

### 3) No other direct imports of numpy/torch/transformers/etc in this file
- `core/orchestration.py` itself does **not** import numpy/torch/transformers/sentence-transformers/langchain-community/faiss.
- Those dependencies are pulled indirectly through the import of `memory.memory_vector` at module import time.

---

## Audit: which imports pull in AI stack dependencies?

Since this audit is restricted to `core/orchestration.py` only, the mapping is:

### A) `memory.memory_vector` import (core/orchestration.py)
**Import statement location:**
- `from memory.memory_vector import query_memory, query_visual_memory`

**What it pulls (via `memory/memory_vector.py` imports, not directly in this file):**
- `numpy` (`import numpy as np`)
- `torch` (`import torch`)
- `transformers` (`from transformers.models.clip import CLIPProcessor, CLIPModel`)
- `langchain-community` (`from langchain_community.vectorstores import FAISS`, `from langchain_community.embeddings import HuggingFaceEmbeddings`)
- `sentence-transformers` (indirect via `HuggingFaceEmbeddings` model loading; not imported as a package here, but is part of the model/runtime stack)
- `faiss` (indirect via FAISS vectorstore backend; `langchain-community` + `faiss-cpu` provides persistence/runtime)
- `PIL` (not in your requested list, but it’s imported in `memory_vector.py`)

**Required at module import time?**
- **YES**
- Reason: this import is executed at top-level, so Python must fully import `memory.memory_vector` to resolve `query_memory` and `query_visual_memory` before `core/orchestration.py` finishes importing.

---

### B) `memory.memory_engine` import
**Import statement location:**
- `from memory.memory_engine import recall`

**What it pulls (re: your requested AI packages):**
- Does not require numpy/torch/transformers/langchain/faiss in the code shown from `memory_engine.py` (it uses stdlib: `os`, `json`, `logging`, `datetime`).

**Required at module import time?**
- **YES**, but it is not responsible for numpy/torch/etc.

---

### C) `intelligence.vibra` import
**Import statement location:**
- `from intelligence.vibra import get_vibra_shift`

**What it pulls (re: your requested AI packages):**
- Does not require numpy/torch/transformers/langchain/faiss in the code shown from `intelligence/vibra.py` (stdlib only).

**Required at module import time?**
- **YES**, but not responsible for numpy/torch/etc.

---

## For each dependency requested: module-import requirement classification

### `numpy`
- **Pulled by:** `from memory.memory_vector import query_memory, query_visual_memory`
- **Module import time required?** **YES**

### `torch`
- **Pulled by:** same import
- **Module import time required?** **YES**

### `transformers`
- **Pulled by:** same import
- **Module import time required?** **YES**

### `sentence-transformers`
- **Pulled by:** `HuggingFaceEmbeddings(model_name="sentence-transformers/...")` inside `memory_vector.py`
- **Module import time required?** **YES-ish / runtime-on-first-use**
  - The package may not be imported by name, but model loading and/or downstream components require the model ecosystem.

### `langchain-community`
- **Pulled by:** same import
- **Module import time required?** **YES**

### `faiss`
- **Pulled by:** same import (via FAISS backend; typically provided by `faiss-cpu`)
- **Module import time required?** **YES** (at least import-time module availability + deserialization/persistence support)

---

## Dependency chain diagram (import-time)

**User code**
- `from core.orchestration import *`

**core/orchestration.py module import executes:**
- `from memory.memory_vector import query_memory, query_visual_memory`
  -> loads `memory/memory_vector.py`
    -> imports numpy/torch/transformers/PIL/langchain-community (+ FAISS)

**Result**
- Module import fails unless numpy/torch/transformers/langchain/faiss packages are installed.

---

## Refactor recommendation (no code modifications performed)

### For the import of `memory.memory_vector` (critical)
- `from memory.memory_vector import query_memory, query_visual_memory`

**Recommendation label: MOVE to lazy/runtime import**

**Justification**
- `process_prompt()` only needs these functions when:
  - vector search is attempted (`query_memory(prompt, k=3)`)
  - visual multimodal search is attempted (`query_visual_memory(...)`)
- Many call paths may not require vector/visual search.
- Moving imports inside `process_prompt()` (or a dedicated lazy loader) prevents `numpy/torch/transformers/langchain/faiss` from being required for *importing* `core.orchestration`.

---

## Summary table (core/orchestration.py)

| Import line (exact) | Pulls numpy/torch/etc? | Required at module import time? | Recommendation |
|---|---:|---:|---|
| `from memory.memory_engine import recall` | No (AI stack) | Yes | KEEP (module level) |
| `from memory.memory_vector import query_memory, query_visual_memory` | Yes | **Yes** | **MOVE to lazy/runtime import** |
| `from intelligence.vibra import get_vibra_shift` | No | Yes | KEEP (module level) |
| `from dotenv import load_dotenv` | No | Yes | KEEP |
| `from openai import OpenAI` | No | Yes | KEEP |
