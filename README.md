# MimarLLM V2 — Offline Mimari Analiz Çekirdeği

**ARCH-CORE Local gelecek planı:** Aynı `src/mimarllm/` modüler monoliti üstüne kaynaklı 2.5D, yerel VLM, pedagojik rubrik ve sıralı jüri yorumlarının isteğe bağlı eklenmesi. **Bu ileri-sürüm özellikleri henüz gerçek kodda yoktur.** [Birleştirilmiş master mimari](docs/master-mimari-arch-core-local.md) · [Güncel gelişim sırası](docs/uygulama-yol-haritasi.md).

**Çalışma ilkesi:** Windows-first, tek bilgisayar, internet/harici ücretli AI API/token gerektirmeyen runtime. Hedef i7 14. nesil, 32 GB RAM, RTX 4070 8 GB. **Gerçek Windows 10/11/Edge kullanıcı kabulü, tamamen offline installer ve gerçek hukukî uygunluk onayı henüz tamamlanmadı.**

## Şu anda GitHub'da bulunan gerçek yetenekler

| Bileşen | Mevcut Python kodu | Statü |
| --- | --- | --- |
| DXF/PDF kaynaklı içe aktarma | `src/mimarllm/importers/dxf.py`, `pdf.py`, `pdf_ir.py` | KISMI / sentetik CI |
| Orijinal koordinat, CAD handle, kaynak SHA, birim ve kalibrasyon | `src/mimarllm/core/ir.py`, `units.py` | KISMI / sentetik CI |
| Shapely kesişim, kapalı yüz ve duvar adayı | `src/mimarllm/geometry/spatial.py`, `walls.py` | KISMI / gerçek oda semantiği REVIEW |
| NetworkX mekan/geçiş çizgesi | `src/mimarllm/geometry/topology.py` | KISMI / sadece kaynaklı insan incelemesi |
| Teknik RuleEngine | `src/mimarllm/rules/engine.py`, `base.py` | KISMI / teknik örnekler; hukuki PASS yok |
| LegalAST, PDF kaynak ve inceleme kaydı | `src/mimarllm/legal/` | KISMI / özgün yerel PDF SHA/page/quad; hukukî geçerlilik HOLD |
| SQLite FTS5 BM25 / opsiyonel local CPU dense / RRF | `src/mimarllm/rag/` | KISMI / gerçek RG corpus kalite kabulü bekliyor |
| Kaynaklı SVG/HTML/JSON/Markdown/PDF özet | `src/mimarllm/reports/` | KISMI / PDF özet HTML ile aynı görsellikte değil |
| Bütünleşik analiz CLI | `src/mimarllm/pipeline.py`, `cli.py` | KISMI / aşama manifesti, teknik hata ve kullanıcı referansı |
| Tek kullanıcılı localhost Türkçe dashboard | `src/mimarllm/app/server.py`, `launch.py`, `static/` | KISMI / kaynaklı upload, analiz, rapor, kalibrasyon |

**Son kapanmış kod paketi:** [İşlem 019](docs/islem_019.md), GitHub-hosted **Ubuntu 295 PASS, Windows 295 PASS** sentetik test raporu: [CI 38557404737](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38557404737). Bu bir gerçek müşteri cihazında kabul testi, kusursuz otomatik CAD çizim semantiği veya hukukî sertifika değildir.

### PDF ve OCR kesin mimarisi

| İşlev | Seçilen yerel teknoloji |
| --- | --- |
| PDF native metin/vektör | `pdfplumber` |
| PDF sayfa ve ROI görseli | `pypdfium2` |
| Taranmış/eksik ROI aday metni | `RapidOCR + onnxruntime CPU` |
| PDF/DXF kaynak koordinatları | `DrawingIR`, gerçek PDF SHA/page/quad, CAD handle/layout |

OCR varsayılan otomatik tam sayfa tarama değildir. Çizim yalnız vektör metin içeriyorsa bile SHX/raster bölge ayrı değerlendirilebilir; kaynak ROI ve yeniden kalibrasyon olmadan koordinat/ölçüm kesinliği ilan edilmez. Geniş A0/A1 tiled OCR **yeni geliştirme hedefidir**, uygulanmış kabul değildir.

## Yerel çalıştırma — geliştirici kurulumu

