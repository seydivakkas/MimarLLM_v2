@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 exit /b 2
set "WHEELHOUSE=%~dp0wheelhouse"
set "MANIFEST=%~dp0wheelhouse-manifest.json"
if not exist "%WHEELHOUSE%\" (
  echo MIMARLLM_ERROR: Missing prepared wheelhouse folder. 1>&2
  exit /b 2
)
if not exist "%MANIFEST%" (
  echo MIMARLLM_ERROR: Missing wheelhouse integrity manifest. 1>&2
  exit /b 2
)
where py >nul 2>nul
if errorlevel 1 (
  echo MIMARLLM_ERROR: Python 3.11 Windows launcher unavailable. 1>&2
  exit /b 2
)
py -3.11 -c "import sys; assert sys.platform == 'win32' and sys.version_info[:2] == (3,11)"
if errorlevel 1 (
  echo MIMARLLM_ERROR: Python 3.11 Windows x64 is required for this wheelhouse. 1>&2
  exit /b 2
)
py -3.11 "scripts\windows\package_manifest.py" verify --directory "%WHEELHOUSE%" --manifest "%MANIFEST%" --kind WHEELHOUSE --pyproject "pyproject.toml"
if errorlevel 1 (
  echo MIMARLLM_ERROR: Wheelhouse failed SHA256/platform verification. 1>&2
  exit /b 2
)
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  py -3.11 -m venv "%~dp0.venv"
  if errorlevel 1 (
    echo MIMARLLM_ERROR: Cannot create local venv. 1>&2
    exit /b 2
  )
)
"%PY%" -m pip install --disable-pip-version-check --no-index --only-binary=:all: --find-links "%WHEELHOUSE%" "mimarllm-v2[dashboard,reports]" "pyinstaller>=6,<7"
if errorlevel 1 (
  echo MIMARLLM_ERROR: Local wheel dependency resolution failed; no network fallback. 1>&2
  exit /b 2
)
"%PY%" "scripts\windows\launch_dashboard.py" --self-check
if errorlevel 1 (
  echo MIMARLLM_ERROR: Runtime import smoke failed. 1>&2
  exit /b 2
)
echo MIMARLLM_OFFLINE_ENV_READY: Run run.bat
exit /b 0
