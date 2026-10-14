# MimarLLM V2 — Bağımlılığa Dayalı Uygulama Yol Haritası

- **Kayıt:** [islem_006](islem_006.md)
- **Referans:** [Özellik envanteri](ozellik-envanteri.md)
- **Durum:** PLAN / teknik yol haritası; yüklenen taslaklardaki `islem_002…020` yeni GitHub kayıt numarası değildir.

## 1. Sabit mimari kararlar

Tek paket: `src/mimarllm`. Tek kullanıcı, offline-first, modüler monolit. CPU geometri/topoloji/kural, yerel RAG (SQLite FTS5 ve CPU embeddings); yerel VLM yalnız semantik aday ve GPU bütçesi içinde. PDF/OCR: `pdfplumber + pypdfium2 + RapidOCR(onnxruntime CPU)`. Teknik ve hukukî kanıt ayrı doğrulanır.

## 2. Paket ve kayıt sırası

| GitHub işlem kaydı | Geliştirme hedefi | Özellik ID | Bağımlılık | Çalışma kabulü |
| --- | --- | --- | --- | --- |
| islem_001–005 | Başlangıç, kapsam, RAG tasarım, OCR/PDF ilk gerçek kod | F03/F04 (kısmi) | — | Tarihsel kayıt korunur |
| **islem_006** | Bu kapsam/öncelik/uygunluk konsolidasyonu | F01–F24 | Önceki 001–005 | Dürüst feature envanteri |
| **islem_007** | DrawingIR v0.1 + birim/kalibrasyon/source mapping | F01 | Mevcut modeller | 2 koordinat sisteminde girdi doğruluğu |
| islem_008 | DXF + layer/blok/nested INSERT | F02 | 007 | CAD handle/transforms geri izlenir |
| islem_009 | PDF native/ROI/rotasyon + OCR layout entegrasyonu | F03/F04 | 007/008 | Kaynak poligonları / CPU OCR doğrulama |
| islem_010 | Geometri oda, iç duvar ve net/brüt alan | F05 | 007/008 | Sentetik iki oda + scale unknown |
| islem_011 | Mekânsal topoloji/erişilebilirlik | F06 | 010 | Gerçek kapı/geçit grafı; dışa çıkış sınıfı |
| islem_012 | Kural motoru + durumlar + güvenilir kural kaydı | F07 | 010/011 | Kaynak eksikliğinde hukukî PASS yok |
| islem_013 | Yerel mevzuat ETL + LegalAST + PDF span/source index | F13 | 009 | Özgün kaynak ve değişiklik zinciri |
| islem_014 | FTS5/dense/RRF + source spans ile RAG sonuçları | F14 | 012/013 | PDF SHA/page/quad ve BM25/RRF; semantic benchmark HOLD |
| islem_015 | Yerel özgün PDF SHA ve polygon denetimi + hukuki değişiklik/proje applicability bağlayıcısı | F15 | 012/013/014 | Source consistency + RuleEngine REGULATORY HOLD |
| islem_016 | Özgün PDF görsel vurgulu kaynak inceleme ve tarihsel sürüm kıyas iş akışı | F15 ve F18 mevzuat alt küme | 013–015 | Source SHA, sayfa, quad, imzasız reviewer; hukukî HOLD |
| islem_017 | Rapor, çizim işaretleme + bulgudan belge sayfasına geçiş | F17/F18 | 014–016 | İki kaynak bbox doğrulama |
| islem_018 | Yerel DXF/PDF → DrawingIR → Shapely/NetworkX/RuleEngine → rapor pipeline + CLI | F16 | 017 | Kaynak SHA/frame, user-confirmed physical scale, stage manifest; F19 ayrı |
| islem_019 | FastAPI localhost F19 Türkçe proje yükle/analiz et/kanıt gezgini | F19 | 018 | Yalnız 127.0.0.1, kaynak SHA, CSRF/Host/Origin, sentetik Linux/Windows CI |
| islem_020 | Windows-first offline dashboard/CLI onedir, yerel başlatma, wheelhouse ve SBOM | F20 | 018/019 | PyInstaller smoke, paket lisansları, gerçek Windows kabul HOLD |
| islem_021 | Yerel VLM aday semantiği, deterministik kaynak üzerine yazmaz | F21/F22 | 009/010/019 | GPU 8 GB VRAM benchmark, CPU fallback HOLD |
| islem_022 | Çapraz modül gerçek çizim benchmark ve bağımsız Windows kabulü | F23/F24 | Tüm gerekli paketler | PASS/HOLD matrisleri |

**Önemli:** Bu ilerideki `islem_007…021` adları yalnız **planlanan sıra**, dosyalar henüz oluşturulmamıştır. Bir işlemin kapsamı değişirse yeni karar kaydı güncellenir, geçmiş numaralar yeniden kullanılmaz. İş paketleri gerçek uygulama modülüne göre bölünebilir; otomatik olarak tamamlandı kabul edilmez.

## 3. Öncelik ve ilk çalışan ürün

```text
DrawingIR -> DXF -> Geometri -> Topoloji -> kural çerçevesi
  -> minimal geometrik bulgu + koordinatlı JSON/HTML
  -> mevzuat LegalAST + kaynak bbox
  -> FTS5/dense retrieval -> hukuken onaylı rule bindings
  -> beş mevzuat ailesi (onaylı alt kapsam)
  -> web UI / rapor / offline Windows paket
  -> opsiyonel VLM -> gerçek donanım benchmark
```

Mevzuat kural modülü hukukî doğrulama beklese bile geometri ve çizim kalite kontrolü ilk kullanılabilir ürünü oluşturmalı. Aynı anda hem AI hem hukukî danışman hem tam proje sertifikasyonu hedeflenmez.

## 4. Mühendislik düzeltmeleri ve kabul

- Net alan: gerçekten iç yüz sınırı çıkarılmalı; CAD duvar çizgileri otomatik net sınır değildir.
- Egress: oda merkezleri arasındaki Öklid uzaklığı doğrudan kaçış mesafesi sayılmaz; yürünebilir serbest alan, alternatif çıkış, çıkmaz kol, kat ve erişim geometrisi gerekir.
- Yanlış oda sınırı: polygonize sliver/outer yüz false-positive analizi; kalibrasyonsuz alan `INSUFFICIENT_EVIDENCE`.
- Yangın: sürümlü Ek-5/B, kullanım/kişi yükü, sprinkler ve proje tarihine göre eşik seçimi.
- Mevzuat: exact source identity + tarihler + mahal / yapı profili, istisnalar; RAG yalnız candidate.
- VLM: `mmproj` / quantization / context/lisans/VRAM ve Windows GPU ölçülmeden varsayılan model yok.
- Windows: bağımlılık kuran `run.bat` için ilk kurulumda internet/yerel wheelhouse gereksinimi dürüstçe gösterilecek; tamamen offline dağıtım için wheelhouse veya onedir paket.
- Test statüleri: yerel sentetik sonuç, CI, gerçek Windows kabul ve bağımsız mevzuat incelemesi **ayrı**.

## 5. Sıradaki somut başlangıç

**İşlem 007:** `DrawingIR`, kalibrasyon ve kural/kanıt sözleşmelerinin kodu ve sentetik fixture testleri. Ürün baştan sona “varmış gibi” gösterilmeden bu temel kullanılarak DXF katmanına geçilecek.


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
