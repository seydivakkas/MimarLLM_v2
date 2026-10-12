# İşlem 005 — Lisansı denetlenebilir hibrit PDF motoru ve ilk çalışan çekirdek

- **Tarih:** 2026-10-12
- **Depo:** `seydivakkas/MimarLLM_v2`
- **Başlangıç durumu:** PLANLANDI — işlem kaydı diğer değişikliklerden **önce** oluşturuldu.
- **Kullanıcı isteği:** PDF motorunu `pdfplumber` (vektör/karakter/çizgiler) + `pypdfium2` (render) olarak tasarla, RapidOCR'yi ONNX Runtime CPU üzerine oturt, lisansları denetle; `docs/adr/ADR-002-PDF-Engine-License.md` ile karar kaydı oluştur, önceki `docs/islem_002.md` geçmişini bozmadan yeni karara atıf ekle ve kodlamayı başlat.

## 1. Kayıt sırası

`islem_001`…`islem_004` mevcut ve tamamlandı. İşlem 002 tarihsel ürün kapsamı kaydıdır; bu kararı **orada yeniden numaralandırmayacağız**. İşlem 005, uygulama ve ADR'nin asıl kaydıdır. İstenildiği üzere İşlem 002'ye **tarihli, salt ek** yönlendirme eklenebilir.

## 2. Teknik seçim ve düzeltmeler

- **Çekirdek PDF vektör metin/objeler:** `pdfplumber` / `pdfminer.six`; karakter bbox, `matrix`, `line/curve/rect` ve özgün sayfa kökeni korunur.
- **Sayfa/ROI render:** `pypdfium2` / PDFium; gerçek sayfa DPI'da tüm paftayı kör rasterleştirme yok, bellek bütçeli crop/ROI.
- **OCR:** güncel `rapidocr` + `onnxruntime` CPU; önce native text, sonra gerekli ROI OCR. Eski `rapidocr_onnxruntime` bakım dışı paket **yeni bağımlılık değil**.
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

## 6. Çalışma sonunda doldurulacak uygulama kaydı

- Commit SHA ve dosyalar
- Gerçekten çalışan testler/bağımlılıklar
- Tamamlanmayan (özellikle Windows/offline, OCR gerçek modeli, lisans/SBOM ve PDF rotasyonu) kabul kapıları
