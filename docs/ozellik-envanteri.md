# MimarLLM V2 — Kapsam ve Gerçekleşme Envanteri v0.1

- **Kayıt:** [islem_006.md](islem_006.md) · **Tarih:** 2026-10-13
- **Tanım:** Yüklenen taslak ve kod örneklerinin **tamamı hedef özelliklerdir**, doğrudan uygulanmış commit sayılmaz.
- **Durumlar:** `MEVCUT_KOD` = GitHub'da kod mevcut ama kabul zorunlu; `KISMI` = başlangıç var, hedef işlev eksik; `PLANLANDI` = kaynak/ürün henüz yok; `HUKUKI_HOLD` = mevzuat sürümü, dayanak ve uygulanabilirlik doğrulanana kadar etkinleştirilemez.

## Fonksiyonel özellik ve geliştirme takip matrisi

| Kimlik | Gerekli işlev | Hedef kod / bileşen | Mevcut durum | Kabul için somut kanıt | Kullanıcı taslağı |
| --- | --- | --- | --- | --- | --- |
| F01 | Birim, ölçek, CAD/DXF veri modeli `DrawingIR` | `core/ir.py`, `core/units.py` | PLANLANDI; PDF gözlem modelleri mevcut | Birim bilinmiyorsa kalibrasyonsuz gerçek ölçüm yok | Genel kapsam |
| F02 | DXF ayrıştırma, block/nested INSERT ve layer sinyali | `importers/dxf.py`, `importers/layers.py` | **KISMI / MEVCUT_KOD — sentetik CI kontrolü** | Katman/handle/transform ve bozulan bloklarda güvenli hata | (2) / eski 003 |
| F03 | PDF native vector + ROI + source provenance | `importers/pdf.py` | **MEVCUT_KOD, kabul bekler** | PDF char/line/curve/rect; dönüş/limit/görsel bbox ölçümü | İlk PDF kararları |
| F04 | OCR ve pafta layout (antet, mahal, kot, tablo) | `ocr/rapid_engine.py`, `ocr/layout.py` | **KISMI** (adapter) | CPU provider, Türkçe/simge CER, bbox + doğru yöne dönüş | (6) / eski 007 |
| F05 | Oda/duvar/poligon ve net-brüt alan, snap | `geometry/spatial.py`, `geometry/walls.py` | **KISMI / MEVCUT_KOD — sentetik CI kontrollü** | İki oda, açık sınır ve wall-inner-boundary referans alanı | (3) / eski 004 |
| F06 | Mekânsal topoloji, kapı bağlantısı, geçiş grafı | `geometry/topology.py` | **KISMI / MEVCUT_KOD — sentetik CI** | Unreachable ve articulation; dış kapı/balkon ayrımı | (4) / eski 005 |
| F07 | Deterministik rule engine + altı durum ve kanıt | `rules/base.py`, `rules/engine.py` | **KISMI / MEVCUT_KOD — sentetik CI** | PASS/FAIL/REVIEW/INSUFFICIENT/NA/ERROR; hesap izi | (5) / eski 006 |
| F08 | Planlı Alanlar İmar Yönetmeliği denetimi | `rules/registry/tr_imar.py` | **HUKUKI_HOLD** | Onaylı madde-fıkra-eşik, tarih, proje kapsamı ve bbox | (5) / eski 006 |
| F09 | BYKHY kaçış, kapı, çıkmaz koridor, sirkülasyon | `rules/registry/tr_yangin.py` | **HUKUKI_HOLD** | Ek-5/B doğru sürüm; yürünebilir yol/exit/sprinkler/occupancy | (12) / eski 014 |
| F10 | Otopark adedi, boyut, rampa ve manevra | `rules/registry/tr_otopark.py` | **HUKUKI_HOLD** | Kullanım/konum/tarih, gerçek kural, 3B rampa bilgisi | (13) / eski 015 |
| F11 | Sığınak ihtiyacı, kapasite, alan, kapı/çıkış | `rules/registry/tr_siginak.py` | **HUKUKI_HOLD** | 2025 değişikliklerinin sürüm zinciri; ek proje verisi | (14)=(15) / eski 016 |
| F12 | BEP/TS 825 pencere, enerji ve kabuk verileri | `rules/registry/tr_bep.py` | **HUKUKI_HOLD** | TS hakları + U/hesap/iklim/3B veri; 2B'den sahte PASS yok | (16) / eski 017 |
| F13 | Hiyerarşik mevzuat AST ve değişiklik/yürürlük | `legal/models.py`, `legal/extractor.py`, `legal/parser.py`, `legal/changes.py`, `legal/etl.py` | **KISMI / MEVCUT_KOD — sentetik CI** | Kaynak hash + madde/fıkra/ek + gerçek PDF page/quad | (7) / eski 008 |
| F14 | SQLite FTS5 ve CPU dense hibrit RAG, RRF | `rag/store.py`, `rag/retriever.py`, `rag/embeddings.py`, `rag/indexer.py`, `rag/models.py` | **KISMI / MEVCUT_KOD — sentetik CI** | Kaynak/version ID, exact match ve lexical fallback | (7) / eski 008 |
| F15 | RuleResult–LegalNode kaynak bağlama | `rules/evidence.py`, `legal/verification.py`, `legal/versions.py`, `legal/applicability.py` | **KISMI / MEVCUT_KOD — sentetik CI** | Exact verified binding; arama benzerliği asla hukukî PASS değil | (8) / eski 009 |
| F16 | Analiz hattı + CLI | `pipeline.py`, `cli.py` | PLANLANDI | Sentetik DXF -> geometrik bulgu -> rapor; hata/iptal | (9) / eski 010 |
| F17 | JSON/Markdown/HTML/PDF rapor | `reports/models.py`, `reports/builder.py`, `reports/exporter.py` | **KISMI / MEVCUT_KOD — sentetik CI** | Ölçüm ve kaynak iki yönlü izlenebilir; sahte hüküm yok | (8) / eski 009 |
| F18 | SVG/HTML koordinatlı işaretleme | `reports/visualizer.py` + `reports/exporter.py` + `legal/review_viewer.py` | **KISMI / MEVCUT_KOD — DrawingIR ve mevzuat kaynakları** | Offline, X/Y dönüşümü, hata pinine tıklayınca kaynak | (10) / eski 011 |
| F19 | Tek kullanıcılı localhost dashboard | `app/server.py`, `app/static/` | PLANLANDI | Sadece 127.0.0.1; izinli dosya; CDN yok, upload sınırı | (11) / eski 012 |
| F20 | Windows `run.bat`, `build_exe.bat`, `mimar.spec` | Root / `scripts/` | PLANLANDI | Sonraki gerçek CLI/dashboard entrypoint ile offline onedir | Sohbet / eski 013 |
| F21 | Yerel Qwen-VL ile aday sınıflandırma | `vision/vlm.py`, `vision/prompts.py` | PLANLANDI | GGUF + mmproj/Windows ölçümü; 8 GB peak VRAM | (17) / eski 018 |
| F22 | VLM adayını etiketleme, no-overwrite | `vision/semantic.py` | PLANLANDI | Native/certified kanıt ezilmez; belirsiz REVIEW | (18) / eski 019 |
| F23 | Çapraz modül benchmark, QA ve CI | `scripts/benchmark_audit.py`, `tests/`, `.github/workflows/` | PLANLANDI | Windows gerçek ölçüm, sentetik baseline, CPU/GPU peak | (19) / eski 020 |
| F24 | Dürüst README, kurulum ve işletim kılavuzu | `README.md`, `docs/` | KISMI | Gerçek özellik durumu, bağımlılık/kurulum ve lisans gerçeği | (20) |

