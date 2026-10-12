# İşlem 002 — Ürün kapsamının kesinleştirilmesi ve teknik plan

- **Tarih:** 2026-10-12
- **Depo:** `seydivakkas/MimarLLM_v2`
- **İstek:** Mimari teknik çizim analizi ve hata tespiti çekirdek ürün olarak belirlensin; pedagojik eğitim portalı ilk ürün kapsamından çıkarılsın. Bu karar işlem kaydına işlensin ve teknik gereksinimler ile aşamalı modül planı oluşturulsun.
- **Durum:** UYGULANDI (dokümantasyon; yazılım geliştirme yapılmadı)
- **İş türü:** Ürün kapsamı + teknik tasarım / dokümantasyon. Henüz kod geliştirme değil.

## 1. Kesinleşen ürün kararı

**MimarLLM V2 = Yerel Mimari Teknik Çizim Analizi ve Hata Tespiti Sistemi.**

Bir kullanıcı tek Windows bilgisayarında çizim dosyası açar; sistem teknik çizim elemanlarını çıkarır, birim ve koordinatlarını doğrular, geometri/topoloji hesaplarını yapar, belirlenmiş teknik kontrol kurallarına göre olası hataları ve eksikleri konumları ve gerekçeleriyle raporlar.

**İlk ürün kapsamı dışında:** pedagojik eğitim portalı (LMS), öğrenci ilerleme ve sınıf yönetimi, öğretmen hesapları, jüri karakterleri, otomatik not verme, çoklu AI agent mimarisi, bulut AI API hizmetleri, generatif mimari proje üretimi. Bu alanlar kaynak kod ve menülerde varsayılan modül olarak açılmaz.

**Kesin teknik sınırlar:** Windows, Intel i7 14. nesil, 32 GB RAM, NVIDIA RTX 4070 8 GB VRAM, tek bilgisayar, yerel çıkarım; model için internet/API çağrısı yok. Public depoya kullanıcı çizimleri, gerçek veritabanları, model ağırlıkları veya özel veriler girmez.

## 2. Sınırlandırılmış ilk kullanıcı akışı

1. Yerel çizim dosyasını seç (ilk dosya türü ve sırası teknik planda **öneri** olarak ele alınır).
2. Güvenli içe alma ve format/ölçek/birim tespiti yap; belirsizliği kullanıcıya bildir.
3. Geometrik elemanları ortak bir çizim veri modeline dönüştür.
4. Ölçülebilir ve uygulanabilir denetimleri deterministik motorla gerçekleştir.
5. Şüpheli geometri, eksik veri ve doğrulanabilen ihlalleri plan üzerindeki koordinatlarıyla göster.
6. İhlal/uyarı listesini ölçüm, kural sürümü ve kanıt bağlantısıyla raporla.
7. Gerekli ise, OCR/VLM yalnızca etiket/nesne **adayı** üretir; ölçüm veya düzenleyici `PASS` üretmez.

## 3. Bu istekle oluşturulacak / güncellenecek belgeler

- `docs/teknik-gereksinimler.md`: FR/NFR tanımları, girdi/çıktı sözleşmesi, doğruluk/kanıt/VRAM ve offline sınırları, kabul kriterleri.
- `docs/modul-plani.md`: modül sınırları, bağımlılıklar, P0–P9 iş paketleri, her aşamanın çıktısı ve kabul koşulu.
- `docs/kararlar.md`: K-007 kesinleştirme, K-008 kapsam dışı kararı, diğer açık kararları koruma.
- `docs/kapsam.md`: ürünün birincil akışı ve kapsam dışı özellikleri açık belirtme.
- `README.md`: ana ürün tanımı ve belgelerin bağlantıları.

**Önemli:** Kullanıcının bu mesajı giriş formatını, kesin UI teknolojisini, belirli modeli, mevzuat kapsamını veya test performans eşiğini belirlemedi. Bu konular öneri olarak yazılır, kesin karar olarak işaretlenmez.

## 4. Mühendislik yaklaşımı