**Python 3.11+** ve desteklenen bağımlılıklar gerekir. Aşağıdaki `pip` adımı kurulum aşamasında paketleri çevrimiçi indiriyor olabilir; paket ve wheelhouse önceden yerel diskte tutulmadıkça henüz “tam offline installer” değildir. Uygulamanın tasarlanan çalışma yolu harici AI API kullanmaz.

```powershell
# Kaynak deposu klonlandıktan sonra (Windows PowerShell)
py -3.11 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dashboard,reports]"

# Tek kullanıcı local dashboard; yalnız 127.0.0.1
.venv\Scripts\python.exe -m mimarllm.app.launch --workspace "C:\MimarLLM\workspace" --port 8765

# Aynı ortamda CLI örneği (output klasörü önceden var olmalı)
.venv\Scripts\python.exe -m mimarllm.cli analyze "C:\projeler\plan.dxf" --output-dir "C:\projeler\raporlar"
```

Tarayıcı dashboard adresi: `http://127.0.0.1:8765`. HTML/JSON/Markdown/PDF ve `pipeline-manifest.json` örneği, [pipeline kullanım şartnamesinde](docs/specs/pipeline-cli-v0.1.md). Belgeler ve kalibrasyon yalnız kullanıcının yerel kaynak verisi üzerinden çalışır; var olan raporların üzerine yazılmaz.

**Geçerlilik sınırı:** `$INSUNITS` bilinmesi `CONFIRMED` ölçek değildir. Gerçek kaynak native çizgi, bilinen metre ve açık inceleme gerekiyor. Oda-yüzeyi adayı ≠ güvenilir net alan; reviewed passage hop ≠ yangın kaçış mesafesi. RAG benzerliği ≠ hukukî doğruluk. `RuleDomain.REGULATORY` değerleri `INSUFFICIENT_EVIDENCE` ve `HUKUKI_HOLD` çerçevesindedir.

## ARCH-CORE Local — gelecek modüller (PLAN, henüz kod yok)

- **CAD güvenilirlik iyileştirmesi:** Açık/mükerrer çizgi için kaynak-koruyan onarım önerisi, Layer 0 duvar/kapı/kolon tahmini, birim hipotezi. Sanal çizgi veya histogram sonucu kesin kaynak/ölçü yerine geçmeyecek.
- **A0/A1 OCR ve mimari dil:** Bounded tiled OCR, kaynak PDF point dönüşümü; Türkçe mimari jargon eşanlamları ve lisanslı mevzuat FTS5 query expansion.
- **Yerel veri ve stüdyo görünümü:** SQLite WAL analiz geçmişi, sınırlandırılmış arka plan işçisi/SSE, 2D source overlay ve **onaylı 2.5D** Three.js görüntüsü.
- **Yerel AI ve eğitim:** GPU modeli/MMProj/Windows VRAM ölçülünce opsiyonel GGUF, structured JSON ve no-overwrite semantik aday; 8 boyutlu score-in-code rubrik ve tek modelden sıralı pedagojik yorum/perspektifler; izinli öğrenci analitiği. **Gerçek mimar/öğretim üyesinin değerlendirmesi olarak sunulmaz.**
- **TÜBİTAK 2209-A bilimsel hedefleri:** Geometri IoU/recall, OCR CER/WER, RAG Recall@10, GPU VRAM/latency, uzman karşılaştırması κ/ICC ve kullanıcı SUS. Bu ölçütler **henüz elde edilmiş sonuç değil, deney taslağıdır**.

**Yapılmayacaklar:** Bulut tabanlı OpenAI/Gemini/Claude API; mikroservis için zorunlu Qdrant/Neo4j/PostgreSQL/Redis/vLLM; ikinci `src/mimar_core` veya ayrı `ARCH-CORE/backend`; gizli ölçü tahminiyle mevzuat PASS; gerçek mevzuat/TS/kitap metninin telif hakkı olmadan yeniden dağıtımı.

## Aktif dokümantasyon ve işlem kanıtı

