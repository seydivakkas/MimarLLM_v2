@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if errorlevel 1 exit /b 2
set "PY=%~dp0.venv\Scripts\python.exe"
set "WHEELHOUSE=%~dp0wheelhouse"
set "MANIFEST=%~dp0wheelhouse-manifest.json"
if not exist "%PY%" (
  echo MIMARLLM_ERROR: Install hashed offline venv first: install_offline.bat. 1>&2
  exit /b 2
)
if not exist "%MANIFEST%" (
  echo MIMARLLM_ERROR: Missing verified wheelhouse manifest. 1>&2
  exit /b 2
)
"%PY%" "scripts\windows\package_manifest.py" verify --directory "%WHEELHOUSE%" --manifest "%MANIFEST%" --kind WHEELHOUSE --pyproject "pyproject.toml"
if errorlevel 1 exit /b 2
"%PY%" -c "import sys, importlib.metadata as m; assert sys.platform == 'win32'; import PyInstaller, onnxruntime, pypdfium2, shapely, rapidocr, fastapi; assert 'CPUExecutionProvider' in onnxruntime.get_available_providers(); assert not any(x.metadata.get('Name','').lower().replace('_','-') == 'onnxruntime-gpu' for x in m.distributions())"
if errorlevel 1 (
  echo MIMARLLM_ERROR: Required preinstalled CPU build dependencies missing. 1>&2
  exit /b 2
)
"%PY%" -m PyInstaller --noconfirm --clean "mimar.spec"
if errorlevel 1 (
  echo MIMARLLM_ERROR: PyInstaller build failed. 1>&2
  exit /b 2
)
if not exist "%~dp0dist\MimarLLM_V2\MimarLLM_V2.exe" (
  echo MIMARLLM_ERROR: Expected onedir executable was not produced. 1>&2
  exit /b 2
)
"%~dp0dist\MimarLLM_V2\MimarLLM_V2.exe" --self-check
if errorlevel 1 (
  echo MIMARLLM_ERROR: Frozen executable static/DLL/CPU smoke failed. 1>&2
  exit /b 2
)
"%PY%" "scripts\windows\package_manifest.py" create --directory "%~dp0dist\MimarLLM_V2" --manifest "%~dp0dist\MimarLLM_V2.manifest.json" --kind WINDOWS_ONEDIR --pyproject "pyproject.toml"
if errorlevel 1 exit /b 2
"%PY%" "scripts\windows\package_manifest.py" verify --directory "%~dp0dist\MimarLLM_V2" --manifest "%~dp0dist\MimarLLM_V2.manifest.json" --kind WINDOWS_ONEDIR --pyproject "pyproject.toml"
if errorlevel 1 exit /b 2
echo MIMARLLM_ONEDIR_CANDIDATE_READY: dist\MimarLLM_V2
echo IMPORTANT: Build+hash alone do not prove clean Windows startup, network isolation or commercial licenses.
exit /b 0
