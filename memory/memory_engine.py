import os
import json
import logging # Import logging
from datetime import datetime

# --- Robust absolute path for zon_memory ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GRANDPARENT_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))  # Go up two levels from zon_mcp/zon_mcp/
MEMORY_DIR = os.path.join(GRANDPARENT_DIR, "zon_memory")
ACTIVE_SCOPE = "default"

logger = logging.getLogger(__name__) # Get a logger instance

def get_memory_file():
    return os.path.join(MEMORY_DIR, f"{ACTIVE_SCOPE}.json")

def load_memory():
    file = get_memory_file()
    if not os.path.exists(file):
        os.makedirs(MEMORY_DIR, exist_ok=True)
        with open(file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
        return []
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning(f"Corrupt memory file '{file}', resetting. Reason: {e}", exc_info=True)
        with open(file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
        return []

def save_memory(memories):
    file = get_memory_file()
    os.makedirs(MEMORY_DIR, exist_ok=True)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(memories, f, indent=4)

def remember(topic: str, info: str):
    memories = load_memory()
    memories.append({
        "topic": topic,
        "info": info,
        "timestamp": datetime.now().isoformat()
    })
    save_memory(memories)
    logger.info(f"ZoN remembered '{topic}' in scope '{ACTIVE_SCOPE}'")

def recall(topic: str):
    memories = load_memory()
    matches = [m for m in memories if topic.lower() in m["topic"].lower()]
    if not matches:
        logger.info(f"Recall: Nothing found for '{topic}' in scope '{ACTIVE_SCOPE}'.")
        return []
    for mem in matches:
        logger.info(f"Recall Match in '{ACTIVE_SCOPE}': Topic: {mem['topic']}, Info: {mem['info'][:50]}..., Date: {mem['timestamp']}")
    return matches

def forget(topic: str) -> bool:
    memories = load_memory()
    original_length = len(memories)
    filtered = [m for m in memories if topic.lower() not in m["topic"].lower()]
    if len(filtered) == original_length:
        logger.info(f"Forget: Nothing found with topic '{topic}' to forget in scope '{ACTIVE_SCOPE}'.")
        return False
    save_memory(filtered)
    logger.info(f"Forgotten all memory entries matching: '{topic}' in scope '{ACTIVE_SCOPE}'")
    return True

def set_scope(scope_name: str):
    global ACTIVE_SCOPE
    ACTIVE_SCOPE = scope_name.strip().lower()
    logger.info(f"ZoN memory scope set to: {ACTIVE_SCOPE}")

def get_active_scope():
    return ACTIVE_SCOPE