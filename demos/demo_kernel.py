"""
demo_kernel.py — CreatorOS Hackathon Demo

6-act product experience for the AMD Act II Hackathon.
Not a technical validation — a story about a creative operating system.
"""

import os
import sys
import time
import textwrap
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

# -- Console styling ---------------------------------------------------------
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"

def speak(text, delay=0.02):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

def header(text):
    print(f"\n{BOLD}{text}{RESET}")

def dim(text):
    print(f"{DIM}{text}{RESET}")

def ok(text):
    print(f"  {GREEN}+{RESET} {text}")

def line():
    print(f"  {DIM}{'-' * 56}{RESET}")

def gap():
    print()

def pause(sec=0.8):
    time.sleep(sec)

# -- Seed data ---------------------------------------------------------------
DOBA_PROFILE = {
    "creator_name": "DoBA",
    "brand_voice": "Afrofuturist visionary — ancestral futurism, tech-infused spirituality",
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
    "Launch the 'Digital Diaspora' EP — a 6-track Afrofuturist project "
    "blending Yoruba talking drums, vocals, and IDM production. "
    "Target: 18-35 tech-savvy creatives. Build a community launch campaign."
)

# -- Pipeline runner with live progress --------------------------------------
def run_pipeline(kernel, context, result_holder):
    result_holder["result"] = kernel.execute(context)
    result_holder["done"] = True

def show_pipeline_progress(kernel, context, result_holder, provider_name):
    thread = threading.Thread(target=run_pipeline, args=(kernel, context, result_holder))
    thread.start()
    stages = [
        ("Context Assembly", "Assembling creator context..."),
        ("Orchestrator", "Scanning intent... matched 'launch', 'campaign'"),
        ("Planning Agent", f"Calling {provider_name}..."),
        ("Artifact", "Saving to workspace..."),
    ]
    for name, desc in stages:
        print(f"  [{DIM} {RESET}] {name}", end="\r")
        time.sleep(0.3)
        print(f"  [{YELLOW}*{RESET}] {name}  {DIM}{desc}{RESET}", end="\r")
        if name == "Planning Agent":
            start_wait = time.time()
            while not result_holder.get("done"):
                elapsed = int(time.time() - start_wait)
                print(f"  [{YELLOW}*{RESET}] Planning Agent  {DIM}Calling {provider_name}... ({elapsed}s){RESET}", end="\r")
                time.sleep(0.5)
            elapsed = int(time.time() - start_wait)
            print(f"  [{GREEN}+{RESET}] Planning Agent  {DIM}Response received ({elapsed}s){RESET}")
        else:
            time.sleep(0.5)
            print(f"  [{GREEN}+{RESET}] {name}  {DIM}{desc}{RESET}")
        time.sleep(0.4)
    thread.join()


