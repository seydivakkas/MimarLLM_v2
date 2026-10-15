"""Windows frozen entry point. Run the actual existing dashboard, not a mock UI.

The PyInstaller onedir directory is treated as immutable code: all user
projects live under the current user's LOCALAPPDATA / home directory.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys


def default_workspace() -> Path:
    local_app = os.environ.get("LOCALAPPDATA")
    if local_app and os.name == "nt":
        base = Path(local_app)
    else:
        base = Path.home() / ".local" / "share"
    return base / "MimarLLM" / "workspace"


def main(argv: list[str] | None = None) -> int:
    from mimarllm.app.launch import main as dashboard_main

    chosen = list(sys.argv[1:] if argv is None else argv)
    # Existing launcher already constrains host to 127.0.0.1 and port 1024+.
    # Preserve its CLI. Add only a user-writable workspace if not supplied.
    if not any(arg == "--workspace" or arg.startswith("--workspace=")
               for arg in chosen):
        chosen = ["--workspace", str(default_workspace()), *chosen]
    return dashboard_main(chosen)


if __name__ == "__main__":
    raise SystemExit(main())
