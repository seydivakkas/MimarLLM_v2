# MimarLLM V2 × ARCH-CORE Local — Gerçekleşme ve Gelecek Özellik Envanteri v1.0

- **İlk kayıt:** [islem_006.md](islem_006.md) · **Güncel yeniden baz:** [islem_020.md](islem_020.md), 2026-10-15. **Master mimari:** [master-mimari-arch-core-local.md](master-mimari-arch-core-local.md)
- **Tanım:** Önceki taslaklarda yer alan yeni öneriler kendiliğinden kodlanmış sayılmaz; buna karşılık İşlem 007–019 boyunca gerçekte eklenen dosyalar ve sentetik CI'lar tablodaki **MEVCUT_KOD/KISMI** olarak gösterilir. 020 yalnız mimari/dokümantasyon yeniden yapılanmasıdır.
- **Durumlar:** `MEVCUT_KOD` = GitHub'da kod mevcut ama kabul zorunlu; `KISMI` = başlangıç var, hedef işlev eksik; `PLANLANDI` = kaynak/ürün henüz yok; `HUKUKI_HOLD` = mevzuat sürümü, dayanak ve uygulanabilirlik doğrulanana kadar etkinleştirilemez.

## Fonksiyonel özellik ve geliştirme takip matrisi

| Kimlik | Gerekli işlev | Hedef kod / bileşen | Mevcut durum | Kabul için somut kanıt | Kullanıcı taslağı |
| --- | --- | --- | --- | --- | --- |
| F01 | Birim, ölçek, CAD/DXF veri modeli `DrawingIR` | `core/ir.py`, `core/units.py` | **KISMI / MEVCUT_KOD — sentetik CI** | Birim bilinmiyorsa kalibrasyonsuz gerçek ölçüm yok | Genel kapsam |
| F02 | DXF ayrıştırma, block/nested INSERT ve layer sinyali | `importers/dxf.py`, `importers/layers.py` | **KISMI / MEVCUT_KOD — sentetik CI kontrolü** | Katman/handle/transform ve bozulan bloklarda güvenli hata | (2) / eski 003 |
| F03 | PDF native vector + ROI + source provenance | `importers/pdf.py`, `importers/pdf_ir.py` | **KISMI / MEVCUT_KOD — sentetik CI** | PDF char/line/curve/rect; dönüş/limit/görsel bbox ölçümü | İlk PDF kararları |
| F04 | OCR ve pafta layout (antet, mahal, kot, tablo) | `ocr/rapid_engine.py` (adapter MEVCUT), `ocr/tiled_regions.py` (PLAN) | **KISMI / MEVCUT_KOD — CPU adapter, layout/tiled OCR planlı** | CPU provider, Türkçe/simge CER, bbox + doğru yöne dönüş | (6) / eski 007 |
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
| F16 | Analiz hattı + CLI | `src/mimarllm/pipeline.py`, `src/mimarllm/cli.py`, `reports/builder.py` | **KISMI / MEVCUT_KOD — sentetik CI** | Sentetik DXF -> geometrik bulgu -> rapor; hata/iptal | (9) / eski 010 |
| F17 | JSON/Markdown/HTML/PDF rapor | `reports/models.py`, `reports/builder.py`, `reports/exporter.py` | **KISMI / MEVCUT_KOD — sentetik CI** | Ölçüm ve kaynak iki yönlü izlenebilir; sahte hüküm yok | (8) / eski 009 |
| F18 | SVG/HTML koordinatlı işaretleme | `reports/visualizer.py` + `reports/exporter.py` + `legal/review_viewer.py` | **KISMI / MEVCUT_KOD — DrawingIR ve mevzuat kaynakları** | Offline, X/Y dönüşümü, hata pinine tıklayınca kaynak | (10) / eski 011 |
| F19 | Tek kullanıcılı localhost dashboard | `src/mimarllm/app/server.py`, `app/launch.py`, `app/static/` | **KISMI / MEVCUT_KOD — sentetik Linux/Windows CI** | Sadece 127.0.0.1; izinli dosya; CDN yok, upload sınırı | (11) / eski 012 |
| F20 | Windows `run.bat`, `build_exe.bat`, `mimar.spec` | Root / `scripts/windows/` | **PLANLANDI — islem_021'e taşındı** | Sonraki gerçek CLI/dashboard entrypoint ile offline onedir | Sohbet / eski 013 |
| F21 | Yerel GGUF/VLM ile semantik aday | `vision/local_vlm.py`, `vision/grammar.py` (PLAN) | **AR-GE / PLAN — model doğrulanmadı** | GGUF + mmproj/Windows ölçümü; 8 GB peak VRAM | (17) / eski 018 |
| F22 | VLM adayını etiketleme, no-overwrite | `vision/semantic.py` (PLAN) | **PLAN — native evidence korunur** | Native/certified kanıt ezilmez; belirsiz REVIEW | (18) / eski 019 |
| F23 | Çapraz modül benchmark, QA ve CI | `benchmarks/` (PLAN), `tests/`, `.github/workflows/` (MEVCUT sentetik) | **KISMI — sentetik CI mevcut, gerçek benchmark PLAN** | Windows gerçek ölçüm, sentetik baseline, CPU/GPU peak | (19) / eski 020 |
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


