# MimarLLM V2 — Windows Tek Tık ve PyInstaller Dağıtım Planı

**İşlem:** [islem_006.md](islem_006.md) · **Durum:** PLAN; henüz `run.bat`, `build_exe.bat`, `mimar.spec` veya web GUI yok.

## 1. Neden taslak betikleri doğrudan kopyalamıyoruz?

Yüklenen eski betik örnekleri `src.mimar.app`, `src/mimar/server/static` ve `requirements.txt` kabul ediyor. **Gerçek repo** paket yolu `src/mimarllm` ve `pyproject.toml`; uygulama `src/mimarllm/app` henüz mevcut değil. Sırf bir .exe üretmek veya browser açmak, DXF denetim motorunun çalıştığını kanıtlamaz.

Süre sürekliliği: kurulum ve başlangıç hızı milisaniye olarak vaat edilmez; test edilmesi gerekir. PyInstaller onedir çoğu paket için mantıklı ilk denemedir ama garanti değildir.

## 2. Geliştirici çalıştırıcı — `run.bat`

- Windows destekli Python sürüm politikasını kesinleştir; repo en az **Python 3.11** istiyor.
- `%~dp0` ile repo köküne geç; `setlocal`, path ve başarısız komut `errorlevel` açık işlenir.
- `.venv` ilk kurulumunda `python -m venv`; `python -m pip install -e .` gerçek `pyproject.toml` üzerinden. `pip install -r requirements.txt` hayalî dosyaya dayanamaz.
- **Tam offline ilk kurulum** için uyumlu önceden hazırlanmış hash doğrulanmış `wheelhouse/` / yerel `--no-index --find-links` şart; ağ kapalıyken PyPI pip'e ulaşmaya çalışıp “offline” iddiasını bozma. Model ağırlıkları da yerel hazırlanmalı.
- Stamp dosyası yalnız `pyproject.toml` + lockfile + wheelhouse/model manifest hash'i eşleştiğinde geçerli; salt boş stamp yanlış ortamı “tam” gösterir.
- **Gerçek entrypoint hazır olana kadar** UI başlatma işlemi başarısızlık ve eksik modül mesajı verecek, sahte panel açılmayacak.
- Analiz boyunca dış API çağrısı yok; localhost opsiyonel; istemci tarayıcı varsayılan olarak dış CDN/font aramamalı.

## 3. PyInstaller — `onedir`

- Giriş `mimarllm.app` veya gerçek `cli` console entrypoint hazır olduğunda doğrulanır. `src.mimar.app` eski yanlıştır.
- `mimar.spec`: `pathex` src kökü, mevcut paketleri toplama, `collect_dynamic_libs`/binaries ve model/NOTICE yalnız gerçekten gerekli olanlar. Varsayımsal static klasör veya import listesi yok.
- ONNX Runtime CPU DLL, PDFium binary/build license, GEOS/Shapely DLL ve GUI'nin dağıtım hakları gerçek Windows wheel üzerinde denetlenir.
- `upx=False` ilk kararlı paket deneyi için başlangıç tercihidir; bazı DLL/antivirüs sorunlarını azaltmaya yardımcı olabilir; zorunlu test.
- `console=True` ilk hata ayıklama; UI olgunlaşınca isteğe bağlı sessiz mod.
- `build_exe.bat`: kullanıcı izni olmadan ortam kurmaz, PyInstaller'ın önceden kurulmuş sürümü aranır; doğru `mimar.spec` ile `--clean --noconfirm` derler, sonuç SHA ve binary NOTICE listesi üretilir.
- Dağıtımda `dist/MimarLLM_V2/MimarLLM_V2.exe` dosyasının bulunması tek başına smoke PASS değildir.

## 4. Localhost FastAPI / statik arayüz güvenliği

- Server sadece `127.0.0.1` veya özel izinle açılır; rastgele sabit/kişisel localhost portu port çakışmasında doğrulanır.
- Web açma davranışı açık; sırf `webbrowser.open` sonucu “server hazır” olarak kabul edilmez; `/health` readiness kontrolü gerekir.
- Upload: uzantı/MIME imza, dosya/sayfa/entity sınırı, symlink/path traversal, temp klasör ve yaşam döngüsü.
- Web local olsa bile CSRF ve localhost'a dış origin erişim riskleri için Origin/Host koruması.
- Bütün HTML/CSS/JS/fontlar yerel; harici CDN/Google Fonts yok.
- Statik dosya yoksa `404` alan yol üretimde açılmaz; paketlemeden önce test.

## 5. İlk gerçek Windows kabul matrisi

| Kontrol | Geçiş |
| --- | --- |
| Python geliştirici modu | temiz Windows'ta pyproject/wheelhouse ile bağımlılıklar |
| Tam offline kurulum | ağ kapalıyken, önceden paketli wheel/model ile kurulum |
| Standalone executable | Python kurulu olmayan hedef Windows PC'de açılış |
| Çizim | sentetik DXF ve PDF seçip gerçek geometri bulgusu alma |
| Kaynak inceleme | çizimde koordinat + özgün mevzuat PDF sayfa/alan |
| Performans | hedef i7/32GB/4070 kaynak ölçümü, RAM peak ve VRAM |
| Licenses | PDFium/ONNX/GEOS/SSL/codec/MS runtimes/NOTICE SBOM |
| Stability | yanlış dosya, kilitli port, yetersiz kaynak ve tekrar başlatma |

**Son karar:** bu çalışma bu pakette yalnız plan. Gerçek start scriptleri/gizli import listeleri ancak uygulanmış modüllere göre yazılacak, sahte dosya yolu kullanılmayacak.
