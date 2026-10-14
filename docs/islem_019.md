# İşlem 019 — Yerel çevrimdışı mimari analiz dashboard (F19)

- **Tarih:** 2026-10-14
- **Durum:** UYGULANDI — F19 tek kullanıcılı çevrimdışı localhost FastAPI/HTML+CSS+JS arayüzü, source SHA'lı DXF/PDF upload–pipeline–rapor ve regresyonlar GitHub'a işlendi. **Ubuntu 295/295, Windows 295/295 sentetik CI PASS (her OS bir upstream Starlette test uyarısı).** Gerçek Windows/Edge görsel kullanıcı kabulü, installer ve hukukî onay açık/HOLD.
- **Ön koşul:** İşlem 018 kapatıldı, Ubuntu/Windows 279/279 sentetik test başarılı, F16 pipeline/CLI kısmi.
- **Kapsam:** F19: yerel tek kullanıcıya ait FastAPI/127.0.0.1 tarayıcı uygulaması; Windows-first, hazır çekirdeği yeniden kullanır.
- **İşlem sırası:** Önce bu dosya; sonra kaynak/test/UI/doküman; **en son yine bu dosyaya gerçek commit/test kanıtları yazılarak kapanış**. İşlem 001–018 kayıtları değiştirilmeyecek.

## Hedeflenen çalışan özellikler

1. `src/mimarllm/app/server.py`: `create_app(workspace)`; sabit yerel çalışma alanı; 127.0.0.1/localhost Host ve client doğrulaması; CSRF token, Origin doğrulaması, no-store, CSP, X-Content-Type-Options, dış kaynaklara gerek olmadan FastAPI; upload/analiz isteği tek kullanıcı için sınırlı.
2. `src/mimarllm/app/static/index.html`, `dashboard.css`, `dashboard.js`: Türkçe, erişilebilir yerel arayüz; DXF/PDF yükleme; dosyaları ve önceki analizleri listeleme; ilk analiz; DrawingIR native çizgi ID'si seçip bilinen metre ile kullanıcı referansı ekleyerek ikinci analiz; gelişmiş `PipelineConfig` JSON; frame/katman/kanıt ve teknik/HOLD durumları; gerçek raporu yeni sekmede açma; JSON/MD/PDF/manifest indirme. Her görüntü veri kaynağı çalıştırılmış pipeline/raporla bağlı olmalı.
3. `src/mimarllm/app/launch.py`: `python -m mimarllm.app.launch` / `mimarllm-dashboard` komutu, Uvicorn'un **sadece 127.0.0.1** adresine bağlanması. `--workspace` sadece başlatan yerel kullanıcı argümanı; HTTP talebi çalışma alanı yolunu belirleyemez.
4. Yanlış uzantı/path traversal, aşırı yükleme (DXF 25MB; PDF en çok 50MB), kötü biçimli JSON/config, ikinci eşzamanlı işlem, geçersiz proje/rapor ID, kaynak SHA değişimi, dış Host/Origin/istemci, CSRF ve dashboard kaynaklı HTML injection engellenmeli. Upload dosya adı HTTP dizinine dönüşmemeli. Tarayıcı sadece same-origin statik CSS/JS kullanmalı (CDN yok).
5. Her çalıştırma yeni UUID çalışma dizininde izole kalmalı; raporlar `run_local_pipeline` ve `export_report` aracılığıyla oluşturulmalı; `PARTIAL_WITH_ERRORS` olduğu gibi kullanıcıya gösterilmeli, hukukî `REGULATORY_LOCKED` değişmemeli.
6. `tests/test_dashboard.py` ve `.github/workflows/core-contracts.yml`: GitHub-hosted Linux/Windows üzerinde gerçek ASGI API/HTML yükleme/yeniden analiz/saldırı ve çıktı testleri. Testler gerçek müşteri Windows kullanıcı tarayıcısı kabulünün yerine geçmez.
7. `pyproject.toml` `dashboard` isteğe bağlı ekstra, sürümlemeli kullanım kılavuzu `docs/specs/dashboard-v0.1.md`, README/envanter/yol haritası/kararlar güncellenecek.

## Güven/ürün sınırı