## İşlem 018 — F16 uygulaması ve kalan kabul

**F16 KISMI/MEVCUT_KOD:** `src/mimarllm/pipeline.py` ile .dxf/.pdf yerel input, her DrawingIR frame için sınırlandırılmış Shapely geometrisi, yalnız kullanıcı `SpaceReview/PassageReview` beyanıyla NetworkX, açık `RuleRun` ile teknik karşılaştırma, varsa exact native referans çizgisine dayalı kullanıcı `CalibrationReference` ve tek kaynak SHA üzerinde `build_analysis_report`. `cli.py` ile `mimarllm analyze`, yerel JSON config, yeni dosyada JSON/MD/HTML/PDF raporu ve `pipeline-manifest.json`; sonuç aşamaları `COMPLETE/REVIEW_REQUIRED/SKIPPED/ERROR`, kısmi ERROR çıktısında exit `4`. Çok sayfalı PDF geometrisi ayrı frame'lerde kalır. Report builder `include_unlinked_sources=True` pipeline sayesinde analiz bulgusu olmasa da gerçek kaynak çizgilerinin raporda görülmesini sağlar; sahte finding oluşturulmaz.

**Teknik kontrol güvenlik:** `$INSUNITS`/layer/ODA yazısı fiziksel ölçek ve net alan hükmü değildir. Kullanıcının bilinen metre referansı, kaynak native SEGMENT+inceleme beyanı olmadan teknik metre karşılaştırması `INSUFFICIENT_EVIDENCE`. Geçiş/kapı kaynağı seçilmezse NetworkX `SKIPPED`; topo hop ile gerçek yangın tahliye rotası veya hukukî uygunluk üretilmez. RuleEngine REGULATORY `INSUFFICIENT_EVIDENCE` kaldı. OCR yalnız kullanıcı ROI + açıkça kurulmuş yerel CPU motorla.

**Açık:** F16 otomatik analiz destekli tek tuş GUI, Windows kurulum/paket acceptance, gerçek mevzuat sürüm/hukukî onay, gerçek mimari plan alanları/uzman sınaması; F19 localhost dashboard ve F20 dağıtım planlı. **F08–F12 HUKUKI_HOLD**. [İşlem 018](islem_018.md) · [Şartname](specs/pipeline-cli-v0.1.md).


## İşlem 019 güncellemesi — İlk kullanıcı arayüzü (F19)

**Kodlanan F19 KISMI/MEVCUT_KOD:** `src/mimarllm/app/server.py` ile yalnız 127.0.0.1 Uvicorn'da yerel DXF/PDF ikili upload, SHA-256 metadatası, rastgele proje/run klasörü, aynı anda tek bounded analiz, aynı DrawingIR kaynak kimliğinden `analysis.json`, `analysis.html`, `drawingir.json`, `pipeline-manifest.json` ve opsiyonel MD/PDF; `app/static` içinde Türkçe mobil uyumlu gerçek proje/analiz/rapor ekranı ve kullanıcı referans çizgisiyle ikinci analiz. `pyproject.toml` dashboard extra+entrypoint, `tests/test_dashboard.py` gerçek ASGI TestClient testleri.

**Güven kapıları:** İstemci localhost-only, Host/Origin/CSRF, dosya uzantı/MB/JSON boyutu ve rastgele kaynak klasörü, allowlist dosya okuma, SHA kaynak/rapor bağları, CSP/HTML escaping, hiç dış CDN/API yok. Bu korumalar **yerel bilgisayarın diğer yetkili process'leri için tam kimlik yetkilendirmesi değildir**; gerçek sızma testi/Windows Edge kullanıcı kabulü açık. `PARTIAL_WITH_ERRORS` uygunluk sonucu gösterilmez, `RuleEngine.REGULATORY=INSUFFICIENT_EVIDENCE`.

**Açık:** F20 gerçek Windows onedir/wheelhouse/installer paketleme, SBOM, test kullanıcı dosyaları, kurum resmî RG yetki/yürürlük kanıtı ve F08–F12 HUKUKI_HOLD. [İşlem 019](islem_019.md) · [Şartname](specs/dashboard-v0.1.md).


## İşlem 020 — Yeni ARCH-CORE Local özellik ID'leri (F25–F37)

Mevcut F01–F24 kimlikleri değiştirilmez. Aşağıdakiler **yalnız planlanan modül/kabul sözleşmesidir**; sıfırdan yazılan dosya olarak GitHub'da henüz bulunmaz.

