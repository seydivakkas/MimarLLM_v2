# MimarLLM V2 — Bağımlılığa Dayalı Uygulama Yol Haritası

- **Kayıt:** [islem_006](islem_006.md)
- **Referans:** [Özellik envanteri](ozellik-envanteri.md)
- **Durum:** PLAN / teknik yol haritası; yüklenen taslaklardaki `islem_002…020` yeni GitHub kayıt numarası değildir.

## 1. Sabit mimari kararlar

Tek paket: `src/mimarllm`. Tek kullanıcı, offline-first, modüler monolit. CPU geometri/topoloji/kural, yerel RAG (SQLite FTS5 ve CPU embeddings); yerel VLM yalnız semantik aday ve GPU bütçesi içinde. PDF/OCR: `pdfplumber + pypdfium2 + RapidOCR(onnxruntime CPU)`. Teknik ve hukukî kanıt ayrı doğrulanır.

## 2. Paket ve kayıt sırası

| GitHub işlem kaydı | Geliştirme hedefi | Özellik ID | Bağımlılık | Çalışma kabulü |
| --- | --- | --- | --- | --- |
| islem_001–005 | Başlangıç, kapsam, RAG tasarım, OCR/PDF ilk gerçek kod | F03/F04 (kısmi) | — | Tarihsel kayıt korunur |
| **islem_006** | Bu kapsam/öncelik/uygunluk konsolidasyonu | F01–F24 | Önceki 001–005 | Dürüst feature envanteri |
| **islem_007** | DrawingIR v0.1 + birim/kalibrasyon/source mapping | F01 | Mevcut modeller | 2 koordinat sisteminde girdi doğruluğu |
| islem_008 | DXF + layer/blok/nested INSERT | F02 | 007 | CAD handle/transforms geri izlenir |
| islem_009 | PDF native/ROI/rotasyon + OCR layout entegrasyonu | F03/F04 | 007/008 | Kaynak poligonları / CPU OCR doğrulama |
| islem_010 | Geometri oda, iç duvar ve net/brüt alan | F05 | 007/008 | Sentetik iki oda + scale unknown |
| islem_011 | Mekânsal topoloji/erişilebilirlik | F06 | 010 | Gerçek kapı/geçit grafı; dışa çıkış sınıfı |
| islem_012 | Kural motoru + durumlar + güvenilir kural kaydı | F07 | 010/011 | Kaynak eksikliğinde hukukî PASS yok |
| islem_013 | Yerel mevzuat ETL + LegalAST + PDF span/source index | F13 | 009 | Özgün kaynak ve değişiklik zinciri |
| islem_014 | FTS5/dense/RRF + provenance + rule evidence | F14/F15 | 012/013 | Kesin citation ve applicability |
| islem_015 | İmar/yangın kural paketleri (önce source onayı) | F08/F09 | 011/012/014 | Kontrol başına veri/yürürlük/özel durum |
| islem_016 | Otopark/sığınak/BEP (önce source onayı) | F10/F11/F12 | 015 + ek proje verisi | İnsan hukukî inceleme; hold ayrı |
| islem_017 | Rapor, çizim işaretleme + bulgudan belge sayfasına geçiş | F17/F18 | 014–016 | İki kaynak bbox doğrulama |
| islem_018 | Pipeline + CLI + offline yerel FastAPI dashboard | F16/F19 | 017 | Sentetik çizim/rapor, localhost güvenliği |
| islem_019 | Windows run.bat + PyInstaller onedir + offline wheelhouse | F20 | Gerçek CLI/dashboard | Yerel Windows paket smoke ve SBOM |
| islem_020 | Yerel VLM + semantik etiket no-overwrite | F21/F22 | 009,010,018 | Gerçek 4070 8GB benchmark/CPU fallback |
| islem_021 | Çapraz modül benchmark, gerçek çizim ve regresyon, paket kabulü | F23/F24 | Tüm gerekli paketler | PASS/HOLD matrisleri |

**Önemli:** Bu ilerideki `islem_007…021` adları yalnız **planlanan sıra**, dosyalar henüz oluşturulmamıştır. Bir işlemin kapsamı değişirse yeni karar kaydı güncellenir, geçmiş numaralar yeniden kullanılmaz. İş paketleri gerçek uygulama modülüne göre bölünebilir; otomatik olarak tamamlandı kabul edilmez.

## 3. Öncelik ve ilk çalışan ürün

```text
DrawingIR -> DXF -> Geometri -> Topoloji -> kural çerçevesi
  -> minimal geometrik bulgu + koordinatlı JSON/HTML
  -> mevzuat LegalAST + kaynak bbox
  -> FTS5/dense retrieval -> hukuken onaylı rule bindings
  -> beş mevzuat ailesi (onaylı alt kapsam)
  -> web UI / rapor / offline Windows paket
  -> opsiyonel VLM -> gerçek donanım benchmark
```

Mevzuat kural modülü hukukî doğrulama beklese bile geometri ve çizim kalite kontrolü ilk kullanılabilir ürünü oluşturmalı. Aynı anda hem AI hem hukukî danışman hem tam proje sertifikasyonu hedeflenmez.

## 4. Mühendislik düzeltmeleri ve kabul

- Net alan: gerçekten iç yüz sınırı çıkarılmalı; CAD duvar çizgileri otomatik net sınır değildir.
- Egress: oda merkezleri arasındaki Öklid uzaklığı doğrudan kaçış mesafesi sayılmaz; yürünebilir serbest alan, alternatif çıkış, çıkmaz kol, kat ve erişim geometrisi gerekir.
- Yanlış oda sınırı: polygonize sliver/outer yüz false-positive analizi; kalibrasyonsuz alan `INSUFFICIENT_EVIDENCE`.
- Yangın: sürümlü Ek-5/B, kullanım/kişi yükü, sprinkler ve proje tarihine göre eşik seçimi.
- Mevzuat: exact source identity + tarihler + mahal / yapı profili, istisnalar; RAG yalnız candidate.
- VLM: `mmproj` / quantization / context/lisans/VRAM ve Windows GPU ölçülmeden varsayılan model yok.
- Windows: bağımlılık kuran `run.bat` için ilk kurulumda internet/yerel wheelhouse gereksinimi dürüstçe gösterilecek; tamamen offline dağıtım için wheelhouse veya onedir paket.
- Test statüleri: yerel sentetik sonuç, CI, gerçek Windows kabul ve bağımsız mevzuat incelemesi **ayrı**.

## 5. Sıradaki somut başlangıç

**İşlem 007:** `DrawingIR`, kalibrasyon ve kural/kanıt sözleşmelerinin kodu ve sentetik fixture testleri. Ürün baştan sona “varmış gibi” gösterilmeden bu temel kullanılarak DXF katmanına geçilecek.
