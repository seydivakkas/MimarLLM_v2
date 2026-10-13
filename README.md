# MimarLLM V2

**Amaç:** Tek Windows bilgisayarında çalışan, mimari DXF/PDF paftalarını ölçüm, geometri, topoloji ve mevzuat kaynağı açısından denetlemeye yönelik yerel yazılım.

**Donanım:** Intel i7 14. nesil, 32 GB RAM, RTX 4070 8 GB VRAM. Yapay zekâ çıkarımı yerel, harici AI API'si yok.

## Kesin PDF / OCR teknolojileri

| İş | Yerel bileşen |
| --- | --- |
| PDF native karakter/çizgi/dikdörtgen/eğri gözlemleri | **pdfplumber** |
| PDF raster sayfa veya ROI üretimi | **pypdfium2** |
| Taranmış/eksik metinleri OCR | **RapidOCR + ONNX Runtime CPU** |

**Önce vektör, sonra OCR.** Tamamen seçilebilir PDF metni bile kontur haline gelmiş ölçü, SHX karakter veya taranmış bölge içeriyor olabilir; OCR yalnız gereken bölgeye uygulanır. PDF kaynak koordinatları/sha256 korunur.

### Mimari sınırlar

- **Deterministik karar:** OCR ve yerel VLM yalnız aday üretir; fiziksel alan/ölçü ve mevzuat uygunluk kararı doğrulanmış geometrik girdilerden gelir.
- **Mevzuat RAG:** Yapısal madde/fıkra/bent, tarih, istisna, tablo-hücre ve özgün kaynak sayfası/alanı. Yerel hazırlık ETL; çevrim dışı çalışma.
- **Kanıt ekranı:** Hata bulunduğu çizim koordinatı ↔ özgün mevzuat sayfası/bounding polygon.
- **Tek kullanıcılı modüler monolit:** LMS/öğrenci portalı, jüri karakterleri, çoklu AI agent ve dış API çağrısı yok.
- **Lisans:** Seçilen motorlar izinli ana lisanslara sahip; transitif binary/model/dağıtım lisanslarının son kabulü henüz yapılmadı.
- **Public depo:** Özel müşteri çizimleri, mevzuat tam metinleri, model ağırlıkları, sırlar ve yerel indeksler Git'e alınmaz.

## Mevcut uygulama durumu (İşlem 005)

İlk kod: `src/mimarllm/core/models.py` kaynak aday sözleşmesi, `src/mimarllm/importers/pdf.py` native gözlem/ROI raster, `src/mimarllm/ocr/rapid_engine.py` CPU OCR adaptörü. `pyproject.toml` ve sentetik PDF testleri eklendi.

**Henüz yapılmadı:** DrawingIR'nin tüm CAD nesneleri, DXF parser, OCR gerçek model benchmark'ı, mevzuat indeksleme, hukukî doğrulama, Windows kurulum/benchmark, UI ve offline paket kabulü.

## Belgeler

- [İşlem kayıtları 001–005](docs/islem_005.md)
- [ADR-002: PDF motoru ve lisans kararı](docs/adr/ADR-002-PDF-Engine-License.md)
- [Teknik PDF/OCR sözleşmesi](docs/ocr-mimari-pafta.md)
- [OCR kaynak yönetimi](docs/ocr-ve-bellek.md)
- [Lisans envanteri](docs/pdf-lisans.md)
- [Mevzuat RAG](docs/mevzuat-rag.md)
- [Sistem mimarisi](docs/sistem-mimarisi.md)
- [Modül ve iş planı](docs/modul-plani.md)
- [Teknik gereksinimler](docs/teknik-gereksinimler.md)
- [Kapsam](docs/kapsam.md)
- [Kararlar](docs/kararlar.md)

Her yeni AI destekli istek **önce** `docs/islem_NNN.md` dosyasına işlenir. Yapılmayan işin durumunu PASS gösterme.


## Güncel tam kapsam ve gerçek ilerleme (İşlem 006, 2026-10-13)

Kullanıcının sağladığı mimari ve kod taslakları V2'nin **hedef özellik envanterine** işlendi: DXF/ölçek, duvar-oda geometri ve net/brüt alan, spatial topology/kaçış, beş mevzuat ailesi, hiyerarşik RAG+FTS5+yerel embedding, kural–özgün kaynak bağlama, yerel RapidOCR ve VLM, rapor/SVG, offline localhost paneli, run.bat / PyInstaller onedir ve Windows benchmark.

