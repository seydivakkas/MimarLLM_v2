# İşlem 019 — MimarLLM çevrimdışı yerel dashboard v0.1

**Kaynak:** [İşlem 019](../islem_019.md). Kod: `src/mimarllm/app/server.py`, `launch.py`, `static/index.html`, `static/dashboard.css`, `static/dashboard.js`.

## 1. Başlatma (Windows-first)

Önceden kurulmuş yerel Python 3.11+ ve paket bağımlılıkları gerekir. Yazılım **çalışma sırasında bulut hizmeti/API key/ücretli LLM çağırmaz**, fakat ilk bağımlılık kurulumu için paketlerin önceden indirilmiş wheel/cache olarak hazır bulunması gerekebilir.

```powershell
# Yerel paketler/wheelhouse hazır ise, geliştirme ortamında:
python -m pip install -e ".[dashboard]"
python -m mimarllm.app.launch --workspace "C:\MimarLLM\workspace" --port 8765

# Alternatif console script:
mimarllm-dashboard --workspace "C:\MimarLLM\workspace" --port 8765
```

Tarayıcıda yalnızca `http://127.0.0.1:8765` adresini açın. Program zorunlu olarak `127.0.0.1` adresine bağlanır; başlatıcıda bir `--host 0.0.0.0` seçeneği yoktur. Başka makine/şirket LAN sunucusu erişimine açılması desteklenmez. Bu, Windows installer/PyInstaller paketi değildir.

## 2. Gerçek kullanıcı ekranları

- **Genel bakış:** yerel proje sayısı, seçili çizim türü, son teknik bulgu sayısı ve **HUKUKİ HOLD** göstergesi.
- **Çizim yükleme:** Kullanıcı DXF/PDF seçer; içerik tarayıcıdan ikili veri olarak gönderilir. Sunucu **kullanıcı dosya adını saklamak için bir dosya yolu olarak kullanmaz**; otomatik proje kimliği altında `input.dxf/input.pdf` oluşturur. DXF en çok 25 milyon byte, PDF en çok 50 milyon byte.
- **Kayıtlı projeler:** Kaynak SHA-256, dosya tipi, yükleme zamanı; her projenin önceki analiz çalıştırmalarına geçiş.
- **Analiz laboratuvarı:** mevcut `run_local_pipeline` pipeline'ını `config: PipelineConfig` JSON ve çıktı formatlarıyla çalıştırır; default JSON+HTML, isteğe bağlı Markdown/PDF özet. Her koşu yeni rastgele UUID dizinindedir. Bir önceki analizin raporu korunur.
- **İnceleme ve kalibrasyon:** İlk analiz sonrasında raporun gerçek DrawingIR varlıklarından **native LINE + SEGMENT** listesi elde edilir. Kullanıcı doğru kaynak çizgi ID, bilinen metre ve incelemeci etiketi verirse ikinci analizde `USER_REFERENCE` ile kalibrasyon talep eder; `$INSUNITS`, katman adı veya PDF başlığı kendiliğinden fiziksel ölçek onayı üretmez.
- **Aşama paneli:** `IMPORT / CALIBRATION / GEOMETRY / TOPOLOGY / RULES / REPORT` aşamalarının durum/reason kodları doğrudan `pipeline-manifest.json` ile görünür. `PARTIAL_WITH_ERRORS` yeşil uygunluk olarak sunulmaz.
- **Kanıt ve rapor:** seçili çalıştırmanın `report.findings`, gerçek native referans çizgileri, frame'ler, kaynak bağlantılı `analysis.html` sayfası; indirilebilir JSON, MD, PDF ve manifest. HTML raporda mevcut `#finding`↔`#source` bağlantıları İşlem 017 tarafından sağlanır. Kanıtın mevcut olmaması mevzuat `PASS` yaratmaz.

Tarayıcı JS uygulaması `textContent` ve DOM ile veri gösterir, kullanıcı metnini `innerHTML` olarak çalıştırmaz; CSS/JS yalnız paket içindeki kendi statik varlıklarıdır. CDN veya haricî görsel/font yüklenmez.

## 3. Yerel HTTP sözleşmesi

