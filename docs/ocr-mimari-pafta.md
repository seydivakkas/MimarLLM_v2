# Mimari Pafta için Native PDF + RapidOCR CPU Sözleşmesi

- **Durum:** Teknik tasarım ve başlangıç kodu. İşlem kaydı: [islem_005.md](islem_005.md)
- **Tek PDF OCR hattı:** `pdfplumber` + `pypdfium2` + `rapidocr` / `onnxruntime` CPU.
- **Karar:** [ADR-002](adr/ADR-002-PDF-Engine-License.md)

## Format önceliği

```text
DXF -> ezdxf CAD text/block/attributes (ileride)
PDF -> pdfplumber chars/lines/curves/rects -> TextCandidate/VectorObservation
        | bozuk Unicode, outlined SHX, native text eksikliği vb.
        v
      pypdfium2 target ROI -> PIL bitmap
        v
      RapidOCR CPU ONNX -> 4-point quad
        v
      normalized pdf_top_left_pt source coordinate
        v
      candidate/evidence; fiziksel geometri için kalibrasyon gerekir
```

## PDF native kaynak yapısı

- `pdfplumber`: `page.chars`, `lines`, `curves`, `rects` ve `char["matrix"]`.
- Normalleştirilmiş PDF koordinatı **üst-sol orijinli PDF points**. Kaynak bbox ile gerçek dört köşe `quad` aynı şey değildir; varsayılan ilk karakter polygon'u axis-aligned bbox üzerinden üretilir ve rotated glyph doğruluğu için ek çalışma gerektirir.
- `matrix` dönüş bilgisi saklanır; 45°/90°/270° glyph gerçek quad matematiği henüz uygulanmış değildir.
- Sayfa/açı/cropbox bilinmiyorsa “tam koordinat doğrulandı” kararı verilemez.
- Vektör öğeler CAD duvarı veya kapı **olarak sınıflandırılmaz**, yalnız `VectorObservation` olarak saklanır.

## Raster ROI ve kaynak konumu

- `pypdfium2.PdfPage.render(scale=dpi/72, crop=(left,bottom,right,top))` ile bölgesel render.
- Crop metodu sayfa rotasyonunun etkisine bağlıdır. İlk çalışan kod döndürülmüş sayfayı açıkça reddeder.
- `max_pixels` ve dosya/page limitleri uygulanır. Daha büyük pafta küçük tile olarak işlenebilir (sonraki iş).
- OCR noktası `(px,py)` → PDF noktası `(roi_left+px/scale, roi_top+py/scale)`. Render clip/rotasyon/farklı page box desteği ayrı sentetik kabulden geçecek.
- ROI görüntüsünün ortamdaki dosyalarla ilgisi çözüm sırasında `document_sha256` ile korunur.

## RapidOCR adapter

- `rapidocr` paketinin güncel kullanımında `result.boxes, result.txts, result.scores` vardır; `boxes` `N×4×2` poligonları temsil eder.
- `onnxruntime` CPU wheel ve CPUExecutionProvider şarttır.
- Model dosyaları normal çalışma anında indirilmez.
- Tespit skoru metnin kesin doğru olduğu anlamına gelmez. Kullanıcı/onay/ölçü doğrulaması gerekir.
- 90°/270° ve 45° yazılar için crop rotate + inverse matrix işlemi planlıdır; varsayılan classifier 0°/180° ayrımı tam çözüm değildir.
- Teknik işaretler ve Türkçe karakterler için `exact token match` ve karakter hata oranı raporlanacak.

## Gelecek modüller

```text
src/mimarllm/
  core/models.py             # Source/quad/karakter/vektör sözleşmeleri
  importers/pdf.py           # pdfplumber native + pypdfium2 crop
  ocr/rapid_engine.py        # RapidOCR CPU wrapper
  ocr/text_extractor.py      # Native kalite kapısı + ROI orkestrasyonu [sonraki]
  ocr/box_utils.py           # rotate/deskew/homography [sonraki]
  regulations/extraction.py  # ayrı offline ETL [sonraki]
```

## Sentetik kabul

- Native PDF character positions, fonts, line/rect/curve gözlemleri.
- Raster crop 72/144/300 DPI, doğru source coordinate ve pixel budget.
- Döndürülmüş sayfa kontrollü ret; sonradan dönüş matrisi kanıtı.
- 0/45/90/180/270° yazıda 4 noktalı bbox/quad karşılaştırma.
- Türkçe `ş ğ ı İ ç ö ü`, teknik simgeler `Ø ± ° ²`, ölçü metni CER.
- Belge değiştiğinde `SHA-256` ile eski source span yeniden kullanımına izin verilmemesi.
- Çok sütun/tablolar için özgün PDF page + cell bbox referansı.

**Gerçek OCR inference/Windows testi ve yüksek çözünürlüklü pafta ölçek doğrulaması henüz geçmedi.**

Kaynaklar: [pdfplumber](https://github.com/jsvine/pdfplumber) · [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) · [RapidOCR](https://github.com/RapidAI/RapidOCR).
