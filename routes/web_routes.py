"""
web_routes.py — CreatorOS Web UI

Serves the Visual Operating System interface via Jinja2 templates.
All data comes from existing API services — no new backend logic.
"""

import os
import time
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from services.workspace_service import WorkspaceService
from services.profile_service import ProfileService
from services.artifact_service import ArtifactService
from core.pie import ProductionIntelligenceEngine
from core.pipeline_progress import current as pipeline_current

router = APIRouter(tags=["Web UI"])
_base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(_base, "templates"))

ws_service = WorkspaceService()
profile_service = ProfileService()
artifact_service = ArtifactService()
pie = ProductionIntelligenceEngine()


def _load_workspace_data():
    workspaces = ws_service.list_workspaces()
    if not workspaces:
        return None

    ws = workspaces[-1]
    projects = ws_service.list_projects(ws.workspace_id)
    profiles = profile_service.profile_engine.list_profiles()
    creator_name = profiles[-1] if profiles else None
    profile = profile_service.get_creator_profile(creator_name) if creator_name else None
    active = [p for p in projects if p.active]
    project = active[0] if active else (projects[-1] if projects else None)

    artifact_ids = artifact_service.list_artifacts(ws.workspace_id)
    artifacts = []
    for aid in artifact_ids:
        art = artifact_service.retrieve_artifact(aid, ws.workspace_id)
        if art:
            artifacts.append(art)

    existing_types = {a.get("artifact_type", "unknown") for a in artifacts}
    state = pie.determine_state(existing_types, {})

    providers = [a.get("provider", "unknown") for a in artifacts if a.get("provider")]
    confidences = [a.get("confidence") for a in artifacts if a.get("confidence") is not None]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0

    return {
        "workspace": ws,
        "project": project,
        "creator_name": creator_name,
        "profile": profile,
        "artifacts": artifacts,
        "state": state,
        "providers": list(dict.fromkeys(providers)),
        "avg_confidence": round(avg_conf, 2),
        "artifact_count": len(artifacts),
    }


@router.get("/", response_class=HTMLResponse)
def os_dashboard(request: Request):
    data = _load_workspace_data()
    if not data:
        return templates.TemplateResponse(request, "os.html", {
            "ready": False,
            "ws_name": "",
            "creator_name": "",
            "project_name": "",
            "phase": "ideation",
            "phase_next": "",
            "momentum": 0,
            "momentum_total": 0,
            "artifacts": [],
            "providers": [],
            "avg_confidence": 0,
            "artifact_count": 0,
            "blockers": [],
            "requirements": [],
            "can_transition": False,
        })

    state = data["state"]
    req_evidence = [e for e in state.evidence if e.artifact_type in (
        t for t, m in pie.state_map.items() if m["required_for_transition"]
    )]
    momentum_passed = len([e for e in req_evidence if e.exists])
    momentum_total = max(len(req_evidence), 1)
    vibra = getattr(data["profile"], "personality", "Creative") if data["profile"] else "Creative"
    brand = getattr(data["profile"], "brand_voice", "") if data["profile"] else ""

    return templates.TemplateResponse(request, "os.html", {
        "ready": True,
        "ws_id": str(data["workspace"].workspace_id),
        "ws_name": data["workspace"].name,
        "creator_name": data["creator_name"] or "",
        "project_name": data["project"].name if data["project"] else "",
        "vibra": vibra,
        "brand": brand,
        "phase": state.current_state.value,
        "phase_next": state.next_state.value if state.next_state else "",
        "momentum": momentum_passed,
        "momentum_total": momentum_total,
        "artifacts": data["artifacts"],
        "providers": data["providers"],
        "avg_confidence": data["avg_confidence"],
        "artifact_count": data["artifact_count"],
        "blockers": state.blockers,
        "requirements": state.requirements,
        "can_transition": state.can_transition,
    })


@router.get("/pipeline/progress")
def pipeline_progress():
    return pipeline_current()
