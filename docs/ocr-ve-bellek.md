# OCR ve Yerel Kaynak Yönetimi — Güncel Tasarım

- **Karar kaydı:** [ADR-002](adr/ADR-002-PDF-Engine-License.md) · [islem_005.md](islem_005.md)
- **Durum:** Kod çekirdeği başladı; RapidOCR gerçek modeli ve hedef Windows makinesi henüz test edilmedi.
- **Kesin bileşenler:** `pdfplumber`, `pypdfium2`, `rapidocr` + `onnxruntime` **CPU**.

## Veri ve model akışı

```text
DXF CAD TEXT / PDF native glyph (pdfplumber)
           |
  Source-character quality gate
           |
   Eksik/şüpheli PDF ROI
           |
 pypdfium2 bounded raster
           |
 RapidOCR ONNX CPU
           |
 Four-point OCR polygon + text
           |
 pixel->PDF point transform
           |
 DrawingIR evidence candidate
```

Metin katmanı olup olmadığını sayfa genelinde değil **bölge ve karakter düzeyinde** inceleriz. Gövde metninin seçilebilir olması SHX veya çizgiye dönmüş ölçü işaretlerinin okunabildiğini kanıtlamaz.

## Donanım ve offline şartları

- Intel i7 14. nesil, 32 GB RAM; OCR **ONNX Runtime CPUExecutionProvider** ile çalışır, CUDA VRAM tahsisine ihtiyaç duymaz.
- 8 GB VRAM yerel VLM'ye bırakılır. Buna rağmen OCR CPU ve RAM bütçesiyle, VLM GPU işi aynı makinede performansı etkileyebilir.
- İlk kodda `onnxruntime-gpu` kurulumu açıkça reddedilecek şekilde tasarlandı; doğru provider, gerçek Windows ortamında doğrulanacak.
- Model indirmesi **normal analiz sırasında yasak**. Yerel model manifest/hash ve dağıtım hakları paketleme aşamasında doğrulanır.
- `RapidOCR` sonuçları `boxes`, `txts`, `scores` içerir; her kutu PDF ROI'ye ait 4 noktayla geri dönüştürülür.
- Varsayılan line-angle classifier yalnız 0°/180° ayrımına dayanır. 45°/90°/270° pafta yazıları için crop orientasyonu ve özel sentetik karşılaştırmalar gerekir.
- Türkçe (İ, ı, ğ, ş, ç, ö, ü) ve teknik semboller (Ø, ±, °, ²) model sözlüğü ve gerçek karakter hata oranıyla ayrı doğrulanır; kayıpsız okuma sözü yok.
- Paftanın tamamını 300 DPI üretme varsayılan değildir; kaynak piksel üst limiti, küçük ROI ve kontrollü hata geçerlidir.

## PDF kaynak koordinat sözleşmesi

- Birincil `pdfplumber` koordinatı: üst-sol orijin, PDF point.
- `pypdfium2` render crop girişi: left/bottom/right/top **kenar marjları**; dönüşüm adapter'da açık.
- Kaynak PDF'nin rotation/cropbox durumu doğrulanmadan ROI render doğruluğu varsayılmaz. İlk dar kod rotasyonlu sayfayı açıkça reddedebilir.
- OCR kutuları `pixel->pdf_top_left_pt` ölçeğiyle taşınır; geometrik fiziksel metreye dönüşüm yalnız doğrulanmış kalibrasyonla yapılır.
- Kaynak `SHA-256 + page_index + four-point polygon + method + model/version` izlenebilirliği zorunludur.

## Mevzuat OCR — ayrı offline hazırlık

Yönetmelik belgeleri kullanıcı tarafından açıkça seçilen bir **yerel ETL** işlemiyle (`pdfplumber native text + table parsing -> gerektiğinde pypdfium2 + RapidOCR CPU`) hazırlanır. AST/madde/fıkra/bent ve FTS5/vector indeksleri bu safhada üretilir, normal pafta analizine OCR hazırlama maliyeti bindirilmez. Özgün resmî kaynak dosyaları public repoya konulmaz.

## Test ve kabul durumu

| Kontrol | Durum |
| --- | --- |
| PDF okuma ve source modelleri | Kod başlangıcı; sentetik yerel test kontrolü gerektirir |
| ROI raster render 8 milyon piksel sınırı | Kod başlangıcı; rotation/cropbox kapsamı dar |
| RapidOCR gerçek model inference | ÇALIŞTIRILMADI |
| Türkçe/simgeler ve yönlü metin CER/IoU | ÇALIŞTIRILMADI |
| Windows 4070 8GB, i7, 32GB ve offline | ÇALIŞTIRILMADI |
| Kapalı kaynak yeniden dağıtım SBOM | HOLD |

Kaynaklar: [RapidOCR kurulum](https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/install/) · [RapidOCR sonuçları](https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/usage/) · [PDF render API](https://pypdfium2.readthedocs.io/en/stable/python_api.html).
