> **LİSANS KAPISI:** PyMuPDF, AGPLv3 veya ticari lisanslıdır. Kapalı kaynak müşteri dağıtımı için üretim bağımlılığı olarak henüz onaylanmadı; `PdfTextBackend` ile pypdfium2/pdfplumber alternatifleri açık tutulur. Metin önceliği ilkesi kesin, **PDF motoru koşullu**. [Lisans karar belgesi](pdf-lisans.md).

# Mimari Pafta OCR — PyMuPDF + RapidOCR CPU Tasarımı v0.1

- **İşlem:** [islem_004.md](islem_004.md)
- **Durum:** Tasarım ve kabul sözleşmesi; Python OCR modülleri henüz geliştirilmedi veya Windows'ta test edilmedi.
- **Karar:** MimarLLM V2'nin varsayılan pafta OCR hattı **önce doğrudan CAD/PDF metni, yalnız eksik bölgede RapidOCR ONNX CPU** olacaktır.
- **Not:** Bu yaklaşım RapidOCR/ONNX Runtime için RTX 4070 VRAM'ini kullanmayı **gerektirmez**, ama CPU ve RAM bütçesine sahiptir. VLM için GPU ayrı tutulur.

## 1. Format başına doğru okuma sırası

### DXF (ilkeli, vektör öncelikli)

```text
DXF -> ezdxf -> TEXT/MTEXT/ATTRIB/ATTDEF/DIMENSION + block INSERT
                   |
             entity handle + layer + placement + rotation
                   |
           CAD koordinatındaki doğrudan metin adayı
                   |
      render edilen alanlarda eksik/özel şekilli yazı varsa
                   -> kontrollü RapidOCR ROI (CPU)
```

DXF'de `DIMENSION` gösterim değerini yazı olarak kabul etmek her durumda doğru değildir: boyut stili, kullanıcı override değeri, birim, tolerans ve geometri karşılaştırılmalı. Block transform (`INSERT`) döndürme/ölçek/öteleme ve nested INSERT için kaynak kimliği korunmalı. Metnin OCR'dan gelmesi ikinci tercihtir.

### PDF (mevzuat ve çizim)

```text
PDF sayfası
   |
PyMuPDF metin/span/char -> text_quality_gate ----> güvenilir vektör metin
   |                                |
   |                         boş/eksik/kısmen bozuk
   v                                v
raster/vektör karma içerik      sadece gereken ROI render
                                     |
                              RapidOCR (ONNX CPU)
                                     |
                            dört köşeli OCR poligonu
                                     |
                         pixel -> page-point ters dönüşüm
                                     |
                   normalized TextCandidate + SOURCE_PROVENANCE
```

**Önemli:** “PDF üzerinde bir miktar seçilebilir metin var” diye bütün sayfada OCR'ı kapatma. Antet seçilebilir iken SHX ölçüler vektörel çizgilere dönüşebilir. Native text ve OCR adayları ayrı kanıt olarak saklanır, yakın konumdaki kopya metinler bbox/text kaynaklı dedup kontrolünden geçer.

## 2. PyMuPDF native çıkarım kalite kapısı

Planlanan inceleme alanları:
- `get_text("rawdict")` veya `get_text("dict")`: blok, satır, span, char/font/origin.
- `line["dir"]` üzerinden doğrultu; döndürülmüş span highlight için `pymupdf.recover_quad` veya `recover_line_quad`.
- `get_texttrace()` gerektiğinde glif/unicode sorunları, düşük seviye text traces.
- U+FFFD/bozuk Unicode oranı, görünür metin karşılığı, sayfa alanlarına dağılım, aşırı sayıda kontrol karakteri, karışık okuma sırası ve metinsiz büyük raster bölgeler `TEXT_UNRELIABLE`/ `PARTIAL_TEXT` adayı oluşturur.
- SHX fonts ve kontura çevrilmiş ölçüler doğrudan extract edilemeyebilir; Autodesk AutoCAD PDF dışa aktarma ayarları sonucu etkiler.

