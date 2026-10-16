# MimarLLM V2 — Bağımlılığa Dayalı Uygulama Yol Haritası

- **Tarihsel kök:** [İşlem 006](islem_006.md) · **Güncel yeniden baz:** [İşlem 020](islem_020.md), 2026-10-15.
- **Referans:** [özellik envanteri](ozellik-envanteri.md), [master mimari](master-mimari-arch-core-local.md), [2209-A iş paketleri](tubitak-2209a-is-paketleri.md).
- **Durum:** 001–019 çekirdek/UI kodu kısmi mevcut; 020 yalnız master mimari/dokümantasyon; **021 Windows dağıtım betikleri + sentetik CI kısmi mevcut, gerçek onedir Windows cihaz kabulü HOLD**. 022–031 gelecek plan numaralarıdır.

## 1. Sabit mimari kararlar

Tek paket: `src/mimarllm`. Tek kullanıcı, offline-first, modüler monolit. CPU geometri/topoloji/kural, yerel RAG (SQLite FTS5 ve CPU embeddings); yerel VLM yalnız semantik aday ve GPU bütçesi içinde. PDF/OCR: `pdfplumber + pypdfium2 + RapidOCR(onnxruntime CPU)`. Teknik ve hukukî kanıt ayrı doğrulanır.

## 2. Güncel işlem takvimi — 2026-10-15 yeniden baz çizimi

**Kanonik kapsam:** [ARCH-CORE Local master mimari](master-mimari-arch-core-local.md). **Risk/kalite:** [B planları](risk-ve-dogrulama-matrisi.md). **Durumlar:** MEVCUT KOD / KISMI / PLAN / HUKUKI_HOLD / AR-GE, “tüm sistem tamam” anlamına gelmez. Gerçek işlem numarası yeni GitHub kaydı açıldığı zaman geçerlidir.

