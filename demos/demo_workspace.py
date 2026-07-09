"""
demo_workspace.py — CreatorOS Workspace Dashboard

Mission 010: Primary interface — visual OS surface, no chat/prompts/JSON.
Mission 011: AMD Excellence — performance observability, provider intelligence,
             infrastructure awareness, production metrics.
"""

import os
import sys
import time
from uuid import UUID

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from core.pie import ProductionIntelligenceEngine
from core.schemas import ProductionState
from services.workspace_service import WorkspaceService
from services.profile_service import ProfileService
from services.artifact_service import ArtifactService

BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"

SEP = f"  {DIM}{'-' * 56}{RESET}"

PROVIDER_COLORS = {
    "ollama_cloud": CYAN,
    "nvidia": GREEN,
    "static": YELLOW,
}


class WorkspaceDashboard:
    def __init__(self):
        self.boot_time = time.perf_counter()
        self.ws_service = WorkspaceService()
        self.profile_service = ProfileService()
        self.artifact_service = ArtifactService()
        self.pie = ProductionIntelligenceEngine()

    def render(self):
        t0 = time.perf_counter()
        workspace, projects, creator_name, profile = self._load_identity()
        if not workspace:
            workspace, creator_name = self._create_demo_workspace()
            profile = None

        active_project = self._get_active_project(workspace.workspace_id, projects)
        artifacts = self._get_artifacts(workspace.workspace_id)
        existing_types = {a.get("artifact_type", "unknown") for a in artifacts if isinstance(a, dict)}
        state_assessment = self.pie.determine_state(existing_types, {})
        load_time = time.perf_counter() - t0

        print(CLEAR, end="")
        self._header(creator_name or "Creator", load_time)
        print(SEP)
        self._identity_section(workspace, creator_name, profile)
        print(SEP)
        self._infrastructure_section()
        print(SEP)
        self._project_section(active_project, state_assessment)
        self._momentum_section(state_assessment)
        print(SEP)
        self._performance_section(artifacts)
        self._recent_work(artifacts)
        self._recommended_section(state_assessment)
        self._footer()

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
        from memory.creator_profile import CreatorProfile
        profile = CreatorProfile(
            creator_name="Christopher Israel Ahiome",
            brand_voice="Bold, introspective, Afro-futurist",
            writing_style="Poetic narrative",
            goals=["Release EP", "Build audience", "Establish brand"],
            preferred_platforms=["Spotify", "YouTube", "Instagram"],
            personality="Ardent Pulse",
            preferred_tools=["FL Studio", "Ableton Live"],
            working_habits=["Late night sessions", "Lyrics first", "Beat-driven"],
        )
        self.profile_service.update_creator_profile(profile)
        self.ws_service.create_project(ws.workspace_id, "Digital Diaspora")
        return ws, "Christopher Israel Ahiome"

    @staticmethod
    def _get_active_project(ws_id, projects):
        active = [p for p in projects if p.active]
        return active[0] if active else (projects[-1] if projects else None)

    def _get_artifacts(self, ws_id):
        ids = self.artifact_service.list_artifacts(ws_id)
        return [self.artifact_service.retrieve_artifact(aid, ws_id) for aid in ids if aid]

    # -- Display sections --------------------------------------------------

    def _header(self, creator_name, load_time):
        version = "0.7.0"
        restore = load_time
        print()
        print(f"  {BOLD}{CYAN}CreatorOS{RESET}  {DIM}v{version}{RESET}")
        print(f"  {DIM}The Operating System for Creative Production{RESET}")
        print()
        print(f"  {DIM}Welcome back, {BOLD}{creator_name}{RESET}{DIM}. Your workspace is ready.{RESET}")
        print(f"  {DIM}Workspace restored in {restore:.2f}s{RESET}")
        print()

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

    def _infrastructure_section(self):
        print(f"  {DIM}Infrastructure{RESET}")
        print(f"    {GREEN}AMD{RESET} {DIM}Developer Cloud{RESET}")
        print(f"    {DIM}Persistent Workspace{RESET}")
        print()

    def _project_section(self, project, state):
        print(f"  {DIM}Project{RESET}")
        print(f"    {BOLD}{project.name if project else 'No active project'}{RESET}")
        print()

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
        if state.next_state:
            print(f"    {DIM}Next:{RESET} {state.next_state.value.title()}")
        print()

    def _momentum_section(self, state):
        required = [e for e in state.evidence if e.artifact_type in (
            t for t, m in self.pie.state_map.items() if m["required_for_transition"]
        )]
        passed = len([e for e in required if e.exists])
        total = max(len(required), 1)
        ratio = passed / total

        bar_len = 20
        filled = int(ratio * bar_len)
        bar = f"{GREEN}{'#' * filled}{DIM}{'.' * (bar_len - filled)}{RESET}"

        print(f"  {DIM}Momentum{RESET}")
        print(f"    {bar}")
        print(f"    {BOLD}{passed}{RESET} {DIM}complete /{RESET} {total}")
        if state.can_transition:
            ready_message = f"{GREEN}Ready to advance +{RESET}"
            print(f"    {ready_message}")
        print()

    def _performance_section(self, artifacts):
        valid = [a for a in artifacts if isinstance(a, dict)]
        providers = [a.get("provider", "unknown") for a in valid if a.get("provider")]
        unique_providers = list(dict.fromkeys(providers))

        confidences = [a.get("confidence") for a in valid if a.get("confidence") is not None]
        avg_conf = sum(confidences) / len(confidences) if confidences else 0

        print(f"  {DIM}Inference{RESET}")
        if unique_providers:
            for p in unique_providers:
                pc = PROVIDER_COLORS.get(p, DIM)
                count = providers.count(p)
                label = p.replace("_", " ").title()
                print(f"    {pc}{label}{RESET} {DIM}({count} call{'s' if count != 1 else ''}){RESET}")
        else:
            print(f"    {DIM}No inference history{RESET}")
        if avg_conf > 0:
            print(f"    {DIM}Avg confidence:{RESET} {BOLD}{avg_conf:.0%}{RESET}")
        print()

        if valid:
            print(f"  {DIM}Pipeline{RESET}")
            print(f"    {DIM}Artifacts:{RESET} {BOLD}{len(valid)}{RESET}")
            types = {a.get("artifact_type", "unknown") for a in valid}
            print(f"    {DIM}Types:{RESET} {BOLD}{len(types)}{RESET}")
            total_eval = sum(1 for a in valid if a.get("artifact_type") in ("launch_plan", "campaign_plan", "content_calendar"))
            print(f"    {DIM}Evaluations:{RESET} {BOLD}{total_eval}{RESET}")
            if avg_conf > 0:
                print(f"    {DIM}Avg quality:{RESET} {BOLD}{avg_conf:.0%}{RESET}")
            print()

    def _recent_work(self, artifacts):
        valid = [a for a in artifacts if isinstance(a, dict)]
        print(f"  {DIM}Recent Work{RESET}")
        if valid:
            for art in valid[-6:]:
                atype = art.get("artifact_type", "unknown").replace("_", " ").title()
                prov = art.get("provider", "")
                prov_label = f" [{prov.replace('_', ' ').title()}]" if prov else ""
                print(f"    {GREEN}+{RESET} {BOLD}{atype}{RESET}{DIM}{prov_label}{RESET}")
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
        print(SEP)
        print(f"  {DIM}Continue:{RESET} python demos/demo_kernel.py")
        print(f"  {DIM}Refresh:{RESET} Press Enter")
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
