"""Launch MimarLLM F19 strictly on the local loopback interface."""
from __future__ import annotations

import argparse
from pathlib import Path


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="mimarllm-dashboard",
        description="Offline single-user dashboard; only local browser can access it.",
    )
    parser.add_argument("--workspace", type=Path,
                        default=Path.home() / "MimarLLM" / "workspace",
                        help="Private workspace directory on this computer")
    parser.add_argument("--port", type=int, default=8765)
    options = parser.parse_args(argv)
    if not 1024 <= options.port <= 65535:
        parser.error("Port must be between 1024 and 65535.")
    try:
        import uvicorn
        from mimarllm.app.server import create_app
    except ImportError:
        parser.error("Install the optional local dashboard dependencies: .[dashboard]")
    app = create_app(options.workspace)
    print(f"MimarLLM LOCAL ONLY: http://127.0.0.1:{options.port}")
    print("Legal compliance is LOCKED; this is a source-evidence inspection UI.")
    uvicorn.run(
        app, host="127.0.0.1", port=options.port,
        proxy_headers=False, server_header=False, access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
