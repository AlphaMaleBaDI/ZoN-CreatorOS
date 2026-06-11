# M1.3-A Import Refactor — Migration Notes (Imports Only)

Scope (per request):
- core/orchestration.py
- memory/memory_engine.py
- memory/memory_vector.py
- intelligence/router.py
- api/memory_routes.py

## 1) core/orchestration.py

### Old import
```python
from memory_engine import recall
```

### New import
```python
from memory.memory_engine import recall
```

### Reason
Removes dependency on the old/top-level module layout; aligns import with CreatorOS `memory/` package.

---

### Old import
```python
from memory_vector import query_memory, query_visual_memory
```

### New import
```python
from memory.memory_vector import query_memory, query_visual_memory
```

### Reason
Removes dependency on the old/top-level module layout; aligns import with CreatorOS `memory/` package.

---

### Old import
```python
from mood_bridge import get_vibra_shift
```

### New import
```python
from intelligence.vibra import get_vibra_shift
```

### Reason
`mood_bridge` does not exist in this extracted/CreatorOS layout; vibra implementation lives in `intelligence/vibra.py`.

---

## 2) api/memory_routes.py

### Old import
```python
from memory_engine import remember, recall, forget, set_scope
```

### New import
```python
from memory.memory_engine import remember, recall, forget, set_scope
```

### Reason
Removes dependency on the old/top-level module layout; aligns import with CreatorOS `memory/` package.

---

## 3) memory/memory_engine.py
- No internal import statements pointing to old zon_mcp layout found; no changes required for imports.

## 4) memory/memory_vector.py
- No internal import statements pointing to old zon_mcp layout found; no changes required for imports.

## 5) intelligence/router.py
- No internal import statements pointing to old zon_mcp layout found; no changes required for imports.
