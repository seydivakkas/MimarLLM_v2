"""Run installed Windows Microsoft Edge headless against the actual local dashboard.

CI smoke only: NOT an independent physical Windows user-acceptance test.
No downloads, public addresses, telemetry or outside page navigation from app.
"""
from __future__ import annotations

import json
from hashlib import sha256
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
from time import monotonic, sleep
from urllib.request import urlopen


def find_edge() -> Path:
    paths=[
        Path(os.environ.get("PROGRAMFILES(X86)", "C:/Program Files (x86)"))/"Microsoft/Edge/Application/msedge.exe",
        Path(os.environ.get("PROGRAMFILES", "C:/Program Files"))/"Microsoft/Edge/Application/msedge.exe",
    ]
    for path in paths:
        if path.is_file():
            return path
    raise RuntimeError("Edge binary unavailable on Windows host")


def main() -> int:
    if sys.platform!="win32":
        raise RuntimeError("Edge smoke only supports Windows")
    artifact=Path("artifacts")
    artifact.mkdir(exist_ok=True)
    edge=find_edge()
    with tempfile.TemporaryDirectory(prefix="mimar-edge025-") as temporary:
        root=Path(temporary)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1",0))
            port=sock.getsockname()[1]
        command=[sys.executable,"-c",
                 "import uvicorn; from mimarllm.app.server import create_app; "
                 f"uvicorn.run(create_app({str(root/'workspace')!r}),host='127.0.0.1',"
                 f"port={port},proxy_headers=False,log_level='warning')"]
        server=subprocess.Popen(command,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        url=f"http://127.0.0.1:{port}/"
        try:
            until=monotonic()+25
            while monotonic()<until:
                if server.poll() is not None:
                    raise RuntimeError("Local server exited before readiness")
                try:
                    with urlopen(url+"api/session",timeout=2) as response:
                        result=json.load(response)
                        if result.get("legal_gate")=="REGULATORY_LOCKED":
                            break
                except (OSError, ValueError):
                    sleep(.3)
            else:
                raise RuntimeError("Loopback server not ready")
            # Three.js must be served by localhost, with pinned SHA, not CDN.
            with urlopen(url+"static/three.module.js",timeout=10) as response:
                vendor=response.read()
            if sha256(vendor).hexdigest()!="76dea8151bc9352aef3528b4262e249b2604f62543828328db978d060d61a495":
                raise RuntimeError("Local Three.js vendor SHA mismatch")
            with urlopen(url+"static/scene25d.js",timeout=10) as response:
                scene_code=response.read().decode("utf-8")
            if 'import * as THREE from "./three.module.js"' not in scene_code:
                raise RuntimeError("026 local Three.js import path invalid")
            with urlopen(url+"api/vlm/status",timeout=10) as response:
                vlm_status=json.load(response)
            if vlm_status.get("configured") is not False or vlm_status.get("legal_gate")!="REGULATORY_LOCKED":
                raise RuntimeError("VLM fail-closed unavailable-state not visible on fresh localhost")
            with urlopen(url+"api/rubric/profile/1",timeout=10) as response:
                year1=json.load(response)
            with urlopen(url+"api/rubric/profile/4",timeout=10) as response:
                year4=json.load(response)
            if (year1.get("official_grade") is not False or
                    len(year1.get("axes",[]))!=8 or len(year1.get("criteria",[]))!=6 or
                    len(year4.get("criteria",[]))!=16):
                raise RuntimeError("Rubric year gating or official-grade lock failed in Edge smoke")
            base=[str(edge),"--headless=new","--disable-gpu","--no-first-run",
                  "--disable-background-networking","--no-default-browser-check",
                  "--user-data-dir="+str(root/"edge-profile"),
                  "--virtual-time-budget=4000"]
            process=subprocess.run(base+["--dump-dom",url],text=True,encoding="utf-8",errors="replace",capture_output=True,timeout=65)
            if process.returncode!=0:
                raise RuntimeError("Edge DOM smoke failed")
            dom=process.stdout
            required=[
              "Proje inceleme paneli","id=\"drawing-2d\"",
              "id=\"edit-run\"","id=\"edit-undo\"",
              "id=\"massing-canvas\"","id=\"massing-build\"",
              "id=\"vlm-opt-in\"","id=\"vlm-infer\"","id=\"vlm-results\"",
              "id=\"rubric-year\"","id=\"rubric-criteria\"","id=\"rubric-evaluate\"",
              "id=\"jury-generate\"","id=\"jury-next\"","id=\"jury-download\"","id=\"jury-turns\"",
              "Henüz yerel çizim eklenmedi",
              "Hukukî doğrulama kilitli",
            ]
            absent=[name for name in required if name not in dom]
            if absent:
                raise RuntimeError("Edge did not render expected offline DOM nodes: "+repr(absent))
            report={
                "kind":"GITHUB_HOSTED_WINDOWS_EDGE_HEADLESS_SMOKE_NOT_PHYSICAL_UAT",
                "platform":platform.platform(),
                "edge_exe":edge.name,
                "loopback_only":True,"required_nodes_verified":required,
                "local_three_sha_verified":True,
                "local_026_module_verified":True,
                "rubric_028_year1_year4_profiles_verified":True,
                "jury_029_panel_verified":True,
                "offline_runtime_network_not_proven":True,
                "javascript_visible_project_empty_state":True,
                "legal_gate":"REGULATORY_LOCKED",
                "physical_windows10_11_edge_uat":"HOLD",
            }
            (artifact/"edge-smoke-025.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
            print(json.dumps(report,ensure_ascii=True))
            return 0
        finally:
            server.terminate()
            try:server.wait(timeout=7)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=7)


if __name__=="__main__":
    raise SystemExit(main())
