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


def self_check() -> int:
    """Read-only local executable/import/static-assets smoke (no server launch)."""
    try:
        from importlib import metadata
        from importlib.resources import files

        for name in ("index.html", "dashboard.css", "dashboard.js"):
            asset = files("mimarllm.app").joinpath("static", name)
            content = asset.read_bytes()
            if not 0 < len(content) < 10_000_000:
                raise ValueError("Missing or oversized bundled static asset")
        from mimarllm.app.server import create_app  # noqa: F401
        import pypdfium2  # noqa: F401
        import shapely  # noqa: F401
        import rapidocr  # noqa: F401
        import onnxruntime

        try:
            metadata.version("onnxruntime-gpu")
        except metadata.PackageNotFoundError:
            pass
        else:
            raise RuntimeError("GPU ONNX Runtime wheel is not allowed for OCR CPU")
        providers = onnxruntime.get_available_providers()
        if "CPUExecutionProvider" not in providers:
            raise RuntimeError("CPUExecutionProvider is unavailable")
        print(
            "MIMARLLM_LOCAL_BUNDLE_SELF_CHECK_OK: "
            + ("FROZEN" if getattr(sys, "frozen", False) else "SOURCE")
            + "; legal compliance remains locked"
        )
        return 0
    except Exception as exc:
        print(
            "MIMARLLM_BUNDLE_INCOMPLETE: " + type(exc).__name__,
            file=sys.stderr,
        )
        return 2


def main(argv: list[str] | None = None) -> int:
    chosen = list(sys.argv[1:] if argv is None else argv)
    if chosen == ["--self-check"]:
        return self_check()
    from mimarllm.app.launch import main as dashboard_main
    # Existing launcher already constrains host to 127.0.0.1 and port 1024+.
    # Preserve its CLI. Add only a user-writable workspace if not supplied.
    if not any(arg == "--workspace" or arg.startswith("--workspace=")
               for arg in chosen):
        chosen = ["--workspace", str(default_workspace()), *chosen]
    return dashboard_main(chosen)


if __name__ == "__main__":
    raise SystemExit(main())