| GitHub kayıt | İşlev / modül | Durum / bağımlılık | Kesin kabul sınırlaması |
| --- | --- | --- | --- |
| `islem_001–006` | ilk kapsam, offline mimari, PDF/OCR kararları | TARİHSEL / KAPALI | özgün kayıtlar değişmez |
| `islem_007–009` | DrawingIR + birimler + DXF/PDF/OCR source bağlantısı | KODLANDI/KISMI | native handle, page, quad, SHA; gerçek saha HOLD |
| `islem_010–012` | Shapely, NetworkX, RuleEngine | KODLANDI/KISMI | unclassified face, reviewed passage; hukukî PASS yok |
| `islem_013–016` | LegalAST, FTS5+RRF, hukukî source/version HOLD, PDF review | KODLANDI/KISMI | resmî yürürlük ve etkili sürüm HOLD |
| `islem_017–019` | kaynaklı HTML/JSON/MD/PDF, CLI pipeline, localhost dashboard | KODLANDI/KISMI | İşlem 019 CI Linux/Windows 295 PASS; gerçek kullanıcı cihazı HOLD |
| **`islem_020`** | **Bu yeniden mimari ve ARCH-CORE Local geliştirme planı** | **DOKÜMAN KARARI** | Kod/jüri/3D/modeller eklenmiş sayılmaz |
| `islem_021` | Windows-first offline wheelhouse/onedir, başlatıcı, SBOM | KISMI / KODLANDI — kaynak betikleri; actual Windows exe HOLD | `run.bat`, `install_offline.bat`, `mimar.spec`, SHA/metadata manifest, sentetik Linux/Windows CI; gerçek PC ve ticari dağıtım doğrulaması en sonda |
| `islem_022` | Kirli CAD kaynak-koruyan repair-overlay; unit hypothesis; Layer0 heuristik | PLAN, 007–011 | önerilen geometri/orijinal entity ayrılır; SI onayı yok |
| `islem_023` | A0/A1 tile/ROI OCR ve belge layout/antet konum adayları | KISMI / KODLANDI, 009/022 | bounded tile, PDF source quad/dedup, sentetik CI; gerçek OCR/CER/RSS finalde |
| `islem_024` | Türkçe mimari arama ipuçları + sınırlı SQLite RAG pasaj cache'i | KISMI / mevcut kod, 013–015/019 | Opt-in kurasyonlu FTS arama, SHA izolasyonu; genel workspace/WAL/retention HOLD |
| `islem_025` | Dashboard 2B kaynak çizgisi, bounded işler, dar DXF Model LINE revizyon/undo | MÜHENDİSLİK_ADAYI / SENTETİK_CI_PASS / DRAFT PR #2 | fiziksel Edge, gerçek CAD/PDF ve offline exe yalnız son İşlem 031 kabulünde; 026'yı bloklamaz |
| `islem_026` | Kaynak bağlı 2.5D prizma ve çevrimdışı Three.js | MÜHENDİSLİK KOD ADAYI / SENTETİK_CI_PASS, 025 bağımlı dal | Yalnız doğrudan CAD Model LINE + bağımsız CONFIRMED ölçek + kullanıcı beyanı yüksekliği; fiziksel UAT 031 |
| `islem_027` | Yerel GGUF/MMProj VLM, VRAM profiler, structured response/no-overwrite | AR-GE, 023/025 | model Windows/8GB ölçümü, GPU fallback gerçek QA |
| `islem_028` | Sekiz boyutlu rubrik ontolojisi/weight/supervisor, score-in-code | PLAN, 017/027 bağımsız GPU modu | uzman onaylı kriter yoksa otomatik gerçek not yok |
| `islem_029` | Sıralı pedagojik jüri/persona/ton (isteğe bağlı) | PLAN, 027/028 | çok metinsel persona = bağımsız uzman oyu değildir |
| `islem_030` | Öğrenci analitiği, trend, izinli geçmiş ve radar rapor (isteğe bağlı) | PLAN, 028/029 | onam, küçük örneklem belirsizliği, kimlik/gizlilik |
| `islem_031` | Son fiziksel Windows/Edge/onedir, gerçek CAD/PDF/A0, bağımsız benchmark, GPU, kullanıcı/uzman ve 2209-A kabulü | SON KABUL / HOLD, 026–030'dan sonra | 021–030'un tüm ertelenmiş fiziksel ve gerçek veri testleri burada toplanır; ölçülmeyen kappa/Recall/FPS/süre vaadi yok |
| ayrı hukukî kapı | Gerçek kaynaktan madde/fıkra, değişiklik/yürürlük konsolidasyonu, projeye uygulanabilirlik ve uzman onayı | **F08–F12 HUKUKI_HOLD** | onaysız kural threshold ve "uygunluk sertifikası" yok |

**İşlem 020 sadece plan ve doküman revizyonudur.** Önceki planın `islem_020` Windows paketleme hedefi, kullanıcı tarafından sağlanan yeni kapsam nedeniyle `islem_021`'e; önceki `islem_021` VLM odağı `islem_027`'ye; eski `islem_022` benchmark hedefi son kabul `islem_031`'e taşındı. Bu yer değiştirme **geçmiş işlem dosyası yeniden numaralandırması değildir**.

## 3. Mühendislik paketlerine göre teslim sırası

**Çekirdek P0 (kısmi çalışan):** Kaynak-bağlı DXF/PDF ve raporlar, CLI, tek kullanıcı localhost ekran. **P1:** paketleme ve kirli CAD/kalibrasyon/OCR kalitesi. **P2:** RAG terminoloji ve yerel kalıcı veri + kaynaklı UI. **P3 (isteğe bağlı):** kanıtlı 2.5D önizleme. **P4 (AR-GE):** yerel VLM strict schema; **P5 (eğitim genişlemesi):** rubrik/jüri/analitik. **P6:** gerçek benchmark/saha/Windows/GPU bilimsel son kabul.

```text
Mevcut deterministik V2 [MEVCUT KOD / KISMI]
    |
    v
Windows dağıtım + kirli CAD, ölçek, PDF kalite kapıları [PLAN]
    |
    v
Kaynaklı gözlem/RAG terminoloji + local UI [PLAN]
    |
    +----> 2.5D, yerel VLM semantik aday [PLAN / AR-GE]
                 |
                 +----> rubrik, pedagojik jüri, eğitim analitiği [PLAN]
    |
    v
Gerçek cihaz + resmî kaynak + eğitim uzmanı + 2209-A kabul [BAĞIMSIZ]
```