- [İşlem 020 — yeniden yapılandırma ve doğrulama kaydı](docs/islem_020.md)
- [ADR-004 — ARCH-CORE Local opsiyonel eğitim kapsamı](docs/adr/ADR-004-ARCH-CORE-Local-Kapsam-Genislemesi.md)
- [TÜBİTAK 2209-A araştırma/12 aylık iş paketleri taslağı](docs/tubitak-2209a-is-paketleri.md)
- [Master sistem mimarisi](docs/master-mimari-arch-core-local.md)
- [F01–F37 kapsam/uygulama envanteri](docs/ozellik-envanteri.md)
- [İşlem 020–031 geliştirme sırası](docs/uygulama-yol-haritasi.md)
- [Yedi risk + alternatif plan + bilimsel test matrisi](docs/risk-ve-dogrulama-matrisi.md)
- [Güncel dosya düzeni — mevcut vs plan](docs/planlanan-dosya-yapisi.md)
- [Kapsam ve hukukî/güvenlik kapıları](docs/kapsam.md)
- [İşlem 019 localhost dashboard API/tehdit modeli](docs/specs/dashboard-v0.1.md)

**Lisans ve veri gizliliği:** Public depoda özel müşteri/öğrenci çizimi, model ağırlığı, tam lisanslı TS standardı, gerçek mevzuat korpus kopyası veya yerel SQLite arşivi yayımlanmaz. Gelecekteki wheelhouse/installer/native kütüphane/GGUF model lisansları SBOM ve yeniden dağıtım kontrolüne tabidir. Tüm bağımlılıkların “%100 permissif” olduğu şu an sertifikalanmadı.


## İşlem 021 — Windows çevrimdışı dağıtım kaynakları (aday, üretim kabulü değil)

