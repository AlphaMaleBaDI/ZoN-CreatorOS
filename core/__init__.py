"""ZoN CreatorOS core package.

The `core` package holds the shared contracts every other layer in
CreatorOS depends on. Today it contains only Pydantic schemas; future
modules that need a stable home (orchestration, request lifecycle,
telemetry) can land here too, but only if they are referenced by more
than one other layer.
"""
