import os
import sys
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api.memory_routes import router as memory_router
from core.kernel import Kernel
from core.schemas import ContextObject, ProductionState, CurrentUnderstanding
from core.pie import ProductionIntelligenceEngine
from core.onboarding import OnboardingEngine, get_session, create_session
from core.intent_engine import IntentEngine, WorkspaceContext
from core.observer import CreatorMindObserver, MIND_DIR
from core.reasoning import ShadowReasoning
from core.conversation import classify_intent, is_project_relevant, social_response, ConversationIntent
from core.domains import detect_domain, get_domain_profile, CreativeDomain, CreativeActivity, detect_activity, activity_intro, normalize_input
from core.production import ProductionEngine, Artifact
from services.workspace_service import WorkspaceService
from services.profile_service import ProfileService
from services.artifact_service import ArtifactService
from services.snapshot_service import SnapshotService
from memory.creator_profile import CreatorProfile
from routes.web_routes import router as web_router

app = FastAPI(title="ZoN CreatorOS", version="0.8.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(memory_router, prefix="/memory", tags=["Memory"])
app.include_router(web_router)

pie_engine = ProductionIntelligenceEngine()

workspace_service = WorkspaceService()
profile_service = ProfileService()
artifact_service = ArtifactService()
snapshot_service = SnapshotService()
onboarding_engine = OnboardingEngine()
intent_engine = IntentEngine()
observer = CreatorMindObserver()
reasoning_engine = ShadowReasoning()

# In-memory reasoning cache: workspace_id → last ReasoningCandidate
_reasoning_cache: dict = {}

# Conversation phase: tracks linear demo flow across turns
_conversation_phase: dict = {}  # "reflect" → "propose" → "complete"

# Last understanding captured when reflect was dispatched (used by phase intercept)
_last_reflection_understanding: dict = {}


def _is_affirmation(text: str) -> bool:
    """Check if a message affirms a reflection (control signal, not evidence)."""
    t = text.strip(".,!?;:").lower()
    if t in {"yes", "yeah", "yep", "exactly", "precisely", "correct", "that's right", "that's it", "i agree", "i do"}:
        return True
    return t.startswith("yes,") or t.startswith("yes that") or t == "y"


def _is_approval(text: str) -> bool:
    """Check if a message approves generation (control signal, not evidence)."""
    t = text.strip(".,!?;:").lower()
    if t in {"proceed", "go ahead", "yes", "start", "begin", "let's go", "do it", "sure", "generate", "create", "ready", "generate it", "let's do it"}:
        return True
    return t.startswith("go ahead") or t.startswith("yes,") or t.startswith("yes ") or t == "y"




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
    artifact_type: str = "launch_plan"


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


@app.post("/workspaces/{workspace_id}/new-project")
def new_project(workspace_id: UUID):
    ws_str = str(workspace_id)
    project = workspace_service.create_project(ws_str, "Untitled Film")
    mind_path = os.path.join(MIND_DIR, ws_str, "creator_state.json")
    os.makedirs(os.path.dirname(mind_path), exist_ok=True)
    with open(mind_path, "w", encoding="utf-8") as f:
        f.write(CurrentUnderstanding().model_dump_json(indent=2))
    _reasoning_cache.pop(ws_str, None)
    return {
        "status": "ok",
        "project_id": str(project.project_id),
        "project_name": project.name,
        "message": "Fresh slate. What are we making?",
    }


# -- Profile endpoints ------------------------------------------------

@app.get("/profiles")
def list_profiles():
    return profile_service.profile_engine.list_profiles()


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


# -- Pipeline diagnostics ----------------------------------------------

@app.get("/workspaces/{workspace_id}/diagnostics")
def pipeline_diagnostics(workspace_id: UUID):
    artifact_ids = artifact_service.list_artifacts(workspace_id)
    existing_types = set()
    for aid in artifact_ids:
        art = artifact_service.retrieve_artifact(aid, workspace_id)
        if art:
            atype = art.get("artifact_type")
            if atype:
                existing_types.add(atype)
    state = pie_engine.determine_state(existing_artifact_types=existing_types, eval_scores={})
    pie = pie_engine.analyze(
        artifact_type="launch_plan",
        existing_artifact_types=existing_types,
        eval_scores={},
    )
    sa = state.model_dump()
    next_state = sa.get("next_state")
    transition_artifact = None
    if next_state:
        for atype, mapping in pie_engine.state_map.items():
            if mapping["state"] == next_state and mapping["required_for_transition"]:
                if atype not in existing_types:
                    transition_artifact = atype
                    break
    return {
        "workspace_id": str(workspace_id),
        "existing_artifact_types": sorted(list(existing_types)),
        "current_state": sa["current_state"],
        "next_state": next_state,
        "can_transition": sa["can_transition"],
        "blockers": sa["blockers"],
        "requirements": sa["requirements"],
        "transition_artifact": transition_artifact,
        "pie_recommended_next": pie.recommended_next,
        "total_artifacts": len(artifact_ids),
    }


# -- Onboarding endpoints (Mission 015) ----------------------------------------

@app.get("/onboarding/status")
def onboarding_status():
    profiles = profile_service.profile_engine.list_profiles()
    workspaces = workspace_service.list_workspaces()
    needs_onboarding = len(profiles) == 0 or len(workspaces) == 0
    return {
        "needs_onboarding": needs_onboarding,
        "workspace_id": str(workspaces[0].workspace_id) if workspaces else None,
    }


class OnboardingStartResponse(BaseModel):
    session_id: str
    workspace_id: str
    first_message: str


@app.post("/onboarding/start")
def onboarding_start() -> OnboardingStartResponse:
    session = create_session()
    ws = workspace_service.create_workspace("CreatorOS")
    session.workspace_id = str(ws.workspace_id)
    first_message = onboarding_engine.start(session)
    return OnboardingStartResponse(
        session_id=session.session_id,
        workspace_id=str(ws.workspace_id),
        first_message=first_message,
    )


class OnboardingMessageRequest(BaseModel):
    session_id: str
    message: str


class OnboardingMessageResponse(BaseModel):
    response: str
    phase: str
    done: bool
    extraction: dict = {}


@app.post("/onboarding/message")
def onboarding_message(req: OnboardingMessageRequest) -> OnboardingMessageResponse:
    session = get_session(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    response = onboarding_engine.process_message(session, req.message)

    done = session.phase == "complete"
    extraction = {}
    if session.extraction:
        extraction = {
            "domain": session.extraction.domain,
            "intent": session.extraction.intent,
            "themes": session.extraction.themes,
            "confidence": session.extraction.confidence,
            "project_name": session.extraction.project_name,
            "audience": session.extraction.audience,
            "timeline": session.extraction.timeline,
        }

    return OnboardingMessageResponse(
        response=response,
        phase=session.phase,
        done=done,
        extraction=extraction,
    )


# -- Creator State (Observer Mode — Mission 016B) --------------------------------

@app.get("/workspaces/{workspace_id}/mind")
def get_creator_mind(workspace_id: UUID):
    state = observer.get_state(str(workspace_id))
    return state.model_dump()


# -- Shadow Reasoning (Mission 017B) --------------------------------------------

@app.get("/workspaces/{workspace_id}/reasoning")
def get_shadow_reasoning(workspace_id: UUID):
    cached = _reasoning_cache.get(str(workspace_id))
    if not cached:
        return {"reflection": "", "confidence": 0.0, "suggested_action": "wait",
                "reasoning_trace": [], "unanswered_questions": [],
                "risks": [], "opportunities": []}
    return cached.model_dump()


# -- Production State endpoint (Mission 009) -----------------------------------

@app.get("/workspaces/{workspace_id}/state")
def get_production_state(workspace_id: UUID):
    artifact_ids = artifact_service.list_artifacts(workspace_id)
    existing_types = set()
    eval_scores = {}
    for aid in artifact_ids:
        art = artifact_service.retrieve_artifact(aid, workspace_id)
        if art:
            atype = art.get("artifact_type")
            if atype:
                existing_types.add(atype)
    state_assessment = pie_engine.determine_state(
        existing_artifact_types=existing_types,
        eval_scores=eval_scores,
    )
    return {
        "workspace_id": str(workspace_id),
        "state_assessment": state_assessment.model_dump(),
    }


# -- Debug / Trace ----------------------------------------------------------

@app.get("/debug/trace/{workspace_id}")
def debug_trace(workspace_id: UUID):
    ws_str = str(workspace_id)
    understanding = observer.get_state(ws_str)
    candidate = _reasoning_cache.get(ws_str)
    return {
        "workspace_id": ws_str,
        "domain": understanding.domain,
        "activity": understanding.activity,
        "version": understanding.version,
        "observations": [
            {"id": o.id, "content": o.content[:80], "confidence": o.confidence, "impact": o.impact, "source": o.source.value}
            for o in understanding.observations[-10:]
        ],
        "beliefs": [
            {"id": b.id, "statement": b.statement[:80], "lifecycle": b.lifecycle.value, "confidence": b.confidence}
            for b in understanding.beliefs[-10:]
        ],
        "requirements": [
            {"area": r.area, "status": r.status.value, "confidence": r.confidence, "evidence": r.evidence_ids}
            for r in understanding.requirement_states
        ],
        "tensions": [
            {"id": t.id, "description": t.description, "status": t.status, "priority": t.priority.value}
            for t in understanding.tensions
        ],
        "reasoning": {
            "reflection": candidate.reflection[:120] if candidate else "",
            "action": candidate.suggested_action if candidate else "",
            "confidence": candidate.confidence if candidate else 0,
            "questions": candidate.unanswered_questions[:5] if candidate else [],
        } if candidate else None,
    }


# -- Conversation Response Builders (Mission 018 — Creative Partner) ---------

_INTERRUPT_KEYWORDS = ["wait", "actually", "hold on", "stop", "no,", "no ", "not quite", "thats not", "that's not", "actually,"]

def _categorize_beliefs(understanding):
    active = [b for b in understanding.beliefs if b.lifecycle.value == "active"]
    categories = {"project": [], "audience": [], "direction": [], "constraints": [], "values": []}
    for b in active:
        s = b.statement.lower()
        if any(w in s for w in ["ep", "album", "song", "track", "project", "making", "creating", "producing", "building"]):
            categories["project"].append(b)
        elif any(w in s for w in ["audience", "fans", "listeners", "target", "diaspora", "demographic"]):
            categories["audience"].append(b)
        elif any(w in s for w in ["style", "genre", "vibe", "aesthetic", "theme", "direction", "introspective", "optimism"]):
            categories["direction"].append(b)
        elif any(w in s for w in ["budget", "cost", "tight", "limited", "dollar", "deadline", "timeline", "constraint"]):
            categories["constraints"].append(b)
        elif any(w in s for w in ["authentic", "real", "genuine", "values", "goal", "vision", "ambitious"]):
            categories["values"].append(b)
        else:
            categories["project"].append(b)
    return categories


_EMOTION_WORDS = {"hope", "fear", "joy", "love", "loss", "grief", "anger", "wonder",
                  "curiosity", "nostalgia", "loneliness", "belonging", "courage",
                  "sadness", "regret", "envy", "pride", "shame", "guilt", "awe",
                  "surprise", "disgust", "excitement", "sorrow", "melancholy"}


def _build_explore_response(candidate, understanding, domain=None, intro="") -> str:
    # Emotion word follow-up — standalone, no reflection prefix
    if domain and getattr(domain, 'value', '') == 'film':
        last_obs = understanding.observations[-1].content.strip().lower() if understanding.observations else ""
        if last_obs in _EMOTION_WORDS:
            if last_obs == "hope":
                return (
                    "Hope can come from many places.\n\n"
                    "Is this hope because someone survives...\n"
                    "because someone forgives...\n"
                    "or because the future can still change?"
                )
            return f"{last_obs.title()} can come from many places.\n\nWhat kind of {last_obs} is this?"

    parts = []
    if intro:
        parts.append(intro)
    elif candidate.reflection:
        parts.append(candidate.reflection)

    if candidate.unanswered_questions:
        q = candidate.unanswered_questions[0]
        parts.append(q)

    return "\n\n".join(parts).strip()


def _build_checkpoint_response(candidate, understanding, artifact_type) -> str:
    cats = _categorize_beliefs(understanding)
    label = artifact_type.replace("_", " ").title()
    lines = ["Here is how I currently understand your project:\n"]

    if cats["project"]:
        lines.append("Project")
        for b in cats["project"]:
            lines.append(f"  {b.statement[:80]}")
        lines.append("")

    if cats["audience"]:
        lines.append("Audience")
        for b in cats["audience"]:
            lines.append(f"  {b.statement[:80]}")
        lines.append("")

    if cats["direction"]:
        lines.append("Creative Direction")
        for b in cats["direction"]:
            lines.append(f"  {b.statement[:80]}")
        lines.append("")

    if cats["constraints"]:
        lines.append("Constraints")
        for b in cats["constraints"]:
            lines.append(f"  {b.statement[:80]}")
        lines.append("")

    if candidate.unanswered_questions:
        lines.append("Still learning")
        for q in candidate.unanswered_questions[:3]:
            lines.append(f"  \u2022 {q}")
        lines.append("")

    confidence = round(candidate.confidence * 100)
    lines.append(f"Confidence: {confidence}%\n")

    lines.append(f"Is this accurate?")
    lines.append(f"")
    lines.append(f"Say **proceed** to create a {label}, or correct anything above.")

    return "\n".join(lines).strip()


def _build_interruption_response(candidate, understanding) -> str:
    lines = ["I hear you. Let me reconsider what I know.\n"]
    if candidate.reflection:
        lines.append(candidate.reflection)
    lines.append("\nI will update my understanding before we move forward.")
    return "\n".join(lines).strip()


def _build_reflect_response(candidate, understanding) -> str:
    parts = []

    if candidate.reflection:
        parts.append(candidate.reflection)

    if not candidate.is_insight:
        active = [b for b in understanding.beliefs if b.lifecycle.value == "active"]
        if active:
            parts.append("Here's what I'm hearing so far:")
            for b in active[:3]:
                s = b.statement[:70]
                parts.append(f"  \u2022 {s}")
            parts.append("")

        if candidate.unanswered_questions:
            parts.append("Does that feel right so far?")
            parts.append(candidate.unanswered_questions[0])
        else:
            parts.append("Does that feel right so far?")
    else:
        parts.append("Does that resonate?")

    return "\n".join(parts).strip()


def _build_proposal_response(candidate, understanding, artifact_type) -> str:
    label = artifact_type.replace("_", " ").title()
    lines = []
    if candidate.reflection:
        lines.append(candidate.reflection)
        lines.append("")
    lines.append(f"Based on what I'm seeing, I think a **{label}** would move things forward.")
    lines.append("")
    lines.append("Shall I go ahead and create that?")
    return "\n".join(lines).strip()


def _build_film_concept(candidate, understanding) -> str:
    beliefs = [b.statement for b in understanding.beliefs if b.lifecycle.value == "active"]
    obs = [o.content for o in understanding.observations if o.confidence >= 0.3]

    # Find the emotional core
    emotion = "hope"
    for s in obs + beliefs:
        sl = s.lower()
        for w in ["hope", "fear", "joy", "love", "loss", "loneliness", "belonging", "courage", "redemption"]:
            if w in sl:
                emotion = w
                break

    # Find the theme
    theme = "discovering what it means to feel"
    for s in obs + beliefs:
        if "future" in s.lower() or "change" in s.lower():
            theme = "hope — because the future can still change"
            break

    # Find character
    character = "A being discovering emotion for the first time"
    for s in obs + beliefs:
        if "ai" in s.lower() or "learn" in s.lower():
            character = f"An AI learning what it means to feel"
            break

    # Build from what we know
    lines = [
        "Here's the concept I'd build.",
        "",
        "━━━━━━━━━━━━━━━━━━━━",
        "",
        f"""LOGLINE
A story about {emotion} told through {character.lower()} in a world where {theme.lower()}.""",
        "",
        f"""THEME
{theme.title()}. The film explores how even a machine can learn what it means to care.""",
        "",
        f"""MAIN CHARACTER
{character}. A perspective that doesn't take humanity for granted.""",
        "",
        """WORLD
A near future where technology and humanity are no longer separate — where the line between machine and feeling has begun to blur.""",
        "",
        """THREE-ACT ARC
Act 1 — Awakening. Something new becomes aware.
Act 2 — Discovery. It learns what it means to hope.
Act 3 — Choice. It must decide what to do with what it now understands.""",
        "",
        """VISUAL STYLE
A visual poem blending cold metallic tones with warm human moments — a palette that moves from isolation toward connection.""",
        "",
        """AI GENERATION PROMPT
Cinematic shot of an awakening, warm light entering dark circuitry, soft focus, hopeful atmosphere, 35mm film grain.""",
    ]
    return "\n".join(lines).strip()


def _build_review_response() -> str:
    return (
        "Take a look.\n\n"
        "This is no longer just an idea.\n"
        "It's the beginning of a film.\n\n"
        "We've established the emotional core.\n\n"
        "From here we could:\n\n"
        "• deepen the protagonist\n"
        "• expand the world\n"
        "• build the opening scene\n\n"
        "Where would you like to go next?"
    )


class TemplateEngine(ProductionEngine):
    """Deterministic template builder. Current default production engine."""

    def generate(self, candidate, understanding, artifact_type: str = "") -> Artifact:
        body = _build_film_concept(candidate, understanding)
        return Artifact(type="film_concept", title="Film Concept", body=body)


def get_engine() -> ProductionEngine:
    engine_name = os.environ.get("PRODUCTION_ENGINE", "template")
    if engine_name == "amd":
        try:
            from core.production_amd import AMDEngine
            return AMDEngine()
        except ImportError:
            pass
    return TemplateEngine()


# -- Intent Resolution (Context-Aware Shell) ---------------------------------

class IntentResolveRequest(BaseModel):
    workspace_id: UUID
    input: str


@app.post("/intent/resolve")
def intent_resolve(req: IntentResolveRequest):
    try:
        return _resolve_intent(req)
    except Exception as e:
        print(f"[intent/resolve] Error: {e}")
        return {
            "action": "chat",
            "artifact_type": "",
            "narrative": "I hit an unexpected snag processing that. Could you rephrase or try again?",
            "requires_confirmation": False,
        }


def _resolve_intent(req: IntentResolveRequest):
    ws = workspace_service.get_workspace(req.workspace_id)
    if not ws:
        return {"action": "chat", "artifact_type": "", "narrative": "I don't see that workspace. Try creating one first.", "requires_confirmation": False}

    # Input normalization — handle typos and informal speech gracefully
    normalized = normalize_input(req.input)

    # Conversation Classifier — filter out non-project messages before any processing
    intent, _ = classify_intent(normalized)
    if not is_project_relevant(intent):
        print(f"[intent/resolve] chat_input={req.input!r} intent={intent.value}")
        return {
            "action": "chat",
            "artifact_type": "",
            "narrative": social_response(intent),
            "requires_confirmation": False,
        }

    ws_str = str(req.workspace_id)

    # Phase intercept — control signals bypass observer+reasoning entirely
    msg_lower = normalized.lower().strip()
    phase = _conversation_phase.get(ws_str, "")

    if phase == "reflect" and _is_affirmation(msg_lower):
        narrative = "Great.\n\nI think we found the heart of your story.\n\nShall I develop it into a full concept?"
        _conversation_phase[ws_str] = "propose"
        print(f"[intent/resolve] path=propose(affirmation)")
        return {"action": "ask", "artifact_type": "", "narrative": narrative, "requires_confirmation": False}

    if phase == "propose" and _is_approval(msg_lower):
        _conversation_phase[ws_str] = "complete"
        cached_u = _last_reflection_understanding.get(ws_str)
        cached_c = _reasoning_cache.get(ws_str)
        domain_check = CreativeDomain.FILM
        if cached_u:
            try:
                domain_check = CreativeDomain(cached_u.domain)
            except ValueError:
                pass
        if domain_check == CreativeDomain.FILM and cached_c and cached_u:
            engine = get_engine()
            result = engine.generate(cached_c, cached_u, "film_concept")
            concept = result.body
            review = _build_review_response()
            print(f"[intent/resolve] path=generate(approval)")
            return {"action": "generating", "artifact_type": "film_concept", "narrative": concept, "review": review, "requires_confirmation": False}
        print(f"[intent/resolve] path=generate(approval,other)")
        return {"action": "generate", "artifact_type": "launch_plan", "narrative": "Great. Let's proceed.", "requires_confirmation": False}

    # Creative Context Detection — read from persisted state, not RAM cache
    persisted = observer.get_state(ws_str)
    current_domain = CreativeDomain(persisted.domain) if persisted.domain != "unknown" else CreativeDomain.UNKNOWN
    current_activity = CreativeActivity(persisted.activity) if persisted.activity != "unknown" else CreativeActivity.UNKNOWN
    detected_domain = detect_domain(normalized, existing_domain=current_domain if current_domain != CreativeDomain.UNKNOWN else None)
    detected_activity = detect_activity(normalized)
    if detected_domain != current_domain:
        current_domain = detected_domain
    if detected_activity != current_activity:
        current_activity = detected_activity

    artifact_ids = artifact_service.list_artifacts(req.workspace_id)
    existing_types = set()
    for aid in artifact_ids:
        art = artifact_service.retrieve_artifact(aid, req.workspace_id)
        if art:
            atype = art.get("artifact_type")
            if atype:
                existing_types.add(atype)

    state = pie_engine.determine_state(existing_artifact_types=existing_types, eval_scores={})
    pie = pie_engine.analyze(
        artifact_type="launch_plan",
        existing_artifact_types=existing_types,
        eval_scores={},
    )

    # Determine the next artifact required for state transition
    next_state = state.next_state.value if state.next_state else None
    transition_artifact = None
    if next_state:
        for atype, mapping in pie_engine.state_map.items():
            if mapping["state"] == next_state and mapping["required_for_transition"]:
                if atype not in existing_types:
                    transition_artifact = atype
                    break

    profiles = profile_service.profile_engine.list_profiles()
    creator_name = profiles[-1] if profiles else "OdiBa"
    projects = workspace_service.list_projects(req.workspace_id)
    project_name = projects[0].name if projects else ws.name

    ctx = WorkspaceContext(
        current_state=state.current_state.value,
        next_state=next_state,
        transition_artifact=transition_artifact,
        existing_artifact_types=list(existing_types),
        blockers=state.blockers,
        requirements=state.requirements,
        recommended_next=pie.recommended_next,
        completed_count=len(existing_types),
        creator_name=creator_name,
        project_name=project_name,
    )

    decision = intent_engine.resolve(normalized, ctx)
    # IntentEngine output is EVIDENCE, not authority. Reasoning decides whether to generate.

    # Observer Mode — witness every shell message (pure side effect, never influences response)
    understanding = observer.observe(normalized, ws_str, domain=current_domain, activity=current_activity)

    # Shadow Reasoning — produces reflections and suggestions, never influences execution
    candidate = reasoning_engine.reason(understanding, pie_recommended=pie.recommended_next, domain=current_domain)
    _reasoning_cache[ws_str] = candidate
    print(f"[intent/resolve] input={req.input!r} normalized={normalized!r} intent={intent.value} domain={current_domain.value} activity={current_activity.value}")
    print(f"[intent/resolve] reasoning action={candidate.suggested_action!r} confidence={candidate.confidence} obs={len(understanding.observations)} beliefs={len(understanding.beliefs)}")

    # Build debug payload for every response path
    _debug = {
        "domain": current_domain.value if hasattr(current_domain, 'value') else str(current_domain),
        "activity": current_activity.value if hasattr(current_activity, 'value') else str(current_activity),
        "requirements": {r.area: r.status.value for r in understanding.requirement_states},
        "reasoning": {"action": candidate.suggested_action, "confidence": candidate.confidence},
        "belief_count": len(understanding.beliefs),
        "version": understanding.version,
    }

    # Creative Partner: decide how to respond based on cognitive state
    msg_lower = normalized.lower().strip()

    # First-ever message: warm intro + first discovery question
    if len(understanding.observations) <= 1:
        if current_domain == CreativeDomain.FILM:
            narrative = "That's exciting.\n\nBefore we talk about characters or scenes...\n\nWhat feeling do you want your audience to leave with?"
        else:
            intro = activity_intro(current_activity, current_domain, len(understanding.observations))
            if intro:
                narrative = _build_explore_response(candidate, understanding, domain=current_domain, intro=intro)
            else:
                narrative = _build_explore_response(candidate, understanding, domain=current_domain)
        print(f"[intent/resolve] path=ask(first_turn) domain={current_domain.value}")
        return {"action": "ask", "artifact_type": "", "narrative": narrative, "requires_confirmation": False, "_debug": _debug}

    # Interruption detection
    is_interruption = any(msg_lower == kw or msg_lower.startswith(kw) for kw in _INTERRUPT_KEYWORDS)

    if is_interruption:
        narrative = _build_interruption_response(candidate, understanding)
        print(f"[intent/resolve] path=reflect(interruption)")
        return {"action": "reflect", "artifact_type": "", "narrative": narrative, "requires_confirmation": False, "_debug": _debug}

    # Reasoning-owned branches
    if candidate.suggested_action in ("ask", "wait", "continue"):
        narrative = _build_explore_response(candidate, understanding, domain=current_domain)
        print(f"[intent/resolve] path=ask(reasoning) candidate_action={candidate.suggested_action}")
        return {"action": "ask", "artifact_type": "", "narrative": narrative, "requires_confirmation": False, "_debug": _debug}

    if candidate.suggested_action == "reflect":
        narrative = _build_reflect_response(candidate, understanding)
        _conversation_phase[ws_str] = "reflect"
        _last_reflection_understanding[ws_str] = understanding
        print(f"[intent/resolve] path=reflect candidate_action={candidate.suggested_action}")
        return {"action": "reflect", "artifact_type": "", "narrative": narrative, "requires_confirmation": False, "_debug": _debug}

    if candidate.suggested_action not in ("ask", "wait", "continue", "generate"):
        narrative = _build_proposal_response(candidate, understanding, candidate.suggested_action)
        print(f"[intent/resolve] path=propose artifact={candidate.suggested_action}")
        return {"action": "propose", "artifact_type": candidate.suggested_action, "narrative": narrative, "requires_confirmation": True, "_debug": _debug}

    if candidate.suggested_action == "generate":
        is_film = current_domain == CreativeDomain.FILM
        if any(w in msg_lower for w in ["generate", "create", "ready", "proceed", "go ahead", "yes", "start"]):
            if is_film:
                engine = get_engine()
                result = engine.generate(candidate, understanding, "film_concept")
                narrative = result.body
                return {
                    "action": "chat",
                    "artifact_type": "",
                    "narrative": narrative,
                    "requires_confirmation": False,
                    "_debug": _debug,
                }
            narrative = _build_explore_response(candidate, understanding, domain=current_domain)
            return {
                "action": "generate",
                "artifact_type": candidate.suggested_action,
                "narrative": narrative,
                "requires_confirmation": False,
                "_debug": _debug,
            }
        else:
            # Propose first — ask user to affirm before generating
            narrative = _build_explore_response(candidate, understanding, domain=current_domain)
            narrative += "\n\nI think I have enough to work with.\n\nShall I develop this into a full concept?"
            return {
                "action": "ask",
                "artifact_type": "",
                "narrative": narrative,
                "requires_confirmation": False,
                "_debug": _debug,
            }

    print(f"[intent/resolve] path=ask(catchall)")
    return {
        "action": "ask",
        "artifact_type": "",
        "narrative": _build_explore_response(candidate, understanding, domain=current_domain),
        "requires_confirmation": False,
        "_debug": _debug,
    }


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
    result = kernel.execute(context, artifact_type=req.artifact_type)
    data = result.model_dump() if hasattr(result, "model_dump") else dict(result)
    pie = getattr(result, "_pie_assessment", None)
    if pie:
        data["pie"] = pie.model_dump()
    eval_result = getattr(result, "_eval_assessment", None)
    if eval_result:
        data["eval"] = eval_result.model_dump()
    metrics = getattr(result, "_pipeline_metrics", None)
    if metrics:
        data["metrics"] = metrics.model_dump()
    return data


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
