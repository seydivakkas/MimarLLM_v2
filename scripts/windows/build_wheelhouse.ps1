# Explicit predeployment preparation. This is NOT a runtime dependency.
# Internet access is only permitted when the operator passes -AllowNetwork.
param(
    [switch]$AllowNetwork,
    [string]$Python = "py"
)
$ErrorActionPreference = "Stop"
if (-not $AllowNetwork) {
    throw "Preparation can access package indexes. Pass -AllowNetwork explicitly; never run at runtime."
}
if (-not $IsWindows -and $env:OS -ne "Windows_NT") {
    throw "Prepare the wheelhouse on target Windows Python 3.11, not a foreign platform."
}
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$wheelhouse = Join-Path $root "wheelhouse"
$manifest = Join-Path $root "wheelhouse-manifest.json"
if (Test-Path $manifest) {
    throw "Existing wheelhouse-manifest.json must be archived/removed explicitly for new snapshot."
}
if (Test-Path $wheelhouse) {
    if (@(Get-ChildItem -Force $wheelhouse).Count -gt 0) {
        throw "Wheelhouse already contains files. Refusing mixed/unreviewed dependency snapshots."
    }
} else {
    New-Item -ItemType Directory -Path $wheelhouse | Out-Null
}
Push-Location $root
try {
    & $Python -3.11 -c "import sys; assert sys.platform == 'win32' and sys.version_info[:2] == (3, 11)"
    if ($LASTEXITCODE -ne 0) { throw "Use Windows Python 3.11 for target wheels." }
    # Resolve only binary 3rd-party wheels; prepare root project wheel locally.
    & $Python -3.11 -m pip wheel --only-binary=:all: --wheel-dir $wheelhouse ".[dashboard,reports]" "pyinstaller>=6,<7"
    if ($LASTEXITCODE -ne 0) { throw "Binary-only dependency wheel resolution failed." }
    & $Python -3.11 "scripts\windows\package_manifest.py" create --directory $wheelhouse --manifest $manifest --kind WHEELHOUSE --pyproject "pyproject.toml"
    if ($LASTEXITCODE -ne 0) { throw "Wheel manifest generation failed." }
    & $Python -3.11 "scripts\windows\package_manifest.py" verify --directory $wheelhouse --manifest $manifest --kind WHEELHOUSE --pyproject "pyproject.toml"
    if ($LASTEXITCODE -ne 0) { throw "Wheel SHA verification failed." }
    Write-Host "WHEELHOUSE_PREPARED: local SHA inventory, NOT code signature or license approval."
} finally {
    Pop-Location
}
