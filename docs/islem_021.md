# İşlem 021 — Windows Offline Paketleme / Onedir / Wheelhouse / SBOM

- **Tarih:** 2026-10-15
- **Durum:** UYGULANDI / KAPATILDI — F20 Windows offline wheelhouse/onedir paketleme kaynak betikleri, frozen self-check ve SHA256/SBOM envanteri kodlandı. Windows 310 PASS; Ubuntu 309 PASS + 1 Windows-only SKIP (sentetik CI). **Gerçek exe derlemesi/temiz Windows kullanıcısı/bağımsız lisans kabulü HOLD.**
- **Ön koşullar:** İşlem 018 pipeline/CLI, 019 localhost FastAPI dashboard, 020 yalnız ARCH-CORE gelecek mimari planı. İşlem 001–020 tarihçesi değiştirilmez.
- **Düzen:** Bu kayıt ilk GitHub yazımı → gerçek kod/test/CI/doküman → bu kayıt **son GitHub yazımı** ile kapanış.

## 1. Geliştirme hedefi ve dosyaları

1. `scripts/windows/launch_dashboard.py`: mevcut `mimarllm.app.launch` gerçek dashboard modülünü başlatan Windows bundle entrypoint; çalışma alanı paket dizinine yazılmaz, loopback-only.
2. `mimar.spec`: kaynak paketi `src/mimarllm`, yerel app/static, PyInstaller `onedir`, `upx=False`, tanımlı PDFium/GEOS/ONNX Runtime CPU/FastAPI/RapidOCR bağımlılıkları için fail-closed hazırlama.
3. `run.bat`: Windows kaynak geliştirme başlatıcısı; mevcut sanal ortamı ya da doğrulanmış yerel wheelhouse'u kullan; `--no-index` dışında sessiz pip ağ bağlantısı yok.
4. `build_exe.bat`, `scripts/windows/build_wheelhouse.ps1`: bilinçli, ayrı hazırlanan wheelhouse ve onedir build; platform/Python kontrolü, doğrulanmış SHA manifesti, önceden kurulu PyInstaller zorunluluğu.
5. `scripts/windows/package_manifest.py`: wheel dosyalarını SHA256 ile listeleyen ve tekrar doğrulayan bağımsız manifest; build artifact SHA listesi, Python/package metadata ve iddia edilmeyen lisans beyanları. SBOM envanteri bir lisans hukuku onayı değildir.
6. `tests/test_windows_packaging.py` ve CI Ubuntu/Windows kaynak/bundle manifest sözleşme testleri; gerçek uzun Windows onedir/sıfır ağ/temiz PC acceptance ayrı.
7. `docs/specs/windows-offline-package-v0.1.md`, README, F20 envanteri/yol haritası/kararlar.

## 2. Güven sınırı

- Scriptin depoya girmesi derlenmiş exe, gerçek Windows kurulum, Offline bağımlılıkların hazır olması veya lisansların onaylanması demek değildir. Kullanıcı Windows hedefinde smoke final aşamada.
- Runtime hiçbir cloud AI API, CDN, telemetri veya model indirimi gerektirmeyecek. Wheelhouse hazırlama başka bir **bilinçli build aşamasıdır**; bunun ağ kullanımı runtime'dan ayrı açıklanır.
- Yerel CPU PDF/OCR/GEOS/DLL teknik hak ve kullanım koşulları kontrol edilmemişse “ticari dağıtım hazır” denmez.
- `REGULATORY_LOCKED` ve `HUKUKI_HOLD` korunur. ARCH-CORE 3D/yerel VLM/jüri kodlanmış sayılmaz.

## 3. Gerçek kod/commit zinciri

İşlem 021 kapsamında **ilk GitHub yazımı**, bu belgenin `docs/islem_021.md` oluşturulduğu `27a6d3c66c9625165222e47d54c77007e414c27a` commit'idir. Kod, test, spec ve diğer dokümanlar **bundan sonra** değiştirildi; 001–020 işlem kayıtları değiştirilmedi.