| Yöntem / URL | İşlev |
|---|---|
| `GET /` | Türkçe dashboard HTML |
| `GET /static/dashboard.css`, `dashboard.js` | Offline statik dosya |
| `GET /api/session` | Bu yerel uygulama örneğinin CSRF token'ı ve `REGULATORY_LOCKED` |
| `GET /api/projects` | En fazla 100 yerel projenin metadata listesi |
| `POST /api/projects` | Ham DXF/PDF; `X-Mimar-Extension: dxf/pdf` ve `X-Mimar-CSRF` |
| `GET /api/projects/{project_id}` | Proje metadata ve en fazla 100 analiz çalıştırması |
| `POST /api/projects/{project_id}/runs` | `{"config": {...}, "formats": ["json","html"]}`; tek seferde yalnız bir işlem |
| `GET /api/projects/{project_id}/runs/{run_id}` | Manifest + kaynak çizgiler + bulguların sınırlandırılmış ön izlemesi |
| `GET /api/projects/{project_id}/runs/{run_id}/files/{filename}` | Sadece sabit izinli rapor dosyaları; `analysis.html` HTML olarak görüntülenir, diğerleri indirilir |

**Depolama:** `workspace/projects/<uuid>/project.json`, `input.dxf/pdf`, `runs/<uuid>/analysis.json`, `analysis.html`, `drawingir.json`, `pipeline-manifest.json` ve seçilen ek formatlar. HTTP istekleri çalışma alanı dizini, dosya yolu veya çıktı konumunu seçemez. Kaynak SHA yeniden okunmadan analiz başlamaz; değiştirilmiş yükleme reddedilir.

## 4. Güvenlik sözleşmesi ve sınırlar

1. **Loopback:** Uvicorn `127.0.0.1` dinler; `proxy_headers=False`. Middleware HTTP `Host`, ASGI peer IP, verilmişse `Origin` doğrular; remote veya DNS rebinding yönelimli Host istekleri reddedilir.
2. **CSRF:** POST isteklerine rastgele üretilen uygulama token'ı gerekir. Yerel sayfa aynı origin üzerinden oturum anahtarını alır. Bu, kimlik doğrulamalı çok kullanıcılı erişim sistemi veya yerel kötü amaçlı process'e karşı tam savunma değildir.
3. **İçerik ve depolama:** Boyut sınırı stream boyunca ve varsa Content-Length ile denetlenir. Rasgele 32 hex proje/çalışma kimlikleri, dosya allowlist, kaynak hash, path traversal ve symlink engelleri. İptal veya hata halinde yalnız yeni analiz/metadata dizini geri alınır. Kaynak PDF/DXF asla tarayıcının ilettiği dosya yolu olarak değerlendirilmez.
4. **Çıktı:** `Cache-Control: no-store`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, `X-Frame-Options: DENY`, çevrimdışı CSP. İncelenen rapor HTML'sinin kendi SVG/PNG içeriği için ayrıca script engelli CSP uygulanır.
5. **Kaynak otantikliği:** SHA eşleşmesi, görsel rapor veya inceleme formu belgenin gerçek Resmî Gazete yayımı, tarihsel yürürlük ve hukukî uzman onayı **değildir**. `RuleEngine.REGULATORY` kilidi mevcut çekirdekte aynen korunur.
6. **Kısıtlar:** Sunucu yerel tek kullanıcı taslağı; bağımsız gerçek Chrome/Edge/Windows kabulü ve sızma testi henüz yapılmamış. Birden fazla server process aynı workspace'e bağlanmamalıdır; eşzamanlı çalışma kilidi process içindedir, dağıtık kilit/e-imza/şifreli veri deposu yoktur. Büyük projelerin sonuçları UI ön izlemesinde kısıtlanır; asıl rapor dosyaları yerelde tutulur.
7. **Doğrulama:** Sentetik GitHub Actions Linux/Windows FastAPI TestClient, kaynak DXF/PDF importer ve browser varlık HTTP sözleşmesi. GUI piksel-tutarlılığı, kullanıcı deneyimi ve gerçek mimari ölçüm kabulü ayrı iş.

## 5. Sonraki mühendislik hedefi

F19 arayüz çekirdeğinin gerçek Windows/Edge kullanımı, yerel dosya/donanım performansı ve ayrıntılı form/katman etkileşimleri olgunlaştırılmalı. F20 offline Windows `onedir`/wheelhouse başlatma ve SBOM; büyük proje UI; güvenlik denetimi ilerleyen ayrı paketlerde. İşlem 019 açık veya kapanmış olsa dahi **F08–F12 HUKUKI_HOLD** korunur.
