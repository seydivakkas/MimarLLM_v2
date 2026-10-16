# İşlem 023 — A0/A1 PDF Karo OCR, Kaynak Koordinatı ve Belge Yerleşim Adayları

- **Tarih:** 2026-10-16
- **Durum:** ÖN KAYIT — bu işlem kapsamındaki **ilk GitHub yazımı**; sonraki kod/doküman değişikliklerinden önce oluşturuldu.
- **Ön koşul:** İşlem 009 PDF native/ROI OCR→DrawingIR; İşlem 018 pipeline/CLI; İşlem 019 localhost UI; İşlem 022 kaynak koruyan kirli CAD önerileri. Önceki `docs/islem_001.md`–`docs/islem_022.md` kayıtları değiştirilmeyecek.
- **Kesin güven sınırı:** OCR metinleri/geometrileri `OCR_CANDIDATE` ve `review_required`; hiçbir karo OCR sonucu fiziksel ölçek, oda, kapı, yangın tahliyesi, mevzuat uygunluğu veya resmî kaynak doğrulaması sağlamaz. RAG ve RuleEngine hukukî HOLD kilidi değişmez.

## 1. Uygulama kapsamı

1. `src/mimarllm/ocr/tiles.py`: kullanıcıca seçilmiş özgün PDF-point üst-sol ROI için tam sayfayı büyük bitmap olarak açmadan pypdfium2 bounded karo planı; DPI, halo/overlap, max tile pixels, toplam sayfa/karo/piksel/tokencount ve kaynak SHA; kayan ve yinelenen koordinatlarda deterministik karolar. OCR okuyucu injection gereklidir, varsayılan hiç OCR yok.
2. `tiles.py`: `RenderedRegion` gerçek `pixel_origin_pdf_points` ile `RapidCpuOcr` CPU `TextCandidate` dörtgeninin orijinal PDF page koordinatına geri bağlanmasını doğrula; sayfa/ROI dışı, değişmiş PDF SHA, yanlış OCR yöntemi ve nonfinite/boş polygon fail-closed. Tile overlap metinlerinin kontrollü normalize+IoU dedup, confidence/çakışma gerekçeleri ve kaynak tile indeks/ROI kanıtı.
3. `src/mimarllm/ocr/layout.py`: native/OCR adayları ve sayfa boyutları üzerinden sol/sağ/üst/alt marj ve sağ-alt **antet konum adayı**, konum/type/quad kaynağı; OCR sonucu antet içeriğini resmî yapı ruhsatı/yapı kullanımı gibi kesin semantiğe yükseltme yok.
4. `src/mimarllm/importers/pdf_ir.py`, `src/mimarllm/pipeline.py`, `src/mimarllm/cli.py`: explicit JSON `tiled_ocr` config ile seçilmiş PDF sayfası/ROI; yerel RapidOCR CPU dışında OCR engine yok. Karo adaylarının `DrawingIR` içinde `OCR_CANDIDATE`, `SourceReference.document_sha256/page_index/source_polygon` ve benzersiz kanıt kimliği. Native PDF vektörleri ve önceki ROI OCR geriye uyumlu kalmalı.
5. `tests/test_tiled_ocr.py`, gerekirse mevcut test dosyaları: ReportLab sentetik büyük PDF sayfaları + enjekte edilmiş deterministik sahte OCR CPU reader; sınır/bellek/rotasyon/ROI, overlap dedup ve SHA, sahte quad, orijinal sayfa dönüşümü, multi-page izolasyon, güvenli antet adayı, CLI/Pipeline hukukî kilit. CI Ubuntu/Windows.
6. `.github/workflows/core-contracts.yml`, teknik şartname `docs/specs/tiled-ocr-v0.1.md`, README/özellik envanteri/yol haritası/karar defteri. Yeni testler ancak gerçek loglarla kabul edilecek.

## 2. Kabul ve açık riskler

- `pypdfium2.render_region` mevcut sürümde döndürülmüş PDF sayfaları için full page fallback kullanır; A0/A1 dönmüş sayfada bu bellek bütçesini aşarsa **reddedilecek**, orijinal koordinatları bozacak sahte dönme dönüşümü yapılmayacak.
- Nondefault CropBox hâlâ fail-closed; MediaBox/CropBox ve OCR bbox geometrisi kullanıcıya yanlış konumda gösterilmeyecek.
- A0/A1 “karo sayfası kodu var” demek gerçek A0 taranmış mimari PDF üzerinde OCR kalitesi, peak RSS, latans, CER/WER veya Türkçe OCR doğruluğu ölçüldü demek değildir.
- Native selectable text mevcut diye PDF sayfasındaki eksik SHX/raster bölgelere OCR otomatik engellenmeyecek; ayrıca native tek glyph ile OCR aynı metinmi bilinmiyorsa onaylı sonuç üretilmeyecek.
- Model dosyası internetten otomatik indirilmez, RapidOCR CPU kurulu değilse açık ret. PyInstaller gerçek Windows offline binary, büyük antet OCR ve hukukî resmiyet kabulü açık kalır.

## 3. Son iş kaydı

Uygulanan gerçek dosya ve commit SHA, sentetik Linux/Windows CI run/test PASS/FAIL, düzeltme geçmişi, ertelenen gerçek kabul ve F03/F04/F28 kapsamı **aynı dosyanın son GitHub yazımı** olarak eklenecek.
