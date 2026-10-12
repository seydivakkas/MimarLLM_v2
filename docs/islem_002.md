# İşlem 002 — Ürün kapsamının kesinleştirilmesi ve teknik plan

- **Tarih:** 2026-10-12
- **Depo:** `seydivakkas/MimarLLM_v2`
- **İstek:** Mimari teknik çizim analizi ve hata tespiti çekirdek ürün olarak belirlensin; pedagojik eğitim portalı ilk ürün kapsamından çıkarılsın. Bu karar işlem kaydına işlensin ve teknik gereksinimler ile aşamalı modül planı oluşturulsun.
- **Durum:** PLANLANDI (işlem kaydı, diğer dosyalardan önce oluşturuluyor)
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

İlk işlem kaydından sonra doldurulacak.
