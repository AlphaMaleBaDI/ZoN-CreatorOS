import pytest
import time
from uuid import uuid4
from memory.creator_profile import CreatorProfile, CreatorProfileEngine
from memory.vibra_state import VibraStateEngine
from services.workspace_service import WorkspaceService
from services.memory_service import MemoryService
from services.artifact_service import ArtifactService
from core.context_assembly import ContextAssemblyEngine
from agents.orchestrator_agent import OrchestratorAgent
from artifacts.launch_plan import LaunchPlan


class TestCreatorProfileEngine:
    def test_save_and_load_profile(self, tmp_path):
        engine = CreatorProfileEngine(storage_path=str(tmp_path))
        profile = CreatorProfile(
            creator_name="TestArtist",
            brand_voice="Afrofuturist",
            writing_style="Vibrant",
            goals=["Launch album", "Grow audience"],
            preferred_platforms=["Spotify", "YouTube"],
            personality="Bold",
            preferred_tools=["Ableton", "Python"],
            working_habits=["Morning sessions"]
        )
        assert engine.save_profile(profile) is True
        loaded = engine.load_profile("TestArtist")
        assert loaded is not None
        assert loaded.creator_name == "TestArtist"
        assert loaded.brand_voice == "Afrofuturist"
        assert "Launch album" in loaded.goals

    def test_load_nonexistent_profile(self, tmp_path):
        engine = CreatorProfileEngine(storage_path=str(tmp_path))
        assert engine.load_profile("NonExistent") is None

    def test_list_profiles(self, tmp_path):
        engine = CreatorProfileEngine(storage_path=str(tmp_path))
        assert engine.list_profiles() == []
        engine.save_profile(CreatorProfile(
            creator_name="ArtistA", brand_voice="V1", writing_style="W1", personality="P1"
        ))
        engine.save_profile(CreatorProfile(
            creator_name="ArtistB", brand_voice="V2", writing_style="W2", personality="P2"
        ))
        profiles = engine.list_profiles()
        assert "artista" in profiles
        assert "artistb" in profiles


class TestWorkspaceService:
    def test_create_and_list_workspaces(self, tmp_path):
        import os
        os.environ["WORKSPACE_STORAGE_DIR"] = str(tmp_path)
        ws = WorkspaceService()
        w1 = ws.create_workspace("TestWorkspace")
        assert w1.name == "TestWorkspace"
        assert w1.workspace_id is not None
        workspaces = ws.list_workspaces()
        assert len(workspaces) == 1

    def test_create_and_list_projects(self, tmp_path):
        import os
        os.environ["WORKSPACE_STORAGE_DIR"] = str(tmp_path)
        ws = WorkspaceService()
        w = ws.create_workspace("Test")
        p = ws.create_project(w.workspace_id, "ProjectAlpha")
        assert p.name == "ProjectAlpha"
        assert p.workspace_id == w.workspace_id
        projects = ws.list_projects(w.workspace_id)
        assert len(projects) == 1

    def test_get_workspace(self, tmp_path):
        import os
        os.environ["WORKSPACE_STORAGE_DIR"] = str(tmp_path)
        ws = WorkspaceService()
        w = ws.create_workspace("FindMe")
        found = ws.get_workspace(w.workspace_id)
        assert found is not None
        assert found.name == "FindMe"


class TestVibraStateEngine:
    def test_compute_vibra(self):
        engine = VibraStateEngine()
        shift = engine.compute_vibra(
            user_prompt="Let's launch a dance party build",
            system_state={},
            memory_snapshot=[]
        )
        assert shift.active_vibe is not None
        assert 0.0 <= shift.energy_level <= 1.0
        assert "signals" in shift.model_dump()

    def test_record_shift(self):
        engine = VibraStateEngine()
        proj_id = uuid4()
        from memory.vibra_state import VibraShift
        shift = VibraShift(active_vibe="Ardent Pulse", energy_level=0.9)
        engine.record_shift(proj_id, shift)
        assert len(engine.state_history[proj_id]) == 1


class TestContextAssembly:
    def test_assemble_context_with_profile(self):
        engine = ContextAssemblyEngine()
        ws_id = uuid4()
        context = engine.assemble_context(
            workspace_id=ws_id,
            user_request="Drop a new single",
            creator_profile={"creator_name": "OdiB\u00e0", "goals": ["Release music"]}
        )
        assert context.workspace_id == ws_id
        assert context.creator_profile["creator_name"] == "OdiB\u00e0"
        assert "Release music" in context.goals
        assert context.vibra_state is not None

    def test_assemble_context_minimal(self):
        engine = ContextAssemblyEngine()
        context = engine.assemble_context(user_request="Test")
        assert context.user_request == "Test"
        assert context.vibra_state is not None


class TestArtifactService:
    def test_save_and_retrieve_artifact(self, tmp_path):
        svc = ArtifactService()
        svc.storage_path = str(tmp_path)
        ws_id = uuid4()
        data = {"plan": "test", "score": 0.85}
        assert svc.save_artifact(ws_id, "test_plan", data) is True
        retrieved = svc.retrieve_artifact("test_plan", workspace_id=ws_id)
        assert retrieved is not None
        assert retrieved["plan"] == "test"
        assert retrieved["score"] == 0.85
        listed = svc.list_artifacts(ws_id)
        assert "test_plan" in listed

    def test_list_artifacts_empty(self):
        svc = ArtifactService()
        ws_id = uuid4()
        assert svc.list_artifacts(ws_id) == []


class TestOrchestratorAgent:
    def test_routes_to_planning_agent(self):
        from core.schemas import ContextObject
        agent = OrchestratorAgent()
        context = ContextObject(
            workspace_id=uuid4(),
            user_request="Create a launch plan for a new album",
            timestamp=time.time()
        )
        result = agent.plan_execution(context)
        assert isinstance(result, LaunchPlan)

    def test_ollama_generates_launch_plan(self):
        from core.schemas import ContextObject
        agent = OrchestratorAgent()
        context = ContextObject(
            workspace_id=uuid4(),
            user_request="Plan a release for an Afrofuturist album",
            creator_profile={"creator_name": "OdiB\u00e0", "brand_voice": "Afrofuturist"},
            timestamp=time.time()
        )
        result = agent.plan_execution(context)
        assert result.release_strategy is not None
        assert len(result.release_strategy) > 10
        assert result.confidence_score is not None
