# D:\my programming\AfroVBra\backend\zon_mcp\api\memory_routes.py
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from memory.memory_engine import remember, recall, forget, set_scope


router = APIRouter()

class MemoryPayload(BaseModel):
    topic: str
    info: str
    scope: str = "default"

@router.post("/remember")
def remember_memory(payload: MemoryPayload):
    set_scope(payload.scope)
    remember(payload.topic, payload.info)
    return {"status": "success", "message": f"Memory stored under topic '{payload.topic}' in scope '{payload.scope}'."}

@router.get("/recall")
def recall_memory(topic: str = Query(...), scope: str = "default"):
    set_scope(scope)
    results = recall(topic)
    if not results:
        raise HTTPException(status_code=404, detail="No matching memory found.")
    return {"status": "success", "scope": scope, "results": results}

@router.delete("/forget")
def forget_memory(topic: str = Query(...), scope: str = "default"):
    set_scope(scope)
    result = forget(topic)
    if result:
        return {"status": "success", "message": f"Memory topic '{topic}' forgotten in scope '{scope}'."}
    else:
        raise HTTPException(status_code=404, detail=f"No memory found for topic '{topic}' to forget.")
