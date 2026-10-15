# İşlem 021 — Windows Offline Paketleme / Onedir / Wheelhouse / SBOM

- **Tarih:** 2026-10-15
- **Durum:** ÖN KAYIT. İşlem 021 kapsamındaki **ilk GitHub yazımıdır**; paketleme kodu ve başka belge değiştirilmedi.
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

## 3. Gerçek commit/test bilgisi

Son yazımda dosya/commit listesi, Ubuntu/Windows CI PASS/FAIL, yapılan/yapılmamış binary build, wheelhouse offline kabul, insan Windows UI kabulü ve lisans HOLD ayrımı doldurulacak.
