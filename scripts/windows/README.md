# Windows offline packaging source scripts

The local **runtime** requires no public PyPI connection, CDN or paid LLM API.

1. On a **preparation Windows Python 3.11** machine, with deliberate network approval, execute:
   `powershell -ExecutionPolicy Bypass -File scripts/windows/build_wheelhouse.ps1 -AllowNetwork`
   This creates `wheelhouse/` and `wheelhouse-manifest.json`. Review the wheel snapshot and keep the manifest in a separately protected release location. A SHA stored alongside mutable files is not a signature.
2. Transfer a matched wheelhouse, manifest, code and `pyproject.toml` to the intended machine. Use `install_offline.bat`: hash/platform check then `pip --no-index`. This is an **explicit** setup step, not hidden runtime package installation.
3. Use `run.bat` to start the already-implemented loopback browser dashboard using the local venv. This is the developer launcher.
4. On a **Windows build machine**, run `build_exe.bat` with the preinstalled local toolchain. It creates an experimental `dist/MimarLLM_V2/MimarLLM_V2.exe` onedir candidate and `dist/MimarLLM_V2.manifest.json` integrity inventory. The frozen app's user workspace is outside its executable folder (under `LOCALAPPDATA`).
5. Independent acceptance before any external delivery: static assets, complete offline machine, Windows Defender/SmartScreen, DLL/codec/VC++ rights, startup/health/UI/Edge, DXF+PDF local reports, CPU-only runtime, SBOM/NOTICE/license verification and real Windows package reproduction.

Do NOT distribute as a validated installer or certified statutory compliance program based on scripts alone. PyInstaller output may require further Windows-specific hooks; CI contract tests do not substitute for executable build or target-machine smoke.

`mimar.spec` is a source implementation of onedir packaging, not a signed MSI/MSIX installer. No installer is created by this process.
