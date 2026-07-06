import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.memory_routes import router as memory_router
from core.kernel import Kernel
from core.schemas import ContextObject
from services.workspace_service import WorkspaceService
from services.profile_service import ProfileService
from services.artifact_service import ArtifactService
from services.snapshot_service import SnapshotService
from memory.creator_profile import CreatorProfile

app = FastAPI(title="ZoN CreatorOS", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memory_router, prefix="/memory", tags=["Memory"])

workspace_service = WorkspaceService()
profile_service = ProfileService()
artifact_service = ArtifactService()
snapshot_service = SnapshotService()


@app.get("/health")
def health():
    return {"status": "ok", "service": "ZoN CreatorOS"}


class CreateWorkspaceRequest(BaseModel):
    name: str


class CreateProjectRequest(BaseModel):
    workspace_id: UUID
    name: str


class SaveProfileRequest(BaseModel):
    creator_name: str
    brand_voice: str = ""
    writing_style: str = ""
    goals: List[str] = []
    preferred_platforms: List[str] = []
    personality: str = ""
    preferred_tools: List[str] = []
    working_habits: List[str] = []


class GenerateLaunchPlanRequest(BaseModel):
    workspace_id: UUID
    project_id: Optional[UUID] = None
    user_request: str
    creator_name: Optional[str] = None


@app.post("/workspaces")
def create_workspace(req: CreateWorkspaceRequest):
    ws = workspace_service.create_workspace(req.name)
    return {"workspace_id": str(ws.workspace_id), "name": ws.name}


@app.get("/workspaces")
def list_workspaces():
    return [{"workspace_id": str(w.workspace_id), "name": w.name}
            for w in workspace_service.list_workspaces()]


@app.post("/workspaces/{workspace_id}/projects")
def create_project(workspace_id: UUID, req: CreateProjectRequest):
    proj = workspace_service.create_project(workspace_id, req.name)
    return {"project_id": str(proj.project_id), "name": proj.name}


@app.get("/workspaces/{workspace_id}/projects")
def list_projects(workspace_id: UUID):
    projs = workspace_service.list_projects(workspace_id)
    return [{"project_id": str(p.project_id), "name": p.name, "active": p.active}
            for p in projs]


# -- Profile endpoints ------------------------------------------------

@app.post("/profiles")
def save_profile(req: SaveProfileRequest):
    profile = CreatorProfile(**req.model_dump())
    ok = profile_service.update_creator_profile(profile)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save profile")
    return {"status": "saved", "creator_name": req.creator_name}


@app.get("/profiles/{creator_name}")
def get_profile(creator_name: str):
    profile = profile_service.get_creator_profile(creator_name)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile.model_dump()


# -- Artifact retrieval (Mission 004.3) --------------------------------

@app.get("/workspaces/{workspace_id}/artifacts")
def list_artifacts(workspace_id: UUID):
    ids = artifact_service.list_artifacts(workspace_id)
    results = []
    for aid in ids:
        art = artifact_service.retrieve_artifact(aid, workspace_id)
        if art:
            results.append({
                "artifact_id": art.get("artifact_id", aid),
                "artifact_type": art.get("artifact_type", "unknown"),
                "created_at": art.get("created_at"),
                "created_by": art.get("created_by"),
                "provider": art.get("provider"),
                "confidence": art.get("confidence"),
            })
    return sorted(results, key=lambda x: x.get("created_at", 0), reverse=True)


@app.get("/workspaces/{workspace_id}/artifacts/{artifact_id}")
def get_artifact(workspace_id: UUID, artifact_id: str):
    art = artifact_service.retrieve_artifact(artifact_id, workspace_id)
    if not art:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return art


# -- Snapshot retrieval (Mission 004.4) --------------------------------

@app.get("/workspaces/{workspace_id}/snapshots")
def list_snapshots(workspace_id: UUID):
    return snapshot_service.list_snapshots(workspace_id)


# -- Launch plan generation via Kernel ---------------------------------

@app.post("/generate-launch-plan")
def generate_launch_plan(req: GenerateLaunchPlanRequest):
    kernel = Kernel()
    kernel.initialize(
        workspace_id=req.workspace_id,
        creator_name=req.creator_name,
    )
    context = kernel.assemble_context(
        user_request=req.user_request,
        project_id=req.project_id,
    )
    result = kernel.execute(context)
    return result.model_dump() if hasattr(result, "model_dump") else result


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