## 4. Değişmeyen fail-closed sözleşmeler

- DXF `$INSUNITS`/dimension/door histogramı **INFERRED**; orijinal CAD/PDF koordinatları yerinde, SI yalnız açık doğrulanmış referansla.
- Virtual door bridging ve toleranslı snap **repair overlay**; orijinal çizimde sessiz değişiklik ve kendiliğinden certified room/net-brut alan yok.
- Reviewed NetworkX geçidi yangın **yürüme mesafesi** değildir. Kat/çıkış/yol engelleri, bina profili ve hükmün doğru sürümü olmadan mevzuat iddiası yok.
- VLM/persona daima çekirdek teknik ve hukukî kanıt üzerinde **yorum/adayı**; kesin sayı/alan/kapı/medeni norm hükmü üretemez.
- Model/MMProj/lisans/VRAM/CUDA gerçek Windows ölçümü olmadan Qwen/başka model default seçim ya da performans garantisi yok.
- Gerçek müşteri, uzman, mevzuat onayı ve Windows kabul **son aşamada**; sentetik CI her modülde sürer, güvenlik/hukukî HOLD hiçbir anda kalkmaz.

## 5. Tarihsel geliştirme notları (İşlem 007–019)

Aşağıdaki notlar tarihsel olarak bırakılmıştır; içlerindeki “bir sonraki işlem henüz yapılmadı”, “ilk çalışan modül yok” gibi geçmiş zamanlı ifadeler **bugünkü durum değildir**. Güncel kod gerçeği, İşlem 019 kapanış kaydı, bu 020 master ve yukarıdaki yeniden baz çizimidir.

## İşlem 007 yürütme notu (2026-10-13)

`islem_007` dosyası oluşturuldu ve `core/ir.py`, `core/units.py`, kaynak/kalibrasyon sentetik testleri kodlandı. Gerçek test/CI sonucu ilgili [işlem kaydında](islem_007.md) izlenir. Sonraki mühendislik işi [islem_008] kapsamında `ezdxf` ile DXF entity/layout/nested INSERT + `DrawingIR` köprüsüdür. İleri aşamalardaki hukukî `HOLD` kararları değişmedi.


## İşlem 008 uygulama notu (2026-10-13)

`islem_008` ön kaydından sonra `src/mimarllm/importers/dxf.py` ve `layers.py` eklendi. DXF/CAD handle, nested INSERT/MINSERT, vektörel WCS 2B geometry, katman ve ayrı annotation adayları için sentetik testler oluşturuldu. F02 `KISMI/MEVCUT_KOD`: gerçek Windows saha testi yapılmadı.

Sıradaki `islem_009`: `pdfplumber` glyph/vektör, `pypdfium2` ROI ve `RapidOCR` poligonlarını aynı `DrawingIR` kaynak frame ile bağlamak; PDF source page/rotation/crop ve y-ekseni dönüşümlerinin sentetik kabulü.


## İşlem 009 uygulama notu (2026-10-13)

`src/mimarllm/importers/pdf_ir.py` ile PDF native ve açıkça istenen OCR ROI kaynakları DrawingIR v0.1'e bağlandı. 90° ROI render'da PDFium doğrudan crop uyuşmazlığı sentetik testte tespit edildi; güvenli çözüm: **döndürülmüş sayfalarda yalnız sınıra sığan tam sayfayı rasterleştirip Pillow ile ROI al**. `CropBox != MediaBox` durumu yanlış koordinat göstermemek adına şimdilik reddedilir. F03/F04 kabul kapıları için [islem_009.md](islem_009.md) güncel referanstır.

**Sırada:** `islem_010` Shapely geometri; güvenilir duvar iç sınırı, oda poligonu, topolojik açıklık adayı ve kalibrasyonsuz net alan `INSUFFICIENT_EVIDENCE`.


