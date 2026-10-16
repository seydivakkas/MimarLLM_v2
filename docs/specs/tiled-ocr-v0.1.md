# İşlem 023 — A0/A1 Tiled OCR v0.1: Yerel ROI, PDF Kaynak Dörtgeni ve Antet Konum Adayı

**Kod:** `src/mimarllm/ocr/tiles.py`, `ocr/layout.py`, `importers/pdf_ir.py`, `pipeline.py`, `cli.py`. **İşlem kaydı:** [islem_023.md](../islem_023.md). Bu metin **kaynak kod sözleşmesini** açıklar; gerçek Türkçe OCR kalitesi ve A0 peak RSS/latency ölçülmedi.

## 1. Opt-in A0/A1 karo akışı

İlk önkoşul: pdfplumber yerel native metin ve CAD vektörlerini okumaya devam eder. Eksik raster/SHX metin alanlarını kullanıcı `tiled_ocr` ile açıkça seçebilir. A0/A1 PDF'de birkaç megapiksel boyutlu her karo sırasıyla `pypdfium2` ile render edilir ve kurulu yerel `RapidOCR + onnxruntime CPU` okuyucusu üzerinden değerlendirilir. Karo listesi OCR başlamadan sayfa boyutu, sayfa numarası, media/crop, /Rotate ve kaynak SHA'yla doğrulanır. Render edilen görüntüler saklanmaz; her karo işlenip temizlenir.

**Varsayılan OCR KAPALI.** Model ağırlıkları/ONNX Runtime bu depo ve sentetik CI tarafından indirilmez. Gerçek OCR için kullanıcı cihazında lisansı/kullanımı incelenmiş model ve CPU runtime önceden kurulmuş olmalıdır.

```json
{
  "tiled_ocr": [
    {
      "page_index": 0,
      "roi_points": [0, 0, 2384, 3370],
      "tile_width_pt": 384,
      "tile_height_pt": 384,
      "overlap_pt": 32,
      "dpi": 144,
      "max_tiles": 128,
      "max_pixels_per_tile": 4000000,
      "max_total_pixels": 60000000,
      "max_ocr_candidates": 3000
    }
  ]
}
```

- `page_index` 0 tabanlı; `roi_points` üst-sol orijinli, **döndürülmüş gösterim koordinatında PDF POINT**, fiziksel metre değildir. Örnek 2384 × 3370 pt *sentetik A0 yakınsamasıdır*, gerçek PDF sayfasının boyutu önceden görülüp onun sınırlarına göre güncellenmelidir.
- `tile_width_pt / tile_height_pt` 32–900, varsayılan 384; `overlap_pt` 0–200 ve her eksenin yarı kenarından küçük olmalı. Varsayılan 32 pt; ardışık karolar kaynak koordinatlarını birbirine taşımaz.
- `dpi` 72–240 (varsayılan 144); bir tile en çok 8 milyon ve varsayılan 4 milyon piksel, varsayılan istek başına toplam 60 milyon piksel, karo sayısı 128, token 3000. Çoklu pipeline'da en fazla 8 istek ve toplam 256 karo beyan bütçesi; maliyet gerçek dosyada ayrıca ölçülecek.
- Pypdfium2 `render_region` döndürülmüş sayfada güvenli fullpage fallback gerektirebilir. A0 döndürülmüş sayfa bu fallback'ın bellek sınırını aşıyorsa `PdfInputError` (no OCR/source guessing). Nondefault CropBox fail closed. ROI dışına çıkmış sahte dörtgen ve süreçte değişmiş PDF byte SHA reddedilir.
- OCR reader'ın `read(RenderedRegion)` sonucu `TextCandidate(method="rapidocr_cpu",page_index,polygon)` olmalı. `RenderedRegion.source_to_pixel`/`pixel_to_source` gerçek yuvarlanmış `pixel_origin_pdf_points` üzerinden PDF üst-sol koordinat geri dönüşümü sağlar. Pipeline **OCR polygonunu kaynak vektör veya bina sınırı diye kullanmaz.**
- Aynı metnin tile overlap'te birden fazla dönmesi: Unicode NFKC+casefold whitespace normalize metin **ve** kaynak bbox IoU en az 0.50 ise tek `OCR_CANDIDATE` saklanır. Daha yüksek confidence tercih edilir; iki ayrı konumda aynı ODA/KAPI etiketi korunur. Bu algoritma gerçek kısmi sözcük/çok satır birleştirme semantik testi değildir; silinen sayı manifestte raporlanır.

