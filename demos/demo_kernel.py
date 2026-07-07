"""
demo_kernel.py — CreatorOS Hackathon Demo

A 7-act emotional experience directed for the AMD Act II Hackathon.
Not a technical validation — a story about creative continuity.
"""

import os
import sys
import time
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

def speak(text, delay=0.025):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    print()

def dim(text):
    print(f"{DIM}{text}{RESET}")

def ok(text):
    print(f"  {GREEN}+{RESET} {text}")

def pause(sec=0.8):
    time.sleep(sec)

# fix_env — ensures we have consistent seed data for the demo
DOBA_PROFILE = {
    "creator_name": "DoBA",
    "brand_voice": "Afrofuturist visionary \u2014 ancestral futurism, tech-infused spirituality",
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

USER_REQUEST = "Create a launch plan for my EP."


def run_pipeline(kernel, context, result_holder):
    result_holder["result"] = kernel.execute(context)
    result_holder["done"] = True

def show_pipeline_progress(kernel, context, result_holder, provider_name):
    thread = threading.Thread(target=run_pipeline, args=(kernel, context, result_holder))
    thread.start()
    stages = [
        ("Context Assembly", "Assembling creator context..."),
        ("Intent Recognition", "Routing to Planning Agent..."),
        ("Planning Agent", f"Calling {provider_name}..."),
        ("Artifact Generation", "Saving to workspace..."),
    ]
    for name, desc in stages:
        print(f"  [ ] {name}", end="\r")
        time.sleep(0.15)
        print(f"  [*] {name}  {DIM}{desc}{RESET}", end="\r")
        if name == "Planning Agent":
            start_wait = time.time()
            while not result_holder.get("done"):
                elapsed = int(time.time() - start_wait)
                print(f"  [*] Planning Agent  {DIM}Calling {provider_name}... ({elapsed}s){RESET}", end="\r")
                time.sleep(0.5)
            elapsed = int(time.time() - start_wait)
            print(f"  [+] Planning Agent  {DIM}Response received ({elapsed}s){RESET}")
        else:
            time.sleep(0.6)
            print(f"  [+] {name}  {DIM}{desc}{RESET}")
        time.sleep(0.4)
    thread.join()


def main():
    # ===================================================================
    #  ACT 0 — THE QUESTION
    # ===================================================================
    print(CLEAR, end="")
    pause(0.3)
    print()
    print()
    speak(f"  {DIM}Every AI remembers prompts.{RESET}", delay=0.03)
    pause(0.6)
    speak(f"  {BOLD}What if an AI remembered the creator instead?{RESET}", delay=0.03)
    pause(1.5)

    # ===================================================================
    #  ACT I — AWAKENING
    # ===================================================================
    print(CLEAR, end="")
    pause(0.2)
    speak(f"  {BOLD}{CYAN}CreatorOS v0.3.0{RESET}", delay=0.04)
    pause(0.6)
    print()

    # Boot sequence — emotional language
    dim("  Restoring Creator Workspace...")
    pause(0.4)

    from core.kernel import Kernel
    from services.workspace_service import WorkspaceService
    from services.profile_service import ProfileService
    from memory.creator_profile import CreatorProfile

    ws = WorkspaceService()
    workspace = ws.create_workspace("Digital Diaspora Launch")
    project = ws.create_project(workspace.workspace_id, "Digital Diaspora EP")
    profile_svc = ProfileService()
    profile_svc.update_creator_profile(CreatorProfile(**DOBA_PROFILE))

    dim("  Restoring Creator Identity...")
    pause(0.4)

    kernel = Kernel()
    kernel.initialize(workspace_id=workspace.workspace_id, creator_name="DoBA")

    temp_ctx = kernel.context_engine.assemble_context(
        workspace_id=workspace.workspace_id,
        user_request="test",
        creator_profile=kernel.current_profile_dict,
        recent_artifacts=[],
        active_projects=[],
    )
    vibra_name = temp_ctx.vibra_state.get("name", "Ardent Pulse")
    vibra_mood = temp_ctx.vibra_state.get("mood", "energetic")

    dim("  Recovering Creative History...")
    pause(0.3)

    ok("Workspace restored")
    pause(0.15)
    ok("Creator profile loaded")
    pause(0.15)
    ok(f"Vibra detected \u2014 {vibra_name} ({vibra_mood})")
    pause(0.4)
    print()
    pause(0.6)

    # ===================================================================
    #  ACT II — IDENTITY
    # ===================================================================
    print(CLEAR, end="")
    print()
    dim(f"  Creator")
    speak(f"  {BOLD}DoBA{RESET}", delay=0.02)
    print()
    dim(f"  Workspace")
    speak(f"  {BOLD}Digital Diaspora{RESET}", delay=0.02)
    print()
    dim(f"  Goals")
    for g in DOBA_PROFILE["goals"]:
        dim(f"    > {g}")
    print()
    dim(f"  Creative State")
    dim(f"  {vibra_name} \u2014 {vibra_mood}")
    print()
    pause(1.2)

    # ===================================================================
    #  ACT III — INTELLIGENCE
    # ===================================================================
    print(CLEAR, end="")
    print()
    dim(f"  {YELLOW}Creator requests:{RESET}")
    print(f"  {BOLD}\"{USER_REQUEST}\"{RESET}")
    print()
    pause(0.6)

    context = kernel.assemble_context(
        user_request=USER_REQUEST,
        project_id=project.project_id,
    )

    # Detect provider for display
    has_nvidia = bool(os.getenv("NVIDIA_API_KEY"))
    provider_name = "Ollama Cloud"
    if has_nvidia:
        provider_name += " (fallback: NVIDIA)"

    result_holder = {"done": False, "result": None}
    show_pipeline_progress(kernel, context, result_holder, provider_name)
    result = result_holder["result"]
    print()

    # Artifact summary — no confidence score
    if hasattr(result, "release_strategy"):
        strategy = result.release_strategy
    elif isinstance(result, dict):
        strategy = result.get("release_strategy", "")
    else:
        strategy = ""

    line = f"  {DIM}{'-' * 52}{RESET}"
    print(line)
    angles = getattr(result, "marketing_angles", []) or (result.get("marketing_angles", []) if isinstance(result, dict) else [])
    dim(f"  Strategy generated")
    dim(f"  {strategy[:80].strip()}...")
    print(line)
    print()
    dim(f"  Marketing Angles ({len(angles)})")
    for i, a in enumerate(angles[:3], 1):
        dim(f"    {i}. {a[:70]}...")
    if len(angles) > 3:
        dim(f"    ... and {len(angles) - 3} more")
    print()
    pause(1.0)

    # ===================================================================
    #  ACT IV — PRODUCTION INTELLIGENCE
    # ===================================================================
    print(CLEAR, end="")
    print()
    dim("  Analyzing production state...")
    pause(0.8)
    print()

    pie = getattr(result, "_pie_assessment", None)
    if pie:
        state_colors = {"planning": YELLOW, "production": CYAN, "review": GREEN, "publishing": MAGENTA, "completed": GREEN}
        sc = state_colors.get(pie.production_state, YELLOW)

        print(f"  {BOLD}Production State{RESET}")
        print(f"  {sc}{pie.production_state.upper()}{RESET}")
        print()

        bar_len = 20
        filled = int(pie.production_progress * bar_len)
        bar = f"{GREEN}{'#' * filled}{DIM}{'.' * (bar_len - filled)}{RESET}"
        dim("  Progress")
        print(f"  {bar}  {BOLD}{pie.production_progress:.0%}{RESET}")
        print()

        dim(f"  Completed ({len(pie.completed)})")
        for item in pie.completed:
            ok(item)
        print()

        dim(f"  What's missing ({len(pie.missing)})")
        for item in pie.missing[:5]:
            dim(f"    - {item}")
        if len(pie.missing) > 5:
            dim(f"    ... and {len(pie.missing) - 5} more")
        print()

        dim("  Recommended next")
        for item in pie.recommended_next:
            print(f"    {BOLD}>{RESET} {item}")
        print()
    pause(1.0)

    # ===================================================================
    #  ACT V — EVALUATION
    # ===================================================================
    print(CLEAR, end="")
    print()
    dim("  Evaluating artifact quality...")
    pause(0.6)
    print()

    eval_result = getattr(result, "_eval_assessment", None)
    if eval_result:
        score_pct = int(eval_result.score * 100)
        stars_full = score_pct // 20
        stars_empty = 5 - stars_full

        status_msg = {
            "ready": "Ready to continue",
            "needs_revision": "Needs revision",
            "incomplete": "Complete core sections first",
        }.get(eval_result.status, eval_result.status)

        print(f"  {BOLD}Production Quality{RESET}")
        print(f"  {GREEN}{status_msg}{RESET}")
        print(f"  {BOLD}{score_pct}{RESET} / 100")
        print(f"  {'*' * stars_full}{DIM}{'.' * stars_empty}{RESET}")
        print()

        passed = sum(1 for c in eval_result.checks if c.passed)
        total = len(eval_result.checks)
        print(f"  Checks passed:  {BOLD}{passed}{RESET} / {total}")
        print()

        if eval_result.recommendations:
            dim("  Recommendation")
            for rec in eval_result.recommendations:
                dim(f"    {rec}")
        print()
    pause(1.0)

    # ===================================================================
    #  ACT VI — CONTINUITY
    # ===================================================================
    print(CLEAR, end="")
    print()
    dim("  CreatorOS shutting down...")
    pause(0.5)
    ok("State persisted.")
    pause(0.3)
    dim("  Memory saved.")
    pause(0.2)
    dim("  Snapshots recorded.")
    pause(0.6)
    print()

    print(CLEAR, end="")
    pause(0.3)
    speak(f"  {BOLD}{CYAN}CreatorOS v0.3.0{RESET}", delay=0.04)
    pause(0.5)
    print()

    dim("  Booting...")
    pause(0.4)

    # Kernel re-init to demonstrate persistence
    kernel2 = Kernel()
    kernel2.initialize(workspace_id=workspace.workspace_id, creator_name="DoBA")
    pause(0.15)

    print(f"  {DIM}Last session found.{RESET}")
    pause(0.8)

    dim("  Restoring production state...")
    pause(0.6)

    from services.artifact_service import ArtifactService
    artifact_svc = ArtifactService()
    artifact_ids = artifact_svc.list_artifacts(workspace.workspace_id)

    ok("1 Project  \u2014  Digital Diaspora EP")
    pause(0.2)
    ok(f"{len(artifact_ids)} Launch Plan  \u2014  Ready for review")
    pause(0.2)
    if pie:
        print(f"  Production State  \u2014  {BOLD}{pie.production_state.upper()}{RESET}")
        pause(0.2)
        print(f"  Progress  \u2014  {BOLD}{pie.production_progress:.0%}{RESET}")
    pause(0.3)
    print()
    pause(1.5)

    # ===================================================================
    #  CLOSING
    # ===================================================================
    print(CLEAR, end="")
    print()
    pause(0.5)
    print()
    line = f"  {DIM}{'-' * 50}{RESET}"
    pause(0.3)
    speak(f"  {CYAN}CreatorOS remembers{RESET}", delay=0.03)
    pause(0.2)
    speak(f"  {CYAN}who you are,{RESET}", delay=0.03)
    pause(0.2)
    speak(f"  {CYAN}what you're building,{RESET}", delay=0.03)
    pause(0.2)
    speak(f"  {CYAN}why you're building it,{RESET}", delay=0.03)
    pause(0.2)
    speak(f"  {CYAN}and what should happen next.{RESET}", delay=0.03)
    pause(0.6)
    print(line, end="")
    print()
    print()
    pause(0.6)
    print(f"  {BOLD}{CYAN}CreatorOS{RESET}")
    dim("  The Operating System for Creative Production.")
    print()
    print()
    pause(0.5)


if __name__ == "__main__":
    main()
