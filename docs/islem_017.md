# İşlem 017 — Mimari Analiz Bulgusu → Geometrik Kaynak → Mevzuat PDF Kanıtı Çift Yönlü Raporlama

- **Tarih:** 2026-10-14
- **Durum:** UYGULANDI — çevrimdışı DrawingIR→bulgu→geometri/LegalAST kaynak HTML/JSON/Markdown/PDF raporu; Ubuntu/Windows 248/248 sentetik CI PASS. Gerçek CAD tam pafta görseli, hukukî resmiyet/yürürlük ve kullanıcı Windows kabulü HOLD.
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

## 3. GitHub'a yazılan gerçek kod ve commitler

**İlk yazılan işlem dosyası:** `docs/islem_017.md`; commit **`4ac8aa41326c3d4a0aab3b6652eb4b6abc6ba38f`**. İlk GitHub değişikliğiydi; bütün İşlem 017 kaynak dosyaları ve doküman güncellemeleri bundan sonra yapıldı. İşlem 001–016 kayıtları değiştirilmedi.

| Dosya | Gerçek uygulama | Commit |
| --- | --- | --- |
| `src/mimarllm/reports/models.py` | `AnalysisReport`, `ReportFinding`, `ReportSource`, `ReportFrame` ve `LegalEvidenceLink` Pydantic kaynak/frame/kanunî onay kilidi | `e2ebdac0`; ölçüm ID / passage evidence ayrımı `cae9c984` |
| `src/mimarllm/reports/builder.py` | `DrawingIR` ve kaynak SHA/frame/evidence referanslarından bulguları, teknik RuleResult'ları, Shapely issue/face ve NetworkX issue'larını rapora bağlama; `RegulatoryEvidenceEvaluation` exact rule/source uyumu | `a356a131`, duplicate rule ret `32bb372f` |
| `src/mimarllm/reports/visualizer.py` | CAD layout vektör kaynak SVG, PDF point frame, CAD Y-up ekran koordinatı, source→finding/finding→source anchor; CAD handle/nested block yolunu koruma | `11fe643d` |
| `src/mimarllm/reports/exporter.py` | Gerçek Drawing PDF SHA doğrulanmış pypdfium2 sayfası + DrawingIR SVG, özgün mevzuat PDF LegalAST node/quad sarı vurgusu, çift yönlü anchor, JSON/Markdown/HTML ve ReportLab PDF **metinsel özet**; kaynak eksik/uyuşmazsa fail closed | `e1b6ed9d`, `5014bcbc`, `fe22cf96`; Markdown uyarı düzeltme `37a6e336` |
| `src/mimarllm/reports/__init__.py` | Dışa açılan rapor API'leri | `65de0b9d` |
| `tests/test_reports.py` | ReportLab sentetik mimari plan PDF + gerçek ezdxf DXF, DrawingIR source geometry, gerçek RuleEngine technical length, held regulatory LegalAST node/quad HTML, hash fake, XSS, PDF background, JSON/MD/HTML/PDF ve referential integrity regresyonları | `ead2be74`; fixture/UI beklentileri `837f00dd`, `e7eff337`, `340dcef` |
| `.github/workflows/core-contracts.yml` | `src/mimarllm/reports/**` değişimleri ve `tests/test_reports.py` Ubuntu+Windows matrix | `d21318dd` |
| `pyproject.toml` | İsteğe bağlı `reports` ekstra: yerel `reportlab>=4,<5` | `e06a9cd6` |
| `docs/specs/analysis-reports-v0.1.md` | Kullanım, CAD/PDF kaynak koordinatı, çift yönlü kaynak navigasyonu, PDF özet sınırları ve HUKUKI_HOLD | `cfbea5c8` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F17/F18 `KISMI/MEVCUT_KOD`, F16/F19 ayrı, K-128–K-136 ve güven/hukukî sınırlamalar | `8bcf955c`, `071108dc`, `56eec0cc`, `94a09197` |

## 4. CI gerçekte neyi sınadı?