## 2. Python API ve pipeline çıktı alanları

```python
from mimarllm.ocr.tiles import TiledOcrRequest, plan_ocr_tiles, read_tiled_ocr
from mimarllm.importers.pdf_ir import parse_pdf_ir
from mimarllm.pipeline import PipelineConfig, run_local_pipeline

request = TiledOcrRequest(
    page_index=0, roi_points=(0,0,800,800),
    tile_width_pt=384, tile_height_pt=384, overlap_pt=32,
)
source_tiles = plan_ocr_tiles("C:/mimarlik/orijinal.pdf",request)
# API kullanımında explicit reader enjekte edilir (RapidOCR CPU veya sentetik test stub):
result = parse_pdf_ir("C:/mimarlik/orijinal.pdf",
                      tiled_ocr=(request,), ocr_engine=local_cpu_reader)
assert all(not ent.is_verified_semantics for ent in result.drawing.entities)
pipeline = run_local_pipeline(
    "C:/mimarlik/orijinal.pdf",
    PipelineConfig(tiled_ocr=(request,)), ocr_reader=local_cpu_reader,
)
```

`PdfIrResult.tiled_ocr_results`: karo ROI/source SHA/rotation, OCR review-candidates, token→tile ID eşleşmesi, overlapped duplicate sayısı. `PdfIrResult.layout_candidates`: orijinal PDF SHA/page/quad + gerçek char/token ID listeli yerleşim adayları.

`PipelineManifest` alanları: `ocr_tile_count`, `ocr_candidate_count`, `ocr_overlap_duplicates`, `layout_candidates[]`, mevcut kaynak SHA, frame ID ve `REGULATORY_LOCKED`. PDF raster OCR **import** aşamasını `REVIEW_REQUIRED` yapar; teknik/yangın/hukukî PASS üretmez.

`mimarllm analyze local.pdf --config config.json --output-dir out` sadece kullanıcı tile/ROI seçtiyse `RapidCpuOcr` kurmaya girişir. Yerel OCR bağımlılığı yoksa CLI **açık hata** verir, otomatik ağdan indirme yoktur. DXF için OCR isteği reddedilir.

## 3. Antet ve sayfa düzeni: sadece geometrik gözlem

`detect_layout_candidates` native glyph/OCR text quad ve gerçek PDF sayfa boyutlarından şu konumları aday gösterir:

- `LOWER_RIGHT_TEXT_CLUSTER`: sayfa genişliğinin son %37, yüksekliğin son %35'i içindeki yazılar; **olası antet bölgesi**, doğrulanmış antet / başlık / mimar / ölçek / kurum değildir.
- `TOP_MARGIN_TEXT_CLUSTER`: üst %12'de metin kümesi.
- `BOTTOM_MARGIN_TEXT_CLUSTER`: alt %12'de metin kümesi.

Çıktılar `REVIEW_REQUIRED`, `POSITION_ONLY_NO_TITLE_BLOCK_CERTIFICATION`. Şu an gerçek Türkçe antet alanı tanıma, kot/mahal/simge semantiği, hücrelere ayırma, fotoğraf/scan tekno referansı, PDF editörü veya tutarlı okuma sırası algoritması mevcut değildir.

## 4. Test ve güvenlik sınırları

Sentetik ReportLab PDF üzerinden A0 benzeri büyük sayfada **render yapmadan** bounded karo planı, 4 tile ROI görüntüleme, çakışan 4 OCR token'ın kaynak koordinatına dönüşü/dedup, farklı konumdaki aynı etiketin korunması, sahte page/quad/ROI/method ret, native PDF ve OCR DrawingIR kaynak ayrımı, layout adayları, CLI/pipeline `REGULATORY_LOCKED` durumları test edilir. Test OCR motoru deterministik enjekte edilmiş **fake reader**; gerçek OCR model ağırlıkları veya CER/WER/RSS ölçümü **yoktur**.

**Açık kabul:** gerçek A0/A1 taranmış paftaların çeşitli rotasyon/crop, antet/çizim yazı tipi, Türkçe simge/OCR CER–WER doğruluğu, gerçek hedef Windows cihazının RSS/time/failcase, gerçek RapidOCR CPU model ağırlıklarının kurulumu/hakları ve gerçek kullanıcı Edge görsel koordinat kabulü.

**F28 KISMI/MEVCUT_KOD + Linux/Windows sentetik CI**, **F04 KISMI**, **F03 KISMI**. F08–F12 HUKUKI_HOLD ve hukuken `APPROVED_FOR_CHECK` kapalıdır.