**Eksik olarak bırakılmayacak iki denetim:** yapısal kaynak RAG'de *taranan özgün mevzuat sayfası ve satır/blok/quad* gösterimi; çizimde *ölçümün gerçek source entity/geometriye dönmesi*. Her ikisi de hukuken ve teknik olarak sahici kanıt için gereklidir.

## Taslaklardan taşınmayacak yanlış varsayımlar

- `src/mimar/` yerine **yalnız mevcut `src/mimarllm/`**.
- `rapidocr_onnxruntime` yerine **`rapidocr + onnxruntime CPU`**.
- PDF: yalnız **pdfplumber + pypdfium2**, başka motor ve genel doküman OCR paketi yok.
- “Dört köşeli OCR poligonu varsa 45°/90°/270° kusursuz okunur” geçersiz.
- “En yakın merkezler arasında Dijkstra yangın yürüme mesafesidir” geçersiz; yürüme ağı modelleme şart.
- “Odanın minimum rotated rectangle dar kenarı gerçek net geçiştir” geçersiz; gerçek kesit/geçiş ölçümü farklıdır.
- “Poligona buffer uygulamak duvar kalınlığını doğru düşer” her planda doğru değil.
- Örnek ölçü eşikleri kaynak/onay/yürürlük olmadan üretim kuralı değil.
- “0ms”, “%100 doğruluk”, “maksimum 2.5 GB VRAM” gibi test edilmemiş iddialar kabul değil.
- Kullanıcıların sağladığı yapıştırma dosyaları **telif ve özel veri kontrolünden geçirilmeden olduğu gibi public depoya yüklenmeyecek**.

