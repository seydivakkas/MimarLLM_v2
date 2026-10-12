# İşlem 005 — Lisansı denetlenebilir hibrit PDF motoru ve ilk çalışan çekirdek
- **Tarih:** 2026-10-12
- **Depo:** `seydivakkas/MimarLLM_v2`
- **Son durum:** UYGULANDI — kod başlangıcı, ADR ve dokümantasyon; gerçek Windows/RapidOCR testleri HOLD. Bu işlem kaydı tüm değişikliklerden önce oluşturuldu.
- **Kullanıcı isteği:** PDF motorunu `pdfplumber` (vektör/karakter/çizgiler) + `pypdfium2` (render) olarak tasarla, RapidOCR'yi ONNX Runtime CPU üzerine oturt, lisansları denetle; `docs/adr/ADR-002-PDF-Engine-License.md` ile karar kaydı oluştur, önceki `docs/islem_002.md` geçmişini bozmadan yeni karara atıf ekle ve kodlamayı başlat.
## 1. Kayıt sırası
`islem_001`…`islem_004` mevcut ve tamamlandı. İşlem 002 tarihsel ürün kapsamı kaydıdır; bu kararı **orada yeniden numaralandırmayacağız**. İşlem 005, uygulama ve ADR'nin asıl kaydıdır. İstenildiği üzere İşlem 002'ye **tarihli, salt ek** yönlendirme eklenebilir.
## 2. Teknik seçim ve düzeltmeler
- **Çekirdek PDF vektör metin/objeler:** `pdfplumber` / `pdfminer.six`; karakter bbox, `matrix`, `line/curve/rect` ve özgün sayfa kökeni korunur.
- **Sayfa/ROI render:** `pypdfium2` / PDFium; gerçek sayfa DPI'da tüm paftayı kör rasterleştirme yok, bellek bütçeli crop/ROI.
- **OCR:** `rapidocr` + `onnxruntime` CPU; önce native PDF metni, eksik ROI'de OCR. Güncel paket dışında ikinci OCR motoru yok.
- **Kaynak izlenebilirliği:** PDF sayfası ve dört köşe/source transform; DXF fiziksel birim dönüşümü kalibrasyonla ayrılacak.
- **Kapsam:** İlk uygulama için çalışan `PdfTextBackend` arayüzü, `TextCandidate` sözleşmesi, PDF karakter/vektör çıkarıcı, PDF ROI render ve OCR çıktısı normalize eden CPU adaptör; sentetik testler ve basit komut satırı önizleme.
- **AI API yok:** Hiçbir bulut inference veya haricî servis çağrısı; VLM/RAG/legal rule engine bu ilk kod kapsamında yapılmayacak.
## 3. Lisans kapısı — kesinlik sınırı
`pypdfium2` kendisi Apache-2.0 **veya** BSD-3-Clause; PDFium'un yerleşik bileşenleri ve wheel BUILD_LICENSES bildirimleri ayrıca taşınır; derleme profiline bağlı alt lisans farkları vardır. `pdfplumber` MIT; `pdfminer.six`, Pillow, RapidOCR/ONNX, yerel model ağırlıkları ve diğer dolaylı bağımlılıklar ayrı exact-version SBOM/lisans incelemesi gerektirir. **“Hiç GPL/AGPL kalmaz” veya “yasal risk sıfır” şimdiden PASS değil.** Kapalı kaynak ticari yeniden dağıtım nihai lisans kabulü bekler.
`ezdxf`, `shapely`, `networkx`, `pydantic`, `llama-cpp-python` ve Qwen-VL modelinin tam sürüm/lisans/redistribution şartları da model ve paketleme aşamasında ayrı doğrulanır.
## 4. Tasarlanacak dosyalar
- `docs/adr/ADR-002-PDF-Engine-License.md`: karar, kabul gerekçesi, alternatifler, lisans kanıt tablosu, test kapıları.
- `docs/islem_002.md`: tarihsel kaydı koruyan yeni `islem_005` atfı.
- `docs/kararlar.md`, `docs/pdf-lisans.md`, `docs/ocr-mimari-pafta.md`, `docs/modul-plani.md`, `README.md`: güncel uygulama/karar durumunu belirtme.
- `pyproject.toml`, `src/mimarllm/` çekirdek ve PDF/OCR modülleri, `tests/`: gerçek ilk kod; dosyalar tasarlanıp uygun yerel kontrollerden sonra GitHub'a yazılacak.
## 5. İlk uygulama kapsamı ve kabul sözleşmesi
1. Dosya boyutu/sayfa/ROI piksel limiti, bozuk PDF'de kontrollü hata.
2. Tüm koordinatlar açık sistemde: PDF top-left points; page rotation/crop/scale dönüşümleri belgeleyerek.
3. Native karakterlerin `matrix`/bbox bilgisi korunur; çizgi/rect/curve öğeleri ilk veriye eklenir, bunlara semantik “duvar” kararı verilmez.
4. ROI PDF raster → poligonun PDF sayfa koordinatına geri dönüşü 2B affine/dönüşümle doğrulanır. İlk dar sürümde rotasyonlu crop sınırlanırsa açık reddedilir.
5. RapidOCR olmadan native PDF çıkarımı çalışır. RapidOCR gerçekten kurulmadıysa açık `OCR_UNAVAILABLE`, sahte veri yok.
6. Testler çalıştırılırsa test ortamı ile birlikte raporlanır; Windows/RTX 4070 deneyi Linux yerel testiyle karıştırılmaz.
## 6. Uygulama kaydı
- Commit SHA ve dosyalar
- Gerçekten çalışan testler/bağımlılıklar
- Tamamlanmayan (özellikle Windows/offline, OCR gerçek modeli, lisans/SBOM ve PDF rotasyonu) kabul kapıları

