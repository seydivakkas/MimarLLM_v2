# İşlem 017 — Mimari Analiz Bulgusu → Geometrik Kaynak → Mevzuat PDF Kanıtı Çift Yönlü Raporlama

- **Tarih:** 2026-10-14
- **Durum:** ÖN KAYIT — İşlem 017'nin **ilk GitHub yazımı**, bütün kod ve diğer belge değişikliklerinden önce.
- **Önkoşullar:** 007 DrawingIR v0.1; 008 DXF; 009 PDF; 010 Shapely; 011 NetworkX; 012 RuleEngine; 013–016 LegalAST, RAG, kaynak bağlama ve sarı vurgulu özgün PDF görsel inceleme.
- **Mimari:** Windows-first, çevrimdışı tek kullanıcı, yerel dosyalar; ücretli/uzak API, indirilen model, CDN yasak.
- **Güven sınırı:** Teknik senaryo PASS/FAIL **hukukî uygunluk değildir**. REGULATORY/HUKUKI_HOLD açık kalır; RAG skoru veya sarı kaynak kutusu mevzuatın yürürlükte olduğuna dair kanıt değildir.

## 1. İlk geliştirilecek somut dosyalar

1. `src/mimarllm/reports/models.py`: `DrawingIR` ve `RuleResult` ile bağlantılı sürümlü, fail-closed `AnalysisReport` ve `ReportFinding`. Kaynak çizim SHA, frame, entity/measurement evidence, kaynak handle/blok yolu, geometrik primitive ve legal span ve kural–kaynak bağlantısının durumu ayrı izlenecek. Bulgu–CAD/PDF/LegalAST node cross-reference şeması; görüş bildirilmeyen kaynakta net hukukî başarı alanı olmayacak.
2. `src/mimarllm/reports/builder.py`: DrawingIR, geometri/topoloji ölçüm adayları, RuleResult ve isteğe bağlı `RegulatoryEvidenceEvaluation` ile rapor kanıt zinciri oluştur. Mevcut DrawingIR entity/measurement/coordinates yeniden valide edilecek. RuleResult başka DrawingIR SHA veya olmayan kanıt referansından geldiyse fail-closed. RAG skoru/LegalSourceLocator tek başına orijinal hukukî kaynak bağı sayılmayacak. İsteğe bağlı geometri ve topoloji issue/candidate'leri karar olmayan gözlem olarak dahil et.
3. `src/mimarllm/reports/visualizer.py`: CAD/DXF geometrisini SVG'de **kaynak DrawingIR koordinatları** ile göster; kaynak CAD dosyasının tam pafta render'ı olduğu iddia edilmesin. PDF DrawingIR kaynağında özgün yerel PDF SHA doğrulanırsa pypdfium2 raster sayfa arka planına aynı frame PDF-point koordinatlarında geometri sarı vurgusu. Bir bulguya tıklayınca o kaynağa, kaynaktan bulguya `#...` HTML anchor. Çoklu frame ve PDF sayfaları ayrı görünüm; karışık frame ile sahte konum çizilmez. Orijinal PDF yoksa kaynak pinini asla gerçek PDF diye sunma.
4. `src/mimarllm/reports/exporter.py`: kaynak bağlantılı çevrimdışı JSON, Markdown, kendi kendine yeterli HTML ve istenirse PDF metin özeti; HTML'de geometrik kaynak ve **varsa gerçekten sağlanan özgün mevzuat PDF** için ilgili sayfa/polygonun sarı vurgulu görsel kanıtı. HTML'e resmiyet/yürürlük onayı yerine HOLD ve review gerekçeleri yazılacak. PNG/SVG, metin, CAD layer/handle ve tarih alanında XSS/HTML injection kaçış.
5. `tests/test_reports.py`: ReportLab sentetik PDF ve ezdxf DXF, DrawingIR ve RuleEngine bağları; gerçek kaynak frame, ölçüm evidence, görsel SVG koordinat, sahte SHA ve source, ayrı sayfa ve farklı PDF'lerin izolasyonu, hukukî HOLD ve cross-link, JSON/Markdown/HTML/PDF, XSS, görsel boyut limitleri; Ubuntu/Windows synthetic CI.
6. CI `.github/workflows/core-contracts.yml`, `docs/specs/analysis-reports-v0.1.md`, README, F17/F18 envanter, yol haritası, karar defteri.

## 2. Yasak çıkarımlar ve mühendislik sınırları

- `DrawingIR.SourceReference` CAD handle/blok kaynak yolunun ve PDF page/source polygon'unun **özniteliğidir**; karışık CAD layout/PDF page kendi halinde gösterilir, keyfi ölçek/transform uydurulmaz. DXF kaynak entity geometrisi SVG vektör olarak çizilebilir fakat DXF'in tasarım baskı görünümünü reprodüksiyon olarak iddia edilmez.
- `RuleResult.status=COMPLIANT/NON_COMPLIANT` yalnız `RuleDomain.TECHNICAL` içindir. Bir mevzuat adayı için sonuçlar `INSUFFICIENT_EVIDENCE`, ayrı `RegulatoryEvidenceEvaluation` özgün LegalAST kanıtı olmadan sarı hukukî PDF iddiası üretmez.
- Orijinal mevzuat PDF konumu yalnız `SourceAudit.LOCAL_SOURCE_MATCHED` ve `LegalSourceSpan` exact node referansı varsa görüntülenir; yine de **hukukî kaynak resmiyeti/yürürlük garanti edilmez**. Eğer hukukî PDF yoksa açık “PDF kanıt görseli mevcut değil” notu.
- Kod kapsamı raporlama ve yerel HTML kaynak gezintisidir; localhost dashboard, gerçek Windows installer, tam mimari çizim semantiği, gerçek yangın/imar uygunluk algoritmaları ayrı paketlerde. Testler sentetik; gerçek projeler/hukukî görsel bağımsız kabul son aşamada.

## 3. İş sonunda gerçek kayıt

Gerçek file/commit SHA'lar, Linux/Windows CI run test sayıları, regressions, kalan F17/F18 açık işleri ve hukukî HOLD kapsamı bu **aynı dosyanın son GitHub güncellemesinde** kaydedilecek.