## İşlem 010 uygulama notu (2026-10-13)

`src/mimarllm/geometry/spatial.py` ve `walls.py`, sentetik **gerçek DXF kaydedip açma** + PDF DrawingIR üzerinde Shapely ile doğrulanmış geometrik aday hesaplarını içerir. Frame-bound kaynak SHA/ID, kesişim/tolerans, açık/overlap teşhisleri ve yalnız **reviewer seçilmiş iç yüz/footprint** için CONFIRMED ölçek sonrası alan sözleşmesi eklendi. Büyük pafta `max_segments/max_pairs` kısıtına tabidir; yüksek hacim spatial index optimizasyonu sonra.

F05 `KISMI`: sentetik geometri testleri Linux/Windows CI'da çalışır, gerçek oda/duvar semantiği halen HOLD. Sonraki islem_011: **NetworkX ile oda ve geçiş grafı**, otonom kapı/yangın tespiti iddiası olmadan doğrulanmış adjacency kanıtı.


## İşlem 011 uygulama notu (2026-10-13)

NetworkX `MultiGraph` ile inceleme izine bağlı `ROOM/CORRIDOR/BALCONY/STAIR/LANDING` ve `DOOR/ARCHWAY/OPEN_PASSAGE/EXTERIOR_DOOR` beyanları, Shapely polygon ortak kenar gerçekliği, kaynak marker yakınlık kontrolü, missing review/inconsistent geometry durumda **kenar reddi**, connected components, articulation, bridge ve passage listeli erişim yolu kodlandı. Kaynak SHA ve orijinal native entity ID'leri korunur.

F06 yalnız sentetik tek kat/topolojik kanıta dayalı çalışır; yangın kaçış yolu **metre** veya sınıflandırılmamış otomatik geçiş değildir. Sıradaki `islem_012` deterministik kural motoru sözleşmesi, `APPROVED_FOR_CHECK` hukukî kaynak koşulu. [islem_011](islem_011.md).


## İşlem 012 uygulama notu (2026-10-13)

`RuleEngine` teknik/sentetik değerlendirmeleri, 6 sonuç durumu, kısıtlı Pydantic rule tanımı ve DrawingIR/Shapely/NetworkX'ten tekrar üretilen kanıtlarla kodlandı. Semantik bağ ve `source_sha256/frame_id/evidence_ids` çıktısı kullanılıyor. Ölçüm belirsizliği eşikte `REVIEW_REQUIRED`; sahte kaynak `ERROR/REVIEW_REQUIRED`; eksik ölçüm/kısmi graph `INSUFFICIENT_EVIDENCE`.

**Yönetmelik için hiçbir hazır PASS yolu yok.** Kaynak meta verisi verilmese veya verilmiş gibi yapılsa dahi bütün `REGULATORY` kuralları yasal kaynak onayı olmadan kilitlidir. F07 sadece `KISMI / MEVCUT_KOD`; F08–F12 HUKUKI_HOLD devam. Sonraki `islem_013`: çevrimdışı mevzuat PDF→LegalAST ve özgün konum/versiyon; gerçek yasal norm doğrulaması bundan sonra da ayrı kabul gerektirir. [İşlem 012](islem_012.md).


## İşlem 013 uygulama notu (2026-10-13)

`src/mimarllm/legal/{models,extractor,parser,changes,etl}.py` ile çevrimdışı **orijinal PDF→unreviewed LegalAST** çekirdeği geliştirildi. Native PDF metni/tablo hücresi ve açıkça seçilen sayfalarda RapidOCR CPU quad sonuçları özgün dosya `SHA-256 + PDF page index + source polygon` ile bağlanır. Madde/fıkra/bent, geçici madde ve satır içi fıkra parser'ı ile değişiklik/yürürlük/ilga/istisna ifade adayı vardır.