- [İşlem 021](docs/islem_021.md) · [Windows offline paketleme şartnamesi](docs/specs/windows-offline-package-v0.1.md) · [Betik yönergeleri](scripts/windows/README.md).
- **Kodlandı:** `run.bat` (mevcut yerel Python ortamıyla başlat), `install_offline.bat` (SHA doğrulanmış tekerlek cache'i ve `pip --no-index` ile bilinçli kurulum), `build_exe.bat`, `mimar.spec` (Win32/PyInstaller `onedir` tarifi, `upx=False`), `scripts/windows/launch_dashboard.py` (gerçek FastAPI/127.0.0.1 ve kullanıcı `LOCALAPPDATA` workspace), `scripts/windows/package_manifest.py` (wheel/distribution SHA256, beyan lisans metadata), `build_wheelhouse.ps1` (yalnız açık `-AllowNetwork` hazırlama).
- **Kullanım:** Windows'ta önce bilinçli hazırlık ve hash kontrolü; `install_offline.bat` → `run.bat`. Kurulu PyInstaller ortamından `build_exe.bat` olası `dist/MimarLLM_V2/MimarLLM_V2.exe` için `--self-check` (statik UI ve dependency import) talep eder. SHA manifest elektronik imza veya ticari lisans onayı değildir.
- **Durum:** F20 `KISMI/MEVCUT_KOD` — paketleme **kaynak kodu ve sentetik CI sözleşmesi** mevcut. **Gerçek exe derlemesi, offline temiz Windows kurulum, installer/MSI, DLL bağımlılık/NOTICE-lisans hakları ve yerel kullanıcı Edge tıklama testleri henüz doğrulanmadı.** İşlem 020'de planlanan ARCH-CORE GPU/VLM/2.5D/jüri kodu yok. F08–F12 `HUKUKI_HOLD`.


## İşlem 022 — Kaynak-koruyan CAD onarım adayları

- [İşlem 022](docs/islem_022.md) · [Onarım overlay v0.1 teknik şartnamesi](docs/specs/source-preserving-repair-v0.1.md).
- **Kodlandı:** `geometry/repair.py` ile native CAD kaynağındaki kısa uç boşluğu / önerilen snap, çakışan ve tekrarlı çizgiler için `RepairOverlay` + `RepairCandidate` (salt-okunur). Gerçek kaynak SHA, frame, DXF CAD handle, blok yolu ve entity ID korunur. `geometry/repair_viewer.py` lacivert özgün çizgi/turuncu kesikli sanal bağlantı SVG'si oluşturur.
- **Yalnız kaynak hipotezi:** `UnitHypothesis` mevcut `$INSUNITS`/kalibrasyon beyanını özetler; `Layer0SemanticCandidate` katman 0 çizgilerini kullanıcıya sınıflandırma **adayı** olarak gösterir. Ne fiziksel metre, ne otomatik duvar/kapı/oda, ne yangın kaçış bağlantısı, ne hukukî PASS üretilir. Onarım orijinal `DrawingIR` veya `RuleEngine` verisine uygulanmaz.
- **Durum:** F25 `KISMI/MEVCUT_KOD`; F26 `KISMI` (yalnız birim header, dimension/door histogramı yok); F27 `KISMI` (Layer0 yalnız inceleme; HATCH/ARC mimari semantik yok). Gerçek kirli CAD ve Windows/Edge kullanıcı kabulü, resmî mevzuat sürümleri ve F08–F12 `HUKUKI_HOLD` açık.


## İşlem 023 — A0/A1 PDF opt-in karo/ROI OCR (kaynak kanıtlı, kısmi)

- [İşlem 023](docs/islem_023.md) · [Karo OCR v0.1 teknik sözleşmesi](docs/specs/tiled-ocr-v0.1.md).
- `src/mimarllm/ocr/tiles.py` kullanıcı seçtiği PDF page-point ROI için küçük overlap karoları yaratır; dosya SHA, rotasyon, sayfa ve CropBox, tile/total pixel ve OCR candidate bütçe denetimi. Mevcut `RapidOCR + onnxruntime CPU` **isteğe bağlı**, çevrimdışı kurulmuş olmalı; hiç OCR modeli otomatik indirilmez.
- `importers/pdf_ir.py` ve `pipeline.py` OCR token'larını yalnız `OCR_CANDIDATE`, sayfa/quad/source SHA, şema `REVIEW_REQUIRED` olarak tutar; overlap'teki gerçekten aynı metin+konum tekrarlarını ayırır. `PipelineManifest` OCR tile/token/dedup ve `layout_candidates` kaydeder. `ocr/layout.py` sağ-alt antet/üst-alt marjda **sadece konum ipucu** üretir.
- `mimarllm analyze local.pdf --config tiled.json --output-dir out` örneği teknik şartnamede. Varsayılan OCR kapalı. Döndürülmüş çok büyük sayfa ve özel CropBox güvenli kaynak dönüşümü doğrulanmadıysa reddedilir.
- **Gerçek A0 taranmış belge OCR CER/WER ve bellek benchmark, gerçek Windows/Edge kabulü, gerçek hukukî mevzuat sertifikası yapılmadı.** F04/F28 KISMI; F08–F12 HUKUKI_HOLD.


## İşlem 024 — Türkçe mimari RAG arama ipuçları ve yerel cache

- [İşlem 024](docs/islem_024.md) · [Teknik şartname](docs/specs/rag-lexicon-v0.1.md).
- **Kod:** `rag/lexicon.py` Türkçe tam terim/çok sözcüklü **arama ipuçları** (`ışıklık`, `ışık kuyusu`, `kapı temiz/net genişliği` gibi); `search_legal(..., lexical_expansion=True)` opt-in, özgün BM25 eşleşmeleri ilk sırada, alternatifler ek aday. Metin/LegalAST/source PDF quad ve `UNREVIEWED` korunur.
- **Yerel SQLite:** `rag_lexical_cache` azami 128 FTS arama kimliği ve sıralı passage ID saklar, query/filter/limit için ayrı anahtar; PDF görüntüsü veya ham kullanıcı sorgusu değil. Re-index ve passages SQL trigger'ları cache'i temizler; PDF varlığı ve SHA her sonucun gösteriminde tekrar denetlenir. Başarısız indeksleme eski dizini/önbelleği bozmaz.
- **Hukukî ve semantik sınır:** İpucu sözlüğü mevzuatın **resmî eş anlam sözlüğü değildir**; cache relevance veya yürürlük doğruluğu sağlamaz. Gerçek Türkçe öğrenilmiş embedding benchmark, çok yıllı Resmî Gazete, uzman onayı ve gerçek Windows kabulü HOLD. F29 yalnız başlangıç/kurasyonlu aday; F30 yalnız yerel arama cache'i, **WAL, genel workspace geçmişi ve retention yok**. F08–F12 HUKUKI_HOLD.

## İşlem 025 — Kaynaklı 2B inceleme ve yerel iş durumları (Draft PR #2)

- [İşlem 025 kaydı](docs/islem_025.md) · [API/önizleme şartnamesi](docs/specs/dashboard-2d-jobs-v0.1.md).
- Yeni iş hattı `POST /api/projects/{id}/jobs` (202) + `GET /api/projects/{id}/jobs/{job_id}` ile yerel, sınırlı, geçici `QUEUED/RUNNING/COMPLETED/FAILED` durumlarını verir. Tek worker, en fazla 4 aktif/bekleyen. Eski senkron `/runs` API'si bozulmaz.
- 2B arayüz mevcut kaynağa bağlı native LINE çizgileri için frame/katman filtreli **salt-okunur** SVG önizleme ve SHA/entity/handle/nokta incelemesi sunar. Henüz gerçek CAD edit, kalıcı anotasyon veya kesin mekân tanıma değildir.
- GitHub-hosted [CI 38834544453](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38834544453): Ubuntu 364 PASS/1 SKIP, Windows 365 PASS; gerçek Windows/Edge kullanıcı/performans kabulü ve son PR head CI ayrı. `main` değil, aday `feature/islem-025-source-2d-jobs` dalındadır.

- **Manuel review notu (025 ek aday):** Seçili native LINE/PDF_LINE kaynağına SHA+frame/entity bağlı kullanıcı gözlemi `run/review-notes.json` sidecar'ına yazılır. Kullanıcı notu geri alırsa audit izi korunur. `GET/POST /reviews` ve `DELETE /reviews/{review_id}` yalnız localhost/CSRF kapıları ile; gerçek CAD dosyası, DrawingIR ve analiz raporu değişmez. Bu bir hukukî/teknik uygunluk onayı veya CAD geometrik edit işlemi değildir.


### İşlem 025 ek teslim — Kaynak-koruyan DXF revizyonu (henüz Draft)

- Artık \`cad:Model\` direct \`LINE\` uçlarına dayanarak yeni **türetilmiş** DXF \`drawing.dxf\` revizyon dosyası oluşturma, kaynağa ve CAD handle'a bağlı SHA denetimi, indir ve undo vardır. Orijinal input DXF / DrawingIR / analiz raporu üzerinde değişiklik yapılmaz. PDF veya nested block edit yapılmaz.
- [DXF revizyon sözleşmesi](docs/specs/dxf-revisions-025.md), [gerçek Windows/Edge kabul protokolü](docs/specs/windows-acceptance-025.md), \`scripts/windows/acceptance_025.ps1\`.
- GitHub-hosted sentetik [CI 38850588365](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38850588365) Windows **370 PASS**, Ubuntu **369 PASS / 1 SKIP**; sentetik 500 çizgili bellek/süre profili yalnız build makinesi içindir.
- Gerçek cihaz, onedir dağıtım, Edge etkileşim/erişilebilirlik, gerçek CAD/PDF ölçümü ve bağımsız kullanıcı/uzman kabulü yapılmadı. İşlem 025 Draft, \`main\` değil. \`026\` ve üretim bekletilir.


## 2026-10-16 — Geliştirme ve nihai fiziksel kabulün ayrılması

Kullanıcı kararıyla **İşlem 025'in fiziksel Windows/Edge, gerçek çizim, performans ve offline exe testleri son İşlem 031'e ertelendi.** 025'in 2B/LINE revizyon-kaynaklı not/job uygulaması mevcut sentetik Linux/Windows CI ve GitHub-hosted Edge smoke açısından mühendislik adayıdır; hedef cihazda gerçek kullanıcı tarafından kabul edilmiş ürün değildir.

**Sıra:** 025 mühendislik kod adayı → 026 kaynaklı 2.5D → 027 yerel VLM → 028 rubrik → 029 jüri → 030 öğrenci analitiği → 031 tüm gerçek cihaz/saha, bağımsız performans/hukukî uzman kabulü. Her ara aşamada sentetik regresyon ve güvenlik testleri devam eder. Gerçek kabul ertelenmesi üretim dağıtımına izin vermez. Mevcut Draft PR #2, ana dalın üretim kodu sayılmaz. Ayrıntılar [güncel yol haritasında](docs/uygulama-yol-haritasi.md) ve [karar defterinde](docs/kararlar.md).
