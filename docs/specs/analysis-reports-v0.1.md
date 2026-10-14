# Kaynaklı Analiz Raporları v0.1 — DrawingIR ↔ Geometri ↔ Mevzuat PDF

- **Geliştirme kaydı:** [islem_017.md](../islem_017.md)
- **Kod:** `src/mimarllm/reports/models.py`, `builder.py`, `visualizer.py`, `exporter.py`.
- **Kapsam:** Çevrimdışı kaynak izli JSON / Markdown / HTML / isteğe bağlı ReportLab PDF teknik özet. Mimari teknik senaryo bulgusuna tıklayınca DrawingIR entity kaynak geometrisine; kanıta tıklayınca bulguya dönüş. **Mevzuat kaynağı yalnız RuleEngine kaynak bağlayıcısı ve gerçek yerel PDF sağlanırsa** ayrı sarı kaynak polygonuyla gösterilir.
- **Kesin:** Rapor bir hukukî uygunluk kararı üretmez. İşlem 012 `RuleEngine.REGULATORY` \`INSUFFICIENT_EVIDENCE\` kilidini değiştirmez. Görsel PDF hash eşleşmesi resmî kaynak ve yürürlük sertifikası değildir.

## 1. Çıktı sözleşmesi

`AnalysisReport` v0.1: özgün `DrawingIR.source_sha256`, çizim kaynağı (PDF/DXF), koordinat `frames[]`, `sources[]`, `findings[]`, kalibrasyon durumu ve sabit `legal_gate=REGULATORY_LOCKED`.

- `ReportSource`: gerçek `entity_id`, `DrawingIR.GeometryPrimitive`, özgün `SourceReference`, layer, frame. DXF'de view_id/CAD handle/nested block path; PDF'de page index, source polygon, koordinat birimleri.
- `ReportFinding`: `DRAWING_FINDING` / `TECHNICAL_RULE` / `REGULATORY_CANDIDATE` / `GEOMETRY_ISSUE` / `FACE_CANDIDATE` / `TOPOLOGY_ISSUE`. `check_id`, `status`, `reason_code`, source entity IDs, ölçüm ve diğer evidence IDs (geçit passage ID bir ölçüm değildir), varsa sayısal teknik değer ve eşik. `FACE_CANDIDATE` her zaman `REVIEW_REQUIRED`; bağımsız incelenmiş oda olduğunu ileri sürmez. NetworkX geçit/adım sayısı gerçek kaçış yürüme mesafesi değildir.
- `LegalEvidenceLink`: yalnız mevcut `RegulatoryEvidenceEvaluation`'ın exact `RuleResult`'ı, orijinal LegalAST node ID ve kaynak span ile bağladığı **mevzuat kaynak adayı**. Her durumda `officiality=NOT_VERIFIED`, `effectivity=NOT_VERIFIED`, `legal_compliance_certified=False`. Yalnız `LegalSourceLocator` veya RAG skoru link oluşturmaz.
- `AnalysisReport` referansları ve cross-frame source dağılımını tekrar Pydantic doğrular. Builder RuleResult SHA ve entity/measurement/passage kimliklerini denetler, yanlış çizim ve çapraz sayfa/layout kanıtlarını reddeder.

## 2. Kullanım

```python
from mimarllm.reports import build_analysis_report, export_report

