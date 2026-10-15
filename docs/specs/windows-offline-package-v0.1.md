# İşlem 021 — Windows çevrimdışı dağıtım v0.1: Wheelhouse / Onedir / Kaynak kimliği / SBOM envanteri

**Kaynak kodu:** `run.bat`, `install_offline.bat`, `build_exe.bat`, `mimar.spec`, `scripts/windows/`.

**Kayıt:** [İşlem 021](../islem_021.md). **Hedef:** Windows Python 3.11 ve tek kullanıcı, `src/mimarllm` içindeki gerçek offline DXF/PDF analiz ve localhost FastAPI dashboard'u taşımak. Bu paket önceki kodu değiştirmeden dağıtım tarifi ve hash doğrulama akışı sağlar.

**Durum sınırı:** Paketleme betiklerinin mevcut olması `Windows .exe`'nin üretildiğini veya gerçek kullanıcı Windows/Edge üzerinde açıldığını kanıtlamaz. Bu v0.1 `PyInstaller onedir` **aday yapılandırmasıdır**, `MSI`/`MSIX`/kod imzası yapılmadı.

## 1. İki farklı ortamı ve ağı kesin ayır

Hazırlama bilgisayarında kullanıcı **açıkça** `-AllowNetwork` parametresini verirse paket indeksine erişilerek binary wheels oluşturulabilir:

```powershell
# Windows / Python 3.11 / explicit preparation network
powershell -ExecutionPolicy Bypass -File scripts/windows/build_wheelhouse.ps1 -AllowNetwork
```

Bu çalışma `wheelhouse/` ve `wheelhouse-manifest.json` oluşturur. Manifestte her wheel'in SHA256, byte boyutu, build işletim sistemi ve Python sürümü, mevcut `pyproject.toml` SHA bulunur. Paket hazırlama anında 3. parti wheels `--only-binary=:all:` ile talep edilir; binary wheel bulunmazsa build fail-closed olur. Python kurulumu/SDK/yasal lisans internetten runtime sırasında otomatik yüklenmez.

*Hazırlama bilgisayarına güven* ve haricen imzalı depolanan wheelhouse manifestinin güvenilir kökeni **bu modülde teknik olarak ispatlanmaz**. SHA dosyasıyla aynı yerde tutulup ikisi birlikte değiştirilirse hash doğru görünebilir. Dış imza/kurumsal release hash anchoring gereklidir.

Hedef Windows bilgisayarında **ağ olmadan**, önceden eşlenmiş tekerlek arşivi ve kaynak dosyalar transfer edildikten sonra:

```bat
install_offline.bat
run.bat
```

`install_offline.bat` wheelhouse manifestini hedef Windows/Python 3.11 üzerinde yerelde doğrular, sonra .venv kurar ve `pip install --no-index --only-binary=:all: --find-links ...` kullanır. İndirme/çevrimiçi PyPI fallback **yasaktır**; eksik tekerlek varsa kurulum hata koduyla durur. `run.bat` ortamı hazır değilse sessizce paket indirmez, açık hata verir.

## 2. Gerçek mevcut dashboard entrypoint'i ve workspace

`scripts/windows/launch_dashboard.py` önce mevcut `mimarllm.app.launch` modülünü çağırır, localhost `127.0.0.1` kısıtını kaldırmaz. Veriler `LOCALAPPDATA\MimarLLM\workspace` altında tutulur, derlenmiş `dist/MimarLLM_V2` uygulama dosyalarının altına yazılmaz. Sunucunun güvenlik modeli İşlem 019'daki yalnız tek kullanıcı/loopback ve CSRF/Host/Origin korumalarıyla aynıdır; LAN/multi-tenant/kurumsal kimlik yöneticisi değildir.

`MimarLLM_V2.exe --self-check` çağrısı sunucu açmadan yerel `index.html`/`dashboard.css`/`dashboard.js` içeriklerini, FastAPI app importu, `pypdfium2`, `shapely`, `rapidocr`, `onnxruntime` CPU provider kullanılabilirliğini ve GPU onnxruntime wheel bulunmamasını denetler. **Self-check'i çalıştırmak gerçek UI tıklama veya müşteri kabul testi değildir.**

## 3. PyInstaller aday onedir yapısı

