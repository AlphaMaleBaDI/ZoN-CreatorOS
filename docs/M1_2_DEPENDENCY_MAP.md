# M1.2 Dependency Map (Migration Checklist)

Scope files (migrated / extracted):
- memory/memory_engine.py
- memory/memory_vector.py
- intelligence/vibra.py
- intelligence/router.py
- core/orchestration.py

> Audit output is based strictly on the current file contents present in this workspace.

---

## memory/memory_engine.py

### Imports
- `import os`
- `import json`
- `import logging # Import logging`
- `from datetime import datetime`

### Status
- ✅ OK (standard library only)

### Imports that break (packaging)
- None observed

### Imports still pointing to zon_mcp
- None observed

### Missing modules
- None

### Path changes required
- None

---

## memory/memory_vector.py

### Imports
- `import os`
- `import json`
- `import numpy as np`
- `from langchain_community.vectorstores import FAISS`
- `from langchain_community.embeddings import HuggingFaceEmbeddings`
- `from PIL import Image # type: ignore`
- `import torch`
- `from transformers.models.clip import CLIPProcessor, CLIPModel`
- `import traceback`
- `import logging`

### External dependencies required
- `numpy`
- `langchain_community` (FAISS + HuggingFaceEmbeddings)
- `PIL` (Pillow)
- `torch`
- `transformers`

### Status
- ⚠️ External dependency required (not a path/import break, but a runtime dependency)

### Imports that break (packaging)
- None observed (internal imports not present)

### Imports still pointing to zon_mcp
- None observed

### Missing modules
- None (within CreatorOS); relies on third-party packages

### Path changes required
- None

---

## intelligence/vibra.py

### Imports
- `import logging`
- `from typing import Any, Dict`

### Status
- ✅ OK (standard library only)

### Imports that break (packaging)
- None observed

### Imports still pointing to zon_mcp
- None observed

### Missing modules
- None

### Path changes required
- None

---

## intelligence/router.py

### Imports
- `import os`
- `from openai import OpenAI`
- `from typing import Literal`
- `from dotenv import load_dotenv`

### External dependencies required
- `openai`
- `python-dotenv`

### Status
- ⚠️ External dependency required

### Imports that break (packaging)
- None observed (internal imports not present)

### Imports still pointing to zon_mcp
- None observed

### Missing modules
- None

### Path changes required
- None

---

## core/orchestration.py

### Imports
Standard library / third-party:
- `import os`
- `import logging`
- `from dotenv import load_dotenv`
- `from openai import OpenAI`

Internal CreatorOS imports (as written):
- `from memory_engine import recall`
- `from memory_vector import query_memory, query_visual_memory`
- `from mood_bridge import get_vibra_shift`
- `from pathlib import Path`

### Status
- ❌ Broken (CreatorOS package-relative imports appear inconsistent)

### What imports break?
- `from memory_engine import recall`
  - Breaks unless `memory_engine.py` is importable as a top-level module in `sys.path`.
- `from memory_vector import query_memory, query_visual_memory`
  - Same issue: expects top-level module.
- `from mood_bridge import get_vibra_shift`
  - Likely wrong module name/path for the audited migration.
  - Within this workspace scope, the vibra logic is in `intelligence/vibra.py`, not a `mood_bridge.py`.

### Imports still pointing to zon_mcp
- Not explicitly `zon_mcp` in imports, but the import style (`from X import Y` without package prefixes) risks reintroducing migration coupling via import-path assumptions.

### Missing modules
- `mood_bridge` module (as named in this file) appears missing in this workspace.
- `memory_engine` and `memory_vector` are present under packages (`memory/`), but not imported with package prefixes.

### Path changes required
- Convert imports to package-qualified paths, e.g.:
  - `from memory.memory_engine import recall`
  - `from memory.memory_vector import query_memory, query_visual_memory`
  - `from intelligence.vibra import get_vibra_shift`

---

## CreatorOS Architecture Verdict (based on current audit scope)
Core Schemas: ✅ Complete (not audited here)
Memory Layer: ✅ Migrated (memory modules present)
Intelligence Layer: ✅ Migrated (vibra/router present)
API Layer: ✅ Migrated (memory_routes present; not fully audited here)
Workspace Layer: ❌ Missing
Agent Layer: ❌ Missing
Dashboard Layer: ❌ Missing
AMD Benchmark Layer: ❌ Missing

---

## Summary: Primary Migration Hazards
1. **Import-path coupling**: `core/orchestration.py` uses non-package-relative internal imports.
2. **Module naming mismatch**: `core/orchestration.py` imports `mood_bridge`, but vibra logic lives in `intelligence/vibra.py`.
3. **Third-party stack requirement**: `memory_vector.py` depends on ML/vector libraries.