## Durumun güncellenmesi

Her yeni `docs/islem_NNN.md` dosyasında Fxx kimlikleri korunur. Kod + sentetik test + hedef donanım kabulü + varsa hukukî inceleme sonrasında ayrı `PASS` verilir. Bir özellik yalnız başlığının veya Markdown örneğinin bulunmasıyla tamamlanmış sayılmaz.


## İşlem 007 güncellemesi — F01

**F01 `KISMI/MEVCUT_KOD`:** `DrawingIR v0.1` ve birim/scale/SourceReference kanıt modelleri GitHub'a eklendi. CAD $INSUNITS kodları, explicit source evidence, calibration frame, ölçü dönüşümü ve bu sözleşmenin sentetik testi kapsamda. **F01 bütünü PASS değil:** DXF dosya parser'ı yok; gerçek `dimension entity` veya grafik ölçek tespiti/bağımsız onay UI'si ve gerçek Windows kabulü henüz yapılmadı. [islem_007.md](islem_007.md) · [Teknik sözleşme](specs/drawingir-v0.1.md).


## İşlem 008 güncellemesi — F02

**F02 `KISMI / MEVCUT_KOD`:** `ezdxf.readfile`, `LINE`, `LWPOLYLINE` (bulge), `ARC`, `CIRCLE`, `TEXT`, `MTEXT`, `DIMENSION`, `INSERT`, nested INSERT ve MINSERT örnekleme, satır/katman ipucu ve native CAD handle + block path `DrawingIR` ilişkilendirmesi kodlandı. Kaynak birimleri `INFERRED` kalır.

**F02 henüz tümden PASS değildir:** Dinamik bloklar, XREF çözümleme, ACAD proxy, gerçek nested OCS/3B, doğrulanmış DIMENSION fiziksel kalibrasyonu, seçili müşteri DXF'lerinde gerçek Windows kabulü yapılmadı. [İşlem kaydı](islem_008.md) · [DXF teknik şartnamesi](specs/dxf-import-v0.1.md).


## İşlem 009 güncellemesi — F03 / F04

**F03 `MEVCUT_KOD / SENTETİK CI KABUL`:** `pdf_ir.py` ile sayfa başına kaynak frame, native glyph bbox+matrix, gerçek PDF line/rect, Bezier flattening diagnostic, referans hash ve PDF kaynak polygon'u `DrawingIR`'ye bağlandı. `pdf.py` standart sayfa 0/90/180/270 döndürme ve sınırlandırılmış ROI render desteğiyle güncellendi. **Henüz tam PASS değil:** CropBox != MediaBox için ROI açık reddedilir; rotated native glyph gerçek quad yok; büyük döndürülmüş paftalarda tam sayfa render kapısı var.

