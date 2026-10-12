> **Güncelleme — 2026-10-12, İşlem 005:** Bu dosya önceki mühendislik tartışmasının tarihsel kaydıdır. Güncel, tek PDF/OCR teknoloji kararı: **pdfplumber + pypdfium2 + RapidOCR/ONNX Runtime CPU**. Önceki motor alternatifleri kullanımdan kaldırıldı. Asıl karar [ADR-002](adr/ADR-002-PDF-Engine-License.md). Git geçmişi yeniden yazılmadı.

# İşlem 003 — Mimari çizim denetimi, yerel OCR ve hiyerarşik mevzuat RAG tasarımı
- **Tarih:** 2026-10-12
- **Kullanıcı isteği (tarihsel):** İlk tasarımda yerel OCR ve mevzuat RAG mimarisini genişletme; bugün kesin olan motor seçimi [ADR-002](adr/ADR-002-PDF-Engine-License.md) ile değiştirilmiştir.
- **Depo:** `seydivakkas/MimarLLM_v2` (public).
- **Durum:** PLANLANDI — işlem kaydı tasarım belgelerinden önce oluşturuldu. Kod uygulanmadı.
- **Önceki kayıtlar:** `islem_001` başlangıç; `islem_002` ürün kapsamı ve teknik plan. Bu kayıtlar **yeniden numaralandırılmaz**.
## 1. Sabit hedef
Ana ürün: **Yerel Mimari Teknik Çizim Analizi, Hata Tespiti ve Kaynaklı Mevzuat Denetim Yardımcısı.** Pedagojik LMS, öğrenci takibi, jüri karakterleri, çoklu agent ve bulut AI API'leri kapsam dışı kalır.
Donanım: Windows 10/11 hedef, i7 14. nesil, 32 GB RAM, RTX 4070 8 GB VRAM (kullanıcının bildirdiği hedef). AI inference, arama, indeksleme, veri ve raporlar cihazda çalışır. Önceden hazırlanmış lisanslı kaynaklar ve model ağırlıkları yerel diskte tutulur; normal kullanım ağ gerektirmez.
## 2. En önemli iki ürün sözleşmesi
**A. Drawing Evidence:** CAD/PDF'den çıkarılan her nesne/ölçüm, girdi dosya hash'ine, sayfa/layout'a, CAD handle veya PDF koordinat kutusuna ve birim/ölçek kökenine geri bağlanır.
**B. Legal Evidence:** Kullanılan her hüküm, kaynak PDF/HTML'nin SHA-256'ına, özgün belge ve yayımlanma bilgisine, PDF sayfası ve sayfa içi kutuya, hiyerarşik madde/fıkra/bent/tablo hücresine, ayrıca yürürlük ve uygulanabilirlik durumuna bağlanır.
**Bir bulgunun kanıt zinciri:** DrawingIR entity -> ölçüm ve tolerans -> kural ID/sürümü -> mevzuat koşul çözümlemesi -> sürümlü hukukî hüküm -> PDF'ye geri dönüş -> kullanıcıya yan yana önizleme.
**Dikkat:** PDF satır sayısı genellikle resmî hukukî tanımlayıcı değildir. Sistem görüntüleme sırasında OCR metin blokları üzerinden kaynak içi `line_index` üretebilir; **asıl atıf** madde/fıkra/bent ile sayfa + bounding polygon'dur. Çok sütun, sayfa kayması, ek/madde ayrımı ve tarama hataları doğrulamadan geçirilir. Dijital olarak kaynaklanan belgede resmî PDF yoksa “özgün PDF” uydurulmaz; kaynak HTML ve türetilmiş görüntü ayrıca işaretlenir.
## 3. Mimari kısıtlar
1. **Kural motoru karar verir; RAG hüküm bulur, karar vermez.** Arama isabeti, mevzuatın uygulanabilir olduğu veya teknik kontrolün doğru olduğu anlamına gelmez.
2. **Tarih ve yer bağlamı:** `inspection_date`, `permit_date`, `project_type`, `municipality`, `building_use`, `floor_count` ve benzeri uygulanabilirlik bilgileri yetersizse `REVIEW_REQUIRED`/`INSUFFICIENT_EVIDENCE`.
3. **Mevzuat sürümü:** Yayımlanma tarihi, yürürlük tarihi, değişiklik ilişkisi, istisna, ek/geçici madde, yürürlükten kaldırma ayrı alanlardır. Değişiklik taslak değil yürürlükteki kaynakla bağlanır.
4. **İki ayrı model fazı:** OCR ve VLM GPU'da **eşzamanlı çalışmaz**. Ayrı süreç/memory gate, çıktı kaydı ve süreç kapatılarak VRAM serbest bırakma yaklaşımı tasarlanır. Sadece `gc.collect()`/`empty_cache()` ile GPU belleğinin kesin boşaldığı varsayılmaz.
6. **Donanım uyumu:** Eski ağır GPU OCR fikri tasarımda değerlendirildi, fakat yeni mimaride yalnız CPU RapidOCR bulunur. Test edilmemiş model uyumuna PASS verilmez.
7. **Az bağımlılık:** SQLite FTS5 + yerel embedding ve basit vektör indeks ilk sürüm için yeterli; FAISS veya harici vektör sunucusu zorunlu değil. Reranker sonradan opsiyonel.
8. **Mahremiyet:** Kamuya açık depoya özgün telifli standart PDF'leri, model ağırlıkları, gerçek mimari müşteri paftaları, kullanıcı verileri veya gizli mevzuat indeksleri taşınmaz. Lisans hakkı ayrı incelenir.
## 4. Tasarlanacak kaynak ve karar belgeleri
- `docs/sistem-mimarisi.md`: iki kanıt kanalı, teknik akış, kullanıcı deneyimi, mimarın ilk beş tipik kontrol grubu, modül sınırları ve sade dizin ağacı.
- [OCR ve bellek tasarımı](ocr-ve-bellek.md): native PDF metni, CPU OCR, ROI ve kaynak konum sözleşmesi.
- `docs/mevzuat-rag.md`: mevzuat belge envanteri, AST, amendment graph, lexical/dense hybrid + RRF, kaynak piksel kutusu ve kullanıcı önizleme sözleşmesi.
- `docs/kararlar.md`, `docs/kapsam.md`, `docs/modul-plani.md`, `docs/teknik-gereksinimler.md`, `README.md`: kapsam ve doküman bağlantıları yeni kararlarla güncellenecek. Önceki işlem numaraları ve başarı iddiaları korunacak.
- `.gitignore`: yerel yönetmelik asılları, parse çıktı, indeksler ve model cache'leri için güvenli varsayılanlar.
## 5. Uygulama sınırı
Bu istek, **mimari tasarım ve dosya planı güncellemesi** olarak ele alınır. Yeni `src` altında boş/stub kod, model indirme, sistem benchmark'ı, yasal kural eşiği veya resmî mevzuat metni eklenmez. İlk geliştirme işi bir sonraki işlem numarasıyla başlayacaktır.
## 6. Açık kararlar
- İlk uygulanacak DXF/PDF format sırası ve mimari çizim veri örneği.
- Kesin OCR motorlarının Windows/offline kabulü ve 8 GB GPU VLM benchmark'ı henüz açık.
- Mevzuat kütüphanesinin güncel ve yürürlükte olan belge listesi, erişim ve yayın hakları.
- Kontrollerin kategorileri belirlendi ama **mevzuat eşikleri ve otomatik PASS** yok.
- UI türü (PySide6 vs localhost web) ve belge görüntüleme uygulaması nihai kararı.
## 7. Uygulama kaydı
**Son durum: UYGULANDI — dokümantasyon ve tasarım; kod geliştirme yapılmadı.**
### Bu istek kapsamındaki GitHub değişiklikleri
| Dosya | Sonuç | Commit |
| --- | --- | --- |
| `docs/islem_003.md` | Uygulamadan önce işlem kaydı | `5fe3c71` |
| `docs/sistem-mimarisi.md` | İki kaynaklı kanıt grafı, mimari kullanıcı senaryoları, sade modül ağacı | `e260d39` |
- [OCR ve bellek tasarımı](ocr-ve-bellek.md): native PDF metni, CPU OCR, ROI ve kaynak konum sözleşmesi.
| `docs/mevzuat-rag.md` | LegalAST, sürüm/yürürlük/istisna, retrieval ve özgün PDF page/span | `e08f863` |
| `docs/kararlar.md` | K-017–027 kararları: kesin vs ölçüm bekleyen ayrımı | `d73b95e` |
| `docs/kapsam.md` | Beş mevzuat ailesi, ikili kanıt ve kapsamın güncellenmesi | `c2c31cb` |
| `docs/teknik-gereksinimler.md` | FR-019–028 ve NFR-013–016 ek gereksinimleri | `21c03f9` |
| `docs/modul-plani.md` | R0–R3 ve OCR GPU kabul kapısı, önceki P0–P10 planıyla entegrasyon | `76faeab`; düzeltme `0a9841c` |
| `README.md` | Kamuya açık proje kapsamı ve belge bağlantıları | `9f65573` |
| `.gitignore` | Mevzuat PDF / ham belge / model / indeks dosyaları Git dışı | `d320c07` |
### Yapılmadı
- `src/` veya `app/` altında analiz, OCR, VLM veya RAG kodu **yazılmadı**.
- Gerçek RapidOCR inference ve hedef Windows donanım testi o işlemde gerçekleştirilmedi.
- Resmî mevzuatların ilgili yıldaki konsolide sürümleri, değişiklikleri ve madde/fıkraları **henüz hukukî olarak doğrulanmadı**.
- Herhangi bir belediye plan notu, özel müşteri verisi, gerçek pafta veya telifli yönetmelik PDF'si **public repoya yüklenmedi**.
- Windows kabul, regression, kaynak/satır OCR bbox doğruluğu ve VRAM testleri **çalıştırılmadı**.
### Sonraki adım
**Sıradaki işlem dosyası `docs/islem_004.md` olacaktır.** İlk kod mühendisliği için öneri: `DrawingIR v0.1` + DXF/PDF source location ve coordinate transform sözleşmesi + ilk sentetik geometri fixture'ları. Bu çekirdek hem çizim hem hukukî belge kanıt zincirine temel olacaktır. `islem_002` ve `islem_003` yeniden numaralandırılmayacak.