report = build_analysis_report(
    drawing_ir,
    rules=[technical_rule_result, regulatory_rule_result],
    regulatory_evaluations=[regulatory_evidence_evaluation],
    geometry=geometry_analysis,  # opsiyonel Shapely aday/uyarıları
    topology=topology_result,   # opsiyonel NetworkX inceleme uyarıları
)
export_report(report, "C:/mimarllm/reports/analysis.json")
export_report(report, "C:/mimarllm/reports/analysis.md")
export_report(
    report, "C:/mimarllm/reports/analysis.html",
    drawing_pdf_path="C:/mimarllm/inputs/plan.pdf",  # yalnız PDF DrawingIR ise
    legal_documents=[legal_ast],
    legal_pdf_paths={legal_ast.document_sha256: "C:/mevzuat/orijinal.pdf"},
)
# Yalnız metinsel özeti isteyenler için; ReportLab opsiyonel:
export_report(report, "C:/mimarllm/reports/analysis.pdf")
```

Dosyalar önceden mevcutsa **üzerine yazılmıyor**, kullanıcı yeni yol seçiyor. Yerel çıktıda gerçek kaynak PDF dosyaları içe gömülmüyor; HTML'de yalnız ilgili sayfaların render PNG görüntüleri gömülüyor. İzin verilen veri boyut ve sayfa/piksel sınırları ayrıca kontrol edilir. Dış web sunucusu, CDN, API key gerekmez.

## 3. HTML: bulgudan çizime, çizimden bulguya

Tek bir offline HTML belgesinde:

1. Teknik/kaynak inceleme bulguları, sebep kodları ve `evidence_ids[]`.
2. Her DrawingIR frame için ayrı SVG geometri paneli. Kaynak entity için `#source_<stable hash>`, bulgu için `#finding_<stable hash>` iç bağlantısı. SVG geometri ve altında gerçek CAD handle/blok yolu veya PDF page/frame açıklaması. Geometri üstüne tıklayınca bulguya, bulgu altındaki entity linkinden kaynağa geçilir.
3. **DXF:** Kaynak koordinatları PDF'e çevrilmez; SVG CAD Y-up yönünü doğru göstermek için sadece ekran dönüşümü uygulanır. Bu tüm CAD annotation, hatch ve pafta çıktısını değil, analizle ilişkili DrawingIR native geometrilerini içerir. Kullanıcıya “tam DXF paftası” olduğu iddia edilmez.
4. **PDF DrawingIR:** kullanıcı aynı SHA'ya sahip yerel PDF sağlarsa PDFium ile ilgili sayfa render edilir. DrawingIR PDF-point üst-sol frame'de sayfa \`viewBox\` boyutuna doğrudan yerleştirilir. Sayfa CropBox/Rotate uyuşmazlığında mevcut `render_region` güven kapısı nedeniyle fail-closed. Yerel PDF bulunmazsa yalnız şematik DrawingIR vector ve “PDF sayfası doğrulanmadı” açıklaması vardır.
5. **Mevzuat:** `LegalEvidenceLink` mevcutsa ve özgün PDF/LegalAST sağlanırsa ilgili LegalAST node metni ve bütün \`LegalSourceSpan\` poligonları **orijinal mevzuat PDF sayfası üstüne sarı SVG vurgu** olarak eklenir. Node/metin/span LegalAST uyuşmazlığında veya PDF SHA/page denetimi başarısızsa HTML üretimi reddedilir. Orijinal PDF yoksa sahte kaynak görüntüsü veya URL üretilmez; `HUKUKI_HOLD` gerekçesi korunur.
6. HTML metinleri \`html.escape\` ile korunur; kaynak PDF görüntüsü yalnız byte SHA doğrulandıktan sonra yerel pypdfium2 tarafından üretilir. Kod hiçbir dış siteyi iframe ile açmaz.

**Önemli:** Bir kaynak PDF'sinde dörtgenin doğru yerde görünmesi, işaretlenen metnin hukukî doğruluğunu veya değişikliklerin yürürlükteki konsolide normu ispatlamaz. İmza, yetkili kaynaktan resmî belge doğrulaması, OCR bağımsız insan incelemesi, hukuka uygulanabilirlik **HOLD**.

## 4. JSON/Markdown/PDF özet sınırları

- JSON bütün kaynak IDs, source frames ve LegalAST source quad dizilerini yapısal olarak saklar.
- Markdown metinsel bulgu ve source ID/evidence ID, varsa mevzuat kaynak SHA/page ve HOLD nedeni verir. Canlı SVG HTML'dedir.
- PDF ReportLab ile **özet** üretir; reportlab'ın opsiyonel yerel paket olarak kurulması gerekir. Bu çıktı kaynakların görsel PDF sayfa resimlerini içine gömmez ve HTML'nin iki yönlü görsel gezinti işleviyle aynı değildir. PDF yazı karakterleri varsa yerel Unicode TTF, yoksa Helvetica fallback kullanır. Türkçe metin ve uzun satırlar için gerçek müşterinin tüm çıktıları ayrıca gözden geçirilmelidir.

## 5. Açık kaynaklar ve sonraki işler

Bu aşamada genel rapor pipeline'ı **kısmi**: mevcut DrawingIR, GeometryAnalysis, TopologyResult, RuleResult üzerinden rapor kurucusu mevcut; fakat tek tuşlu CLI, localhost dashboard, canlı seçim, gerçek DXF tam renderer, hukuken onaylı mevzuat kural paketleri, geniş tablo/pafta performansı, gerçek müşteri Windows makinesinde bağımsız kabul henüz kodlanmadı.

**F17 KISMI / MEVCUT_KOD (JSON/Markdown/HTML/PDF özet)** ve **F18 KISMI / MEVCUT_KOD (DrawingIR geometri SVG + özgün PDF sayfa ve mevzuat quad)**. **F08–F12 HUKUKI_HOLD**, F16/F19/F20 ayrıca planlanır.