**F04 `KISMI`:** RapidOCR CPU adapter, `parse_pdf_ir(ocr_regions={...}, ocr_engine=...)` üzerinden poligonları kaynak PDF noktasına bağlar. Sentetik mock OCR ve kaynak ROI sınırları test edildi. **Gerçek model/Windows doğruluğu ve otomatik SHX/ROI kalite seçimi yapılmadı**; operasyonel OCR PASS yok.

[İşlem 009](islem_009.md) · [PDF/OCR kaynak sözleşmesi](specs/pdf-ocr-drawingir-v0.1.md).


## İşlem 010 güncellemesi — F05

**F05 `KISMI / MEVCUT_KOD`:** Shapely üzerinden planar noding, polygonize_full, kapalı yüzey `UNCLASSIFIED_FACE` adayları; kaynak ID ile çizgi uç/kesişim/T junction kanıtları; açık, çakışan, kendiyle kesişen kaynak diagnostikleri. `assess_area` için doğru iç oda sınırı veya dış footprint kullanıcı tarafından açıkça seçilmeli, **aynı frame kaynak ölçek CONFIRMED** olmadan `physical_area_m2` yok. `find_parallel_edge_gaps` paralel iki çizginin örtüşen bölüm aralığını yalnız `REVIEW_REQUIRED` aday olarak döndürür.

**Tam kabul DEĞİL:** otomatik duvar iç-dış konturu, gerçek oda duvarı/kapı açıklığı, global duvar kalınlığı doğrulaması, net/brüt yasal alan toplamı, sahadan gerçek Windows pafta kabulü, NetworkX topoloji ve yangın mesafesi yok. [İşlem 010](islem_010.md) · [Teknik şartname](specs/geometry-v0.1.md).


## İşlem 011 güncellemesi — F06

**F06 `KISMI / MEVCUT_KOD`:** `src/mimarllm/geometry/topology.py`, NetworkX `MultiGraph`, kullanıcıca açıkça gözden geçirilmiş Shapely face→SpaceReview düğümü; yakın native source marker ve geometrik shared-boundary crossing ile incelenmiş PassageReview kenarı, koridor/balkon/merdiven/sahanlık türleri, EXTERIOR soyut düğümü, components/reachability/articulation/bridges, passage-ID'li en az adımlı topolojik rota. Güncel `DrawingIR` native geometri yeniden çözülüp yüzey poligonu/katmanı doğrulanır; sahte face ID/SHA ile graph üretilemez.

**Tam uygunluk DEĞİL:** kapı boşluğu otomatik görüntü/CAD çözümüyle doğrulanmadı; dış çıkış ve kullanıcı `reviewer_id` beyanları güvenilir kurum imzası değil; yürünebilir alan/gerçek yangın kaçış **mesafesi** veya kapı açılış yönü yok. Kaynak kimliği, tek frame, aynı kat, gerçek sınır ve kullanıcının işaretli portal konumu şarttır. [İşlem 011](islem_011.md) · [Topoloji teknik şartnamesi](specs/topology-v0.1.md).


## İşlem 012 güncellemesi — F07

**F07 `KISMI / MEVCUT_KOD`:** `rules/base.py` ve `rules/engine.py` ile 6 sonuç sınıfı, sürümlü `RuleDefinition`, sonlu sayı ve kısıtlı operatörler, segment uzunluğu / gözden geçirilmiş net iç sınır alanı / bina footprint'i / incelenmiş topolojik bağlantı için DrawingIR+Shapely+NetworkX kaynak yeniden hesaplama geliştirildi. Tekil evidence ID, drawing SHA, frame, sınır sonucu, karşılaştırma ve neden kodu çıkarılır. Sadece teknik kurallar COMPLIANT/NON_COMPLIANT üretebilir.