**Önemli sınır:** Değişiklik zinciri tarihsel konsolidasyonu veya hukukî sürüm doğrulaması bu işlemde yapılmaz; metadata kullanıcı beyanı olarak saklanır. F13 yalnız `KISMI/MEVCUT_KOD`. F08–F12 HUKUKI_HOLD ve islem_012 RuleEngine REGULATORY kilidi devam eder. Sıradaki `islem_014` LegalAST SQLite FTS5+yerel semantik retrieval, kaynak bbox'ına geri dönüş.


## İşlem 014 uygulama notu (2026-10-13)

`src/mimarllm/rag/` içinde offline **SQLite FTS5 BM25 + isteğe bağlı CPU local SentenceTransformer + bounded cosine + RRF** kodlandı. `LegalAST` source spans ve tablo cell bbox kayıtları, source PDF hash/0-based page, adım hiyerarşisiyle veritabanına alınır; `search_legal` PDF'de vurgulanabilir konum adaylarını döner. Testler sentetik gerçek PDF'den SQLite ingest→lexical ve sentetik dense rank→RRF akışını kapsar.

F14 `KISMI/MEVCUT_KOD`; gerçek embedding Türkçe benchmarkı, gerçek Resmî Gazete çok yıllı corpus ve hukuki yürürlük onayı henüz yok. **Arama skoru ve aday doküman sonucu hiçbir `RuleEngine.REGULATORY` kilidini açmaz.** Sonraki iş islem_015: kaynak doğrulama/effectivity/applicability sürümlü bağlantısı ve kural bağlayıcı güven kapısı; mevcut hukukî HOLD korunacak.


## İşlem 015 uygulama notu (2026-10-13)

`legal/verification.py`, `versions.py`, `applicability.py` ve `rules/evidence.py` ile yerel PDF kaynak byte/page/quad denetimi, açıklanmış değişiklik hedef–kaynak bağları, proje tarih/yer/yapı/istisna eksikleri ve `RuleDefinition`→LegalAST node→RAG hit tam eşleştirme kodlandı. Yalnız beyanların birbirini tutması hukukî gerçek tarih/istisna veya resmî yayın kaynağını **doğrulamaz**.

F15 `KISMI/MEVCUT_KOD`. F08–F12 mevzuat paketleri hâlâ `HUKUKI_HOLD`; kural eşikleri yazılmayacak. İzleyen mühendislik: kaynak belgeyi görsel olarak inceleme, tarihsel sürüm konsolidasyonu, uzman audit/imza kapıları ve sonrasında ayrı teknik mimari denetimler. [İşlem 015](islem_015.md).


## İşlem 016 uygulama notu (2026-10-14)

`legal/review.py`, `review_viewer.py`, `review_ledger.py` ve `version_workflow.py` ile kaynak PDF'de sarı kanıt polygonu ve offline incelemeci karar JSON taslağı, gerçek node/table cell/amendment source seçimi, iki farklı orijinal PDF arasında beyanlı tarihsel karşılaştırma, hash-chain yerel inceleme günlüğü kodlandı.

**Hukukî sürüm doğrulaması tamamlanmadı:** kaynak resmiyeti, yürürlükte konsolide hükümler, yerel uygulama geçiş/istisna kararları ve kurumsal onay bağımsız olarak bekleniyor. Kullanıcı `VISUALLY_MATCHED` seçimi yalnız metin/konum inceleme beyanıdır. F08–F12 HUKUKI_HOLD; F17 raporlama ve genel F18 CAD/PDF çizim görsel bulgu katmanı ayrı geliştirmedir.


## İşlem 017 uygulama notu (2026-10-14)

`reports/models.py`, `builder.py`, `visualizer.py`, `exporter.py` ile DrawingIR geometrik entity kanıtı, sentetik RuleEngine teknik sonuçları, Shapely yüzey/issue ve NetworkX issue raporun tek kaynak şemasında birleştiriliyor. Teknik bulgulardan source CAD handle/layout veya orijinal PDF page/frame'a, ayrıca bağımsız `RegulatoryEvidenceEvaluation` varsa LegalAST PDF node/quad'ına **çift yönlü çevrimdışı HTML anchor** akışı; JSON/Markdown/HTML ve isteğe bağlı PDF metin özeti. Yanlış source hash/frame/olmayan ID veya hukukî PDF mismatch yanlış kaynak göstermeden reddedilir.