**Hedef kapsam ≠ tamamlanmış uygulama.** Mevcut kod PDF/ROI ve OCR adaptörünün başlangıç düzeyindedir. Resmî mevzuata ilişkin eşikler `HUKUKI_HOLD`; kaynak, madde/fıkra, yürürlük ve proje bağlamı doğrulanmadan kesin kural yok. Yerel Windows, OCR model, VLM ve paketleme sonuçları henüz PASS değildir.

- [İşlem 006 — Kapsam birleştirme günlüğü](docs/islem_006.md)
- [24 maddelik özellik ve durum envanteri](docs/ozellik-envanteri.md)
- [İşlem 007–021 için bağımlılığa dayalı yol haritası](docs/uygulama-yol-haritasi.md)
- [Türkiye mevzuatı doğrulama ve özgün PDF kanıt protokolü](docs/mevzuat-dogrulama-protokolu.md)
- [Sade dizin tasarımı](docs/planlanan-dosya-yapisi.md)
- [Windows tek tık kurulum ve standalone paketleme kabul planı](docs/windows-dagitim-plani.md)
- [ADR-003 — Kanıt temelli mimari karar](docs/adr/ADR-003-Kapsam-Kanit-ve-Kabul-Kapilari.md)

**Bir sonraki geliştirme kaydı:** `docs/islem_007.md` (DrawingIR + birimler + doğrulanmış kaynak dönüşümleri). Önce bu kaydı oluştur, sonra kaynak kodu ekle.

## İşlem 007 — DrawingIR çekirdek sözleşmeleri

