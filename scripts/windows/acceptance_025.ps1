# Manual physical Windows 10/11 acceptance bootstrap; does not self-certify PASS.
# Requires preinstalled Python 3.11, package dependencies and Microsoft Edge.
# Does not run pip or download any dependency/model.
param(
    [string]$OutputDirectory = "artifacts\manual-windows-025"
)
$ErrorActionPreference = "Stop"
if ($env:OS -ne "Windows_NT") { throw "Physical acceptance script requires Windows" }
if (!(Test-Path "pyproject.toml") -or !(Test-Path "scripts\benchmark_025.py")) {
    throw "Run from MimarLLM_v2 repository root"
}
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
& py -3.11 -c "import sys; assert sys.version_info[:2] == (3, 11); import mimarllm, ezdxf, fastapi, pydantic"
if ($LASTEXITCODE -ne 0) { throw "Python 3.11 or required local dependencies unavailable. No automatic network fallback." }
$bench = Join-Path $OutputDirectory "cad-perf-local-025.json"
& py -3.11 scripts\benchmark_025.py --output $bench
if ($LASTEXITCODE -ne 0) { throw "Synthetic local performance smoke failed" }
& py -3.11 scripts\windows\edge_smoke_025.py
if ($LASTEXITCODE -ne 0) { throw "Local Microsoft Edge UI smoke failed" }
if (Test-Path "artifacts\edge-smoke-025.json") {
    Copy-Item "artifacts\edge-smoke-025.json" (Join-Path $OutputDirectory "edge-smoke-local-025.json")
}
$checklist = @"
# İşlem 025 fiziksel Windows kabul kontrol formu

Durum: HOLD - Sadece komutla sentetik profil ve Edge smoke oluşturuldu.
Tarih/saat: $(Get-Date -Format o)
Makine: $env:COMPUTERNAME
İşletim sistemi: $([System.Environment]::OSVersion.VersionString)
Kullanıcı tarafından gözlemlenecek işlemler:
[ ] Resmî/anonimleştirilmiş gerçek DXF+PDF kaynak yükleme ve kaynak SHA teyidi
[ ] Gerçek Edge'de tıklama, erişilebilirlik, zoom ve kaynak-kanıt paneli
[ ] Doğrudan LINE koordinatı değiştir ve türetilmiş DXF indir
[ ] Kaynak DXF SHA değişmedi; türetilmiş DXF yeni CAD handle aynı, koordinatları doğru
[ ] Undo: son revizyon yasal PASS olmaksızın önceki geometriye döndü
[ ] Offline ağ kapalı koşulda gerçek program başlangıcı ve arayüz
[ ] İş kuyruğu limiti, yerel hata/çökme kurtarma ve disk/RAM profili
[ ] Gerçek çizimde bağımsız ölçüm ve geometrik değerlendirme
[ ] Derlenmiş .exe onedir DLL/model asset/SmartScreen/lisans/SBOM ayrı onay
[ ] Kullanıcı ve bağımsız incelemeci imzası; tarih/sürüm/hash kayıtları

Sonuç: HOLD
Notlar ve ölçümler:
"@
Set-Content -Path (Join-Path $OutputDirectory "manual-acceptance-025.md") -Value $checklist -Encoding UTF8
Write-Host "Yerel smoke ölçümleri yazıldı: $OutputDirectory"
Write-Warning "Bu betik fiziksel kullanıcı kabulü veya hukuki onay vermez. Manuel form ve gerçek DXF/PDF sonuçları olmadan İşlem 025 PASS değildir."
