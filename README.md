# MimarLLM V2

**Amaç:** Tek Windows bilgisayarında çalışan, mimari DXF/PDF paftalarını ölçüm, geometri, topoloji ve mevzuat kaynağı açısından denetlemeye yönelik yerel yazılım.

**Donanım:** Intel i7 14. nesil, 32 GB RAM, RTX 4070 8 GB VRAM. Yapay zekâ çıkarımı yerel, harici AI API'si yok.

## Kesin PDF / OCR teknolojileri

| İş | Yerel bileşen |
| --- | --- |
| PDF native karakter/çizgi/dikdörtgen/eğri gözlemleri | **pdfplumber** |
| PDF raster sayfa veya ROI üretimi | **pypdfium2** |
| Taranmış/eksik metinleri OCR | **RapidOCR + ONNX Runtime CPU** |

**Önce vektör, sonra OCR.** Tamamen seçilebilir PDF metni bile kontur haline gelmiş ölçü, SHX karakter veya taranmış bölge içeriyor olabilir; OCR yalnız gereken bölgeye uygulanır. PDF kaynak koordinatları/sha256 korunur.

### Mimari sınırlar

- **Deterministik karar:** OCR ve yerel VLM yalnız aday üretir; fiziksel alan/ölçü ve mevzuat uygunluk kararı doğrulanmış geometrik girdilerden gelir.
- **Mevzuat RAG:** Yapısal madde/fıkra/bent, tarih, istisna, tablo-hücre ve özgün kaynak sayfası/alanı. Yerel hazırlık ETL; çevrim dışı çalışma.
- **Kanıt ekranı:** Hata bulunduğu çizim koordinatı ↔ özgün mevzuat sayfası/bounding polygon.
- **Tek kullanıcılı modüler monolit:** LMS/öğrenci portalı, jüri karakterleri, çoklu AI agent ve dış API çağrısı yok.
- **Lisans:** Seçilen motorlar izinli ana lisanslara sahip; transitif binary/model/dağıtım lisanslarının son kabulü henüz yapılmadı.
- **Public depo:** Özel müşteri çizimleri, mevzuat tam metinleri, model ağırlıkları, sırlar ve yerel indeksler Git'e alınmaz.

## Mevcut uygulama durumu (İşlem 005)

İlk kod: `src/mimarllm/core/models.py` kaynak aday sözleşmesi, `src/mimarllm/importers/pdf.py` native gözlem/ROI raster, `src/mimarllm/ocr/rapid_engine.py` CPU OCR adaptörü. `pyproject.toml` ve sentetik PDF testleri eklendi.

**Henüz yapılmadı:** DrawingIR'nin tüm CAD nesneleri, DXF parser, OCR gerçek model benchmark'ı, mevzuat indeksleme, hukukî doğrulama, Windows kurulum/benchmark, UI ve offline paket kabulü.

## Belgeler

- [İşlem kayıtları 001–005](docs/islem_005.md)
- [ADR-002: PDF motoru ve lisans kararı](docs/adr/ADR-002-PDF-Engine-License.md)
- [Teknik PDF/OCR sözleşmesi](docs/ocr-mimari-pafta.md)
- [OCR kaynak yönetimi](docs/ocr-ve-bellek.md)
- [Lisans envanteri](docs/pdf-lisans.md)
- [Mevzuat RAG](docs/mevzuat-rag.md)
- [Sistem mimarisi](docs/sistem-mimarisi.md)
- [Modül ve iş planı](docs/modul-plani.md)
- [Teknik gereksinimler](docs/teknik-gereksinimler.md)
- [Kapsam](docs/kapsam.md)
- [Kararlar](docs/kararlar.md)

Her yeni AI destekli istek **önce** `docs/islem_NNN.md` dosyasına işlenir. Yapılmayan işin durumunu PASS gösterme.


## Güncel tam kapsam ve gerçek ilerleme (İşlem 006, 2026-10-13)

Kullanıcının sağladığı mimari ve kod taslakları V2'nin **hedef özellik envanterine** işlendi: DXF/ölçek, duvar-oda geometri ve net/brüt alan, spatial topology/kaçış, beş mevzuat ailesi, hiyerarşik RAG+FTS5+yerel embedding, kural–özgün kaynak bağlama, yerel RapidOCR ve VLM, rapor/SVG, offline localhost paneli, run.bat / PyInstaller onedir ve Windows benchmark.

**Hedef kapsam ≠ tamamlanmış uygulama.** Mevcut kod PDF/ROI ve OCR adaptörünün başlangıç düzeyindedir. Resmî mevzuata ilişkin eşikler `HUKUKI_HOLD`; kaynak, madde/fıkra, yürürlük ve proje bağlamı doğrulanmadan kesin kural yok. Yerel Windows, OCR model, VLM ve paketleme sonuçları henüz PASS değildir.

- [İşlem 006 — Kapsam birleştirme günlüğü](docs/islem_006.md)
- [24 maddelik özellik ve durum envanteri](docs/ozellik-envanteri.md)
- [İşlem 007–021 için bağımlılığa dayalı yol haritası](docs/uygulama-yol-haritasi.md)
- [Türkiye mevzuatı doğrulama ve özgün PDF kanıt protokolü](docs/mevzuat-dogrulama-protokolu.md)
- [Sade dizin tasarımı](docs/planlanan-dosya-yapisi.md)
- [Windows tek tık kurulum ve standalone paketleme kabul planı](docs/windows-dagitim-plani.md)
- [ADR-003 — Kanıt temelli mimari karar](docs/adr/ADR-003-Kapsam-Kanit-ve-Kabul-Kapilari.md)

**Bir sonraki geliştirme kaydı:** `docs/islem_007.md` (DrawingIR + birimler + doğrulanmış kaynak dönüşümleri). Önce bu kaydı oluştur, sonra kaynak kodu ekle.

## İşlem 007 — DrawingIR çekirdek sözleşmeleri

- [İşlem 007 ve gerçek kabul durumu](docs/islem_007.md)
- [DrawingIR v0.1 teknik şartnamesi](docs/specs/drawingir-v0.1.md)
- Kodlanan: `core/units.py` (CAD INSUNITS/reference confirmation, SI ölçek), `core/ir.py` (Pydantic DrawingIR, SourceReference, CoordinateFrame, Transform2D, GeometryPrimitive, DrawingEntity, MeasurementEvidence, Finding).
- Güvenlik: `UNKNOWN/INFERRED/CONFLICT` durumunda fiziksel ölçüm yasak; kaynak SHA/entity/frame eşleşmesi; onaylı ölçümün fiziksel değeri kalibrasyonla kontrol edilir. Hukukî uyum sertifikasyonu yasak.
- GitHub Actions sentetik sözleşme testi: [Core contracts](https://github.com/seydivakkas/MimarLLM_v2/actions/workflows/core-contracts.yml).
- Henüz yok: `ezdxf` DXF parser, duvar/oda topolojisi, gerçek mimari pafta kabulü, Windows/i7/4070 deneyleri. Sıradaki kayıt `islem_008`.
