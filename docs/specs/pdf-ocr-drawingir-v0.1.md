# PDF → DrawingIR ve RapidOCR Kaynak Poligonu (v0.1)

- **İşlem:** [islem_009.md](../islem_009.md)
- **Kapsam:** Yerel PDF native karakter, line/rect/curve ve kullanıcı işaretli OCR bölgelerini DrawingIR içinde çift yönlü kaynak iziyle birleştirme.
- **Kesin PDF/OCR yığını:** `pdfplumber`, `pypdfium2`, `rapidocr + onnxruntime CPU`. Dış AI API veya ikinci PDF/OCR motoru kullanılmaz.
- **Kod:** `src/mimarllm/importers/pdf.py`, `src/mimarllm/importers/pdf_ir.py`, `src/mimarllm/ocr/rapid_engine.py`.
- **Durum:** Başlangıç uygulaması mevcut, gerçek Windows OCR modeli, cropbox ve karmaşık kaynak kabulü ayrıdır.

## Temel veri akışı

```text
PDF -> pdfplumber inspect_pdf()
                | native chars -> TextCandidate + DrawingIR(PDF_NATIVE)
                | native lines -> gerçek uç noktalar / SEGMENT
                | native rectangles -> gerçek köşeler / POLYGON
                | cubic curves -> kontrollü Bezier flatten / APPROXIMATED
                |
  kullanıcı seçili ROI -> pypdfium2.render_region()
                          | görüntü ve pixel_origin_pdf_points
                          v
                   RapidCpuOcr.read(region)
                          | CPU ONNX + rotated 4-point polygon
                          v
          DrawingIR(PDF_OCR_TEXT_QUAD / OCR_CANDIDATE)
```

`parse_pdf_ir(path, ocr_regions=None, ocr_engine=None)` fonksiyonu her zaman native okuma ile başlar. OCR ancak **açık ROI listesi ve açıkça enjekte edilmiş yerel OCR motoru** varsa yürütülür. Normal import sırasında otomatik model kurulumu veya indirme yapılmaz. OCR gerekir ama motor yoksa `OcrUnavailable` sonucu döner (hata fırlatılır). Bu **offline ilkesi** açısından önemlidir; kullanıcı orijinal kaynak/model dosyalarını önceden temin etmelidir.

## Kaynak koordinat sistemleri

- Her PDF sayfası ayrı `CoordinateFrame(frame_id="pdf:pageN", kind=PDF_POINT, y_direction=DOWN, page_index=N)`.
- Native karakterler PDF sayfasının üst-sol orijinli `x0/top/x1/bottom` bbox ve varsa `char.matrix` ile izlenir. PDF görüntü koordinatı metre değildir; fiziksel kalibrasyon `UNKNOWN`.
- Native text için `SourceReference.source_polygon` **karakterin eksenlere paralel bounding rectangle'ıdır**; rotasyonlu karakterin gerçek glif dörtgeni olduğu iddia edilemez. `type_candidate="PDF_NATIVE_GLYPH_BBOX"` etiketi bu sınırı açıklar.
- Native `LINE`: **gerçek `pts` uçları** kullanılır; bbox diyagonal çizgi yerine geçmez.
- Native `RECT`: dört `pts` poligonu; `CURVE`: PDF path `m/l/c/h` flatten (her cubic için 16 nokta), `APPROXIMATED_PDF_CURVE` uyarısı.
- OCR `quad`: modelin verdiği **dört noktalı tespit alanıdır**; her nokta `RenderedRegion.pixel_to_source()` ile gerçek PDF point sistemine taşınır; kullanıcı onaylı tam geometri veya doğru hukukî metin sayılmaz.
- `document_sha256` analiz başı-sonu ve ROI bazında kontrol edilir. Aynı PDF adı altında dosya içeriği değişirse kaynak uyumsuzluğu nedeniyle işlem reddedilir.
- `TextCandidate` ve `DrawingEntity` ayrı şekilde döner; metin ve geometriye ait ham kanıt korunur. `DrawingIR.measurements` ve `findings` bu aşamada **boştur**.

