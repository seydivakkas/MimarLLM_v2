# MimarLLM V2 — Yerel OCR ve 8 GB VRAM Çalışma Tasarımı v0.1

- **Bağlı işlem:** [islem_003.md](islem_003.md)
- **Durum:** TASARIM; Baidu Unlimited-OCR hedef donanımda **test edilmedi**.
- **Hedef:** Windows, i7 14. nesil, 32 GB RAM, NVIDIA RTX 4070 8 GB VRAM, offline ve sıfır bulut AI API.

## 1. OCR neden iki farklı yerde kullanılacak?

| Alan | Girdi | OCR amacı | Her bulgunun kaynak izi |
| --- | --- | --- | --- |
| Mimari pafta | DXF'den render, dijital/taranmış PDF, PNG/JPEG | Antet, mahal, aks, kot, ölçü, açıklama, lejant ve tablo adayları | Sayfa/layout, görsel kırpım, bbox/çokgen, tanıma yöntemi |
| Mevzuat | Özgün taranmış PDF / resmî yayım | Madde, fıkra, bent, tablo/ek/başlık ayrıştırmaya yardımcı metin | Kaynak SHA-256, özgün PDF sayfası, bbox, satır/hücre ve doğrulama |

Mühendislik sınırı: OCR geometrik ölçü veya mevzuat uygunluk sonucu **tek başına vermez**. OCR'dan çıkan “90” ve “0.90” gibi değerler çizimde ölçü/birim ile eşleştirilmeden kural hesabına sokulmaz.

## 2. Değerlendirilecek modeller

### A. Baidu Unlimited-OCR — gelişmiş OCR aday motoru

