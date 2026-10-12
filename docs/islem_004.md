> **Güncelleme — 2026-10-12, İşlem 005:** Bu dosya önceki mühendislik tartışmasının tarihsel kaydıdır. Güncel, tek PDF/OCR teknoloji kararı: **pdfplumber + pypdfium2 + RapidOCR/ONNX Runtime CPU**. Önceki motor alternatifleri kullanımdan kaldırıldı. Asıl karar [ADR-002](adr/ADR-002-PDF-Engine-License.md). Git geçmişi yeniden yazılmadı.

# İşlem 004 — Native PDF Metni ve CPU OCR Mimari Kararı (tarihsel kayıt)
- **Tarih:** 2026-10-12
- **Repo:** `seydivakkas/MimarLLM_v2` (public)
- **Durum:** UYGULANDI (yalnızca mimari ve dokümantasyon; uygulama kodu/benchmark yok).
- **İstek (tarihsel):** Yerel ve hafif OCR stratejisinin değerlendirilmesi. Tek motor kararı sonradan [islem_005](islem_005.md) ile kesinleşti.
- **Geliştirme türü:** Teknik karar ve mimari/dokümantasyon güncellemesi. Çalışan model, analiz kodu ve benchmark bu işlemde yapılmış sayılamaz.
## 1. Yeni OCR stratejisi
1. DXF'de metin: önce CAD TEXT/MTEXT/DIMENSION/ATTRIB ve blok dönüşümleri, kaynak handle, açı, birim ve koordinatlar.
2. PDF'nin metni ve döndürülmüş karakterleri doğrudan okuma fikri benimsendi; nihai okuyucu `pdfplumber` olarak seçildi.
3. Dijital PDF içinde metin bulunması yeterli değil: eksik/bozuk Unicode, SHX çizgiye dönüşmüş metin, vektör outlined yazılar, kısmi raster bölgeler ve yanlış okuma sırası için kalite değerlendirmesi gerekir.
4. Sadece gerekli sayfa/bölge ROI'sinde RapidOCR'nin CPUExecutionProvider sürümü çalışır. Dört noktalı poligon + güven skoru + model kimliği döner, transform zinciri saklanır.
5. Açı sınıflandırıcı varsayılan olarak yalnız 0°/180° ayrımı yapar; 90°/270° veya 45° için crop rotasyonu/çoklu yön stratejisi, çıktıyı ters dönüşümle sayfa koordinatına geri alma ve benchmark gerekir.
6. Türkçe ve `Ø ± ° ²` gibi simgeler otomatik kusursuz varsayılmaz; sürüm/karakter sözlüğü/yönerge ve gerçek pafta sentetik doğruluğu ölçülür.
7. Mevzuat PDF indekslemesi normal analizden ayrı offline ETL'de `pdfplumber` + `pypdfium2` + `RapidOCR CPU` ile yapılacak.
8. RapidOCR CPU kullandığında CUDA VRAM ayırmaz, fakat sistem RAM/CPU tüketimi vardır ve bunu ölçmek gerekir. GPU VLM süreciyle bellekte yarışmaz fakat CPU/bellek kaynakları ve toplam gecikme yine yönetilir.
9. Eski alternatif motor seçenekleri kaldırıldı; tek OCR motoru RapidOCR CPU.
10. Güncel kurulum `rapidocr onnxruntime`; bakım dışı paket kullanılmaz.
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
- `docs/ocr-ve-bellek.md`: kesin PDF/OCR seçimi, kaynak koordinatı, offline koşullar ve model hafıza planı.
- `docs/sistem-mimarisi.md`: PDF metin kalite kapısı ve hibrit ROI OCR rotasyon/quad işlemleri.
- `docs/mevzuat-rag.md`: offline ETL, belge sayfa/satır/tablo kökeni ve yasal kanıt koruma.
- `docs/modul-plani.md`, `docs/teknik-gereksinimler.md`, `docs/kararlar.md`, `docs/kapsam.md`, `README.md`: kapsam ve kabul sözleşmeleri, tercihlerin güncellenmesi.
- `docs/ocr-mimari-pafta.md`: gerçek teknik sözleşme, önerilen dosya ağacı, format/rotasyon test matrisi, açık kaynak linkleri.
## 5. Kabul ve uygulanmayan işler
- Belgeler GitHub'da oluşturulmuş, birbirine bağlanmış ve işlem kaydı sonuçlandırılmış olacak.
- Henüz yeni PDF/OCR motoru çalışıyor iddiası yok; sentetik testler ve Windows kabulü sonraki işlemlerdedir.
## 6. Uygulama kaydı
GitHub işlemleri tamamlandıkça gerçek commit bilgileri buraya yazılacak.
## 7. GitHub'da gerçekleşen değişiklikler
**Geliştirme öncesi işlem kaydı:** `docs/islem_004.md` oluşturuldu — `833ab386`.
| Dosya | Yapılan işlem | Commit (ilk / son) |
| --- | --- | --- |
| `docs/ocr-mimari-pafta.md` | RapidOCR CPU + PDF native text kalite/ROI, quad/rotasyon, ETL ve test sözleşmesi | `dbc5d946`, lisans revizyonu `4312c81` |
| `docs/pdf-lisans.md` | Seçilen PDF/OCR motorlarının transitive ve binary lisans kabul planı | `042eaaf` (eski); İşlem 005 ile yenilendi |
- `docs/ocr-ve-bellek.md`: kesin PDF/OCR seçimi, kaynak koordinatı, offline koşullar ve model hafıza planı.
| `docs/sistem-mimarisi.md` | Native CAD/PDF -> kalite kapısı -> ROI OCR ve backend lisans ayrımı | `43f07d1`, `12debb2` |
| `docs/mevzuat-rag.md` | Offline ETL, PDF kaynak bbox, tablo ve ayrı backend | `70a63c4`, `28dc7e3` |
| `docs/kararlar.md` | K-028…K-038 OCR, rotasyon, kurulum ve PDF lisans kararları | `4e8c71d`, `c2453fe` |
| `docs/kapsam.md` | OCR çalışma yolu güncellendi; LMS/agent/AI API hariç tutulmaya devam etti | `3b8b4b7` |
| `docs/modul-plani.md` | P7-A…P7-F OCR iş paketi, PDF backend lisans kapısı | `1254c75`, `ccd3067` |
| `docs/teknik-gereksinimler.md` | FR-029…037 ve NFR-017…021, kabul senaryoları | `83b3f23`, `a4f904e` |
| `README.md` | Seçilen OCR yönü ve PDF lisans uyarısı | `3134bbd`, `bcbbac0` |
**Netleştirilen teknik ayrım:**
- **Kesin:** Native text first + RapidOCR ONNX CPU, metin ve kutu kaynak izi; OCR modelinin 0/180 cls sınırı, 45/90/270 için özel deneme.
- **Eski ağır OCR yaklaşımı:** İşlem 005 itibarıyla kaldırıldı.
- **Uygulama dışı:** bulut API, pedagojik portal, çoklu agent.
**Önerilen İşlem 005:** `DrawingIR v0.1`, `PdfTextBackend` ve `TextCandidate` sözleşmeleri; sentetik 0/45/90/180/270° quad/geometri dönüşüm testleri. Ardından minimum native DXF/PDF okuma ve RapidOCR adapter kodu. Her iş için önce sıradaki `docs/islem_NNN.md` açılacak.