- [İşlem 007 ve gerçek kabul durumu](docs/islem_007.md)
- [DrawingIR v0.1 teknik şartnamesi](docs/specs/drawingir-v0.1.md)
- Kodlanan: `core/units.py` (CAD INSUNITS/reference confirmation, SI ölçek), `core/ir.py` (Pydantic DrawingIR, SourceReference, CoordinateFrame, Transform2D, GeometryPrimitive, DrawingEntity, MeasurementEvidence, Finding).
- Güvenlik: `UNKNOWN/INFERRED/CONFLICT` durumunda fiziksel ölçüm yasak; kaynak SHA/entity/frame eşleşmesi; onaylı ölçümün fiziksel değeri kalibrasyonla kontrol edilir. Hukukî uyum sertifikasyonu yasak.
- GitHub Actions sentetik sözleşme testi: [Core contracts](https://github.com/seydivakkas/MimarLLM_v2/actions/workflows/core-contracts.yml).
- Henüz yok: `ezdxf` DXF parser, duvar/oda topolojisi, gerçek mimari pafta kabulü, Windows/i7/4070 deneyleri. Sıradaki kayıt `islem_008`.


## İşlem 008 — Gerçek DXF ayrıştırıcısı (CPU)

`ezdxf` ile gerçek yerel DXF dosyasını açıp `DrawingIR` nesnelerine aktaran ilk motor geliştirildi. Kod: [dxf.py](src/mimarllm/importers/dxf.py) ve [layers.py](src/mimarllm/importers/layers.py).

**Gözlem düzeyi:** LINE, LWPOLYLINE (bulge dahil), ARC, CIRCLE, TEXT, MTEXT, DIMENSION, INSERT ve iç içe INSERT/MINSERT. Orijinal CAD handle, blok örnekleme yolu, layout/frame ve kaynak SHA-256 korunur. Curve/arc geometrileri açıkça yaklaştırılmış poligondur; DIMENSION etiketi otomatik metrik kalibrasyon değildir. `$INSUNITS` yalnız `INFERRED`.

**Kabul:** [islem_008.md](docs/islem_008.md), [DXF teknik şartnamesi](docs/specs/dxf-import-v0.1.md), [GitHub Actions](https://github.com/seydivakkas/MimarLLM_v2/actions/workflows/core-contracts.yml). CI sentetik/geometri sözleşme testini doğrular; Windows gerçek mimari pafta, DWG/XREF çözümleme, DXF geometri semantiği ve mevzuat uygunluğu **HOLD**.

**Sıradaki paket:** islem_009 PDF native/ROI/OCR koordinat entegrasyonu.


## İşlem 009 — PDF/OCR → DrawingIR kaynak bütünleştirmesi

- [İşlem kaydı](docs/islem_009.md) · [Teknik şartname](docs/specs/pdf-ocr-drawingir-v0.1.md)
- **Kod:** `src/mimarllm/importers/pdf_ir.py` PDF native metin, gerçek line/rect, yaklaşık Bezier curve ve açık ROI'den gelen RapidOCR dörtgenini `DrawingIR` ile aynı kaynak PDF SHA-256/page koordinatına bağlar.
- **Sayfa rotasyonu:** 0° native ROI; 90°/180°/270° bellek sınırı dahilinde tam sayfa render + ROI crop ile tutarlı koordinat. Non-default CropBox + OCR ROI açıkça reddedilir (güvenli fallback).
- **Offline:** RapidOCR yalnız açıkça sağlanan yerel CPU engine ile çağrılır. Otomatik model indirme veya bulut OCR tetiklenmez. Native PDF/OCR karakterinin gerçek geometrik ölçü veya hukukî `PASS` olduğu iddia edilmez.
- **Sınırlar:** Native glyph polygon'u eksenlere paralel bbox'dır, gerçek rotated quad değildir; OCR quad tespit alanıdır. SHX/kalite kapısı ve Türkçe/OCR modelin gerçek doğruluğu hâlâ açık. `max_pixels`, hash ve sınırlı ROI kontrolleri uygulanır.
- **Sonraki işlem:** `islem_010` — Shapely temel oda/duvar çizgi geometri ve net/brüt alan; kaynak/ölçek bilgisi belirsizse sahte fiziksel alan yok.


## İşlem 010 — Shapely geometri, yüzey ve duvar aralığı adayları

- [İşlem 010](docs/islem_010.md) · [Shapely teknik şartnamesi](docs/specs/geometry-v0.1.md)
- **Kod:** `src/mimarllm/geometry/spatial.py`, `walls.py`; `DrawingIR` üzerinden source-hash/frame/entity ID korunarak polygonization (noding, intersections), kapalı yüzey adayları, açık/çakışan çizgi diagnostikleri ve paralel çizgiler arası duvar aralığı **adayları** üretilir.
- **Net/brüt ayrımı:** `assess_area` ancak ayrı seçilip gözden geçirilmiş **iç oda sınırı** (`INTERIOR_ROOM`) veya **bina dış zarfı footprint'i** (`EXTERIOR_ENVELOPE`) tek ve çelişkisiz kapalı yüzeyse, ayrıca aynı coordinate frame için `CONFIRMED` metre dönüşümü varsa fiziksel m² hesaplar. `EXTERIOR_FOOTPRINT_M2` tüm katların yasal brüt alanı değildir.
- **Güven:** Otomatik çizgi kapanması, snap, çizgi katmanı veya paralel boşluk kesin oda/duvar kanıtı sayılmaz. Desteklenmeyen/eksik/çakışan kaynak seçimi `REVIEW_REQUIRED`, ölçek onaysızsa `INSUFFICIENT_EVIDENCE`. Her yüzey baştan `UNCLASSIFIED_FACE`; mevzuat/yangın `PASS` yok.
- **Kapsamı açık:** Gerçek katmanlardan duvar iç-dış yüzü çıkarma, açılmış kapı/pencere hatları, oda-topoloji geçiş grafı, hakiki saha çizimleri ve yerel RTX 4070 Windows kabulü henüz yapılmadı. GitHub-hosted Windows sentetik CI ayrı kanıttır.
- **Sıradaki işlem:** `docs/islem_011.md` — gerçek kapı/açık geçiş/oda ilişki kanıtı ile NetworkX spatial adjacency graph; yangın yürüme ağı ayrıca.


## İşlem 011 — İncelenmiş mekânsal geçiş topolojisi (NetworkX)

- [İşlem 011 uygulama ve CI](docs/islem_011.md) · [Topoloji v0.1 sözleşmesi](docs/specs/topology-v0.1.md)
- **Kodlandı:** `src/mimarllm/geometry/topology.py`; `SpaceReview` ile `ROOM/CORRIDOR/BALCONY/STAIR/LANDING` yüzey incelemeleri, `PassageReview` ile `DOOR/ARCHWAY/OPEN_PASSAGE/EXTERIOR_DOOR` geçiş beyanları, kaynak `DrawingIR` ile **yeniden doğrulanmış** Shapely yüzey sınırı ve native kapı marker referansı, NetworkX `MultiGraph`.
- **İşlevler:** Bağlı bileşenler, en az *geçiş sayısına* göre olası bağlantı yolları, articulation node/bridge edge analizi, dış düğüme doğrulanmış ilişki ve kanıtı bulunmayan mekânlar, kaynak SHA/face/marker ID.
- **Yanlış PASS yok:** Katman adları, OCR metni, oda merkezleri veya duvarda kesintisiz çizgi **otomatik kapı oluşturmaz**. Reviewer kimliği yalnız istemci beyanıdır; kapıların gerçekten geçilebilir olduğu bu modülde bağımsız doğrulanmaz. Sonuçlar yangın kaçış mesafesi, mevzuat veya metre cinsinden yürüyüş mesafesi değildir.
- **Açık:** CAD'den otomatik kapı açıklığı ve net geçiş doğrulaması, kapı yönü, katlar arası merdiven/3B yapı, büyük plan performansı, gerçek i7/4070 Windows saha testi.
- **Sıradaki:** islem_012 kural motoru çerçevesi; herhangi bir hukukî hüküm aktif olmadan önce sürümlü özgün kaynak dayanağı gerekir.


## İşlem 012 — Deterministik teknik RuleEngine v0.1

- [İşlem 012 geliştirme kaydı](docs/islem_012.md) · [RuleEngine v0.1 teknik şartnamesi](docs/specs/rule-engine-v0.1.md)
- **Uygulandı:** `src/mimarllm/rules/base.py` (sürüm/kimlik, metrik ve kanıt şemaları, 6 durum, `LegalSourceLocator`) ile `src/mimarllm/rules/engine.py` (`RuleEngine`).
- **Teknik metrikler:** DrawingIR'den yeniden ölçülen native `SEGMENT_LENGTH_M`; aynı dosyadan yeniden hesaplanan gözden geçirilmiş `REVIEWED_INTERIOR_AREA_M2` ve `REVIEWED_FOOTPRINT_M2`; Shapely/NetworkX'ten yeniden kurulan `REVIEWED_TOPOLOGY_PATH`.
- **Karar türleri:** `COMPLIANT`, `NON_COMPLIANT`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`, `NOT_APPLICABLE`, `ERROR`. `COMPLIANT` burada **yalnız senaryoya ait teknik eşik/bağlantı** anlamına gelir, yapının mevzuata uygunluğu değildir.
- **Hukukî HOLD:** `REGULATORY` tanımı yasal madde/fıkra ve PDF kimliğini aday metadata olarak tutabilir; fakat resmî source/version/yürürlük/applicability/istisna zinciri ve bağımsız onay hattı bulunmadığından **REGULATORY hiçbir zaman COMPLIANT/NON_COMPLIANT/NOT_APPLICABLE üretmez**. Kullanıcı kaynak onay bayrağıyla motoru açamaz. `legal_compliance_certified=True` açıkça reddedilir.
- **Sınırlamalar:** Kural paketleri `tr_imar.py`, `tr_yangin.py` vb. oluşturulmadı; yazılım gerçek mimari hesaplar veya hukuka uygunluk sertifikası sunmuyor. Gerçek Windows i7/4070, resmî mevzuat ve saha testleri ayrı tutulur.
- **Sonraki iş:** `islem_013` resmî mevzuat kaynak PDF'lerini maddeler/fıkralar, değişiklikler ve konum kanıtıyla çevrimdışı LegalAST'ye dönüştürme.


## İşlem 013 — Yerel PDF → LegalAST

- [İşlem 013](docs/islem_013.md) · [LegalAST v0.1 sözleşmesi](docs/specs/legalast-v0.1.md)
- **Gerçek kod:** `src/mimarllm/legal/models.py`, `extractor.py`, `parser.py`, `changes.py`, `etl.py`. Orijinal PDF sayfası/bbox ve hash'ine bağlı metin, bölüm/madde/fıkra/bent/geçici madde, vektör tablo hücreleri ve değişiklik/yürürlük/ilga ifade adayları.
- **OCR:** RapidOCR CPU yalnız açıkça seçilmiş sayfalarda, mevcut yerel OCR reader üzerinden. Belgenin basılı sayfa numarası, resmî başlığı, yürürlük tarihi ve hukukî geçerliliği otomatik varsayılmaz.
- **Dürüst statü:** F13 `MEVCUT_KOD/KISMI`, sentetik Linux+Windows CI doğrulaması. Gerçek Resmî Gazete belgeleri arşivlenmedi/konsolide edilmedi; hukukî uzman onayı/iki sütun/OCR doğrulaması ayrı. F08–F12 REGULATORY hâlâ `INSUFFICIENT_EVIDENCE`.
- **Sıradaki:** islem_014 LegalAST kaynak geri izli SQLite FTS5 + yerel dense/hybrid retrieval.


## İşlem 014 — Yerel hibrit mevzuat RAG (SQLite FTS5 + yerel dense + RRF)

- [İşlem 014](docs/islem_014.md) · [RAG v0.1 teknik şartnamesi](docs/specs/rag-v0.1.md)
- **Kod:** `src/mimarllm/rag/{models,store,embeddings,retriever,indexer}.py`. `LegalDocument` düğüm/fıkra ve tablo hücresi kayıtları SQLite FTS5/BM25 ile aranabilir; kullanıcı bir yerel embedding modelini **açıkça** sağlarsa aynı SQLite üzerinde normalize cosine ve Reciprocal Rank Fusion (RRF) kullanılır.
- **Kaynak izi:** Sonuçlarda `document_sha256`, `regulation_id`, `node_id`, `article/paragraph/item`, `table_id/row/column`, gerçek `LegalSourceSpan.page_index` ve PDF `polygon` ile özgün metin vardır. Yerel PDF hash'i erişilebilir değilse görüntü varmış gibi davranılmaz.
- **Donanım/offline:** SQLite Python stdlib, `LocalSentenceTransformer` yalnız önceden hazır bir **yerel klasör**, CPU, `local_files_only=True`, `trust_remote_code=False`; sentence-transformers temel paket zorunluluğu yapılmadı. Embedding yoksa `LEXICAL_ONLY` çalışır. ANN/FAISS/haricî API henüz yok.
- **Kanıt ve karar ayrımı:** Bütün sonuçlar `UNREVIEWED` / `legal_compliance_certified=False` ve `RETRIEVAL_CANDIDATE_NOT_LEGAL_ADVICE`. RRF skorundan hukukî `COMPLIANT` üretilemez, RuleEngine `REGULATORY` kilidi değişmedi.
- **Sınırlar:** Sentetik CI'da dense pipeline **fake embedder** ile test edildi; gerçek çokdilli model Türkçe ölçüm ve tüm yıl/sürüm mevzuat corpus performansı hâlâ HOLD. 


## İşlem 015 — Kaynak doğrulama, sürüm/uygulanabilirlik kanıtı, RuleEngine bağlayıcısı

- [İşlem 015](docs/islem_015.md) · [Legal binding v0.1 teknik şartnamesi](docs/specs/legal-binding-v0.1.md).
- **Kod:** `src/mimarllm/legal/verification.py` (yerel PDF SHA, sayfa ve polygon sınır denetimi), `legal/versions.py` (orijinal ve amendment PDF/source-node kimlikli insan beyanı, tarih çakışma uyarıları), `legal/applicability.py` (konum/ruhsat/kullanım/istisna eksiklikleri) ve `src/mimarllm/rules/evidence.py` (RuleDefinition→LegalAST node→isteğe bağlı RAG hit→yerel PDF ve proje bağlantısı).
- **Önemli ayrım:** Yerel PDF'yi hash ile eşleştirmek belgeyi resmî yayımlanmış yapmaz; değişiklik ilişkileri henüz hukukî konsolide sürüm değildir. Girdi `reviewer_id` bağımsız hukukçu denetimi/kimlik doğrulaması değildir. Eksik amending özgün PDF kendi `HOLD_AMENDMENT_CHAIN` uyarısını üretir.
- **Hukukî kilit:** RAG skoru veya tüm kullanıcı alanlarının dolu olması `APPROVED_FOR_CHECK` üretmez. `evaluate_regulatory_with_evidence` belge/versiyon/proje kanıtı eksiklerini ve değişmeyen `RuleEngine.REGULATORY: INSUFFICIENT_EVIDENCE` sonucunu birlikte döndürür. F08–F12 HUKUKI_HOLD devam eder.
- **Sonraki mühendislik sınırı:** özgün Resmî Gazete yetkili kaynağının doğrulanması, madde/fıkra bazında gerçekte yürürlükte sürümlerin bağımsız konsolidasyonu ve imzalı uzman onay akışı ayrı geliştirme/bağımsız hukukî kabul ister.