| Dosya / değişiklik | Gerçek katkı | Commit(ler) |
| --- | --- | --- |
| `scripts/windows/launch_dashboard.py` | Gerçek F19 `mimarllm.app.launch` frozen entrypoint; kullanıcı `LOCALAPPDATA` workspace; yerel UI + CPU dependency import `--self-check` | `706ababb`, `01baa125` |
| `scripts/windows/package_manifest.py` | Wheelhouse / Windows onedir SHA256 dosya listesi, byte budget, path/symlink kontrol, pyproject hash, OS+Python hedefi, metadata kaynağı ve `license_review=HOLD` | `4b58596a` |
| `mimar.spec` | Windows-only PyInstaller `onedir`, `console=True`, `upx=False`, gerçek kaynak paket `src/mimarllm`, yerel UI static, PDFium/GEOS/ONNX Runtime CPU/OCR/FastAPI/uvicorn/ReportLab aday binary importları | `b5d5ab5b` |
| `run.bat` | Hazır mevcut yerel .venv'den gerçek FastAPI localhost dashboard; sessiz ağ kurulumu yok | `78e972ad` |
| `install_offline.bat` | Windows Python 3.11 doğrulama, SHA manifest, `pip --no-index` ve explicit hazırlık; env self-check | `2a582acb`, `ea5368e0` |
| `build_exe.bat` | Önceden kurulu PyInstaller ile onedir candidate build tarifi; frozen `--self-check` başarısı ve SHA manifest denetimi; GPU wheel ret | `38de34ca`, `81191742` |
| `scripts/windows/build_wheelhouse.ps1` | Yalnız kullanıcı `-AllowNetwork` ile binary-only wheel dependency **hazırlama**; target Python ve hash manifest | `e1ba0e42` |
| `scripts/windows/README.md` | Adım adım hazırlama/kurulum/build, dış imza ve offline gerçek kabul sınırları | `a6b03442`, `b9ba714d` |
| `tests/test_windows_packaging.py` | SHA değişikliği ve yabancı platform/pyproject, symlink/path kaçışı, onedir Windows artifact hash snapshot, frozen self-check branch, batch script fail-closed sözleşmeleri | `6b25e253`, `044ab629`, `d4e3b2d1` |
| `.github/workflows/core-contracts.yml` | Windows paketleme dosya değişimi ve yeni testlerin iki OS sentetik matrise eklenmesi | `daee7cfd` |
| `.gitignore` | Yerel wheelhouse ve üretilen unsigned dağıtım manifestlerini Git'ten dışla | `c6600dbf` |
| `docs/specs/windows-offline-package-v0.1.md` | Offline runtime ile bilinçli network prep ayrımı, kullanım, binary/NOTICE/security acceptance listesi | `dd98eb9a` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md`, `docs/windows-dagitim-plani.md` | F20 KISMI / MEVCUT_KOD, 021 satırı, K-172–181, tarihsel 020 planı ile güncel aday kod ayrımı | `22a98506`, `99309d43`, `3a1c3008`, `18e0b8da`, `b3aa60c8` |

## 4. CI doğrulama: ne gerçekten çalıştı?

- İlk CI [GitHub Actions **38760617430**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38760617430): Ubuntu ve Windows **307 PASS / 1 FAIL**. Test, hash uyuşmazlığı sınamak için wheel byte dizisini *farklı boyuta* çevirmiş; doğru çalışan boyut kapısı `Package payload absent or wrong byte size` ile önce reddetmişti. Testte değiştirilmiş dosyanın boyutu sabitlendi, doğrudan SHA karşılaştırma kapısı sınandı.
- Kaynak güvenlik ve frozen self-check eklenmiş [GitHub Actions **38761030368**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38761030368): **Ubuntu 308 PASS, Windows 308 PASS**. Her iki platformda F19/Starlette upstream test istemcisi kaynaklı bir warning bulunuyordu.
- **Son test kod commit'i `d4e3b2d1d1f14268f880844bc1cf2aee7498af18`** için [GitHub Actions **38761322902**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38761322902) sonuçları ayrı Windows/Ubuntu job logları üzerinden doğrulandı:
  - GitHub-hosted **Windows Python 3.11: 310 PASS / 0 FAIL (16,71 saniye)**, 1 upstream uyarı.
  - **Ubuntu Python 3.11: 309 PASS / 0 FAIL / 1 SKIP (8,22 saniye)**, 1 upstream uyarı. SKIP, `WINDOWS_ONEDIR` sahte binary dosya SHA manifesti testinin Windows dışında anlamlı olmamasıdır.
- Testler hem repo mevcut çekirdek/dashboards sözleşmelerini hem yeni Python manifest hash/symlink/path/platform ve Windows kaynak script/yapı gereksinimlerini sınadı. **CI gerçek PyInstaller `mimar.spec` build'ini, exe çalışmasını, üçüncü taraf OCR model ağırlıklarını, fiziksel internet-kapalı Windows kurulumu veya dış lisans incelemesini yapmadı.**

## 5. Gerçek kabul ve güven sınırı

**Mevcut kod:** Windows offline kuruluma yönelik gerçek `.bat/.ps1` betikleri, mevcut FastAPI uygulamasını çağıran frozen başlatıcı, PyInstaller onedir spec, wheel/onedir dosyalarının SHA256 manifesti ve kaynak testleri. Bu betikler çalıştırıldığında seçilen dağıtım hash'ini denetleyip eksik/bozuk öğeyi reddetmeye programlandı; henüz doğrulanmış müşteriye teslim edilen paket üretilmedi.

**HOLD:**
- Windows 10/11 temiz ve internet kapalı hedef PC'de uygun `wheelhouse` hazırlığı, `install_offline.bat` çalıştırması ve gerçek derlenmiş `MimarLLM_V2.exe --self-check` sonucu / UI Edge tarayıcı tıklama kabulü.
- PyInstaller hidden imports, pypdfium2/PDFium, GEOS, onnxruntime CPU/RapidOCR DLL ve model asset dağıtım tamlığı, antivirüs/SmartScreen/VC++/UCRT kullanım kapsamı, codec hakları ve dağıtım lisans/NOTICE/SBOM bağımsız incelemesi. Manifestte `declared_license` yalnız paket metadata'sıdır, onay değildir; hash manifest tek başına dijital imza değildir.
- Kullanıcı donanımı Intel i7/32 GB/RTX4070 üzerinde kaynak tüketimi ve gerçek CAD, büyük A0 PDF, mimarî doğruluk kabulü. 020 ARCH-CORE VLM, 2.5D, jüri/rubrik ileri sürüm kodu bu pakette yazılmadı.
- F08–F12 `HUKUKI_HOLD` ve `RuleEngine.REGULATORY=INSUFFICIENT_EVIDENCE` korunur. Teknik sentetik PASS hukukî veya yapı can güvenliği sertifikası değildir.

**Özellik durumu:** `F20 KISMI/MEVCUT_KOD + SENTETİK_LINUX_WINDOWS_CI_PASS`; gerçek exe ve müşteri dağıtım kabulü `HOLD`. İşlem 021 paket kaynakları/dokümantasyon kapsamı bitmiştir. 

## 6. Sıradaki paket

`docs/islem_022.md` **henüz oluşturulmadı**; bundan sonraki ilk GitHub kod değişikliğinden önce yeni işlem kaydı **ilk GitHub yazımı olarak** açılacaktır. Öncelik yeni master plana göre **kirli CAD geometrisini onarma yerine orijinal DrawingIR CAD handle/koordinatını bozmayan kaynak işaretli onarım adayı katmanı**. Mevcut LLM/VLM, resmî hukukî onay veya 3D kapsamı yanlışlıkla işlev tamamlandı diye sunulmayacak.

