# İşlem 023 — A0/A1 PDF Karo OCR, Kaynak Koordinatı ve Belge Yerleşim Adayları

- **Tarih:** 2026-10-16
- **Durum:** UYGULANDI / KAPATILDI — A0/A1 açık istekli karo OCR, kaynak PDF quad/doğrulama, overlap dedup, layout/antet konum adayları ve pipeline/CLI manifesti geliştirildi. Son Linux sentetik CI 345 PASS/1 Windows'a özel SKIP; Windows 346 PASS. Gerçek A0 OCR model doğruluğu, bellek ve hukukî kabul HOLD.
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

## 3. GitHub'a gerçekten uygulanan modüller ve yazım zinciri

**İlk GitHub yazımı:** Bu dosyanın açıldığı `ddef71441115ac6f6b924bdac5cc9f05c02dba85` commit'i. Bütün kod, test, CI ve diğer dokümanlar **bundan sonra** eklendi. İşlem 001–022 geçmiş kayıtları yeniden yazılmadı.

| Kaynak | Gerçek iş | Başlıca commitler |
| --- | --- | --- |
| `src/mimarllm/ocr/tiles.py` | `TiledOcrRequest`, gerçek PDF SHA/page/rotation/CropBox ve tile/pixel/token budget'lı kaynak ROI planı; pypdfium2 render; injected yerel CPU OCR; quad bounds/NaN ve source kimlik kapısı, normalize metin+IoU≥0.50 overlap dedup | `43586e03`, `c126156e` |
| `src/mimarllm/ocr/layout.py` | PDF page top-left point konumuna bağlı sağ-alt antet olabilecek text cluster, üst/alt margin yazı kümeleri; kesin semantik yok | `307122fc` |
| `src/mimarllm/importers/pdf_ir.py` | `tiled_ocr` explicit input, OCR token→`DrawingIR` `OCR_CANDIDATE`/`SourceReference` PDF quad ve her batch'ın tile metadata; native vector/ROI yolu korunur | `74eff025` |
| `src/mimarllm/pipeline.py` | `PipelineConfig.tiled_ocr`, kümülatif tile/pixel/token budget, PDF'de explicit OCR, DXF ret; `PipelineManifest` tile/text/dedup sayıları ve source-located layout adayları | `c8187381`, `a30359ca`, `fbb3fa3b` |
| `src/mimarllm/cli.py` | `mimarllm analyze --config tiled.json` için yalnız opt-in kurulu `RapidCpuOcr`; varsayılan OCR başlatılmaz | `2fbecf85` |
| `src/mimarllm/ocr/tiles.py` ve `layout.py` | `REVIEW_REQUIRED` immutable Literal; output tile SHA/page tutarlılığı; karo listesi **oluşturulmadan** grid count matematiksel preflight | `87b99ce7`, `32db9d7c`, `921b0b47` |
| `tests/test_tiled_ocr.py` | A0 benzeri fiziksel sayfa ölçülü sentetik PDF tile planı; 4 tile'ın fake OCR üzerinden PDF pixel↔point quad dönüşümü/dedup; duplicate-different-position koruma; malformed OCR/page, source hash, yanlış budget ve antet/manifest/HUKUKI_HOLD; allocation-before-limit ve reviewer status forgery testleri | `0f677cef`, `e762ac1e`, `eb8535f3`, `16ead828` |
| `.github/workflows/core-contracts.yml` | `tests/test_tiled_ocr.py` Ubuntu/Windows synthetic CI tam regresyona dahil | `46745a22` |
| `docs/specs/tiled-ocr-v0.1.md` | Gerçek JSON/Python kullanım, kaynak koordinat/overlap/bütçe davranışı, rotasyon/CropBox ve test/kabul sınırları | `a609c3bc` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F04/F28 kısmi mevcut kod, F03 kısmi korunur; K-191–K-198; sonraki 024 RAG terminoloji | `4d24c952`, `95d67d56`, `84e68d9b`, `97cdfa4e` |

## 4. Gerçek CI sonuçları ve düzeltme geçmişi

