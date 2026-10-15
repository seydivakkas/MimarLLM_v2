# -*- mode: python ; coding: utf-8 -*-
"""Windows-only, console-first PyInstaller onedir: MimarLLM current F19 app.

This spec must be executed from a locally-prepared, hash-reviewed Windows
venv. Collect only installed actual package dependencies and local static UI.
No silent package, OCR model, ONNX provider or cloud download is allowed.
"""
from pathlib import Path
import importlib.util
import sys

from PyInstaller.utils.hooks import collect_all


if sys.platform != "win32":
    raise SystemExit("MimarLLM_V2 onedir can only be built on Windows")

ROOT = Path(SPECPATH).resolve()
SRC = ROOT / "src"
ENTRY = ROOT / "scripts" / "windows" / "launch_dashboard.py"
STATIC = SRC / "mimarllm" / "app" / "static"

if not ENTRY.is_file() or not STATIC.is_dir():
    raise SystemExit("Actual dashboard launcher or local static UI missing")

# All packages below are used in the implemented drawing/PDF/OCR/report
# pipeline and/or loopback FastAPI UI. Missing builds MUST fail.
REQUIRED = (
    "mimarllm", "pdfplumber", "pypdfium2", "ezdxf", "shapely",
    "networkx", "pydantic", "PIL", "rapidocr", "onnxruntime",
    "fastapi", "starlette", "uvicorn", "reportlab",
)
datas, binaries, hiddenimports = [], [], []
for package in REQUIRED:
    if importlib.util.find_spec(package) is None:
        raise SystemExit(f"Required installed package missing: {package}")
    package_datas, package_binaries, package_hidden = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hidden

# Enforce current repo's single static UI; never rely on non-existent
# old src/mimar or external CDN copies.
datas.append((str(STATIC), "mimarllm/app/static"))
hiddenimports += ["mimarllm.app.launch", "mimarllm.app.server",
                  "mimarllm.pipeline", "mimarllm.reports.exporter"]

a = Analysis(
    [str(ENTRY)],
    pathex=[str(SRC)],
    binaries=binaries,
    datas=datas,
    hiddenimports=sorted(set(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["onnxruntime_gpu", "torch", "tensorflow",
              "PyQt5", "PyQt6", "PySide2", "PySide6"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="MimarLLM_V2",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe, a.binaries, a.datas,
    strip=False,
    upx=False,
    name="MimarLLM_V2",
)
