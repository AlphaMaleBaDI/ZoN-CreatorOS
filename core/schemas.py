"""ZoN CreatorOS shared schemas.

This module defines the Pydantic contracts shared by the API, the
agent framework, the dashboard, and the Adaptive Intelligence layer.
There is no logic, no I/O, and no runtime side effects here - only
data shapes.

Wire format policy:
  - Python attribute names use snake_case.
  - JSON field names on the wire use camelCase, generated automatically.
  - `to_wire(model)` returns the dict with aliases and no nulls.

The base class `CreatorOSModel` centralizes this behavior so every
schema picks it up by inheritance. New fields, new validators, and
new serialization rules should be added to the base, not to individual
models.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# camelCase alias generator (defined first because CreatorOSModel needs it)
# ---------------------------------------------------------------------------


def _to_camel(snake: str) -> str:
    """Convert a snake_case string to camelCase.

    Pydantic calls this for every field name. The leading underscore
    rule keeps dunder and private fields out of the wire format.
    """

    if snake.startswith("_"):
        return snake
    parts = snake.split("_")
    return parts[0] + "".join(p.title() for p in parts[1:])


# ---------------------------------------------------------------------------
# Base model and serialization helpers
# ---------------------------------------------------------------------------


class CreatorOSModel(BaseModel):
    """Base model for every CreatorOS contract.

    Inheriting from this class gives a model:
      - snake_case attribute names in Python
      - camelCase field names on the wire (JSON)
      - acceptance of both casings on inbound payloads
      - `to_wire()` for serializing to a clean dict with no nulls
    """

    model_config = ConfigDict(
        populate_by_name=True,
        alias_generator=_to_camel,
        frozen=False,
        extra="forbid",
    )


def to_wire(model: CreatorOSModel) -> Dict[str, Any]:
    """Serialize a model to its wire representation.

    Returns a dict with camelCase keys and `None` fields stripped. The
    `exclude_none` flag is intentional: nulls on the wire are noise for
    the agent framework and the dashboard, and the previous `zon_mcp`
    surface leaked them on every response.
    """

    return model.model_dump(by_alias=True, exclude_none=True)


# ---------------------------------------------------------------------------
# Identity and scope
# ---------------------------------------------------------------------------


class ScopeRef(CreatorOSModel):
    """Reference to a project scope.

    Every model that touches memory carries a `ScopeRef` so the memory
    engine can route reads and writes to the correct scope without
    ambient state.
    """

    scope: str = Field(default="default", min_length=1, max_length=64)

    @field_validator("scope")
    @classmethod
    def _normalize_scope(cls, value: str) -> str:
        return value.strip().lower()


# ---------------------------------------------------------------------------
# Artifact references
# ---------------------------------------------------------------------------


ArtifactKind = Literal[
    "release_plan",
    "marketing",
    "next_actions",
    "release_strategy",
    "audience_analysis",
    "memory_dump",
    "vibra_history",
]


class ArtifactRef(CreatorOSModel):
    """Pointer to a structured artifact produced by CreatorOS.

    The agent framework uses `kind` to dispatch to the right renderer.
    The dashboard uses `artifact_id` to fetch the full artifact body
    from the artifacts API. The API uses it to wire the artifact back
    into the `PromptResponse` envelope.
    """

    artifact_id: str = Field(min_length=1, max_length=128)
    kind: ArtifactKind
    scope: ScopeRef = Field(default_factory=ScopeRef)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# Memory
# ---------------------------------------------------------------------------


class MemoryEntry(CreatorOSModel):
    """A single memory record.

    Carries the topic, the body, the scope it lives in, and optional
    metadata. `vibra` and `tags` are defaulted to neutral values so the
    memory engine in M1.2 can decide how to populate them - we do not
    bake assumptions in here.
    """

    topic: str = Field(min_length=1, max_length=128)
    info: str = Field(min_length=1)
    scope: ScopeRef = Field(default_factory=ScopeRef)
    vibra: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# File and folder context (used by PromptRequest)
# ---------------------------------------------------------------------------


class FileContext(CreatorOSModel):
    name: str
    content: str
    reasoning: Optional[str] = None


class FolderContext(CreatorOSModel):
    name: str
    files: List[str]


# ---------------------------------------------------------------------------
# Prompt request and response
# ---------------------------------------------------------------------------


class PromptRequest(CreatorOSModel):
    """A user prompt bundled with everything CreatorOS needs to answer.

    The `artifact_kind` field is a hint to the intelligence layer about
    what kind of structured object, if any, the caller wants back. The
    agent framework uses it to dispatch; the API uses it to type-check
    the response.
    """

    prompt: str = Field(min_length=1)
    scope: ScopeRef = Field(default_factory=ScopeRef)
    file_context: Optional[FileContext] = None
    folder_context: Optional[FolderContext] = None
    project_context: Optional[Dict[str, Any]] = None
    dry_run: bool = False
    confirm_apply: bool = False
    artifact_kind: Optional[ArtifactKind] = None


class PromptResponse(CreatorOSModel):
    """The answer to a `PromptRequest`.

    The shape is intentionally symmetric with the request: `dry_run`
    is echoed, `applied` reports whether the change was actually
    written, and `artifact` is a first-class pointer at any structured
    object the call produced.
    """

    response: str
    scope: ScopeRef = Field(default_factory=ScopeRef)
    vibra_shift: Optional[Dict[str, Any]] = None
    artifact: Optional[ArtifactRef] = None
    memory_references: List[MemoryEntry] = Field(default_factory=list)
    dry_run: bool = False
    applied: bool = False
    diff: Optional[str] = None
    backup_path: Optional[str] = None


# ---------------------------------------------------------------------------
# Model routing surface
# ---------------------------------------------------------------------------


class ModelInfo(CreatorOSModel):
    """A single model exposed by the intelligence router."""

    model_id: str
    name: str
    source: Literal["openai", "openrouter", "localai", "amd_cloud"]
    free: bool = False
    context_window: Optional[int] = None


class ModelSwitchRequest(CreatorOSModel):
    """Request to switch the active model.

    `model_id` is required; `source` defaults to `openrouter` because
    that is the source the existing `zon_mcp` router speaks to by
    default. `amd_cloud` is included so the benchmark in M1.6 can flip
    to MI300X without a code change.
    """

    model_id: str = Field(min_length=1)
    source: Literal["openai", "openrouter", "localai", "amd_cloud"] = "openrouter"


class ModelListResponse(CreatorOSModel):
    """Response to a model listing request."""

    active_backend: str
    active_model: str
    models: List[ModelInfo] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Adaptive Intelligence - Vibra
# ---------------------------------------------------------------------------


VibraName = Literal[
    "ardent_pulse",
    "indigo_depths",
    "verdant_dawn",
    "twilight_echo",
    "etheric_matrix",
    "sacred_order",
    "steady_harmonic",
]


class VibraSnapshot(CreatorOSModel):
    """A single Vibra reading for a scope at a point in time.

    Lives in `core/schemas.py` rather than `intelligence/vibra.py`
    because the dashboard, the memory engine, the API, and the
    intelligence layer all need to import it. Putting it in `core`
    avoids a circular dependency on day one.

    The dashboard charts a time series of these; the agent framework
    conditions on `name`; the memory engine persists them alongside
    topics.
    """

    name: VibraName
    color: str = Field(pattern=r"^#[0-9A-Fa-f]{6}$")
    mood: str
    description: str
    scope: ScopeRef = Field(default_factory=ScopeRef)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = [
    "CreatorOSModel",
    "to_wire",
    "ScopeRef",
    "ArtifactKind",
    "ArtifactRef",
    "MemoryEntry",
    "FileContext",
    "FolderContext",
    "PromptRequest",
    "PromptResponse",
    "ModelInfo",
    "ModelSwitchRequest",
    "ModelListResponse",
    "VibraName",
    "VibraSnapshot",
]


if __name__ == "__main__":
    # Smoke test: construct one of each model, serialize via to_wire,
    # print the result. Verifies the alias generator and the default
    # factories without touching the network or the filesystem.
    import json

    scope = ScopeRef(scope="AfroVBra")
    artifact = ArtifactRef(artifact_id="a-001", kind="release_plan", scope=scope)
    memory = MemoryEntry(topic="audience", info="core 18-34", scope=scope, vibra="verdant_dawn")
    req = PromptRequest(prompt="plan the release", scope=scope, artifact_kind="release_plan")
    resp = PromptResponse(response="drafting...", scope=scope, artifact=artifact, memory_references=[memory], dry_run=True)
    model_info = ModelInfo(model_id="openrouter/auto", name="Auto", source="openrouter", free=True)
    switch = ModelSwitchRequest(model_id="openrouter/auto")
    listing = ModelListResponse(active_backend="openrouter", active_model="openrouter/auto", models=[model_info])
    vibra = VibraSnapshot(name="verdant_dawn", color="#50C878", mood="hopeful", description="first light", scope=scope)

    samples = {
        "scope": to_wire(scope),
        "artifact": to_wire(artifact),
        "memory": to_wire(memory),
        "request": to_wire(req),
        "response": to_wire(resp),
        "model_info": to_wire(model_info),
        "switch": to_wire(switch),
        "listing": to_wire(listing),
        "vibra": to_wire(vibra),
    }

    print(json.dumps(samples, indent=2, default=str))
