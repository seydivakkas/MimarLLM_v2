# ADR-002 — Hibrit PDF Motoru ve Yeniden Dağıtım Kararı

- **Karar tarihi:** 2026-10-12
- **Durum:** KABUL EDİLDİ — teknoloji mimarisi; bağımlılık zinciri ve gerçek Windows paket lisansı nihai kabul bekliyor.
- **İşlem kaydı:** [İşlem 005](../islem_005.md)
- **Hedef:** Tek Windows PC, 32 GB RAM, 8 GB VRAM, sıfır harici AI API; ileride kapalı kaynak dağıtımı mümkün kılan izinli bileşenler.

## Karar

1. **Vektör çizim/metin/tablo:** `pdfplumber` (MIT) ve onun PDF çözümleme alt bağımlılıkları.
2. **Raster render:** `pypdfium2` (Apache-2.0 / BSD-3-Clause; PDFium ve build içi üçüncü taraf lisansları ayrıca).
3. **Yerel OCR:** güncel `rapidocr` + `onnxruntime`, CPUExecutionProvider, bağımsız kurulabilir ve native PDF analizi için opsiyonel.
4. Tek Python paket adı: `src/mimarllm/`. Ayrı servisler/agent akışı yok.
5. Girdi belgesindeki gerçek kaynak sayfa, koordinat ve hash izlenebilir olmalı. OCR yalnız görüntü bölgelerindeki metin **adayıdır**.

**Yalnız bu üç motor kullanılacak.** Önceki alternatif OCR/PDF motorları, kaynak kodu, dependency dosyası ve aktif mimari karar listesinden çıkarılmıştır.

## Veri akışı

```text
PDF input -> pdfplumber page/chars/lines/curves/rects -> native source candidates
        \-> pypdfium2 ROI render (bounded pixels) -> RapidOCR CPU -> polygon candidates
                   |                                      |
                   +--------> source coordinate mapping <-+
                                       |
                                    DrawingIR
                                       |
                               geometry/rules/evidence
```

PDF sayfasında metin var diye sayfanın geri kalanındaki kesik çizgi/metin alanlarının okunmuş olduğu varsayılmaz. PDF `page.extract_words` veya `chars` gerçek metin çıkarır; SHX/glyph outline vakaları raster ROI OCR gerektirebilir. İkisinde de `(x0, top, x1, bottom)` **sayfa üst-sol başlangıçlı point** koordinatları normalize edilir. `pypdfium2` render için DPI/72 uygulanır; sayfa dönüş/crop etkileşimi test ve source-transform ile ele alınır. Her OCR kutusu orijinal PDF koordinatına döner.

## Lisans ve doğruluk kapıları

| Bileşen | Üst seviye lisans | Durum |
| --- | --- | --- |
| pdfplumber | MIT | Ana paket doğrulandı; alt bağımlılık kilit dosyası daha oluşturulacak |
| pypdfium2 | Apache-2.0 / BSD-3-Clause | PDFium, bundled license ve wheel build bildirimleri ayrıca doğrulanacak |
| rapidocr | Apache-2.0 | Seçilen motor ve taşınan ONNX model dosyası ayrıca incelenecek |
| onnxruntime | MIT | CPU wheel alt bileşenleri ve dağıtım notları ayrıca incelenecek |
| Pillow / pdfminer.six | Dağıtım sürümüne göre izinli lisanslar | Nihai SBOM gerektirir |

**Hukukî sonuç:** Bu seçim copyleft riskini azaltır; sıfır hukukî yükümlülük veya tüm transitif bağımlılıklarda GPL/AGPL bulunmadığı garantisi değildir. Kapalı kaynak müşteriye paketlemeden önce gerçek Windows wheel/SDK/SBOM ve lisans dosyaları doğrulanır.

## Performans ve veri güvenilirliği

- Sayfa render'ı kör 300 DPI tam pafta değil; ROI öncelikli ve piksel sınırı zorunlu.
- Metin yönü, PDF char matrix ve OCR polygon'u aynı koordinat sisteminde dönüştürülür.
- OCR kutusu dört nokta olduğundan dikdörtgen alanın sınırları ile içerik doğruluğu karıştırılmaz.
- CPU OCR, CUDA VRAM kullanmamalıdır; 8 GB VLM VRAM'i ayrı tutulur, CPU RAM sınırsız değildir.
- İlk real-system testleri: Windows paketleme, matris/rotation, multi-column, SHX, PDF page box, tablo hücre kökeni, büyük format/OOM.
- Mevzuat PDF'leri **ayrı yerel ETL** ile indekslenir; runtime çevrim dışıdır.

## Önceki kayıtların korunması

`islem_001`–`islem_004` tamamlanmış işlem numaraları olarak kalır; geçmişte önerilen fakat artık kullanılmayan teknoloji kararları bu ADR ile geçersizdir. Git commit geçmişi yeniden yazılmadığı için eski sürümler geçmişten erişilebilir.

## Kaynaklar

- [pdfplumber](https://github.com/jsvine/pdfplumber)
- [pypdfium2](https://github.com/pypdfium2-team/pypdfium2)
- [RapidOCR](https://github.com/RapidAI/RapidOCR)
- [RapidOCR kurulum](https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/install/)
