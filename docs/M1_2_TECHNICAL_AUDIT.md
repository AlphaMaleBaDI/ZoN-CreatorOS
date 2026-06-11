# M1.2 Technical Audit — Dependency Audit (Extracted CreatorOS Foundation Modules)

Scope files:
- memory/memory_engine.py
- memory/memory_vector.py
- intelligence/vibra.py
- intelligence/router.py
- core/orchestration.py

---

## memory/memory_engine.py

### Imports (exactly as written)
```python
import os
import json
import logging # Import logging
from datetime import datetime
```

### External Dependencies (exact package names)
- None (standard library only)

### Globals (every module-level mutable object)
- `ACTIVE_SCOPE = "default"` (mutable state; changed via `set_scope()`)
- `logger = logging.getLogger(__name__)` (logger instance)

### File Dependencies (every file read/write)
- `MEMORY_DIR` (directory creation)
- Read: `get_memory_file()` -> `os.path.join(MEMORY_DIR, f"{ACTIVE_SCOPE}.json")`
- Write (new/repair): same `{scope}.json` writes via `json.dump([], ...)`
- Write (save): same `{scope}.json` writes via `json.dump(memories, ...)`

### Environment Dependencies (every env var reference)
- None

### Refactor Risk
- **YELLOW** — Uses module-level state `ACTIVE_SCOPE` affecting all memory operations; hardcoded storage layout via `MEMORY_DIR` derived from file locations. Otherwise internal logic is self-contained.

### CreatorOS Recommendation
- **REPLACE** — Move away from module-global `ACTIVE_SCOPE`; inject scope into functions or encapsulate in a class/service. Keep filesystem IO behind a storage interface.

---

## memory/memory_vector.py

### Imports (exactly as written)
```python
import os
import json
import numpy as np
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from PIL import Image # type: ignore
import torch
from transformers.models.clip import CLIPProcessor, CLIPModel
import traceback
import logging
```

### External Dependencies (exact package names)
- `numpy`
- `langchain_community` (provides `FAISS`, `HuggingFaceEmbeddings`)
- `PIL` (Pillow)
- `torch`
- `transformers`
- `logging`, `traceback` (standard library)

### Globals (every module-level mutable object)
- `logger = logging.getLogger(__name__)`
- `FAISS_PATH`
- `VISUAL_REGISTRY_PATH`
- `EMBEDDINGS_DIR`
- `_embedding_model = None`
- `_clip_model = None`
- `_clip_processor = None`

### File Dependencies (every file read/write)
- Directory creation (at import time): `os.makedirs(EMBEDDINGS_DIR, exist_ok=True)`
- FAISS index:
  - Read: `FAISS.load_local(FAISS_PATH, ...)` if `os.path.exists(FAISS_PATH)`
  - Write: `db.save_local(FAISS_PATH)`
- Visual registry JSON:
  - Read: `VISUAL_REGISTRY_PATH` via `open(..., "r", encoding="utf-8")`
  - Write: `VISUAL_REGISTRY_PATH` via `open(..., "w", encoding="utf-8")`
- Visual embedding files:
  - Write: `np.save(emb_path, img_emb)` to `EMBEDDINGS_DIR/{safe_name}.npy`
  - Read: `np.load(emb_file)` in `query_visual_memory`

### Environment Dependencies (every env var reference)
- None

### Refactor Risk
- **RED** — Heavy third-party ML stack; module-level singletons (`_embedding_model`, `_clip_model`, `_clip_processor`) and import-time directory creation; filesystem persistence and deserialization rely on `allow_dangerous_deserialization=True`.

### CreatorOS Recommendation
- **REFACTOR** — Encapsulate model loading and persistence into explicit services; remove import-time side effects; add configuration injection for directories and safety flags.

---

## intelligence/vibra.py

### Imports (exactly as written)
```python
import logging
from typing import Any, Dict
```

### External Dependencies (exact package names)
- None (standard library only)

### Globals (every module-level mutable object)
- `VIBRA_MAP` (dict)
- `DEFAULT_VIBRA` (dict with `keywords`: `set()`)
- `logger = logging.getLogger(__name__)`

### File Dependencies (every file read/write)
- None

### Environment Dependencies (every env var reference)
- None

### Refactor Risk
- **GREEN** — Pure in-memory mapping and deterministic keyword scoring; minimal side effects.

### CreatorOS Recommendation
- **KEEP**

---

## intelligence/router.py

### Imports (exactly as written)
```python
import os
from openai import OpenAI
from typing import Literal
from dotenv import load_dotenv
```

### External Dependencies (exact package names)
- `openai`
- `python-dotenv` (provides `load_dotenv`)

### Globals (every module-level mutable object)
- `ModelSource` (type alias)
- No other explicit module-level mutable state besides the class definition (client/model are instance members)

### File Dependencies (every file read/write)
- Indirect via `load_dotenv()` (loads `.env` from default search locations)

### Environment Dependencies (every env var reference)
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-4`)
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL` (default: `openrouter/auto`)
- `LOCALAI_API_KEY` (default: `local-key`)
- `LOCAL_MODEL` (default: `gpt4all`)

### Refactor Risk
- **YELLOW** — Global behavior depends on environment variables; runtime selection via `source`. Side effects occur during `_init_client()` based on env state.

### CreatorOS Recommendation
- **REPLACE** — Centralize configuration validation; avoid implicit `.env` loading inside module. Prefer explicit dependency injection and fail-fast validation per chosen provider.

---

## core/orchestration.py

### Imports (exactly as written)
```python
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
```

Additional imports (note: appear after client initialization; exact as written):
```python
from memory_engine import recall
from memory_vector import query_memory, query_visual_memory
from mood_bridge import get_vibra_shift
from pathlib import Path
```

### External Dependencies (exact package names)
- `python-dotenv` (provides `load_dotenv`)
- `openai`

### Globals (every module-level mutable object)
- `logger = logging.getLogger(__name__)`
- `api_key` (env-derived)
- `base_url` (env-derived)
- `client = OpenAI(...)` (singleton client)
- `PROMPT_FILE` (path object)
- `SYSTEM_PROMPT` (mutable string)

### File Dependencies (every file read/write)
- `.env` loading (indirect):
  - `load_dotenv()` default lookup
  - `load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))`
- Prompt file:
  - Read: `PROMPT_FILE` via `open(..., "r", encoding="utf-8")` if exists
- Calls into internal modules which perform their own IO:
  - `query_memory`, `query_visual_memory`, `recall` (see their module-level audits)

### Environment Dependencies (every env var reference)
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL` (default: `https://openrouter.ai/api/v1`)

### API Dependencies
- OpenAI client configured to call OpenRouter endpoint via `base_url`

### Refactor Risk
- **RED** — Module import-time side effects:
  - validates env and raises at import time
  - creates global `client` singleton
  - loads prompt file at import time
  - uses non-package-relative imports (`from memory_engine import ...`, `from memory_vector import ...`, `from mood_bridge import ...`) which can break depending on working directory / package layout.

### CreatorOS Recommendation
- **REFACTOR** — Move initialization into functions/classes; use package-relative imports; add configuration object; avoid import-time execution.

---

## Notes on Cross-Module Internal Dependency Mismatches
- `core/orchestration.py` imports `from mood_bridge import get_vibra_shift`, but within this audited scope the file is `intelligence/vibra.py` (function name is `get_vibra_shift`). This suggests a potential internal import-path inconsistency relative to package structure.