**Bu kalite kapıları heuristiklerdir.** Çok az metin çıkması, sayfanın gerçekten metinsiz bir çizim olması nedeniyle de olabilir. Böyle durumda tüm sayfa OCR yerine tespit edilmiş ölçü/antet/mahal ROI'leri denenir ve kullanıcıya gerekçe sunulur.

## 3. RapidOCR Windows CPU çalışma sözleşmesi

- Güncel kurulum adayı: `python -m pip install rapidocr onnxruntime`.
- **Eski `rapidocr_onnxruntime` paketi yeni sistem için kullanılmayacak**; resmi proje güncel `rapidocr` paketine geçmiştir.
- API adayı: `from rapidocr import RapidOCR; engine = RapidOCR(params=...); result = engine(image)`.
- Motorun çalışma kayıtlarında ONNX Runtime/CPU provider kullanıldığı **doğrulanacak**; `CUDAExecutionProvider` veya `DmlExecutionProvider` kullanılmayacak.
- Modellerin cihazda *önceden* mevcut olması gerekiyor. Kurulum sırasında model sürümü, hash, Python/ONNX Runtime, dil karakter listesi ve licence manifest kaydedilmeli.
- `rapidocr` sürümüne göre çıktı biçimi değişebilir; `rapid_engine.py` bütünleşik `TextCandidate` sözleşmesine normalize eder.
- Onaylanmamış internet indirmesi, örnek URL bağımlılığı veya bulut çağrısı normal runtime içinde olmayacak.
- CPU thread sayısı ilk testte kontrollü ayarlanır (ör. 4 başlangıç deney adayı); hedef i7'nin gerçek çekirdek/iş parçacığı miktarı ve hız ölçülür. 14. nesil i7'nin AVX-512 desteği varsayılmaz.
- OCR `score` bir tanıma modeli skorudur; metnin gerçek doğruluk olasılığı olduğu iddia edilmez.

## 4. Mimari pafta rotasyon stratejisi

RapidOCR'nin standart sınıflandırıcısı 0°/180° yön ayrımıdır; 90°/270° ve 45° otomatik olarak garanti edilmez.

Planlanan adaptör algoritması:

1. Native vektör metin için **PDF metin çizim yönünü** doğrudan kullan; OCR için raster/polygon adayı çıkar.
2. OCR detector'ın döndürülmüş dört köşe poligonu varsa o ROI'yi perspektif/affine rectification ile yataylaştır.
3. Boyu-en oranı, geometrik duvar ekseni ve metin kutusu eğimiyle `0, 90, 180, 270` yön hipotezleri oluştur; gerekiyorsa `45, 135, 225, 315` açılı ROI denemesi (deneysel).
4. Tam sayfayı 8 yönle OCR'dan geçirme. Sadece şüpheli küçük bölgelerde farklı yönleri dener.
5. Adayları semantik/şekil doğrulama ve OCR skoru ile sıralar. Birim/çap/kot/alan gibi kritik sembollerde belirsizlik kalırsa `REVIEW_REQUIRED`.
6. Seçilen rotasyondaki `OCR_quad` dönüştürme matrisinin tersiyle özgün page point koordinatlarına döner. Hem özgün ROI hem dönüşüm matrisi kaydedilir.
7. Rapor PDF açıldığında kutu doğru yerde değilse geometrik doğrulama kapısı `FAIL` olur; sahte highlight yok.

**Not:** Rotasyon denemelerinin tümü tasarım hipotezidir; hangi açılarda başarılı olduğu ancak sentetik gerçek veri benchmark'ıyla belirlenecek.

## 5. `box_utils.py` — koordinat geometrisi

