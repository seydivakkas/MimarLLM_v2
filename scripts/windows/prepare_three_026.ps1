# Explicit predeployment only. Offline runtime never invokes npm.
param([switch]$AllowNetwork)
$ErrorActionPreference = "Stop"
$root=(Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Push-Location $root
try{
  if($AllowNetwork){
    & npm install --ignore-scripts --no-audit --no-fund --package-lock=false --save=false
    if($LASTEXITCODE -ne 0){throw "Offline Three vendor dependency preparation failed"}
    & node scripts\build_three_vendor_026.mjs
  }else{
    & node scripts\build_three_vendor_026.mjs --verify
  }
  if($LASTEXITCODE -ne 0){throw "Local Three.js vendor verification failed"}
  Write-Host "THREE026_VERIFIED: bundled ESM + local manifest (NOT final redistribution license signoff)."
}finally{Pop-Location}
