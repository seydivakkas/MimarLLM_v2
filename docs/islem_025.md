# İşlem 025 — Kaynak-bağlı 2B inceleme ve sınırlı iş kuyruğu

- Tarih: 2026-10-16
- Durum: GELİŞTİRME / KABUL BEKLİYOR
- Dal: `feature/islem-025-source-2d-jobs`; hedef `main`.
- Ön koşul: İşlem 019 dashboard, İşlem 022 kaynak bozmayan CAD onarım adayları, İşlem 023 kaynaklı PDF OCR, İşlem 024 yerel RAG cache.
- İlk işlem kaydı: Bu dosya yeni dalda ilk kod/doküman yazımıdır. Tarihsel `islem_001.md`–`islem_024.md` değiştirilmez.

## Hedefler
1. Mevcut DXF/PDF analiz çıktısını bozmadan 2B kaynak-native LINE/PDF_LINE üzerinden **salt okunur** çizim görselleştirme, frame/katman filtresi, özgün CAD handle/entity ID ve belge SHA kanıt odaklaması. SVG çizim üzerinde yapılan seçimler orijinal DrawingIR, PDF veya CAD dosyasını değiştirmez. Kanıtla doğrulanmayan semantik çizgiye oda/kapı/kolon adı verilmez.
2. Bir kullanıcı için **tek çalışan iş ve küçük sınırlandırılmış bekleme kuyruğu**; POST ile anonim ancak aynı uygulama oturumundan erişilen iş kimliği, GET ile durum sorgusu. İlerleme, yalnız gerçekten bilinen `QUEUED/RUNNING/COMPLETED/FAILED` ayrımını verir; sahte yüzde veya aşama süreleri yok. İş kimlikleri ve yerel SHA izolasyonu korunur.
3. Mevcut `POST .../runs` senkron istemci sözleşmesi, HTTP CSRF/Origin/Host/loopback sınırları ve sonuç dosyaları geriye dönük kırılmayacak. Önceki kaynak rapor ve kalibrasyon davranışı korunacak. İstemci yeni iş API'sini kullanır.
4. Yeni sentetik regresyon: kapasite, aynı anda çalışan iş, iki proje arasında bağlam/sınıf karışmaması, değişmiş kaynak SHA'sı, durum erişimi, yasal HOLD ve 2B statik UI/CSP/XSS sözleşmeleri. Ubuntu/Windows CI başarılı olmadan kapalı sayılamaz.

## Kapsam dışında
- DXF üzerinde kalıcı edit, onaylanmamış oda/geçiş semantiği veya model yaratma.
- 2.5D/Three.js, GPU/VLM, gerçek pedagojik puan, jüri, resmî mevzuat PASS.
- Kullanıcının fiziksel Windows 10/11/Edge/gerçek A0 pafta/kullanıcı kabulü; İşlem 031'e taşınır.
- Harici ağ, CDN, telemetri, SaaS ve ek ücretli API.

## Son kapı
Dalların kod/test değişiklikleri, CI sonuçları, bilinen eksikler ve gerçek PR özeti bu dosyaya işlemin sonunda işlenecektir. Gerçek kanıt olmadan `KAPATILDI` yazılamaz.