- İlk tümleşik CI [**38524425745**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38524425745): **245 PASS, 3 FAIL**. PDF kaynak SVG viewBox ondalık format beklentisi; orijinal PDF'nin yokluğu uyarısı metninin büyük/küçük harf farklılığı; önemli uygulama hatası olarak LegalAST/yerel PDF hiç verilmediğinde mevzuat-source HOLD kartının görünmemesi.
- Eksik kaynaklı hukukî HOLD kartı kodda düzeltildi, format/uyarı beklentileri testte revize edildi. [**38524569799**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38524569799): **247 PASS, 1 FAIL**. Test PDF'deki gerçek vektör yerine kaynak glyph/point seçiyordu; buna rağmen `<polyline>` bekliyordu. Gerçek çizgi/poligon kaynak varlığı test fixture'ında açıkça seçildi.
- [**38524680293**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38524680293) : **Ubuntu 248/248 PASS**, **Windows 248/248 PASS**; 2 Python uyarısının nedeni Markdown backtick'te gereksiz ters-slash karakteriydi.
- **Son kod HEAD `37a6e336fc4d30d6c96b51e7214e5364a8808aea`** için [**GitHub Actions 38525132239**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38525132239): **Ubuntu Python 3.11 248/248 PASS (6,60 sn), GitHub-hosted Windows Python 3.11 248/248 PASS (10,70 sn)**; Python pytest uyarısı yok. İki OS job logları ayrı incelendi.
- Testler gerçekten sentetik ReportLab PDF ve ezdxf DXF üretip `parse_pdf_ir` / `parse_dxf` ile DrawingIR'ye alır; teknik RuleEngine hesabını, kaynak geometri SVG HTML, gerçek PDFium page PNG embedding, özgün LegalAST span bazlı hukukî PDF vurgusu, sahte source SHA ve yasa dışı verdict reddini kontrol eder. **İnsan gözüyle gerçek RG/bina paftası görsel kabulü, gerçek kullanıcı Windows bilgisayarı, gerçek hukukî uzman/source imza kabulü bu CI kapsamı değildir.**

## 5. Kalan eksikler ve sonraki işlem

**F17 KISMI:** JSON/Markdown/HTML + ReportLab PDF metinsel raporu var. PDF, HTML kadar interaktif ya da vurgulu orijinal kaynak görsellerini içine almış değil. Rapor çıktısı tek rapor API'siyle ve verilen mevcut DrawingIR/RuleResult girdisiyle yapılır; uçtan uca otomatik CLI/workspace orchestration henüz yok.

**F18 KISMI:** DXF/CAD için SVG sadece rapor bulgularının kullandığı DrawingIR kaynak geometrisini gösterir, bütün paftanın tam mühendislik CAD görünümü değil. PDF kanıtındaki sarı konum için gerçek SHA eşleşmiş sayfa ve exact LegalAST node/span gerekir. Tarayıcı click davranışının gerçek Chrome/Edge kabulü ve uzun belge performansı henüz ayrıca görülmeli.

**F08–F12 HUKUKI_HOLD:** Resmî Gazete PDF yetkili kaynak/doğruluk imzası, yıl yıl hüküm konsolidasyonu, geçici maddeler/istisna/belediye projeye uygulanabilirliği, gerçek uzman imzalı karar henüz yok. Teknik `COMPLIANT` yalnız teknik sentetik kıyastır; `RuleEngine REGULATORY` sonuçları `INSUFFICIENT_EVIDENCE` olmaya devam eder. Kullanıcı dosyasına ait RAG skoru veya sarı görsel hukukî PASS oluşturmaz.

**Sonraki işlem:** `docs/islem_018.md` **henüz oluşturulmadı**. F16 mevcut modüllerin ortak analiz pipeline/CLI'si ve rapor/yerel arayüz entegrasyonu mantıklı sonraki mühendislik paketi. Sonraki ilk GitHub yazımı işlem kayıt dosyası oluşturulması olacak; 001–017 önceki kayıtlar korunacak.