- `Point(x,y)`, `Quad(p1,p2,p3,p4)`; 4 köşenin sayısal doğruluğu, sıra ve yönü doğrulanır.
- `Transform2D`: raster pixel -> ROI pixel -> page pixel -> PDF point -> DrawingIR world gibi dönüşüm zinciri.
- PDF: `MediaBox/CropBox`, sayfa dönüşü, render matrisi, clip rectangle; y ekseni ve nokta birimi açık.
- Raster ve ROI: kaynağa göre görüntü çözünürlüğü / deskew / rotation homography bilgisi. Homografi gerektiğinde **3x3** matris, düz affine için 2x3/3x3 saklanır.
- Rotated PDF span'ın axis-aligned bbox'ı yeterli değil; gerçek dört köşe `Quad` tutulur.
- PDF'den CAD metre değerine dönüşüm yalnız kullanıcı veya çizim metaverisinden güvenilir kalibrasyon varsa yapılır.
- Roundtrip kabulü: normalize `Quad` -> render koordinatı -> geri `Quad` eşlemesi; tolerans sayfa dpi/pixel çözünürlüğüne ve kalibrasyona bağlı olarak ayrı ölçülür.

## 6. `TextCandidate` birleşik kanıt şeması

```json
{
  "candidate_id": "txt-001",
  "source_sha256": "synthetic-sha256",
  "source_kind": "pdf",
  "page_index": 0,
  "source_method": "pymupdf_native|rapidocr_cpu|dxf_text",
  "text_raw": "±0.00",
  "text_normalized": "±0.00",
  "polygon": [[100.0,40.0],[135.0,40.0],[135.0,52.0],[100.0,52.0]],
  "coord_system": "pdf_page_point",
  "rotation_degrees": 0.0,
  "confidence_score": null,
  "model_id": null,
  "quality_flags": [],
  "validation_state": "REVIEW_REQUIRED",
  "transform_id": "t-page-0"
}
```

Bu alanlar **örnektir**, gerçek OCR sonucu değildir. `confidence_score` native text'te null olabilir; tanınan kritik ölçü veya mevzuat numaraları ancak geometri/kaynak kontrolleriyle doğrulanır.

## 7. Yönetmelik indeksleme hattı: ayrı offline ETL

```text
local_data/regulations/raw/         # resmî PDF, HTML ve kaynak künyesi
    |
PyMuPDF native text + gerçek bbox   # birincil
    |
Sayfa/bölge kalite kapısı
    |
RapidOCR CPU (tarama/eksik kısımlar)
    |
Tablolar: pdfplumber -> doğrulanmayanlarda Docling CPU adayı
    |
SourceSpan (document SHA + page + quad + table cell + line-id)
    |
LegalAST (madde/fıkra/bent/ek, geçici madde, değişiklik, yürürlük)
    |
SQLite FTS5 + yerel CPU embeddings + onaylı RuleBinding
```

- **ETL ayrı bir kullanıcı işlemi / offline hazırlık fazıdır**, çalışan çizim analizi sırasında tekrar OCR yaptırmaz. Yeni kaynak veya sürüm eklendiğinde eski AST/indeksler sürümlü kalır.
- `pdfplumber` ve `Docling` yapıyı *aday* olarak çıkarır; Türkçe hukukî madde/fıkra ve tablo hiyerarşisini kendiliğinden kesin doğru anlamaz.
- Docling tablo/layout modelleri ayrıca CPU/RAM maliyeti taşıyabilir; sadece gerekli belgelerde değerlendirilir. Kaynak orijinal PDF olarak saklanır, türetilmiş Markdown kaynak sayfa/bbox ilişkisinin yerini almaz.
- Tablo hücresi: `table_id,row,col,rowspan,colspan,polygon,raw_text,source_page`; satır ve sütun etiketleri örneklerde doğrulanır.
- Resmî olmayan/derlenmiş belgeyi özgün PDF diye sunma; PDF sayfa indeksi ile basılı sayfa numarasını karıştırma.

## 8. Sade paket dosyaları (planlanan, kod değil)