`mimar.spec` mevcut `src/mimarllm` modül yolunu kullanır. Windows dışından build'i reddeder; gerekli gerçek paketlerde eksik modül varsa gizli başarı üretmez. Özellikle `app/static` asset dizini ile PDFium/GEOS/ONNX Runtime CPU/RapidOCR/Starlette/uvicorn/ReportLab import/binary adayları toplanır. Başlangıç politika `console=True` ve `upx=False`; rastgele GPU/TensorFlow/PyTorch/Qt runtime eklenmez.

```bat
build_exe.bat
```

Bu komut önceden kurulmuş yerel venv'i ve wheelhouse hash'lerini doğrular, `python -m PyInstaller --noconfirm --clean mimar.spec` çalıştırır, `dist\MimarLLM_V2\MimarLLM_V2.exe --self-check` sonucunu ister. Başarılıysa `dist\MimarLLM_V2.manifest.json` oluşturur ve onedir dosya SHA kayıtlarını tekrar kontrol eder. Var olan manifest overwrite edilmez.

**Gerçek Windows build yapılmadıysa**, bu açıklanan adımlar bir *kodlanmış tarif* olarak görülmelidir, çalışan binary garantisi değildir. PyInstaller hidden imports ve native DLL sözleşmeleri gerçek temiz Windows üzerinde ayrı doğrulanacaktır.

## 4. Paket bütünlüğü, envanter ve lisans sınırı

`scripts/windows/package_manifest.py`:

- `create --kind WHEELHOUSE`: yalnız kökteki .whl dosyaları; symlink, boş/tuhaf ad ve bütçe aşımı ret; kayıtlı SHA/byte boyutu.
- `verify --kind WHEELHOUSE`: manifestteki tüm wheel'ler ve **eklenmiş/kaldırılmış** dosyalar kontrol; yerel Python/OS ve seçili pyproject hash aynı değilse ret.
- `create --kind WINDOWS_ONEDIR`: yalnız Windows hostta gerçek `MimarLLM_V2.exe` yolu varsa dağıtım dosyalarının SHA, byte boyutu, kurulmuş Python dağıtımlarının *kendileri tarafından beyan edilen* licence metadata'sı envantere girer.
- `verify --kind WINDOWS_ONEDIR`: tüm dosya snapshot'ı tekrar okunur; symlink ve değişmiş/eksik native asset ret.

**Lisans incelemesi:** PyInstaller/PDFium/GEOS/ONNX Runtime/RapidOCR/codec/VC++ Redistributable/UCRT ve transitive binary lisans/NOTICE dağıtım izinleri henüz bireysel olarak hukukî olarak onaylanmadı. `declared_license` alanı paket metadata'sıdır, SPDX envanterinin veya lisans hakkının bağımsız teyidi değildir. Bu nedenle `license_review=HOLD` sabittir.

**Güvenlik sınırı:** Signature yok, UAC installer veya otomatik güncelleme yok, işletim sistemine dosya/servis eklemiyor; workspace yüklemesi/rapor üretimi yereldir. Yerel malware ve değiştirilebilir wheel manifestine karşı tam tedarik zinciri güvencesi iddiası yok.

## 5. Geliştirme kabulü ve eksikler

Bu modül sentetik GitHub Linux/Windows'da script kaynak yapısı, AST, wheel sha değişimi, büyük/yanlış/sahte dosya, platform mismatch ve statik asset varlık kontrolü için `tests/test_windows_packaging.py` ile ölçülür.

**HOLD / final acceptance:** Windows 10/11 temiz bilgisayarda gerçek wheelhouse hazırla/install, internet fiziksel olarak kapalı onedir launch ve kullanıcı tıklamaları, Windows Defender SmartScreen, binary DLL yükleme, entegrasyon DXF/PDF/RapidOCR/HTML export, gerçek A0 bellek, lisans haklarının bağımsız incelemesi, dağıtım checksum'ın dış imza ile köken kanıtı ve Windows cihazdaki gerçek performans. Yerel RTX 4070 GPU/OCR testi ayrı; OCR mevcut CPU hattıdır, VLM/3D eğitim modülleri plan aşamasındadır.

**Sonraki mühendislik:** İşlem 022 kirli CAD kaynak koruyan onarım *adayı*; mevcut DrawingIR entity/handle ve kalibrasyon değişmez. İşlem 021 CI başarı kriteri **kod/sözleşme testi**, tüm ürün acceptance değil.