F17/F18 `KISMI/MEVCUT_KOD`; PDF özet HTML'nin görsel etkileşimiyle aynı değildir, CAD SVG yalnız rapordaki kaynak geometrinin vektör görünümüdür. F16 pipeline/CLI, F19 dashboard, tam Windows dağıtımı ve hukukî kaynak yürürlük kabulü ayrıca kalır. F08–F12 `HUKUKI_HOLD`. Sonraki paket için `docs/islem_018.md` önce açılmalı.


## İşlem 018 uygulama notu (2026-10-14)

`src/mimarllm/pipeline.py` ve `cli.py` tek yerel .dxf/.pdf dosyasıyla çalışır, kesintisiz source SHA/frame korur. Fiziksel kalibrasyon yalnız native kaynak segmenti üzerinde insan kaynaklı referans; açık `ReviewedTopology` olmadan kapı/kaçış/oda semantiği oluşturulmaz. `RuleRun` yalnız kullanıcı tarafından seçilen `RuleDefinition` ve kaynak evidence'i değerlendirir, yasal RuleEngine kilidini kaldırmaz. `reports/builder.py` çok frame Geometries/Topologies ve kaynak bulgu olmasa da çizim gözlemi göstermeyi destekler. JSON/HTML/MD/isteğe bağlı PDF ve detaylı `pipeline-manifest.json`; hata `PARTIAL_WITH_ERRORS` exit 4 ve görsel kanıtın eksikliği belirtimi.

**Açık sonraki sınır:** F16 `KISMI/MEVCUT_KOD`; F19 dashboard henüz oluşturulmadı ve eski islem_018 yol haritası satırından çıkarıldı (bu değişiklik yalnız **plan durumunun güncellenmesidir**, UI varmış gibi davranılmaz). F20 Windows installer, gerçek Windows 10/11 ve gerçek dosya kabulü, gerçek RG/kural yürürlük onayı ayrıca. `docs/islem_019.md` sonraki işlemin ilk GitHub değişikliği olarak açılmadan kod yazılmamalı.


## İşlem 019 uygulama notu (2026-10-14)

`app/server.py` FastAPI, `app/launch.py` localhost-only Uvicorn ve `app/static` bağımsız Türkçe CSS/JS ile çalışan **gerçek tek kullanıcılı tarayıcı UI çekirdeği** eklendi. Uygulama REST üzerinde yerel DXF/PDF yükler, ŞA+orijinal source ile `run_local_pipeline` ve `export_report` çağırır, aşama/reason kodları, kaynak native çizgi ID, kalibrasyonlu ikinci analiz ve HTML kaynak raporu sunar. Bir işlemde hata varsa `PARTIAL_WITH_ERRORS` saklanır; resmî yasa PASS yok.

**Eski plan değişikliği (yeni uygulama değil):** İşlem 019 eskiden F20 Windows paketleme olarak listelenmişti. F19'un hiç kodlanmamış olması nedeniyle İşlem 019 bu F19 dashboard çekirdeğine ayrıldı; F20 Windows offline dağıtım İşlem 020'ye, daha sonraki VLM/benchmark satırları 021–022'ye kaydırıldı. İşlem 001–018 kayıtlarına müdahale edilmedi.

**F19 KISMI/MEVCUT_KOD:** sentetik ASGI/GitHub-hosted Linux+Windows; gerçek Windows 10/11/Edge cihaz kullanıcısı, sızma testi ve üretim LAN sunucusu kabulü HOLD. **F08–F12 HUKUKI_HOLD**. Bir sonraki kod işleminde ilk GitHub yazımı `docs/islem_020.md` olmalıdır.


## İşlem 021 uygulama notu (2026-10-15)