| Kimlik | Yeni hedef | Kanonik hedef dosya | Gerçek durum | Emniyet/başarı kapısı | Planlanan işlem |
| --- | --- | --- | --- | --- | --- |
| F25 | Kirli CAD için ray/snap/virtual gap bridge *aday katmanı* | `geometry/repair.py` | **PLAN** | orijinal entity/handle ve source polygon değişmez; önerilen köprü PASS değil | 022 |
| F26 | Dimension/door histogramı, birim hipotezi | `core/calibration_candidates.py` | **PLAN** | `INFERRED` ≠ `CONFIRMED`; yanlış fiziksel metreye hukuki sonuç yok | 022 |
| F27 | Layer0, HATCH/ARC duvar/kolon/kapı heuristik adayı | `geometry/heuristics.py` | **PLAN** | güven/provenance/false-positive, sınıf otomatik kesinleştirilmez | 022 |
| F28 | A0/A1 tiled/ROI OCR ve sayfa quad geri dönüşümü | `ocr/tiled_regions.py` | **PLAN** | kaynak PDF page/rotation/crop ve bounded memory | 023 |
| F29 | Mimari jargon/eş anlam sorgu genişletmesi | `rag/synonyms.py` + lisanslı yerel sözlük | **PLAN** | FTS5 baseline'a karşı Recall@k; madde–fıkra karışma yok | 024 |
| F30 | Gömülü SQLite WAL analiz geçmişi/cache/retention | `storage/workspace.py` | **PLAN** | kaynak SHA ve proje izolasyonu, özel veri Git'e yok | 024 |
| F31 | Kaynaklı canlı stage/progress SSE, task budget ve UI genişlemesi | `app/jobs.py` + `app/static/*` | **PLAN** | loopback, request bounds, iş iptali, fallback polling | 025 |
| F32 | 2.5D kütle extrude, Three.js sahne ve kaynak-pin | `geometry/massing.py` + `app/static/scene3d.js` | **PLAN** | onaylı polygon, açık yükseklik, kaynak coordinates; yürürlük/yangın 3D tahmini yok | 026 |
| F33 | Yerel GGUF, multimodal mmproj, gramer, VRAM ön denetimi | `vision/local_vlm.py`, `vision/grammar.py` | **AR-GE/PLAN** | 8 GB Windows gerçek ölçüm, model lisansı, schema/output QA | 027 |
| F34 | 8 boyutlu deterministik pedagojik rubrik | `rubric/ontology.py`, `rubric/grading.py` | **PLAN** | uzman kriterleri ve ağırlıkları; model sayısal notu belirleyemez | 028 |
| F35 | Sıralı jüri karakter/persona/21D ton kritiği | `jury/{schema,personas,runner}.py` | **PLAN** | aynı model çok perspektif = gerçek uzman konsensüsü değildir | 029 |
| F36 | Öğrenci trend/geri bildirim/izinli geçmiş | `analytics/{trend,feedback}.py` | **PLAN** | consent, anonimlik, örneklem ve istatistik belirsizliği | 030 |
| F37 | 2209-A benchmark ve gerçek Windows/GPU/uzman kabul | `benchmarks/` | **PLAN** | kappa/ICC, SUS, CER, Recall, IoU, FPS, VRAM p95 ölçülerek raporlanır | 031 |

### Kaynak metinlerde var ama ürün olarak onaylanmamış iddialar

- `polygon %94+`, `Recall@10 %90`, `300ms`, `60 FPS`, `0 VRAM OOM`, `5 persona 15–25s`: **kanıtlanmış gerçek değer değil**, deneysel hedef/adayı. Bu sayılar README'de gerçekleşmiş gibi sunulamaz.
- `tr_imar/tr_yangin/tr_otopark/tr_siginak/tr_bep/TS` sayısal eşikleri **kaynak PDF yayın sürümü + değişiklik/istisna + proje konum/tarih + bağımsız hukukî onay** olmadan çalışır REGULATORY kontrol olamaz. **F08–F12 HUKUKI_HOLD**.
- `10 jüri`, `15 mimar`, `21 boyut ton`, `8 boyut rubrik` akademik ürün hedefleridir; gerçek bağımsız jüriler, onaylı not algoritması veya pedagojik geçerlilik **şimdi mevcut değildir**.
- "100% permissive dependencies" genişletilmiş pakette transitif/native/model/telif onayı tamamlanmadan söylenmez.
- Bulut sağlayıcı, çoklu Docker DB ve farklı Python codebase mimarisi **plan dışı**. ARCH-CORE özellikleri birinci sınıf ayrı repo/ikinci \`DrawingIR\` değil, mevcut `src/mimarllm/` modülleri olarak tasarlanır.

**Tam kaynak:** [020 master mimari](master-mimari-arch-core-local.md) · [risk matrisi](risk-ve-dogrulama-matrisi.md) · [yeni işlem sırası](uygulama-yol-haritasi.md).