**Hukukî kesin HOLD:** `LegalSourceLocator` yalnız yapılandırılmış **aday yasal kaynak konumu**; orijinal Resmî Gazete PDF, madde/fıkra, mevzuat değişiklik zinciri, yürürlük tarihi ve istisna/applicability denetlenmedi. Bu nedenle **tüm `REGULATORY`** tanımları, kaynak yazılmış olsa bile, `INSUFFICIENT_EVIDENCE` döner. F08–F12 halen **HUKUKI_HOLD**. [İşlem 012](islem_012.md) · [RuleEngine teknik sözleşmesi](specs/rule-engine-v0.1.md).


## İşlem 013 güncellemesi — F13 (LegalAST)

**F13 MEVCUT_KOD/KISMI:** Gerçek PDF dosyası `pdfplumber` üzerinden metin satırı, çok sayfalı BÖLÜM/MADDE/GEÇİCİ MADDE/FIKRA/BENT ağacı ve tablo hücresinin orijinal `pdf page_index + polygon + original PDF SHA256` bağlarıyla ayrıştırılıyor. `pypdfium2 + RapidOCR` yalnız açık OCR sayfası/enjekte edilen CPU okuyucuyla çalıştırılıyor. `LegalChangeCandidate` değişiklik/ilga/yürürlük/istisna sözcüklerini kanıt bağlantılı **adaya** dönüştürüyor; hukukî hüküm konsolidasyonu yapmıyor. JSON export mevcut dosya üzerine yazmayı reddediyor.

**HOLD:** Gerçek Resmî Gazete PDF corpus/baskı ve hukukî kaynak orijin teyidi yok; bütün tarih/yıl değişiklikleri ve madde/fıkra istisnaları birleştirilmedi; gerçek OCR/iki sütun/dipnot karmaşıklığı bağımsız doğrulanmadı. `LegalDocument.review_status=UNREVIEWED`; `RuleEngine` hâlâ tüm `REGULATORY` kurallarını `INSUFFICIENT_EVIDENCE` statüsünde tutuyor. [İşlem 013](islem_013.md) · [LegalAST v0.1 teknik şartnamesi](specs/legalast-v0.1.md).


## İşlem 014 güncellemesi — F14

**F14 `KISMI / MEVCUT_KOD`:** SQLite FTS5 + BM25; `LegalAST` düğüm, fıkra, bent ve tablo hücresi orijinal `document_sha256/page_index/polygon` indekslenir; kaynak SHA ve hiyerarşi çoklu belgeden ayrılır. Unicode/Türkçe lexical normalizasyon, güvenli parametrik sorgu, re-index transaction, model açıkça verilirse yerel normalize dense cosine ve deterministik RRF. `RagHit` kaynak span / table row+column / FTS+dense rank / yerel orijinal PDF hash erişimini verir; tüm sonuçlar `UNREVIEWED`.

**Açık:** Gerçek BGE-M3/e5/SentenceTransformer model dosyaları kurulup Türkçe arama/relevance benchmark yapılmadı, dense CI yalnız sentetik 4D stub; arama/model doğruluğu veya hukukî statü PASS değil. Çok yıllı Resmî Gazete corpus, yürürlük/istisna ve konsolidasyon HOLD; RuleEngine REGULATORY `INSUFFICIENT_EVIDENCE` döndürmeye devam eder. Büyük indeks için ANN ve gerçek saha RAM/latency kabulü yok. [İşlem 014](islem_014.md) · [RAG v0.1 şartnamesi](specs/rag-v0.1.md).


## İşlem 015 güncellemesi — F15 (mevzuat kanıt bağlayıcısı)

**F15 KISMI/MEVCUT_KOD:** `RuleDefinition.legal_source` ile LegalAST node ID, madde/fıkra, sayfa ve özgün source polygon karşılaştırılıyor. Opsiyonel RAG hit'i aynen LegalAST metni/quad'a dönmek zorunda. PDF ve ilgili değişiklik PDF'lerinin yerel SHA ve sayfa koordinatları kontrol edilir; boşluk, bozuk source, yanlış madde, çift amendment, proje tarihi/konumu/istisna eksikleri ayrı kodlu `HOLD` raporu üretir. RuleEngine REGULATORY hâlâ `INSUFFICIENT_EVIDENCE` döndürür. Bu bir resmî kaynak doğrulaması değil, **fiziksel dosya ve kanıt referansı tutarlılık denetimidir**.