F20 için kaynak dosyaları: `run.bat` (hazır yerel ortam), `install_offline.bat` (hash verified wheel cache; `--no-index`), `build_exe.bat`, `mimar.spec` (gerçek F19 dashboard için Windows PyInstaller onedir tarifi), `scripts/windows/build_wheelhouse.ps1` (yalnız bilerek `-AllowNetwork` verilen network hazırlama), `launch_dashboard.py` (LOCALAPPDATA workspace ve `--self-check`), `package_manifest.py` (SHA256 / local distribution metadata / lisans HOLD envanteri). Gerçek exe/temiz Windows kurulum/dağıtım lisans bağımsız kabul **yapılmadı**. Kodun CI'da statik/manifest sözleşmeleri test edilmiş olması Windows binary smoke PASS değildir.

**Sonraki GitHub geliştirme:** `docs/islem_022.md` önce oluşturulmalı; kirli CAD geometrisi *onarım adayı* ve orijinal DrawingIR CAD handle/source frame değişmezliği. Bir sonraki paket üretilmeden önce 021 kayıt kapanışı, CI kanıtı ve kaynak dosya doğrulaması tamamlanacak. ARCH-CORE GPU/2.5D/jüri henüz PLAN/AR-GE.


## İşlem 022 uygulama notu (2026-10-16)

`src/mimarllm/geometry/repair.py` ile orijinal `DrawingIR` kaynak SHA/frame/CAD handle/blok yolu üzerinde salt-okunur kısa boşluk sanal köprü, uç snap, duplicate/overlap çizgi `RepairCandidate` katmanı geliştirildi. `geometry/repair_viewer.py` kaynak çizgiyi lacivert, önerileri turuncu kesikli SVG gösterir. Geometri önerisi `RuleEngine`, `TopologyResult`, gerçek `assess_area` veya tek gerçek DrawingIR kaynağına yazılmaz. Belirsiz komşu uç ve bütçe aşımı reddedilir; kapı boşluğu otomatik kapanmaz.

**F25 KISMI/MEVCUT_KOD**, **F26 KISMI** (mevcut header fiziksel birim ipucu, gerçek dimension/door histogramı yok), **F27 KISMI** (Layer0 kaynak adayı, ARC/HATCH semantiği yok). F08–F12 HUKUKI_HOLD ve kullanıcı Windows onedir/Edge gerçek kabulü ayrıca. **Sıradaki kod paketi `islem_023`** A0/A1 tile/ROI OCR; önce `docs/islem_023.md` yeni ilk GitHub yazımı olarak açılacak.


## İşlem 023 uygulama notu (2026-10-16)

`src/mimarllm/ocr/tiles.py` opt-in A0/A1 PDF ROI'yi pixel/tile/token/çoklu istek bütçeleriyle sıralı render edilmiş kartlara böler. `rapid_engine.py` mevcut CPU OCR adapter'ı korunur; source quad ve PDF SHA/page/rotation doğrulaması olmadan çizim kanıtı üretilmez. Overlap aynı metin + bbox IoU varsa deterministik dedup; `ocr/layout.py` antet/kenar metin **konum** adayı, bina/proje/ölçek semantiği asla onaylı değil. `importers/pdf_ir.py`, `pipeline.py` ve `cli.py` explicit ROI ile birbirine bağlandı; manifestin `layout_candidates` ve tile sayaçları kaynaklıdır.

F28/F04 **KISMI**; sentetik fake CPU reader testleri gerçek OCR modeli doğruluğunu ispatlamaz, döndürülmüş büyük A0 sayfada full-page fallback piksel sınırını aşarsa işlem kesin reddedilir. Gerçek A0/A1 tarama/Windows offline/karakter hata oranı/peak RSS ve hukukî kabul ayrı. Sonraki paket `islem_024` Türkçe mimari jargon eşanlam ve SQLite yerel indeks/cache; `docs/islem_024.md` bir sonraki değişiklikten önce ilk GitHub yazımı olacak.


## İşlem 024 uygulama notu (2026-10-16)

