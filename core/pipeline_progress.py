"""
Pipeline progress tracker.

Minimal shared state for the frontend to observe real-time
Kernel execution stages during artifact generation.

Thread-safe for demo purposes. No database, no service, no schema.
"""

_stage = ""
_progress = 0.0
_message = ""
_elapsed_ms = 0


def update(stage: str, progress: float = 0.0, message: str = "", elapsed_ms: int = 0):
    global _stage, _progress, _message, _elapsed_ms
    _stage = stage
    _progress = progress
    _message = message
    _elapsed_ms = elapsed_ms


def current() -> dict:
    return {
        "stage": _stage,
        "progress": _progress,
        "message": _message,
        "elapsed_ms": _elapsed_ms,
    }


def reset():
    update("", 0.0, "", 0)