**F08–F12 HUKUKI_HOLD:** Resmî belge orijin/otantiklik, her yıllık değişikliğin hukukî konsolidasyonu, geçiş hükümleri, yerel proje uygulanabilirliği ve bağımsız uzman onayı yoktur. Kullanıcı verdiği tam metadata, bağıntı ve RAG sonucu bile `APPROVED_FOR_CHECK` yapamaz. [İşlem 015](islem_015.md) · [Teknik şartname](specs/legal-binding-v0.1.md).


## İşlem 016 güncellemesi — F15 ve F18 alt modülü

**Kodlandı:** `legal/review.py` ile gerçek LegalAST node/fıkra, tablo hücresi, değişiklik kaynakları için tekil PDF SHA/page/quad `ReviewTask`; `review_viewer.py` pypdfium2 bitmap üzerinde sarı SVG dörtgen ve offline kullanıcı görsel inceleme JSON taslak dışa aktarımı; `version_workflow.py` tarihsel base/amendment iki özgün PDF inceleme kuyruğu; `review_ledger.py` kaynak task digest denetimli, tek yazıcı varsayımlı yerel SHA-chain JSONL.

**KISMI:** F18 yalnız mevzuat görsel kaynak inceleme alt modülüdür. Mimari analiz bulgularını CAD/PDF üzerine işleyecek `reports/visualizer.py` ve tam raporlama **PLANLANDI**. SHA zinciri elektronik imza değil; `VISUALLY_MATCHED` kullanıcı beyanıdır, bağımsız uzman kaynak/yürürlük onayı değildir. F08–F12 HUKUKI_HOLD, RuleEngine REGULATORY `INSUFFICIENT_EVIDENCE`. [İşlem 016](islem_016.md) · [Şartname](specs/legal-review-v0.1.md).


## İşlem 017 güncellemesi — F17/F18

**F17 KISMI/MEVCUT_KOD:** `reports/models.py`, `builder.py`, `exporter.py` ile DrawingIR.Finding, kaynak entity/measurement evidence, RuleResult, Shapely GeometryAnalysis issue/face candidate ve NetworkX TopologyResult issue'larını kaynak SHA/frame üzerinden tek rapora bağlıyoruz. JSON tüm yapılandırılmış kaynak IDs/quad; Markdown metinsel durum, kaynak/yasal HOLD; HTML offline çift yönlü görüntüleme; ReportLab PDF yalnız özet (opsiyonel extra).

**F18 KISMI/MEVCUT_KOD:** `reports/visualizer.py` kaynak CAD y-up→SVG ekran dönüşümü, CAD handle/blok source kimliği; PDF DrawingIR için özgün PDF byte SHA/sayfa doğrulanırsa pypdfium2 PNG üzerine SVG kaynak çizimi, `#finding_*`↔`#source_*` anchor navigasyonu. Yasal kaynak yalnız exact `RegulatoryEvidenceEvaluation`, LegalAST source node ve orijinal yasal PDF dosyası varsa sarı PDF sayfa quad. F17/F18 **tam CAD baskı görünümü, F19 localhost GUI veya imzalı hukukî inceleme anlamına gelmez**.

**Açık:** F16 CLI/pipeline, F19 arayüz, kullanıcı gerçek Windows hedef kabulü, büyük çizim bellek/perf, tam DXF grafik render ve tüm yılların resmî mevzuat norm konsolidasyonu. F08–F12 `HUKUKI_HOLD` ve `RuleEngine.REGULATORY=INSUFFICIENT_EVIDENCE`. [İşlem 017](islem_017.md) · [Şartname](specs/analysis-reports-v0.1.md).