`rag/lexicon.py` üzerinden kontrollü tam sözcük mimari terim ipuçları; `retriever.py` opt-in `lexical_expansion` ile özgün FTS5 BM25 önceliği ve ek arama adayları; `rag/store.py` içinde 128 adede kadar yalnız arama passage ID tutan source-filter kimlikli SQLite cache geliştirildi. Re-index aynı transaction içinde ve `passages` SQL trigger'ları ile cache invalidation; yerel PDF hash durumu her sonuçta kontrol edilir. Çoklu belge madde-fıkra ve özgün PDF quad izolasyonu korunur.

**F29 KISMI:** Kurasyonlu aday sözcükler hukukî semantik eşitlik iddiası değildir; gerçek Türkçe relevance/Recall@k/NDGC ve uzman testleri yok. **F30 KISMI:** yalnız yerel lexical query cache, tam workspace geçmişi/WAL/retention yok. F08–F12 HUKUKI_HOLD. Sonraki mühendislik planı mevcut yol haritasındaki `islem_025` kapsamı olacaktır; koddan önce `docs/islem_025.md` ilk GitHub değişikliğiyle açılacak.


**İşlem 025 aday güncellemesi (2026-10-16):** 2B salt-okunur çizgi/kaynak odaklama ve tek-worker/sınırlı polling API'si [Draft PR #2](https://github.com/seydivakkas/MimarLLM_v2/pull/2) içinde; [ilk CI 38834544453](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38834544453) Ubuntu 364 PASS/1 SKIP, Windows 365 PASS. İşlem 025 edit/annotasyon kabulü ve gerçek Windows inceleme bitmeden kapanmaz.

**025 kapsam sınırı güncellemesi:** Türetilmiş DXF LINE revizyonu ve byte-koruyan undo kodlandı; özgün input ve DrawingIR değişmez. \`docs/specs/dxf-revisions-025.md\` sınırları dışında tam CAD düzenleme veya 2.5D başlatma yoktur. Windows/Edge fiziksel kabul ve gerçek performans İşlem 025 kapanışına kadar HOLD.

## 6. 2026-10-16 kullanıcı revizyonu — fiziksel kabul yalnız son aşamada

**Önceki 025→026 blokajı kaldırıldı.** Yukarıdaki tarihsel notlarda geçen "025 fiziksel kabulü bitmeden 026 yok" ifadeleri bu yeni kararla ileriye dönük hükümsüzdür. 025 yalnız **sentetik olarak doğrulanan mühendislik adayıdır**; fiziksel ürün kabulü değildir.

1. **025:** Kaynak-koruyan DXF LINE revizyonu/undo, SVG kaynak incelemesi, job polling ve audit notları; mevcut GitHub-hosted Windows/Ubuntu otomasyon kanıtı korunur. PR #2 Draft kaldığı için ürün yayımlanmış sayılmaz.
2. **026 → 030:** Önce yeni işlem kaydı, sonra özellik kodu ve her aşamada otomatik sentetik CI; başarısız CI, kaynak SHA veya güvenlik kuralı ihlali sonraki aşamaya taşınamaz. Önemli gerçek veri belirsizlikleri `HOLD` olarak izlenir.
3. **031:** Birleştirilmiş nihai gerçek Windows 10/11/Edge kullanıcı kabulü, offline PyInstaller onedir/CRT/DLL/model asset/NOTICE/SBOM incelemesi, gerçek kirli mimari DXF ve A0/A1 PDF, bağımsız fiziksel ölçüm, gerçek cihaz p50/p95/peak RSS/GPU/VRAM, uzman/öğrenci kabulü. Bu kanıtlar elde edilmeden üretim/dağıtım onayı verilmez.
4. **Resmî hukukî kapı:** F08–F12 `HUKUKI_HOLD` ve `RuleEngine.REGULATORY=INSUFFICIENT_EVIDENCE` bütün aşamalarda sürer. Teknik sentetik test veya 2.5D görüntü hukukî PASS olamaz.

**Sıradaki kesin mühendislik yazımı:** `docs/islem_026.md`, 026'nın kendi kaynak dosyalarından *önce* ilk GitHub değişikliği olarak açılacak. 026 dalı gerekiyorsa açık 025 aday dalını temel alabilir; 025 PR #2 Draft ve `main` değişmeden kalır.
