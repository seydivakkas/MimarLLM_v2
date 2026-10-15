@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 (
  echo MIMARLLM_ERROR: Cannot enter project directory. 1>&2
  exit /b 2
)
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo MIMARLLM_ERROR: Offline venv not found. Run install_offline.bat with a prepared wheelhouse first. 1>&2
  exit /b 2
)
"%PY%" -c "import mimarllm.app.launch, fastapi, uvicorn"
if errorlevel 1 (
  echo MIMARLLM_ERROR: Local dashboard dependencies missing. No internet install attempted. 1>&2
  exit /b 2
)
echo MimarLLM local dashboard - source evidence only, no legal certification.
"%PY%" -m mimarllm.app.launch %*
exit /b %errorlevel%