Önceden önerilen `src/mimar/` yerine repo bütünlüğü için **tek isim `src/mimarllm/`**:

```text
src/mimarllm/
├── importers/
│   ├── dxf.py                 # Native CAD entity/attribute
│   ├── pdf.py                 # PyMuPDF page/vector/layout
│   └── image.py               # Pafta raster ROI
├── ocr/
│   ├── text_extractor.py      # Native-first kalite kapısı ve ROI seçimi
│   ├── rapid_engine.py        # RapidOCR CPUExecutionProvider adaptörü
│   └── box_utils.py          # Quad, perspective/rotate, coordinate transforms
├── regulations/
│   ├── extraction.py         # Ayrı offline ETL ve tablo çıkarımı
│   ├── parser.py             # AST, hiyerarşi
│   ├── retrieval.py          # Mevcut FTS5 + dense indeks
│   └── citations.py          # Özgün sayfa/satır/hücre kaynağı
└── vision/
    └── vlm.py                # OCR ile eşzamanlı ağır GPU kullanımı yok
```

**Şimdiki repo:** `src/` altında bu dosyalar henüz yoktur. Kaynak kod ve sentetik test fixture'ı sonraki işlemde yapılacaktır.

## 9. Deney ve kabul matrisi

| Vaka | Beklenen kontrol | Gerekli ölçüt |
| --- | --- | --- |
| Dijital PDF, 0°, TrueType | Native text doğrudan; OCR gereksiz | Text/char recall, elapsed, bbox |
| PDF, 45°/90°/270° native metin | Yönlü quad ve metin çıkarımı | Polygon IoU, char recall |
| SHX → kontur PDF | Kaybolan metni hedef ROI OCR | No false native PASS, CER |
| Kısmi tarama + seçilebilir antet | Yalnız taranmış/eksik bölge OCR | Region selection P/R |
| Yüksek kontrast mimari ölçü | Teknik sayı ve simgeler | Exact-match, symbol error |
| Düşük çözünürlük, kesik çizgiye yakın yazı | Inpaint/mask deney, crop stratejisi | CER ve false-positive oranı |
| Türkçe `ş ğ ı İ ç ö ü` | Doğru modeller ve sözlük | CER/WER per character |
| `Ø ± ° ²`, ölçek 1/100, kot ±0.00 | Özel karakter doğrulama | Exact critical token match |
| Resmî Gazete çok sütun | Doğru okuma sırası ve madde eşlemesi | AST fidelity, bbox citation |
| Çok satırlı / birleşik hücreli tablo | Satır/hücre kaynak ilişkisi | Table cell precision/recall |
| Aynı girdide tekrar | Model/parametre manifest eşit | Normalized output diff |
| Windows offline 32 GB RAM / CPU | RAM, CPU, latency ve dış ağ | Peak RAM, p50/p95, no network |

**Durum:** Benchmark sonuçları mevcut değil. Doğruluk değerleri, CPU gecikmesi veya donanım uyumluluğu önceden PASS ilan edilemez.

## 10. Yetkili teknik kaynaklar

- [RapidOCR güncel paket/install](https://rapidai.github.io/RapidOCRDocs/main/en/install_usage/rapidocr/install/)
- [RapidOCR güncel parametreler (0/180 sınıflandırıcı)](https://rapidai.github.io/RapidOCRDocs/main/install_usage/rapidocr/parameters/)
- [RapidOCR tanıma dil modelleri](https://rapidai.github.io/RapidOCRDocs/main/model_list/)
- [PyMuPDF rotated text ve quad](https://pymupdf.readthedocs.io/en/latest/recipes-text.html)
- [PyMuPDF sorunlu/missing text](https://pymupdf.readthedocs.io/en/latest/recipes-common-issues-and-their-solutions.html)
- [Autodesk SHX PDF geometri açıklaması](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/SHX-files-not-included-in-PDF-import.html)
- [Docling resmî](https://docling.ai/)
