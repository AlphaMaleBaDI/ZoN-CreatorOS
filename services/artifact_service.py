import os
import json
import logging
from typing import Optional, Any
from uuid import UUID

logger = logging.getLogger(__name__)

class ArtifactService:
    def __init__(self, storage_client: Optional[Any] = None):
        self.storage_client = storage_client
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_path = os.path.join(base, "zon_memory", "artifacts")
        os.makedirs(self.storage_path, exist_ok=True)

    def retrieve_artifact(self, artifact_id: str, workspace_id: Optional[UUID] = None) -> Optional[Any]:
        if workspace_id:
            filepath = os.path.join(self.storage_path, str(workspace_id), f"{artifact_id}.json")
        else:
            filepath = os.path.join(self.storage_path, f"{artifact_id}.json")
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to retrieve artifact '{artifact_id}': {e}")
            return None

    def save_artifact(self, workspace_id: UUID, artifact_id: str, artifact_data: Any) -> bool:
        ws_dir = os.path.join(self.storage_path, str(workspace_id))
        os.makedirs(ws_dir, exist_ok=True)
        filepath = os.path.join(ws_dir, f"{artifact_id}.json")
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(artifact_data, f, indent=4, default=str)
            logger.info(f"Artifact saved: {artifact_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save artifact '{artifact_id}': {e}")
            return False

    def list_artifacts(self, workspace_id: UUID) -> list:
        ws_dir = os.path.join(self.storage_path, str(workspace_id))
        if not os.path.exists(ws_dir):
            return []
        return [f.replace(".json", "") for f in os.listdir(ws_dir) if f.endswith(".json")]