- İlk genişletilmiş [GitHub Actions 38829423023](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38829423023): Ubuntu **340 PASS / 1 FAIL / 1 SKIP**, Windows **341 PASS / 1 FAIL**. A0 karo kaynak ölçüsü testinde kayan nokta için mutlak `<=384` karşılaştırma kullanılmıştı; test toleranslı `384+1e-6` olarak düzeltildi (işleme kaynak koordinat değiştirilmedi).
- [GitHub Actions 38829518906](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38829518906): Ubuntu **341 PASS / 1 SKIP**, Windows **342 PASS**. Source output güvenlik kontrolleri ve 3 ek test eklendi; sonraki sentetik koşu Ubuntu **344 PASS / 1 SKIP**, Windows **345 PASS** (GitHub Actions 38829765049).
- Karo grid preflight (`max_tiles` denetlenmeden Python list allocation yok) testi ilk fixture'da 32 pt karo için geçersiz varsayılan 32 pt overlap kullandığından güvenli Pydantic doğrulamasında fail verdi (CI 38830031004); doğrulamanın beklenen karo-grid katmanına erişmesi için test girdisinde `overlap_pt=0` olarak düzeltildi. Nondefault CropBox'ı test ettiğini iddia eden aslında yalnız default CropBox kullanan test de açık biçimde yeniden adlandırıldı.
- **Son kaynak commit `16ead828dfaec101742f21c6bb4025b53ec86d6c`:** [GitHub Actions **38830118073**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38830118073) tam regresyonu iki platformda başarılı:
  - **Ubuntu Python 3.11: 345 PASS, 0 FAIL, 1 SKIP, 1 upstream Starlette warning — 7,44 saniye.**
  - **GitHub-hosted Windows Python 3.11: 346 PASS, 0 FAIL, 1 upstream Starlette warning — 20,37 saniye.**
  - Ubuntu SKIP, önceki Windows onedir snapshot/manifest testinin Windows dışında geçerli olmamasından kaynaklanır. Her iki job'un gerçek logları ayrı okundu.

**Gerçekte çalıştırılan:** Sentetik ReportLab A0 benzeri **sayfa boyutunda karo planı** oluşturma (tüm A0 sayfasında gerçek OCR inference/bitmap tarama DEĞİL), küçük seçilmiş PDF ROI karolarında PDFium render + **deterministik fake OCR okuyucusunun** kaynak dörtgeni + DrawingIR, yerel pipeline manifesti, birleşik önceki DXF/PDF/rules/dashboard/packaging/repair sentetik testleri.

## 5. F03/F04/F28 durumu ve gerçek kabul

**F28 KISMI / MEVCUT_KOD:** Kaynak SHA/page/quad doğrulamalı tile planning, overlap dedup, güvenlik bütçesi, mevcut yerel RapidOCR CPU reader injection ve DrawingIR/CLI JSON manifest sözleşmesi kodlandı. **F04 KISMI:** Başlıktaki metni sağ-alt konum cluster olarak inceleme adayı gösterebilir; semantik antet/tablo/kot/mahal sınıfı veya çizim ölçeği doğrulanmaz. **F03 KISMI:** Native PDF page/ROI/quad kodu korunmuştur, PDF crop/rotasyon kaynak doğruluğu özel durumları sınırlıdır.

**Açık kabul:** F28 gerçek taranmış A0/A1 pdf dosyalarında RapidOCR ağırlığı ile CER/WER, annotation bbox IoU, peak RSS/p50/p95, işletim sistemi/pypdfium2 büyük rotasyon/CropBox varyantları ve gerçek hedef Windows/Edge kullanıcı görsel denetimi. Yerel OCR modelinin kurulu bulunmaması explicit ret; bu sentetik CI RapidOCR modeli yüklemedi ve Windows gerçek air-gapped exe çalıştırmadı.

**Değişmeyen güven:** OCR metinleri `review_required` ve `OCR_CANDIDATE`, geometrik oda/net alan/eğitim jüri/kanun hükümleri değildir. `UnitCalibration.CONFIRMED` için gerçek kaynak segment ve kullanıcı beyanı gereklidir. F08–F12 `HUKUKI_HOLD`; `RuleEngine.REGULATORY=INSUFFICIENT_EVIDENCE`. Kaynak dosyalarına, önceki DrawingIR CAD handle'larına ve asıl CAD geometrisine müdahale edilmedi.

**Sıradaki işlem 024:** Kullanıcının yol haritasına göre Türkçe mimarî jargon/FTS5 eş anlam sorgu genişletmesi ve yerel güvenli indeks/cache; **`docs/islem_024.md` henüz yok**. İlk GitHub yazımı yine yeni işlem dosyası olmalıdır.