- FastAPI dashboard F19'un ilk gerçek çalışan yerel arayüzüdür; **tam modern Windows native desktop installer veya otomatik CAD plot motoru değildir**. Kullanıcı Windows/Edge gerçek makine testi, uzun süreli dosya güvenliği ve sızma testi sonra yapılır.
- Bu aşamada ağdan mevzuat/PDF/model indirilmez. PDF OCR ancak ayrı CPU OCR ve kullanıcı ROI config ile; GPU/cloud ve ücretli API yok. Kaynak PDF SHA/geometri ve teknik ölçek denetimleri İşlem 018'den korunur.
- Teknik RuleEngine senaryosu "COMPLIANT" bina/yasal uygunluk sertifikası değildir. F08–F12 HUKUKI_HOLD ve RuleEngine.REGULATORY INSUFFICIENT_EVIDENCE.
- API'deki tek seferlik CSRF/görsel/Host savunmaları, makinenin ele geçirilmesine veya başka bir yerel process'e karşı yetkilendirme garantisi değildir; ağ erişimini bilinçli olarak loopback'le sınırla. Bu prototip müşteri LAN'ına açılmamalıdır.

## Gerçek değişiklikler ve commit kanıtı

**Zorunlu ilk GitHub yazımı:** `docs/islem_019.md`, commit **`3ff5ac48a2ecfcf452d843eaf86259b0f7a7049c`**. Sonraki bütün kaynak kodu, CI, tasarım varlığı ve destek dokümanı değişiklikleri bu commit'ten sonra oluşturuldu. `docs/islem_001.md`–`docs/islem_018.md` **değiştirilmedi**.

| Dosya | Gerçek eklenen işlev | Commit |
| --- | --- | --- |
| `src/mimarllm/app/server.py` | Yerel FastAPI Host/peer/Origin/CSRF ve CSP/headers, ham DXF/PDF streaming upload, dosya tipi/boyut sınırı, SHA-256, project/run UUID depolama, tek aktif analiz, kaynaklı pipeline/rapor API, izinli rapor download ve özet | `69959c9c` |
| `src/mimarllm/app/__init__.py`, `app/launch.py` | İsteğe bağlı app factory ve Uvicorn `host=127.0.0.1`, `proxy_headers=False`, port/workspace local komut | `9fc3c8be`, `dd7789e2` |
| `src/mimarllm/app/static/index.html` | Türkçe genel bakış, DXF/PDF upload, kayıtlı projeler, analiz laboratuvarı, kalibrasyon için native LINE, manifest aşama paneli ve bulgular/raporlar | `84ef07de` |
| `src/mimarllm/app/static/dashboard.css` | Offline responsive panel, proje/öğe kartları, inceleme/hata durumları, CSS dış kaynak gerektirmez | `b85c38f5` |
| `src/mimarllm/app/static/dashboard.js` | Same-origin `fetch` + CSRF, kaynağa bağlı birinci/ikinci analiz, native çizgi seçimleri, stage/reason görünümü, HTML/JSON/MD/PDF rapor linkleri, DOM `textContent` | `db173366` |
| `tests/test_dashboard.py` | Gerçek sentetik DXF/PDF üzerinden ASGI TestClient, SHA/frame+rapor, ikinci analizde native source segment referansı, hukukî kilit, remote Host/client/Origin/CSRF, dosya sınırı ve path traversal, export HTML+JS/CSS, localhost-only launcher | `873bc45b` |
| `pyproject.toml` | `dashboard` opsiyonel FastAPI+Uvicorn+ReportLab extra, `mimarllm-dashboard` entrypoint, HTML/CSS/JS package-data | `82fb97d6` |
| `.github/workflows/core-contracts.yml` | App/static source değişim izleme ve `tests/test_dashboard.py` Linux/Windows pytest matrisine katılma | `104b21b5` |
| `src/mimarllm/app/server.py` | Analiz config JSON gövdesinin **stream sırasında 256 KB'de kesilmesi** (tüm gövdeyi belleğe almadan), stored project metadata source kind/name/size/hash sağlamasını reddetme | `319b1e71`, `9d6bcef2` |
| `tests/test_dashboard.py` | Aşırı analiz JSON, sahte rapor SHA ve değiştirilmiş proje metadata/path yönlendirme senaryoları | `feba80a0`, `f8e5df6a` |
| `docs/specs/dashboard-v0.1.md` | Gerçek API, UI modülleri, kurulum/çalışma alanı, tehdit modeli ve hukukî HOLD sınırları | `e4fc60c0` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F19 KISMI/MEVCUT_KOD; K-147–156; F20 ayrı Windows paketleme; tarihsel rota 020–022 yeniden sıralama | `31469930`, `55616045`, `dc462a49`, `799aed0f` |

