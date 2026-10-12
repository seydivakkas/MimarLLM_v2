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