- Modüler monolit; gereksiz agent, servis, sürekli açık DB sunucusu yok.
- `DrawingIR` (iç çizim temsili): birimler, koordinat çerçevesi, dönüşüm, kaynak dosya ve sayfa, nesne kimliği, kaynak geometrisi ve güven derecesi.
- Ölçüm ve teknik doğrulama: kaynak ile ölçüm değerini bağla; ölçek yoksa metre/m² cinsinden kesin çıktı verme.
- OCR/VLM: isteğe bağlı yerel semantik yardımcı katman; belirsiz adaylar onay gerektirir.
- Sonuç semantiği: `PASS`, `FAIL`, `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE`, `NOT_APPLICABLE`, `ERROR`. Yalnız açık ölçüt ve yeterli veri ile `PASS`/`FAIL`.
- Kurallar: kimlik, sürüm, uygulanabilirlik koşulu, geometri girdileri, eşik, tolerans, kaynak, yürürlük ve değerlendirme izi; mevzuat uygunluğu yalnız doğrulanmış sürümlerle.
- Rapor: dosya SHA-256, analiz zamanı, yazılım/kural sürümü, koordinat/nesne bağlantısı, karar ve eksik kanıt.

## 5. Kabul ve iş akışı

Bu işlem ancak belgeler GitHub'da oluşturulup okuyarak doğrulandıktan ve işlem kaydı uygulama sonuna güncellendikten sonra `UYGULANDI` sayılabilir.

Kod, AI modeli, arayüz ve gerçek donanım testi kapsam dışında; çalıştırılmış gibi yazılmayacak. Bir sonraki geliştirme isteği için **önce** `docs/islem_003.md` oluşturulacak.

## 6. Uygulama sonuçları

**Uygulanan GitHub işlemleri (2026-10-12, `main`):**

1. Bu işlem kaydı, diğer değişikliklerden **önce** oluşturuldu: commit `53f6265`.
2. `docs/teknik-gereksinimler.md` oluşturuldu: 18 fonksiyonel (FR), 12 fonksiyonel olmayan (NFR) gereksinim; `DrawingIR` / `Finding` taslakları; karar durumu semantiği; kabul senaryoları. Commit `66ee2ee`.
3. `docs/modul-plani.md` oluşturuldu: sorumluluklar, modül bağımlılıkları, P0–P10 iş paketleri, riskler ve ilk çalışan MVP. Commit `5a760d8`.
4. `docs/kararlar.md` güncellendi: mimari çizim hata analizi K-007 **KESİN**, pedagojik/LMS dışlaması K-008 **KESİN**, otomatik jüri dışlaması K-013 **KESİN**, deterministik kontrol K-014 **KESİN**. Diğer açık kararlar açık kaldı. Commit `8e0ff48`.
5. `docs/kapsam.md` güncellendi: ilk ürün kapsamı, kapsam dışı özellikler, ilk kullanıcı akışı, ölçüm ve mevzuat sınırları. Commit `7feb792`.
6. `README.md` güncellendi: ürün tanımı ve belge bağlantıları, çalışma durumu. Commit `a56db85`.

**Yapılmayan işlemler:** `src/` altında uygulama kodu, VLM/OCR kurulumu, UI tasarımı, Windows paketlemesi ve benchmark. Çalışan ürün veya test `PASS` iddiası yok.

**Açık teknik kararlar:** İlk formatın DXF olup olmayacağı; arayüz türü; modellerin kesin sürüm ve lisansları; ilk kontrol kümesi ve tolerans profili; mevzuat kurallarının kapsamı. Bunlar dondurulmadı ve ürün kararıymış gibi uygulanmayacak.

**İşlem 002 kabulü:** Belgelerin GitHub'da varlığı ve birbirine bağlantıları son kontrolle doğrulanacak; kod testi bu işlem kapsamına dahil değil.

**Sıradaki istek protokolü:** Yeni geliştirmeye başlanmadan `docs/islem_003.md` oluşturulacak.

## Sonraki mimari karar bağlantısı (2026-10-12)

Bu işlemde kesinleştirilen **mimari çizim hata analizi** ürün kapsamı değişmedi. PDF metin, raster görüntüleme ve OCR teknolojileri daha sonra [İşlem 005](islem_005.md) kapsamında **pdfplumber + pypdfium2 + RapidOCR/ONNX Runtime CPU** olarak kesinleştirildi. [ADR-002](adr/ADR-002-PDF-Engine-License.md) geçerli teknoloji kaydıdır. Bu bölüm geçmişteki kayıtların numarasını veya orijinal kapsam kararını değiştirmez.