## 7. Gerçekleşen mühendislik çıktıları (2026-10-12)

**Ön kayıt commit:** `e6d7a3e` (`docs/islem_005.md`) — diğer değişikliklerden önce.

**Mimari karar:** `docs/adr/ADR-002-PDF-Engine-License.md` commit `57f5312`. Kesin teknoloji üçlüsü: `pdfplumber`, `pypdfium2`, `rapidocr` + `onnxruntime CPU`. Önceki motor alternatiflerinin adı ve aktif bağımlılığı **mevcut Git çalışma ağacından kaldırıldı**. Eski Git commit'leri yeniden yazılmadı.

**Gerçek ilk kaynak kod ve testler:**

| Dosya | Yapılan iş | İlk commit |
| --- | --- | --- |
| `pyproject.toml` | Seçilen PDF/OCR motorları ve sürüm aralığı; CPU ONNX ana bağımlılık | `7af561c`, revizyon `21cec36` |
| `src/mimarllm/core/models.py` | Pydantic PDF kaynak / karakter / vektör / dört noktalı polygon | `1c81fbb` |
| `src/mimarllm/importers/pdf.py` | pdfplumber native gözlem, pypdfium2 bölge render ve source coordinate, limitler | `fc86dba` |
| `src/mimarllm/ocr/rapid_engine.py` | RapidOCR CPU adaptör; OCR polygonlarını source point alanına taşıma | `dd4a8be` |
| `src/mimarllm/**/__init__.py` | Minimal Python paket iskeleti | çeşitli commit'ler |
| `tests/test_pdf_contract.py` | Raporlanan kaynak, çizgi/rect, ROI, ölçü ve sınır testleri | `60d2687` |

**Belgeler:** `README.md`, `docs/kararlar.md`, `docs/kapsam.md`, `docs/modul-plani.md`, `docs/teknik-gereksinimler.md`, `docs/mevzuat-rag.md`, `docs/sistem-mimarisi.md` güncellendi. `docs/ocr-ve-bellek.md`, `docs/ocr-mimari-pafta.md`, `docs/pdf-lisans.md` güncel karara göre yeniden yazıldı; eski işlem kayıtlarına `ADR-002` bağlantıları eklendi. `docs/islem_002.md` numara değiştirilmeden salt ek yönlendirme aldı (`80057d7`).

**Doğrulama:**
- 16 güncel Markdown belgesinde kaldırılan model/kütüphane isimlerinin bulunmadığı kontrol edildi (GitHub connector içerik taraması).
- Yardımcı ortamda bağımsız sentetik 432×288 PDF oluşturularak `pdfplumber` ile **14 native karakter, 1 çizgi, 1 rect** okunması ve `pypdfium2` ile 144 DPI 100×100 pt ROI'nin **200×200 pixel** render edilmesi gözlendi; PDF rotasyonu 0 idi.
- Bu yardımcı deney, GitHub'a gönderilen `tests/test_pdf_contract.py` dosyasının otomatik çalıştırıldığı veya hedef Windows sistem kabulü anlamına gelmez.
- RapidOCR ve ONNX Runtime yardımcı test ortamında kurulu olmadığından gerçek OCR inference çalıştırılmadı.
- Kaynak Python modüllerinin hedef Windows makinesinde `pytest`/CI ile çalıştırılması ve lisans/dağıtım dosyası doğrulaması henüz **HOLD**.

**Kapsam dışı / açık:** Sayfa rotation != 0 için render erken ret; gerçek rotated glyph quad üretimi, SHX telafisi, karma OCR kalite kapısı, DXF parser, hukukî AST/kurallar, son kullanıcı UI, 8 GB VLM benchmark ve bütünleşik Windows dağıtım henüz uygulanmadı.

**Sonuç:** İstenilen tek teknoloji yığını repo güncel dosyalarına işlendi ve ilk gerçek Python PDF/CPU OCR adaptör kodu oluşturuldu. Sıradaki yeni istek **`docs/islem_006.md`** ile açılacak.
