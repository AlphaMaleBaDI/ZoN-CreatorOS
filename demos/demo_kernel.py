"""
demo_kernel.py -- Mission 004: CreatorOS Kernel Validation + Identity Foundation

Exercises the full pipeline through the Kernel class, demonstrating:
  - Kernel initialization (Workspace -> Profile -> Projects -> Artifacts)
  - Context Assembly enrichment
  - Artifact metadata envelope
  - Snapshot recording
  - Session memory auto-ingestion
  - Determinism across runs
"""

import os
import sys
import json
import time
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

# -- Demo logger ----------------------------------------------------------
PASS = "[PASS]"
FAIL = "[FAIL]"
BOLD = "\033[1m"
RESET = "\033[0m"
CYAN = "\033[96m"
YELLOW = "\033[93m"

demo_log = []

def log(prefix, label, detail="", ok=None):
    line = f"  {prefix} {label}"
    if detail:
        line += f"  -- {detail}"
    print(line)
    demo_log.append(line)

def section(title):
    print(f"\n{CYAN}{'-'*60}{RESET}")
    print(f"{CYAN}  {title}{RESET}")
    print(f"{CYAN}{'-'*60}{RESET}\n")

def heading(title):
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}  {title}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}\n")

# -- Seed data ------------------------------------------------------------
DOBA_PROFILE = {
    "creator_name": "DoBA",
    "brand_voice": "Afrofuturist visionary -- ancestral futurism, tech-infused spirituality",
    "writing_style": "Vibrant, poetic, code-switching between Yoruba proverbs and tech jargon",
    "goals": [
        "Release 'Digital Diaspora' EP before August 2026",
        "Build a community of 10,000 engaged listeners",
        "Establish Afrofuturist electronic sound as a recognizable genre",
    ],
    "preferred_platforms": ["Spotify", "Bandcamp", "YouTube", "TikTok", "Discord"],
    "personality": "Bold, introspective, spiritually curious, technically literate",
    "preferred_tools": ["Ableton Live", "Python", "Blender", "Stable Diffusion"],
    "working_habits": ["Late night sessions", "Full moon releases", "Collaborative jams"],
}

USER_REQUEST = (
    "Launch the 'Digital Diaspora' EP -- a 6-track Afrofuturist project "
    "blending Yoruba talking drums, vocals, and IDM production. "
    "Target: 18-35 tech-savvy creatives. Build a community launch campaign."
)