Resmî kaynaklar:
- [GitHub — baidu/Unlimited-OCR](https://github.com/baidu/Unlimited-OCR)
- [Hugging Face — baidu/Unlimited-OCR](https://huggingface.co/baidu/Unlimited-OCR)

2026 Ekim taramasına göre 3B parametre sınıfı, BF16 bir model, MIT model lisansı. Resmî örnek, `trust_remote_code=True` ile Transformers/CUDA kullanımı ve PDF'den görüntüye dönüştürme + çok sayfalı infer çağrısını gösteriyor. Bunlar **8 GB VRAM'de çalışan Windows benchmark sonucu değildir**.

**Risk:** BF16 ağırlıklar, görüntü kodlayıcı, KV cache, PyTorch CUDA context, fragmentation ve işletim sistemi GPU kullanımı birlikte VRAM'i aşabilir. Uzun çok sayfa bağlamı özellikle risklidir. Nicemlenmiş üçüncü taraf GGUF varyantları bulunabilir; fakat gerekli vision projector'ın çalışması, Windows llama.cpp desteği, lisans ve ölçüm doğrulanmadan uyumluluk PASS verilmez.

### B. Hafif yerel OCR — öncelikli fallback

- Dijital PDF'lerde önce PyMuPDF benzeri **native text/char bbox çıkarımı**. OCR istemiyoruz.
- Taranmış sayfa ve kısa pafta yazıları için düşük bellekli yerel OCR motoru; örneğin PaddleOCR PP-OCRv5 CPU/GPU adayı.
- Yoğun tablo ve karmaşık sayfa yerleşimi için PaddleOCR PP-StructureV3 veya Unlimited-OCR karşılaştırma adayı.
- Motorların Windows, Türkçe, sayfa kutusu, tablo hücresi ve lisans uygunluğu ayrıca kontrol edilir.

[PP-StructureV3 resmî dokümanı](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-StructureV3/PP-StructureV3.en.md)

**Seçim henüz yapılmadı:** “Unlimited-OCR kesin ana OCR motorudur” ya da “PP-OCR daha iyi” kararı benchmark olmadan verilmeyecek. OCR interface motor-bağımsız olacak.

## 3. Phase-Locked Execution (tek ağır GPU işi)

```text
  Yeni OCR işi
      |
  Kaynak -> PDF native text var mı? -- EVET -> metin + bbox (CPU)
      |
      HAYIR
      v
  Görüntü ROI / sayfa dilimleme (CPU)
      |
  Hafif OCR (CPU ilk seçenek) -> güvenilir mi?
      |                             |
      | EVET -> kaydet               HAYIR
      v                             |
     JSON                   [GPU KİLİDİ AL]
                                  |
                         OCR subprocess başlat
                         (Unlimited-OCR aday)
                                  |
                         tek sayfa / sınırlı ROI
                                  |
                         bbox + tablo hücresi kaydet
                                  |
                         subprocess sonlandır
                         GPU telemetrisiyle boşluğu ölç
                                  |
                         [GPU KİLİDİNİ BIRAK]
                                  |
                         Gerekirse VLM subprocess
                                  |
                         rapor doğrulaması (CPU)
```

**Neden subprocess?** `del model`, `gc.collect()` ve `torch.cuda.empty_cache()`, süreçteki CUDA context / framework allocation'ı her zaman tamamen serbest bırakmaz. Sürecin gerçekten bitmesi ve GPU kullanımının gözlenmesi daha güvenilir bellek sınırı sağlar.

**Admission gate önerisi:** GPU modeli başlamadan önce `nvidia-smi`/NVML'den kullanılabilir bellek, önceki model süreçlerinin bitişi, GPU'da başka iş yükü ve tahmini ROI maliyeti kontrol edilir. VRAM sınırı yetersizse doğrudan CPU/OCR fallback veya `INSUFFICIENT_RESOURCES`; OS çökmesi veya sessiz veri kaybı olmaz.

**Operasyonel kararlar:**
- Eşzamanlı ağır model sayısı: **1**.
- Görüntü boyutu: basamaklı düşük çözünürlük -> ROI yükseltme; paftanın tamamını tek seferde aşırı uzun bağlamla işleme varsayılan değil.
- Çok sayfalı PDF: sayfa başına ya da küçük batch; arada checkpoint; başarısız sayfa yeniden denenebilir.
- Embeddings/rule engine: CPU; modelin GPU kullanımını öncelik sırasına göre sınırla.
- Her model için lisans, sürüm/hash, quantization, context, runtime ve kaynak ihtiyacını gösteren manifest zorunlu.
- İnternet indirmesi çalışma anında yasak; kuruluma ait model indirme ayrı ve isteğe bağlı eylem.
- `trust_remote_code=True` yükleme güvenlik riski taşıyabilir; sürüm pinleme, kod incelemesi, offline cache ve hash zorunlu.

## 4. OCR sözleşmesi (yerleşim ve konum korunarak)

```json
{
  "source_sha256": "sha256-placeholder",
  "source_type": "pdf",
  "pdf_page_index": 7,
  "printed_page_label": "5",
  "page_width_pt": 595.0,
  "page_height_pt": 842.0,
  "ocr_engine": "unlimited-ocr-candidate",
  "ocr_model_hash": "model-hash-placeholder",
  "coordinate_system": "pdf_point",
  "blocks": [
    {
      "block_id": "blk-17",
      "type": "paragraph",
      "reading_order": 17,
      "bbox": [85.0, 212.0, 510.0, 245.0],
      "line_ids": ["line-17-1", "line-17-2"],
      "text": "[örnek metin; gerçek mevzuat değildir]",
      "status": "REVIEW_REQUIRED"
    }
  ]
}
```

**Not:** Bu örnek JSON'un ölçüleri ve metinleri sentetiktir. Gerçek belge okunduğu iddia edilmez.

### OCR çıktısında zorunlu dönüşümler

- PDF koordinatları (genellikle nokta) ile render/piksel koordinatı için ayrı forward ve inverse 2D affine transform tutulur; sayfa döndürme ve cropbox dikkate alınır.
- Her OCR satırı tekil `line_id` + okuma sırası + bounding polygon içerir.
- Çok sütunlu metinler soldan-sağa kör sıralanmaz; sütun ve blok okuma sırası saklanır.
- Tablolar: `table_id,row_index,column_index,cell_bbox,raw_text,normalized_value`. Hücre birleşimleri/satır başlıkları açık tutulur.
- OCR'ın üretmiş olduğu “satır 12” belgeye resmen ait numara değildir; referans `PDF sayfa + blok/satır bbox + madde/fıkra` olur.
- Bir bulgunun OCR kaynağına tıklayınca aynı PDF hash'i ve sayfa görseli açılıp doğru alan vurgulanmalıdır; eşleşme bozulursa kaynak bağlantısı doğrulama kapısından geçemez.

## 5. Gerçek donanım benchmark planı — ölçülmedi

**Deney matrisi:** 1 sayfa metin, 1 sayfa tablo, büyük mimari pafta, 10 sayfalı karma PDF; Türkçe karakterler (İ/ı/ğ/ş), madde numaraları, küçük ölçü yazıları, döndürülmüş sayfalar ve çok sütun.

Karşılaştırma:
- native text çıkarımı
- hafif OCR CPU
- PP-StructureV3 (gerekirse)
- Unlimited-OCR BF16 (yalnız güvenli bellek sınırında)
- Unlimited-OCR nicemlenmiş sürüm (yalnız destek/kanıt varsa)

**Metrikler:** karakter hata oranı (CER), kelime hata oranı (WER), madde/fıkra eşleşme doğruluğu, tablo hücre P/R, bbox overlap/IoU, yanlış okunan teknik ölçü oranı, sayfa başına p50/p95 gecikme, GPU VRAM peak, host RAM peak, başarısız iş/OOM ve internet çıkış gözlemi.

**Kabul:** hedef Windows makinede test edilmeden `PASS` yok. 8 GB'ta Unlimited-OCR uyumsuz çıkarsa görev tamamen yerel alternatifle devam eder; bulut fallback uygulanmaz.

## 6. Güvenlik ve dağıtım

- Gerçek müşteri çizimleri ve mevzuat tam metinleri yerel `local_data/` dizininde.
- Kurulan model ağırlıkları `local_data/models/` veya OS'nin yerel cache klasörlerinde; GitHub'a commit edilmez.
- Normal çalışma sırasında uygulama, modeller veya font/CDN gibi bileşenler nedeniyle dış bağlantı başlatmamalı.
- PDF'de bilinen güvenlik riskleri ve aşırı boyut/çözünürlük saldırıları için dosya/page/pixel/tokens sınırı.
- Modelin çıktısı güvenilmeyen veri; talimat gibi yürütülmez. Çok sayfalı parse hatası bir önceki doğru sonucu sessizce değiştirmez.

**İlerideki işlem:** Windows deneyleri ve gerçek model entegrasyonu ayrı `islem_NNN` kaydıyla yapılacak; bu belge yalnız mimari karar ve test sözleşmesidir.
