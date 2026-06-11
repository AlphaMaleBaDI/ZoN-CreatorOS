# M1.3 Dependency Graph — CreatorOS (Imported Foundation Modules)

## Graph (as requested)
orchestration
    ↓
router
    ↓
memory_engine
    ↓
memory_vector
    ↓
vibra

---

## External Dependencies (in this dependency chain)

### core/orchestration.py
- `python-dotenv` (`load_dotenv`)
- `openai` (`OpenAI`)

### intelligence/router.py (router/provider wrapper)
- `openai` (`OpenAI`)
- `python-dotenv` (`load_dotenv`)

### memory/memory_vector.py (vector + multimodal)
- `numpy`
- `langchain_community` (`FAISS`, `HuggingFaceEmbeddings`)
- `PIL` (Pillow, `Image`)
- `torch`
- `transformers` (`CLIPProcessor`, `CLIPModel`)

### memory/memory_engine.py (JSON memory store)
- None (stdlib only)

### intelligence/vibra.py
- None (stdlib only)

---

## Environment Variables (env var references)

### core/orchestration.py
- `OPENROUTER_API_KEY`
- `OPENROUTER_BASE_URL` (default: `https://openrouter.ai/api/v1`)

### intelligence/router.py
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default: `gpt-4`)
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL` (default: `openrouter/auto`)
- `LOCALAI_API_KEY` (default: `local-key`)
- `LOCAL_MODEL` (default: `gpt4all`)

### memory/memory_engine.py
- None

### memory/memory_vector.py
- None

### intelligence/vibra.py
- None

---

## File Reads / Writes (as called by this chain)

### memory/memory_engine.py (JSON persistence)
- File read/write target:
  - `${MEMORY_DIR}/{ACTIVE_SCOPE}.json`
- Writes:
  - If file missing/corrupt: writes `[]` to `{scope}.json`
  - `save_memory(memories)`: writes `memories` to `{scope}.json`
- Reads:
  - `load_memory()`: reads `{scope}.json` if exists

### memory/memory_vector.py (vector + multimodal persistence)
- Directory creation (import-time):
  - `EMBEDDINGS_DIR` = `<memory>/visual_embeddings`
- Reads/Writes:
  - FAISS index directory:
    - `FAISS_PATH` = `<memory>/faiss_index`
    - Read: `FAISS.load_local(FAISS_PATH, ...)` if exists
    - Write: `db.save_local(FAISS_PATH)` after ingestion
  - Visual registry JSON:
    - `VISUAL_REGISTRY_PATH` = `<memory>/visual_registry.json`
    - Read: `open(..., "r", encoding="utf-8")`
    - Write: `open(..., "w", encoding="utf-8")`
  - Visual embedding numpy files:
    - `EMBEDDINGS_DIR/{safe_name}.npy`
    - Write: `np.save(...)`
    - Read: `np.load(...)`

### core/orchestration.py
- `.env` loading:
  - `load_dotenv()` default search
  - `load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))`
- Prompt file:
  - Reads: `<core>/prompt.txt` if it exists

### intelligence/router.py
- `.env` loading:
  - `load_dotenv()` (default search)

### intelligence/vibra.py
- None

---

## Notes
- The import refactor performed for M1.3 affects internal module paths only; it does not change runtime IO behavior described above.
