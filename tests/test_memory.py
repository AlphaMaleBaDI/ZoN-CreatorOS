import pytest
from uuid import uuid4
from core.schemas import WorkspaceScope, ProjectScope, MemoryScope

def test_scope_hierarchy():
    ws_id = uuid4()
    proj_id = uuid4()
    
    workspace = WorkspaceScope(workspace_id=ws_id, name="TestWorkspace")
    project = ProjectScope(project_id=proj_id, workspace_id=ws_id, name="TestProject")
    memory_scope = MemoryScope(workspace_id=ws_id, project_id=proj_id, tags=["test"])

    assert workspace.workspace_id == ws_id
    assert project.workspace_id == ws_id
    assert memory_scope.project_id == proj_id
    assert "test" in memory_scope.tags