## Sayfa rotasyonu ve CropBox davranışı

`pdfplumber` rotated page metin/vektör koordinatlarını görüntülenen sayfa üzerinden verir. `pypdfium2` standart sayfa `/Rotate=0/90/180/270` için render yapar. Bağımsız sentetik testler rotasyonlu tam render ile aynı görüntünün ROI kesitini karşılaştırır:

- **0°:** `pypdfium2` ile doğrudan crop (left,bottom,right,top) ve DPR.
- **90°/180°/270°:** Güvenilirlik için tam sayfayı RAM bütçesi dahilinde render edip **PIL ROI crop**. Çünkü PDFium'da 90° doğrudan crop ile tam sayfa kesimi sentetik örnekte uyuşmamıştır.
- **Büyük döndürülmüş pafta:** Tam sayfa render, `max_pixels` sınırını aşarsa **açık ret**, gizli tahmin veya OOM yok.
- **Standart dışı PDF `CropBox != MediaBox`:** pdfplumber media-page coordinates ile PDFium cropped visible origin farklı olabilir. Kaynak poligonu yanlış konumlandırmamak için şimdilik **açık ret**. Native PDF çıkarımı bu durumda yine kullanılabilir; OCR ROI bu sürümde desteklenmez.
- **Subpixel crop:** ROI'nin başlangıç PDF point'i ile rasterized görüntüdeki ilk gerçek pikselin kaynağı farklı olabilir; `RenderedRegion.pixel_origin_pdf_points` bunu kayıt altına alır. `pixel_to_source` / `source_to_pixel` dönüşümleri gerçek piksel orijinine dayanır.

## Kısıt ve belirsizlik matrisi

| Yetenek | Kapsam / sınır |
| --- | --- |
| PDF native line/rect | Evet; kaynak şekil koordinatları |
| PDF cubic curve | Yaklaşık poligon, `APPROXIMATED` diagnostic |
| PDF karakter metni | Evet; bbox/matrix var, true rotated glyph quad yok |
| OCR region | Evet; kullanıcı açıkça ROI ve CPU engine vermeli |
| RapidOCR CPU gerçek model | Model doğrulama/Windows kabulü HOLD |
| 0/90/180/270 standart rotasyon | Evet; sentetik bitmap karşılaştırma |
| PDF non-default CropBox + ROI | HOLD; açık hata |
| PDF fiziksel ölçü | Otomatik yok; kalibrasyon şart |
| Otomatik text quality gate / SHX detection | Sonraki sürüm; şu an ROI manuel |
| Çok yüksek DPI tiled rotation / renk farklılıkları | HOLD |
| Türkçe, 45° açılı OCR ve Ø/±/°/² doğruluk | Gerçek veriyle CER/quad IoU kabulü HOLD |

## Sentetik test ve kaynaklar

- `tests/test_pdf_ir.py`: iki sayfalı PDF, diagonal native line, rect, Bezier, SHA-256 kaynak zinciri, injected/mock OCR quad, invalid ROI ve non-local source reddi, 0/90/180/270 render karşılaştırma, oversized rotation, non-default CropBox ve subpixel origin.
- `tests/test_pdf_contract.py`: mevcut PDF okuma ve basit bbox/render regresyonları.
- `tests/test_drawing_ir.py` / `tests/test_units.py`: kanıt ve kaynak kalibrasyonu.

Dış teknik belgeler:
- [pypdfium2 crop API (post rotation)](https://pypdfium2.readthedocs.io/en/stable/python_api.html)
- [pdfplumber native vectors/char matrix](https://github.com/jsvine/pdfplumber)

**İşlem 010 ön koşulu:** kaynak metin/çizgi verileri güvenilir aktarılmış olsa da hiçbir PDF segmentine otomatik `WALL` veya `DOOR` kararı verilmedi. Geometri motoru gerçek inner boundary ve toleranslı bağlantı kanıtı oluşturacak.
