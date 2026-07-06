import os
import json
import logging
from typing import Optional, Any, List
from uuid import UUID, uuid4
from dotenv import load_dotenv
from core.schemas import WorkspaceScope, ProjectScope

load_dotenv()
logger = logging.getLogger(__name__)

class WorkspaceService:
    def __init__(self, db_client: Optional[Any] = None):
        self.db_client = db_client
        storage_dir = os.getenv("WORKSPACE_STORAGE_DIR", "./workspace_db")
        self.storage_path = os.path.abspath(storage_dir)
        os.makedirs(self.storage_path, exist_ok=True)
        self._workspaces: dict[UUID, WorkspaceScope] = {}
        self._projects: dict[UUID, list[ProjectScope]] = {}
        self._load()

    def _workspace_file(self):
        return os.path.join(self.storage_path, "workspaces.json")

    def _project_file(self):
        return os.path.join(self.storage_path, "projects.json")

    def _load(self):
        wf = self._workspace_file()
        if os.path.exists(wf):
            try:
                with open(wf, "r") as f:
                    for item in json.load(f):
                        ws = WorkspaceScope(**item)
                        self._workspaces[ws.workspace_id] = ws
            except Exception as e:
                logger.warning(f"Failed to load workspaces: {e}")
        pf = self._project_file()
        if os.path.exists(pf):
            try:
                with open(pf, "r") as f:
                    for ws_id_str, projs in json.load(f).items():
                        self._projects[UUID(ws_id_str)] = [ProjectScope(**p) for p in projs]
            except Exception as e:
                logger.warning(f"Failed to load projects: {e}")

    def _save_workspaces(self):
        with open(self._workspace_file(), "w") as f:
            json.dump([w.model_dump() for w in self._workspaces.values()], f, indent=4, default=str)

    def _save_projects(self):
        data = {str(ws_id): [p.model_dump() for p in projs]
                for ws_id, projs in self._projects.items()}
        with open(self._project_file(), "w") as f:
            json.dump(data, f, indent=4, default=str)

    def create_workspace(self, name: str) -> WorkspaceScope:
        ws = WorkspaceScope(name=name)
        self._workspaces[ws.workspace_id] = ws
        self._projects[ws.workspace_id] = []
        self._save_workspaces()
        self._save_projects()
        logger.info(f"Workspace created: {ws.workspace_id} - {name}")
        return ws

    def list_projects(self, workspace_id: UUID) -> List[ProjectScope]:
        return self._projects.get(workspace_id, [])

    def create_project(self, workspace_id: UUID, name: str) -> ProjectScope:
        proj = ProjectScope(workspace_id=workspace_id, name=name)
        self._projects.setdefault(workspace_id, []).append(proj)
        self._save_projects()
        logger.info(f"Project created: {proj.project_id} - {name}")
        return proj

    def get_workspace(self, workspace_id: UUID) -> Optional[WorkspaceScope]:
        return self._workspaces.get(workspace_id)

    def list_workspaces(self) -> List[WorkspaceScope]:
        return list(self._workspaces.values())
