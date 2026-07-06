import os
import json
import time
import logging
from typing import Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class SnapshotService:
    """
    Records lightweight execution snapshots — not artifacts, not memory,
    but a durable trace of every pipeline execution for analytics,
    evaluation, and timeline visualization.
    """

    def __init__(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.storage_path = os.path.join(base, "zon_memory", "snapshots")
        os.makedirs(self.storage_path, exist_ok=True)

    def record(
        self,
        workspace_id: UUID,
        creator_name: Optional[str],
        project_id: Optional[UUID],
        artifact_id: Optional[str],
        artifact_type: str,
        provider: Optional[str],
        intent: str,
        confidence: Optional[float],
    ) -> dict:
        snapshot = {
            "workspace_id": str(workspace_id),
            "creator": creator_name,
            "project_id": str(project_id) if project_id else None,
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "timestamp": time.time(),
            "provider": provider,
            "intent": intent,
            "confidence": confidence,
        }
        ws_dir = os.path.join(self.storage_path, str(workspace_id))
        os.makedirs(ws_dir, exist_ok=True)
        filename = f"snap_{int(time.time())}.json"
        filepath = os.path.join(ws_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=4)
        logger.info(f"Snapshot recorded: {filename}")
        return snapshot

    def list_snapshots(self, workspace_id: UUID) -> list:
        ws_dir = os.path.join(self.storage_path, str(workspace_id))
        if not os.path.exists(ws_dir):
            return []
        snapshots = []
        for fname in sorted(os.listdir(ws_dir)):
            if fname.endswith(".json"):
                with open(os.path.join(ws_dir, fname), "r") as f:
                    snapshots.append(json.load(f))
        return snapshots