## Linux/Windows CI ve gerçek durum

- İlk birleşik dashboard regresyonu [GitHub Actions **38556435957**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38556435957): Ubuntu **292 PASS**, Windows **292 PASS**. FastAPI/Starlette TestClient bağımlılığından kaynaklı **her platformda 1 adet upstream deprecation warning**; uygulama testlerinde fail yok.
- UI/HTTP güvenlik iyileştirmesi sonrası [GitHub Actions **38556889894**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38556889894): Ubuntu **294 PASS**, Windows **294 PASS**; stream sırasında JSON limiti ve değiştirilmiş rapor SHA denetimi eklendi.
- **Son kod commit `f8e5df6a13762631d44079e2a1c6d83235d9f058`** için [GitHub Actions **38557404737**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38557404737) iki job logu bağımsız doğrulandı:
  - Ubuntu Python 3.11: **295 PASS / 0 FAIL**, 1 upstream test client uyarısı, **7,82 saniye**.
  - GitHub-hosted Windows Python 3.11: **295 PASS / 0 FAIL**, 1 upstream test client uyarısı, **9,82 saniye**.
- Bu testler ASGI üzerinden dosyayı gerçekten yükleyip DXF/PDF ayrıştırır, PipelineConfig'i uygular, raporu üretir ve dashboard REST kaynağını indirir. **Bunlar gerçek bir Windows/Edge kullanıcı oturumunda tıklama, CSS piksel doğrulaması, derlenmiş Windows `.exe` paket veya sızma testi değildir**.

## Kabul statüsü ve sonraki aşama

**Uygulandı:** İsteğe bağlı `dashboard` bağımlılık ekstra'sı ile çalışan, yalnız localhost'a bağlanan Türkçe tarayıcı arayüzü; DXF/PDF yükleme, proje geçmişi, tek aşamalı kaynaklı pipeline çalıştırma, native çizgiyle insan kalibrasyonlu ikinci değerlendirme, kaynaklı bulgu ve HTML/JSON/MD/PDF/manifest rapor erişimi. `PARTIAL_WITH_ERRORS` ve `REGULATORY_LOCKED` sonuçları açıkça kullanıcıya taşınır. Dış API/CDN zorunluluğu yok.

**F19 KISMI/MEVCUT_KOD + sentetik Linux/Windows CI PASS.** Tam native Windows uygulaması, PyInstaller onedir/installer, offline wheelhouse, yazılım bileşen lisans/SBOM denetimi ve gerçek Windows 10/11/Edge etkileşim/görsel acceptance **açık**. Bu sürüm kullanıcı kimlik/rol çoklu tenant sistemi değildir; API yalnız tek kullanıcı loopback kullanımında tasarlandı, OS içerisindeki diğer güvenilir/zararlı process'lere karşı yüksek güvence iddiası yok.

**HUKUKİ HOLD:** Resmî Gazete gerçek kaynak/authenticity, çok yıllı değişiklik–yürürlük konsolidasyonu, proje uygulanabilirlik/istisna/hukukçu onayı yok; `RuleEngine.REGULATORY=INSUFFICIENT_EVIDENCE`, `APPROVED_FOR_CHECK` üretilmez. Teknik COMPLIANT yalnız teknik sentetik referans senaryosudur.

**Sıradaki işlem 020** için `docs/islem_020.md` **henüz açılmadı**: Windows-first offline `onedir` paketleme, wheelhouse/başlatıcı/SBOM planı; önce işlem kaydı açılmalı. F21/F22 yerel VLM denemeleri ve gerçek benchmark sonraki ayrı süreç. 