def main():
    # =====================================================================
    #  ACT I — AWAKENING
    # =====================================================================
    print(CLEAR, end="")
    gap()
    gap()
    speak(f"  {BOLD}{CYAN}CreatorOS v0.3.0{RESET}", delay=0.04)
    gap()
    pause(0.5)

    dim("  Initializing Kernel...")
    pause(0.3)

    from core.kernel import Kernel
    from services.workspace_service import WorkspaceService
    from services.profile_service import ProfileService
    from memory.creator_profile import CreatorProfile

    ws = WorkspaceService()
    workspace = ws.create_workspace("Digital Diaspora Launch")
    project = ws.create_project(workspace.workspace_id, "Digital Diaspora EP")
    profile_svc = ProfileService()
    profile_svc.update_creator_profile(CreatorProfile(**DOBA_PROFILE))

    ok("Workspace loaded")
    pause(0.2)
    ok("Creator profile loaded")
    pause(0.2)

    dim("Restoring Production Context...")
    pause(0.4)

    kernel = Kernel()
    kernel.initialize(workspace_id=workspace.workspace_id, creator_name="DoBA")
    pause(0.3)

    temp_ctx = kernel.context_engine.assemble_context(
        workspace_id=workspace.workspace_id,
        user_request="test",
        creator_profile=kernel.current_profile_dict,
        recent_artifacts=[],
        active_projects=[],
    )
    vibra_name = temp_ctx.vibra_state.get("name", "Ardent Pulse")
    vibra_mood = temp_ctx.vibra_state.get("mood", "energetic")
    ok(f"Vibra detected — {vibra_name} ({vibra_mood})")
    pause(0.3)

    gap()
    header("Context Assembly Complete.")
    gap()
    pause(1.0)

    # =====================================================================
    #  ACT II — IDENTITY
    # =====================================================================
    print(CLEAR, end="")
    gap()
    header(f"  {CYAN}Creator{RESET}")
    gap()
    dim(f"  {DOBA_PROFILE['creator_name']}")
    dim(f"  {DOBA_PROFILE['brand_voice']}")
    gap()
    dim(f"  Workspace")
    dim(f"  Digital Diaspora")
    gap()
    dim(f"  Goals")
    for g in DOBA_PROFILE["goals"]:
        dim(f"    > {g}")
    gap()
    dim(f"  Vibra State")
    dim(f"  {vibra_name}  —  {vibra_mood}")
    gap()
    pause(1.0)

    # =====================================================================
    #  ACT III — INTELLIGENCE
    # =====================================================================
    print(CLEAR, end="")
    gap()
    header(f"  {YELLOW}Request{RESET}")
    gap()
    dim(f"  \"{USER_REQUEST}\"")
    gap()
    pause(0.5)

    header(f"  Pipeline")
    gap()

    context = kernel.assemble_context(
        user_request=USER_REQUEST,
        project_id=project.project_id,
    )

    has_ollama = bool(os.getenv("OLLAMA_API_KEY"))
    has_nvidia = bool(os.getenv("NVIDIA_API_KEY"))
    provider_name = "Ollama Cloud"
    if has_nvidia:
        provider_name += " (fallback: NVIDIA)"

    result_holder = {"done": False, "result": None}
    show_pipeline_progress(kernel, context, result_holder, provider_name)
    result = result_holder["result"]
    gap()
    pause(0.5)

    gap()
    line()
    dim(f"  Provider:  {kernel.orchestrator._last_provider}")
    dim(f"  Strategy:  {result.release_strategy[:80].strip()}...")
    dim(f"  Confidence: {result.confidence_score:.0%}")
    line()

    gap()
    dim(f"  Marketing Angles ({len(result.marketing_angles)})")
    for i, angle in enumerate(result.marketing_angles[:3], 1):
        dim(f"    {i}. {angle[:70]}...")
    if len(result.marketing_angles) > 3:
        dim(f"    ... and {len(result.marketing_angles) - 3} more")
    gap()
    pause(1.0)

    # =====================================================================
    #  ACT IV — PRODUCTION INTELLIGENCE
    # =====================================================================
    print(CLEAR, end="")
    gap()
    header(f"  {MAGENTA}Production Intelligence{RESET}")
    gap()

    pie = getattr(result, "_pie_assessment", None)
    if pie:
        # State badge
        state_colors = {"planning": YELLOW, "production": CYAN, "review": GREEN, "publishing": MAGENTA, "completed": GREEN}
        sc = state_colors.get(pie.production_state, YELLOW)
        dim(f"  State")
        print(f"  {BOLD}{sc}{pie.production_state.upper()}{RESET}")
        gap()

        bar_len = 20
        filled = int(pie.production_progress * bar_len)
        bar = f"{GREEN}{'#' * filled}{DIM}{'.' * (bar_len - filled)}{RESET}"
        dim(f"  Progress")
        print(f"  {bar}  {BOLD}{pie.production_progress:.0%}{RESET}")
        gap()

        dim(f"  Completed  ({len(pie.completed)})")
        for item in pie.completed:
            ok(item)
        gap()

        dim(f"  Missing  ({len(pie.missing)})")
        for item in pie.missing:
            print(f"    {DIM}-{RESET} {item}")
        gap()

        dim(f"  Recommended Next")
        for item in pie.recommended_next:
            print(f"    {BOLD}>{RESET} {item}")
        gap()
    pause(1.0)

    # =====================================================================
    #  ACT V — EVALUATION
    # =====================================================================
    print(CLEAR, end="")
    gap()
    header(f"  {CYAN}Evaluation{RESET}")
    gap()

    eval_result = getattr(result, "_eval_assessment", None)
    if eval_result:
        score_pct = int(eval_result.score * 100)
        stars_full = score_pct // 20
        stars_empty = 5 - stars_full
        print(f"  Score  {BOLD}{score_pct}{RESET} / 100")
        print(f"  {'*' * stars_full}{DIM}{'.' * stars_empty}{RESET}")
        gap()

        passed = sum(1 for c in eval_result.checks if c.passed)
        total = len(eval_result.checks)
        print(f"  Checks  {BOLD}{passed}{RESET} / {total}  passed")
        gap()

        for check in eval_result.checks:
            mark = f"{GREEN}+{RESET}" if check.passed else f"{RED}o{RESET}"
            print(f"  {mark}  {check.name}")

        gap()
        if eval_result.recommendations:
            dim("  Recommendation")
            for rec in eval_result.recommendations:
                dim(f"    {rec}")
            gap()
            dim("  Status")
            if eval_result.status == "ready":
                ok("Proceed to next production step")
            elif eval_result.status == "needs_revision":
                dim("  Revise before continuing")
            else:
                dim("  Complete core sections first")
    gap()
    pause(1.0)

    # =====================================================================
    #  ACT VI — CONTINUITY
    # =====================================================================
    print(CLEAR, end="")
    gap()
    dim("  CreatorOS shutting down...")
    pause(0.6)
    ok("State persisted.")
    pause(0.4)
    dim("  Memory saved.")
    pause(0.3)
    dim("  Snapshots recorded.")
    pause(0.3)
    gap()
    pause(0.8)

    print(CLEAR, end="")
    gap()
    speak(f"  {BOLD}{CYAN}CreatorOS v0.3.0{RESET}", delay=0.04)
    gap()
    pause(0.4)

    dim("  Booting...")
    pause(0.5)

    kernel2 = Kernel()
    kernel2.initialize(workspace_id=workspace.workspace_id, creator_name="DoBA")
    pause(0.3)

    ok("Workspace restored")
    dim(f"     1 Project  —  Digital Diaspora EP")
    pause(0.2)

    from services.artifact_service import ArtifactService
    artifact_svc = ArtifactService()
    artifact_ids = artifact_svc.list_artifacts(workspace.workspace_id)
    dim(f"     {len(artifact_ids)} Launch Plan  —  Ready for review")
    pause(0.2)

    if pie:
        print(f"     Production State  —  {BOLD}{pie.production_state.upper()}{RESET}")
        print(f"     Progress  —  {BOLD}{pie.production_progress:.0%}{RESET}")
    pause(0.4)
    gap()
    pause(1.2)

    # =====================================================================
    #  CLOSING
    # =====================================================================
    print(CLEAR, end="")
    gap()
    pause(0.5)
    speak(f"  {DIM}{'-' * 50}{RESET}", delay=0.01)
    pause(0.3)
    speak(f"  {DIM}Traditional AI remembers prompts.{RESET}", delay=0.03)
    speak(f"  {BOLD}{GREEN}CreatorOS remembers creators.{RESET}", delay=0.03)
    gap()
    speak(f"  {DIM}Traditional AI answers questions.{RESET}", delay=0.03)
    speak(f"  {BOLD}{GREEN}CreatorOS advances production.{RESET}", delay=0.03)
    gap()
    speak(f"  {DIM}Traditional AI starts over every session.{RESET}", delay=0.03)
    speak(f"  {BOLD}{GREEN}CreatorOS continues where you left off.{RESET}", delay=0.03)
    pause(0.5)
    speak(f"  {DIM}{'-' * 50}{RESET}", delay=0.01)
    gap()
    pause(0.6)
    print(f"  {BOLD}{CYAN}CreatorOS{RESET}")
    speak(f"  {DIM}The Operating System for Creative Production.{RESET}", delay=0.02)
    gap()
    gap()


if __name__ == "__main__":
    main()
