# İşlem 009 — PDF native/OCR kaynaklarının DrawingIR ile bütünleştirilmesi

- Tarih: 2026-10-13
- Durum: **ÖN KAYIT** — uygulama kodundan önce oluşturuldu.
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

## Çalışma kaydı

Gerçek commit SHA, CI durumu ve bilinen açık limitler uygulama sonunda işlenecek.
