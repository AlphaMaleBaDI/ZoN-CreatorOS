"""
demo_workspace.py — CreatorOS Workspace Dashboard

The primary interface for CreatorOS. No chat, no prompts, no JSON.
Just the operating system surface: identity, project, phase, work, next steps.
"""

import os
import sys
import time
from typing import Optional
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from core.pie import ProductionIntelligenceEngine
from core.schemas import ProductionState
from services.workspace_service import WorkspaceService
from services.profile_service import ProfileService
from services.artifact_service import ArtifactService

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

SEPARATOR = f"  {DIM}{'-' * 56}{RESET}"


class WorkspaceDashboard:
    """
    Assembles and renders the CreatorOS workspace surface.

    Every field is derived from existing data sources — no new storage,
    no new schemas, no new services. Pure presentation.
    """

    def __init__(self):
        self.ws_service = WorkspaceService()
        self.profile_service = ProfileService()
        self.artifact_service = ArtifactService()
        self.pie = ProductionIntelligenceEngine()

    def render(self):
        workspace, projects, creator_name, profile = self._load_identity()
        if not workspace:
            workspace, creator_name = self._create_demo_workspace()
            profile = None

        active_project = self._get_active_project(workspace.workspace_id, projects)
        artifacts = self._get_artifacts(workspace.workspace_id)
        existing_types = {a.get("artifact_type", "unknown") for a in artifacts if isinstance(a, dict)}
        state_assessment = self.pie.determine_state(existing_types, {})

        self._display(workspace, creator_name, profile, active_project, state_assessment, artifacts)

    def _load_identity(self):
        workspaces = self.ws_service.list_workspaces()
        if not workspaces:
            return None, [], None, None
        ws = workspaces[-1]
        projects = self.ws_service.list_projects(ws.workspace_id)

        profiles = self.profile_service.profile_engine.list_profiles()
        creator_name = profiles[-1] if profiles else None
        profile = self.profile_service.get_creator_profile(creator_name) if creator_name else None
        return ws, projects, creator_name, profile

    def _create_demo_workspace(self):
        ws = self.ws_service.create_workspace("ZoN Labs")
        profile_data = {
            "creator_name": "Christopher Israel Ahiome",
            "brand_voice": "Bold, introspective, Afro-futurist",
            "writing_style": "Poetic narrative",
            "goals": ["Release EP", "Build audience", "Establish brand"],
            "preferred_platforms": ["Spotify", "YouTube", "Instagram"],
            "personality": "Ardent Pulse",
            "preferred_tools": ["FL Studio", "Ableton Live"],
            "working_habits": ["Late night sessions", "Lyrics first", "Beat-driven"],
        }
        from memory.creator_profile import CreatorProfile
        profile = CreatorProfile(**profile_data)
        self.profile_service.update_creator_profile(profile)
        self.ws_service.create_project(ws.workspace_id, "Digital Diaspora")
        return ws, "Christopher Israel Ahiome"

    def _get_active_project(self, ws_id, projects):
        active = [p for p in projects if p.active]
        return active[0] if active else (projects[-1] if projects else None)

    def _get_artifacts(self, ws_id):
        ids = self.artifact_service.list_artifacts(ws_id)
        return [self.artifact_service.retrieve_artifact(aid, ws_id) for aid in ids if aid]

    def _display(self, workspace, creator_name, profile, project, state, artifacts):
        print(CLEAR, end="")
        self._header(creator_name or "Creator")
        print(SEPARATOR)
        self._identity_section(workspace, creator_name, profile)
        print(SEPARATOR)
        self._project_section(project)
        self._phase_section(state)
        self._momentum_section(state)
        print(SEPARATOR)
        self._recent_work(artifacts)
        self._recommended_section(state)
        self._footer()

    def _header(self, creator_name):
        version = "0.6.0"
        greeting = self._time_greeting()
        print()
        print(f"  {BOLD}{CYAN}CreatorOS{RESET}  {DIM}v{version}{RESET}")
        print(f"  {DIM}{greeting}, {creator_name}.{RESET}")
        print()

    @staticmethod
    def _time_greeting():
        h = time.localtime().tm_hour
        if h < 12:
            return "Good morning"
        if h < 18:
            return "Good afternoon"
        return "Good evening"

    def _identity_section(self, workspace, creator_name, profile):
        print(f"  {DIM}Workspace{RESET}")
        print(f"    {BOLD}{workspace.name}{RESET}")
        print()
        if profile:
            vibra = getattr(profile, "personality", None) or "Creative"
            brand = getattr(profile, "brand_voice", "") or ""
            print(f"  {DIM}Creator{RESET}")
            print(f"    {BOLD}{creator_name}{RESET}")
            if brand:
                print(f"    {DIM}{brand}{RESET}")
            print(f"    {DIM}Vibra:{RESET} {BOLD}{vibra}{RESET}")
            print()

    def _project_section(self, project):
        print(f"  {DIM}Project{RESET}")
        if project:
            print(f"    {BOLD}{project.name}{RESET}")
        else:
            print(f"    {DIM}No active project{RESET}")
        print()

    def _phase_section(self, state):
        phase_colors = {
            ProductionState.IDEATION: YELLOW,
            ProductionState.PLANNING: CYAN,
            ProductionState.PRODUCTION: GREEN,
            ProductionState.PUBLISHING: MAGENTA,
            ProductionState.RELEASED: GREEN,
            ProductionState.ARCHIVED: DIM,
        }
        color = phase_colors.get(state.current_state, YELLOW)
        display_name = state.current_state.value.replace("_", " ").title()

        print(f"  {DIM}Phase{RESET}")
        print(f"    {color}{BOLD}{display_name}{RESET}")
        print()

        if state.next_state:
            next_name = state.next_state.value.replace("_", " ").title()
            print(f"    {DIM}Next:{RESET} {next_name}")
            print()

    def _momentum_section(self, state):
        evidence = [e for e in state.evidence if e.exists]
        passed = len(evidence)
        next_state = state.next_state
        if next_state:
            next_artifacts = [e for e in state.evidence if not e.exists]
            total = passed + len(next_artifacts)
        else:
            total = max(passed, 1)
        ratio = passed / max(total, 1)

        bar_len = 20
        filled = int(ratio * bar_len)
        bar = f"{GREEN}{'#' * filled}{DIM}{'.' * (bar_len - filled)}{RESET}"

        print(f"  {DIM}Momentum{RESET}")
        print(f"    {bar}")
        print(f"    {BOLD}{passed}{RESET} {DIM}complete /{RESET} {total}")
        if state.can_transition:
            print(f"    {GREEN}Ready to advance +{RESET}")
        print()

    def _recent_work(self, artifacts):
        print(f"  {DIM}Recent Work{RESET}")
        if artifacts:
            for art in artifacts[-6:]:
                if isinstance(art, dict):
                    atype = art.get("artifact_type", "unknown").replace("_", " ").title()
                    print(f"    {GREEN}+{RESET} {BOLD}{atype}{RESET}")
            print()
        else:
            print(f"    {DIM}No artifacts yet.{RESET}")
            print(f"    {DIM}Start by generating a Launch Plan.{RESET}")
            print()

    def _recommended_section(self, state):
        if state.can_transition:
            print(f"  {DIM}Ready{RESET}")
            if state.next_state:
                print(f"    {GREEN}Advance to {state.next_state.value.title()} phase.{RESET}")
            print()
        elif state.blockers:
            print(f"  {DIM}Blockers{RESET}")
            for b in state.blockers:
                print(f"    {YELLOW}>{RESET} {b}")
            print()
        if state.requirements:
            print(f"  {DIM}Next Steps{RESET}")
            for r in state.requirements:
                print(f"    {CYAN}>{RESET} {r}")
            print()

    def _footer(self):
        print(SEPARATOR)
        print(f"  {DIM}Continue production:{RESET} demos/demo_kernel.py")
        print(f"  {DIM}Workspace state:{RESET} GET /workspaces/{{id}}/state")
        print()

    def wait_and_exit(self):
        try:
            input(f"  {DIM}Press Enter to refresh, Ctrl+C to exit...{RESET}")
            self.render()
            self.wait_and_exit()
        except (KeyboardInterrupt, EOFError):
            print()
            print(f"  {DIM}CreatorOS workspace closed.{RESET}")
            print()


def main():
    dashboard = WorkspaceDashboard()
    dashboard.render()
    dashboard.wait_and_exit()


if __name__ == "__main__":
    main()
