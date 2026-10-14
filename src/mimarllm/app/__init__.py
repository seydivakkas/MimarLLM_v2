"""Offline browser-based local analysis UI (optional FastAPI dependency)."""

__all__ = ["create_app"]


def create_app(workspace):
    from mimarllm.app.server import create_app as factory
    return factory(workspace)
