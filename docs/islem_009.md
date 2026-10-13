# İşlem 009 — PDF native/OCR kaynaklarının DrawingIR ile bütünleştirilmesi

- Tarih: 2026-10-13
- Durum: **UYGULANDI — kaynak kod ve sentetik testler; Windows model/saha ve mevzuat kabulü ayrı.** Ön kayıt ilk commit'te açıldı.
- Öncelik: F03 (PDF native vektör/provenance), F04 (RapidOCR CPU entegrasyonu — gerçek model benchmark ayrı).
- Ön koşul: islem_007 DrawingIR v0.1; islem_008 DXF parsing; teknoloji kararı ADR-002.
- Kesin motorlar: `pdfplumber` karakter/vektör, `pypdfium2` raster bölge render, `rapidocr + onnxruntime` CPU; başka PDF/OCR motoru eklenmeyecek.

## İstenen mühendislik çıktısı

1. Her PDF sayfası için `CoordinateFrame(PDF_POINT, DOWN, page_index)` yaratıp `DrawingIR` içine `SourceReference(document_sha256, page_index, source_polygon)` ve `DrawingEntity` kaydetmek.
2. Native karakterlerden metin+konum metadata'yı kaybetmeden kaynağa dönen kanıt sözleşmesi; `char.matrix` rotasyon bilgisi veya bbox, 4 köşe yalnız güvenilir hesaplanabiliyorsa gerçek quad diye etiketlenecek.
3. Native vektör çizgileri/rect/curve gerçek gözlemler; bbox'tan sahte duvar/oda/diagonal çizgi türetilmeyecek. Güvenilir geometri yoksa `REVIEW_REQUIRED`/diagnostic.
4. `pypdfium2` ROI bitmap için DPI/clip/crop ve kaynak point dönüşümünü açık tutmak; rotasyon/CropBox ekseni belirsizse **sessizce yanlış atıf üretmek yerine fail-closed**.
5. RapidOCR CPU `boxes[N,4,2]` sonuçlarını `RenderedRegion` transformu üzerinden PDF sayfa koordinatına taşımak. Native metin ile OCR sonucunu ayrık metadata tutmak, çakışan metinleri otomatik doğrulanmış saymamak.
6. ROI akışını kullanıcı seçimiyle (taranmış/eksik alan), otomatik OCR tetiklemek için güvenilir kalite kapısı olmadan kullanıcıya açık bir API olarak sunmak. Her durumda CPU ve RAM bütçesi uygulanmalı; çalışırken dış bağlantı/model indirme yok.
7. Sentetik 0/90/180/270 PDF sayfa rotasyonları, kaynak quad, ROI ters dönüşüm, multi-page hash, grafik ve OCR mocked adapter; gerçek Windows RapidOCR inference (yüklü model) ayrıca.
8. Kod/test ve gereksinim/README/feature matrisi güncellemesi; sonuç CI ve tamamlanmayan risklerle raporlanacak.

## Temel şartlar

- `pdfplumber + pypdfium2 + rapidocr` değişmez; `src/mimarllm` paket adı korunur.
- PDF point **fiziksel metre değildir**; kalibrasyon bilinmiyorsa `INSUFFICIENT_EVIDENCE` politika geçerlidir.
- Yalnız bboxes uygun olmayan diagonal glyph'lerde dönüş matrisi/rotasyon korunacak; güvenilmez true quad, kaynak kesinliği diye işaretlenmeyecek.
- Rendered bitmap koordinatı -> PDF sayfa noktası 0/90/180/270 ve CropBox için toleranslı dönüşüm kabulü olmadan genel destek PASS olmayacak.
- Model indirme/runtime telemetry bağımsız kontrol; GPU belleği gerçek cihazda ölçülmeden '0 MB VRAM' iddiası yok.
- `DrawingIR.findings` bu işlemde boş; mevzuat ya da sahte geometrik PASS yok.

## Gerçek uygulama ve commit kayıtları

**Ön-kayıt ilk commit:** `b89c2c81b4b7e4502237192fd2745bfecf70ebdb` — diğer kaynak değişikliklerinden **önce** `docs/islem_009.md` oluşturuldu.