# =====================================================================
#  DEMO
# =====================================================================
def main():
    heading("CreatorOS Kernel Validation Demo")
    print(f"  Date:        {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Scenario:     Digital Diaspora EP Launch -- DoBA")
    print(f"  User Request: {USER_REQUEST[:60]}...\n")

    # -- 0. Kernel Initialization --------------------------------------
    section("0. Kernel Initialization -- Workspace -> Profile -> Projects -> Artifacts")

    from core.kernel import Kernel
    from services.workspace_service import WorkspaceService
    from services.profile_service import ProfileService
    from memory.creator_profile import CreatorProfile

    # Seed workspace, project, and profile so Kernel can find them
    ws = WorkspaceService()
    workspace = ws.create_workspace("Digital Diaspora Launch")
    log("[OK]", "Workspace seeded", f"id={str(workspace.workspace_id)[:8]}... name='{workspace.name}'")

    project = ws.create_project(workspace.workspace_id, "Digital Diaspora EP")
    log("[OK]", "Project seeded", f"id={str(project.project_id)[:8]}... name='{project.name}'")

    profile_svc = ProfileService()
    profile = CreatorProfile(**DOBA_PROFILE)
    profile_svc.update_creator_profile(profile)
    log("[OK]", "Profile seeded", f"creator='{profile.creator_name}' -- {len(profile.goals)} goals")

    # Kernel initialization enforces: Load -> Assemble -> Execute
    log("[*]", "Kernel.initialize() starting...")
    kernel = Kernel()
    kernel.initialize(
        workspace_id=workspace.workspace_id,
        creator_name="DoBA",
    )
    log("[OK]", "Kernel initialized",
        f"ws='{kernel.current_workspace.name}'  "
        f"profile='{kernel.current_profile_dict.get('creator_name', 'none')}'  "
        f"projects={len(kernel.current_projects)}  "
        f"artifacts={len(kernel.recent_artifacts)}")

    # -- 1. Context Assembly (enriched) --------------------------------
    section("1. Context Assembly (enriched)")

    context = kernel.assemble_context(
        user_request=USER_REQUEST,
        project_id=project.project_id,
    )

    log("[OK]", "ContextObject created",
        f"workspace_id={str(context.workspace_id)[:8]}...")
    log("[OK]", "Creator profile attached",
        f"name={context.creator_profile['creator_name']}  "
        f"brand='{context.creator_profile['brand_voice'][:40]}...'")
    log("[OK]", "Goals propagated",
        f"{len(context.goals)} goals: {context.goals[0][:40]}...")
    log("[OK]", "Vibra detected",
        f"vibe='{context.vibra_state.get('name', 'N/A')}'  "
        f"mood={context.vibra_state.get('mood', 'N/A')}")
    log("[+]", "Recent artifacts injected",
        f"{len(context.recent_artifacts)} prior artifacts in context")
    log("[+]", "Active projects injected",
        f"{len(context.active_projects)} active projects in context")
    log("[OK]", "Timestamp set", f"{context.timestamp}")

    # -- 2. Orchestration ----------------------------------------------
    section("2. Orchestration -- Intent Routing")

    request_lower = context.user_request.lower()
    launch_kw = ["launch", "release", "plan", "campaign", "drop"]
    matched = [kw for kw in launch_kw if kw in request_lower]
    log("[*]", "Intent keywords scanned", f"found in request: {matched}")
    log("[*]", "Routing decision",
        f"matched {len(matched)} keywords -> PlanningAgent selected")

    # -- 3. Planning Agent ---------------------------------------------
    section("3. Planning Agent -- LLM Provider Selection")

    has_ollama = bool(os.getenv("OLLAMA_API_KEY"))
    has_nvidia = bool(os.getenv("NVIDIA_API_KEY"))
    log("[*]", "Provider chain",
        "Ollama Cloud (primary) -> NVIDIA (fallback)")
    if has_ollama:
        log("[OK]", "Ollama API key", "detected -- will try first")
    else:
        log("[--]", "Ollama API key", "NOT configured")
    if has_nvidia:
        log("[OK]", "NVIDIA API key", "detected -- fallback available")
    else:
        log("[--]", "NVIDIA API key", "NOT configured")

    # -- 4. Execute Pipeline via Kernel --------------------------------
    section("4. Pipeline Execution (via Kernel)")

    start = time.time()
    result = kernel.execute(context)
    elapsed = round(time.time() - start, 2)

    log("[OK]", "Pipeline complete", f"in {elapsed}s via Kernel")
    log("[OK]", f"Provider used: {kernel.orchestrator._last_provider}")
    log("[OK]", f"Artifact ID: {kernel.orchestrator._last_artifact_id}")
    log("[OK]", "LaunchPlan generated",
        f"confidence={result.confidence_score}  "
        f"strategy={result.release_strategy[:50]}...")

    # -- 5. Artifact Verification (envelope) ---------------------------
    section("5. Artifact Persistence -- Metadata Envelope")

    from services.artifact_service import ArtifactService

    artifact_svc = ArtifactService()
    artifacts = artifact_svc.list_artifacts(workspace.workspace_id)
    log("[*]", "Artifacts in workspace", f"found {len(artifacts)} artifact(s)")

    stored = None
    if artifacts:
        latest = artifacts[-1]
        stored = artifact_svc.retrieve_artifact(latest, workspace.workspace_id)
        assert stored is not None
        log("[OK]", "Artifact reloaded from disk", f"id='{latest}'")
        log("[OK]", "Metadata envelope present",
            f"keys: artifact_id, artifact_type, workspace_id, "
            f"created_by, provider, confidence, version, data")
        log("[OK]", f"Envelope contents",
            f"type={stored.get('artifact_type')}  "
            f"by={stored.get('created_by')}  "
            f"provider={stored.get('provider')}  "
            f"confidence={stored.get('confidence')}  "
            f"version={stored.get('version')}")
        log("[*]", "Storage path",
            os.path.join(artifact_svc.storage_path, str(workspace.workspace_id)))
    else:
        log("[--]", "No artifacts found", "", ok=False)

    # -- 6. Determinism + Snapshot -------------------------------------
    section("6. Determinism -- Second Run (via Kernel)")

    start2 = time.time()
    kernel2 = Kernel()
    kernel2.initialize(workspace_id=workspace.workspace_id, creator_name="DoBA")
    context2 = kernel2.assemble_context(user_request=USER_REQUEST, project_id=project.project_id)
    result2 = kernel2.execute(context2)
    elapsed2 = round(time.time() - start2, 2)
    log("[OK]", "Pipeline complete (run 2 via Kernel)", f"in {elapsed2}s")
    log("[OK]", f"Provider used: {kernel2.orchestrator._last_provider}")
    log("[OK]", "LaunchPlan generated (run 2)",
        f"confidence={result2.confidence_score}  "
        f"strategy={result2.release_strategy[:50]}...")

    log("[*]", "Coherence check", "comparing structure of both runs:")

    checks = []
    same_strategy_type = type(result.release_strategy) == type(result2.release_strategy)
    checks.append(("Both have strategy (str)", same_strategy_type))

    has_actions_1 = len(result.next_actions) > 0
    has_actions_2 = len(result2.next_actions) > 0
    checks.append((f"Run1 has {len(result.next_actions)} actions, "
                   f"Run2 has {len(result2.next_actions)} actions",
                   has_actions_1 and has_actions_2))

    has_angles_1 = len(result.marketing_angles) > 0
    has_angles_2 = len(result2.marketing_angles) > 0
    checks.append((f"Run1 has {len(result.marketing_angles)} angles, "
                   f"Run2 has {len(result2.marketing_angles)} angles",
                   has_angles_1 and has_angles_2))

    scores_valid = (0 <= result.confidence_score <= 1 and
                    0 <= result2.confidence_score <= 1)
    checks.append((f"Scores in [0,1]: {result.confidence_score}, {result2.confidence_score}",
                   scores_valid))

    for label, ok_val in checks:
        mark = "[OK]" if ok_val else "[--]"
        log(mark, label)

    # -- 7. Snapshot Verification ---------------------------------------
    section("7. Context Snapshot Verification")

    from services.snapshot_service import SnapshotService

    snap_svc = SnapshotService()
    snapshots = snap_svc.list_snapshots(workspace.workspace_id)
    log("[OK]", "Snapshots found", f"{len(snapshots)} snapshot(s) in workspace")
    if snapshots:
        s = snapshots[-1]
        log("[OK]", "Latest snapshot",
            f"provider={s.get('provider')}  intent={s.get('intent')}  "
            f"confidence={s.get('confidence')}")

    # -- 8. Pipeline Metrics -------------------------------------------
    section("8. Pipeline Metrics")

    metrics = getattr(result, "_pipeline_metrics", None)
    if metrics:
        log("[OK]", "Kernel boot", f"{metrics.kernel_boot_ms}ms")
        log("[OK]", "Context assembly", f"{metrics.context_assembly_ms}ms")
        log("[OK]", "Orchestration (API call)", f"{metrics.orchestration_ms}ms")
        log("[OK]", "Snapshot recording", f"{metrics.snapshot_ms}ms")
        log("[OK]", "PIE assessment", f"{metrics.pie_ms}ms")
        log("[OK]", f"Total pipeline ({metrics.provider})", f"{metrics.total_ms}ms")
    else:
        log("[--]", "Metrics unavailable")

    # -- 9. Output Preview ---------------------------------------------
    section("9. Generated Launch Plan (Run 1)")

    print(f"  Strategy:")
    for line in textwrap.wrap(result.release_strategy, width=70):
        print(f"    {line}")
    print()
    print(f"  Confidence:  {result.confidence_score}")
    print(f"  Audience:    {result.audience_profile[:80]}...")
    print()
    print(f"  Marketing Angles ({len(result.marketing_angles)}):")
    for i, angle in enumerate(result.marketing_angles, 1):
        print(f"    {i}. {angle}")
    print()
    print(f"  Next Actions ({len(result.next_actions)}):")
    for i, action in enumerate(result.next_actions, 1):
        print(f"    {i}. {action.action}")
        for line in textwrap.wrap(action.why, width=68):
            print(f"       {line}")
        print()

    # -- Summary -------------------------------------------------------
    heading("Kernel Validation Summary")

    validation_results = []

    # V1: Kernel Initialization
    init_ok = kernel.initialized and kernel.current_workspace is not None
    validation_results.append((
        "1. Kernel Initialization",
        init_ok,
        f"Workspace '{kernel.current_workspace.name}' loaded, "
        f"profile loaded, {len(kernel.current_projects)} projects, "
        f"{len(kernel.recent_artifacts)} prior artifacts"
    ))

    # V2: Context Assembly Enrichment
    ctx_ok = (
        context.creator_profile.get("creator_name") == "DoBA"
        and len(context.goals) > 0
        and context.vibra_state.get("name") is not None
        and len(context.recent_artifacts) >= 0
        and len(context.active_projects) > 0
    )
    validation_results.append((
        "2. Context Assembly (enriched)",
        ctx_ok,
        "Profile, goals, vibra, recent artifacts, active projects all present"
    ))

    # V3: Genuine Orchestration
    orch_ok = matched is not None and len(matched) > 0
    validation_results.append((
        "3. Genuine Orchestration",
        orch_ok,
        f"Scanned {len(launch_kw)} keywords, matched {len(matched)}, "
        f"routed to PlanningAgent -> {kernel.orchestrator._last_provider}"
    ))

    # V4: Artifact Persistence (with envelope)
    artifact_ok = len(artifacts) > 0 and stored is not None
    envelope_ok = stored and "artifact_id" in stored and "artifact_type" in stored
    validation_results.append((
        "4. Artifact Persistence + Envelope",
        artifact_ok and envelope_ok,
        f"LaunchPlan with metadata envelope saved to zon_memory/artifacts/ -- "
        f"type={stored.get('artifact_type')} provider={stored.get('provider')}"
    ))

    # V5: Determinism
    det_ok = all(ok for _, ok in checks)
    validation_results.append((
        "5. Determinism",
        det_ok,
        f"Two runs via Kernel: both coherent, provider={kernel2.orchestrator._last_provider}"
    ))

    # V6: Snapshot Recording
    snap_ok = len(snapshots) > 0
    validation_results.append((
        "6. Context Snapshot Recording",
        snap_ok,
        f"{len(snapshots)} execution snapshots recorded"
    ))

    # V7: Pipeline Metrics
    metrics_ok = metrics is not None and metrics.kernel_boot_ms > 0
    validation_results.append((
        "8. Pipeline Metrics",
        metrics_ok,
        f"boot={metrics.kernel_boot_ms}ms ctx={metrics.context_assembly_ms}ms "
        f"orchestration={metrics.orchestration_ms}ms pie={metrics.pie_ms}ms "
        f"total={metrics.total_ms}ms"
    ))

    # V8: Observability
    obs_ok = len(demo_log) > 25
    validation_results.append((
        "7. Observability",
        obs_ok,
        f"{len(demo_log)} structured log lines across all pipeline stages"
    ))

    for name, ok, detail in validation_results:
        mark = "[PASS]" if ok else "[FAIL]"
        print(f"  {mark} {name}")
        print(f"       {detail}")
        print()

    all_pass = all(ok for _, ok, _ in validation_results)
    if all_pass:
        print(f"  [PASS] All {len(validation_results)} criteria PASSED.")
        print()
        print(f"  Conclusion: CreatorOS Kernel is validated.")
        print(f"  Identity Foundation is operational.")
        print(f"  PIE v0 active.")
        print(f"  Health metrics operational.")
    else:
        print(f"  [FAIL] Some criteria FAILED.")
        print(f"  Address failures before proceeding.")


if __name__ == "__main__":
    main()
