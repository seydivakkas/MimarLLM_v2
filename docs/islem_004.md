# İşlem 004 — RapidOCR CPU + PyMuPDF vektör öncelikli OCR mimarisi

- **Tarih:** 2026-10-12
- **Repo:** `seydivakkas/MimarLLM_v2` (public)
- **Durum:** PLANLANDI — değişikliklere başlamadan önce işlem kaydı oluşturuldu.
- **İstek:** Unlimited-OCR'ın 8 GB VRAM/Windows riskleri nedeniyle birincil OCR motorunu RapidOCR (ONNX Runtime CPU) ile değiştirmek, PDF'lerde PyMuPDF vektör/gerçek metin çıkarımını öne almak, mimari paftaların eğik ve dikey etiketlerini ve özgün mevzuat belge konumlarını koruyan sade OCR dosya mimarisi tanımlamak.
- **Geliştirme türü:** Teknik karar ve mimari/dokümantasyon güncellemesi. Çalışan model, analiz kodu ve benchmark bu işlemde yapılmış sayılamaz.

## 1. Yeni OCR stratejisi

1. DXF'de metin: önce CAD TEXT/MTEXT/DIMENSION/ATTRIB ve blok dönüşümleri, kaynak handle, açı, birim ve koordinatlar.
2. PDF'de metin: önce PyMuPDF `rawdict`/`dict` metin, char/line/span, yazı yönü (`dir`) ve PDF koordinatları. Rotated quad, `recover_quad` veya satır quad ile elde edilir.
3. Dijital PDF içinde metin bulunması yeterli değil: eksik/bozuk Unicode, SHX çizgiye dönüşmüş metin, vektör outlined yazılar, kısmi raster bölgeler ve yanlış okuma sırası için kalite değerlendirmesi gerekir.
4. Sadece gerekli sayfa/bölge ROI'sinde RapidOCR'nin CPUExecutionProvider sürümü çalışır. Dört noktalı poligon + güven skoru + model kimliği döner, transform zinciri saklanır.
5. Açı sınıflandırıcı varsayılan olarak yalnız 0°/180° ayrımı yapar; 90°/270° veya 45° için crop rotasyonu/çoklu yön stratejisi, çıktıyı ters dönüşümle sayfa koordinatına geri alma ve benchmark gerekir.
6. Türkçe ve `Ø ± ° ²` gibi simgeler otomatik kusursuz varsayılmaz; sürüm/karakter sözlüğü/yönerge ve gerçek pafta sentetik doğruluğu ölçülür.
7. Mevzuat PDF'lerinde indeks oluşturma işini, analiz anından **ayrı yerel ETL** aşamasında çalıştır. Önce PyMuPDF; tablolar için pdfplumber veya CPU-uyumlu Docling karşılaştırması; taranmış bölüm için OCR. PDF bbox/tablo hücre konumu / LegalAST bağını her zaman koru.
8. RapidOCR CPU kullandığında CUDA VRAM ayırmaz, fakat sistem RAM/CPU tüketimi vardır ve bunu ölçmek gerekir. GPU VLM süreciyle bellekte yarışmaz fakat CPU/bellek kaynakları ve toplam gecikme yine yönetilir.
9. Unlimited-OCR kaldırılmayacak; normal çalışma yolu değil, isteğe bağlı deneysel ve cihazda doğrulanması gereken yedek inceleme seçeneği olarak tutulacak. Varsayılan runtime/download bağımlılığına eklenmez.
10. `rapidocr_onnxruntime` eski ad; bakım politikası nedeniyle yeni kullanım: **`pip install rapidocr onnxruntime`**. Kaynak lisansları, model versiyonları ve Windows paketlemesi ayrıca denetlenir.

## 2. Dizin kararı

Önceki planla uyumlu Python paket ismi `src/mimarllm/` korunacak; `src/mimar/` adıyla ikinci paralel paket açılmayacak.

```text
src/mimarllm/
  importers/
    dxf.py
    pdf.py
    image.py
  ocr/
    text_extractor.py    # PDF/DXF native -> kalite değerlendirmesi -> ROI OCR
    rapid_engine.py      # CPU RapidOCR arabirimi, sürüm/çıktı normalizasyonu
    box_utils.py         # Quad/polygon, rotasyon ve koordinat dönüşümleri
  regulations/
    extraction.py        # Offline mevzuat ETL, kaynak belge konumu
    parser.py            # Madde/fıkra/bent/tablo AST
    ...
  vision/
    vlm.py               # VLM ayrı, zorunlu OCR bileşeni değil
```

Yapı **taslak** olarak kaydedilecektir; boş klasörler, işlevi varmış izlenimi veren kod şablonları ve bulut servisleri oluşturulmaz.

## 3. Teknik risk ve düzeltmeler

- `get_text()` `%100` garantili veya `0ms` değildir. SHX ve Unicode `U+FFFD` vakaları kalite kapısı gerektirir.
- RapidOCR OCR `cls` varsayılan yön etiketleri `0/180`; 90/270/yatay dışı metinlerin otomatik tam düzeltilmesi iddia edilmez.
- 4 köşe poligonu geometrik tespit alanıdır, **tanınan metnin mutlak doğruluğu** değildir.
- Raster OCR için `pixel -> page_point` dönüşümüne crop/rotate/scale ve gerektiğinde `page_point -> DrawingIR` kalibrasyonu dahildir.
- Mevzuatta satır numaraları türetilmiş; asıl kaynak kimliği `document_sha256 + PDF page + polygon + article/paragraph/item/cell`.
- Docling yerelde çalışabilir, ancak tablo anlama için ek model/bellek maliyeti var; varsayılan bağımlılık seçimi benchmark ile yapılır.
- Yerel paket runtime hiçbir indirme/remote AI/telemetri gerektirmeyecek; modellerin önceden elde edilmesi ve hash doğrulaması gerekir.

## 4. Bu işlemde değiştirilecek belgeler

- `docs/ocr-ve-bellek.md`: aktif stratejiyi RapidOCR + PyMuPDF olarak öne al; eski Unlimited-OCR bölümlerini tarihsel/deneysel diye etiketle.
- `docs/sistem-mimarisi.md`: PDF metin kalite kapısı ve hibrit ROI OCR rotasyon/quad işlemleri.
- `docs/mevzuat-rag.md`: offline ETL, belge sayfa/satır/tablo kökeni ve yasal kanıt koruma.
- `docs/modul-plani.md`, `docs/teknik-gereksinimler.md`, `docs/kararlar.md`, `docs/kapsam.md`, `README.md`: kapsam ve kabul sözleşmeleri, tercihlerin güncellenmesi.
- `docs/ocr-mimari-pafta.md`: gerçek teknik sözleşme, önerilen dosya ağacı, format/rotasyon test matrisi, açık kaynak linkleri.

## 5. Kabul ve uygulanmayan işler

- Belgeler GitHub'da oluşturulmuş, birbirine bağlanmış ve işlem kaydı sonuçlandırılmış olacak.
- Raporda `PyMuPDF+RapidOCR` desteği **çalışıyor** gibi gösterilmeyecek. Python kodu, Windows testleri, gerçek VRAM/latency ölçümü ve Türkçe karakter doğruluğu ayrı işlem numarasıyla yapılacak.

## 6. Uygulama kaydı

GitHub işlemleri tamamlandıkça gerçek commit bilgileri buraya yazılacak.