| Dosya | Gerçek geliştirilen özellik | Örnek commit |
| --- | --- | --- |
| `src/mimarllm/importers/pdf.py` | 0/90/180/270 standart /Rotate için koordinatlı ROI; 90° crop uyuşmazlığına bounded full-page çözümü; subpixel pixel-origin metadata; CropBox fail-closed | `b179f036`, `cbefd89b`, `c57a4611` |
| `src/mimarllm/importers/pdf_ir.py` | pdfplumber glyph/line/rect/Bezier gözlemlerini DrawingIR ve kaynağa bağlı text candidate; kullanıcı seçili ROI'de injected RapidOCR CPU four-point quad | `caba5fb7` |
| `tests/test_pdf_ir.py` | Çok sayfa/provenance, gerçek diagonal line, yaklaşık eğri, mock OCR, wrong page/source, OCR polygon ROI, 4 PDF /Rotate, malformed CropBox, memory cap, subpixel origin | `557221a7`, `d1a0b711`, `475ee2ec` |
| `.github/workflows/core-contracts.yml` | PDF OCR entegre testinin CI'a eklenmesi; sonrasında ubuntu+Windows sentetik matrix | `ef382d6d`, `b1f72177` |
| `docs/specs/pdf-ocr-drawingir-v0.1.md` | Çizim kaynak sözleşmesi; rotasyon, bbox gerçeği, veri güvenlik/sınır tablosu | `fdb85702` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F03/F04 gerçek durum + sonraki iş + kararlar | `9c6d4433`, `d93ce873`, `85394e5e`, `7a40dbfd` |

### GitHub Actions testleri ve gerçek hata analizi

- İlk tümleştirme CI [38342025131](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38342025131): **84 PASS / 1 FAIL**. Gerçek hata: /Rotate=90 sayfasında PDFium doğrudan ROI crop ile tam sayfa üzerinde aynı bölge uyuşmuyordu. Çözüm: rotasyonlu standart sayfada yalnız bellek bütçesine sığan tam sayfa render + Pillow ROI crop; bellek limitini aşan büyük sayfa açık hata.
- ROI/CropBox negatif testindeki [38342268760](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38342268760) çalışması: **87 PASS / 1 FAIL**. Bu hatanın nedeni üretim kodu değil, `reportlab.setCropBox` fonksiyonuna dört koordinat yerine iki değer verilerek geçersiz PDF fixture üretilmesiydi. Fixture düzeltildi.
- Sonraki bütünleşik Ubuntu test [38342398039](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38342398039): **88 PASS / 0 FAIL**, gerçek sentetik PDF, bbox, 4 sayfa rotasyonu, injected mock OCR ve DrawingIR testleri.
- Güncel son commit'e yönelik [Linux + Windows matrix 38342517550](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38342517550): sonucu ayrıca doğrulanacak. GitHub-hosted Windows runner **kullanıcının RTX 4070/i7/32GB makinesi değildir**.

### Biten / bitmeyen kabul kapıları

**Kodlandı:** Native karakter matrisi ve bbox, gerçek line/rect, Bezier flattening diagnostic, kaynak hash ve sayfa, 4 noktalı OCR candidate, render pixel↔PDF point dönüşümü, standart /Rotate, ROI bazında kaynak doğrulama.

**HOLD:** Gerçek RapidOCR model inference, Türkçe/Ö/Ø/±/°/² karakter CER, font outline/SHX için otomatik ROI kalite kontrolü, tek PDF içinde değişik CropBox, rotasyonlu dev pafta tiled-render, kırpılmış PDF sayfalarda source mapping, gerçek Windows/AutoCAD/Revit/ArchiCAD paftalarıyla kabul. Başka PDF/OCR motoru eklenmedi.

**Anlam sınırı:** Native glyph bounding rectangle, gerçek eğik glyph poligonu değildir. OCR quad, tespit poligonudur; fiziksel ölçüm/duvar/kapı/mevzuat `PASS` değildir. `DrawingIR.findings` ve fiziksel ölçümler boş, kalibrasyon `UNKNOWN`.

**Sonraki işlem `docs/islem_010.md`:** Shapely ile segment noding, snap toleransı, gerçek oda iç poligonu, duvar sınır adayları ve geometrik belirsizlik; doğrulanmamış fiziksel alan üretimi yok.
