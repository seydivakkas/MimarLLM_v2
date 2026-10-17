# İşlem 030 — Açık rızalı yerel proje geçmişi ve sekiz eksenli analitik

**Tarih:** 2026-10-17 · **Durum:** GELİŞTİRME / sentetik CI adayı  
**Yeni dal:** `feature/islem-030-private-analytics`; temel İşlem 029 `feature/islem-029-sequential-jury` (Draft PR #7). **İlk GitHub yazımı bu dosyadır.**

## Hedef ve mühendislik sınırları
1. Öğrenci/incelemeci açık rızası olmadan **analitik geçmişi tutulmaz**. Analiz, rubrik ve jüri çağrıları history yazımını tetiklemez. Yerel kayıt sadece `history/create` ve her bir `history/add` işlemindeki `consent=true` ile oluşabilir.
2. İsim, e-posta, telefon, öğrenci numarası, özgün CAD/PDF, VLM sorusu, insan rubrik notu ve kişisel kimlik verisi **analitik veri tabanına yazılmaz**. Rastgele 128 bit yerel koleksiyon erişim belirteci, yalnız SHA-256 özetiyle veri tabanında eşlenir. Token kaybolursa sistem yeni kimlik uydurmaz veya genel koleksiyonları listelemez.
3. Sekiz boyutun salt kodda hesaplanmış 028 rubrik taslak sonuçları, kaynak run'ı kontrol edildikten sonra kaydedilebilir: `LOCAL_DRAFT_ONLY`, kısmi kaynaklarda `NOT_SCORED`, null eksen değerleri korunur. Yapay zekâ notu, jüri oyu veya resmî not geçmişe alınmaz.
4. Aynı rubrik sürümü ve sınıf seviyesine sahip iki snapshot için **karşılaştırılabilirlik kontrolü**. Farklı sınıf/rubrikte ham delta veya gelişim hükmü yok; aynı sınıfta bile değerler sadece **insan öz-beyanlı taslak puan farklılıklarıdır**, öğrenme etkisi veya gerçek akademik ilerleme kanıtı değildir.
5. Yerel SVG radar, sekiz eksen ve veri olmayanları `N/A` gösterir; eksik eksenleri sıfır olarak çizmez. Yeterli bütünlük yoksa kapalı çokgen yapılmaz. Tamamen çevrimdışı; üçüncü taraf CDN/API yok.
6. Silme: tek kaydı silme, koleksiyon rızasını geri çekerek tüm analitik geçmişi silme, süre bitiminde otomatik son kullanım-temelli temizleme; SQLite `secure_delete=ON` + mümkün olduğunda `VACUUM`. OS yedekleri/gölge kopyaları ve özgün proje/rapor dosyaları **bu işlem kapsamında silinmez**. Fiziksel adli güvenli silme garantisi verilmez.
7. Veritabanı operatör çalışma alanında özel `0600` dosya izinleriyle, başka bir API'ye gönderilmeden tutulur. Çok kullanıcılı/işletim sistemi çapında güçlü hesap izolasyonu bu sürümün kapsamı değildir.
8. Sentetik Windows/Ubuntu testleri: ön-onay yokluğunda dosya yaratmama, token yetkisi, sahte SHA/puan/AI alanı reddi, kapsama ve sınıf karşılaştırılabilirliği, null radar, küçük veri/kayıt sınırı, eski kayıt temizleme/silme, CSRF/immutable DrawingIR/rapor, saf SVG.
9. Gerçek öğrenci verisi/onam yönetimi, fiziksel Windows/Edge/EXE, ergonomi ve pedagojik uzman kabulü **İşlem 031/HOLD**. PR #2/#4/#5/#6/#7 Draft ve `main` korunur.

## Sıra
1. `analytics/store.py` mahremiyet odaklı yerel snapshot deposu.
2. `analytics/trends.py` 028 RubricOutcome şemasından fail-closed karşılaştırma.
3. Salt-okunur kaynaklı run + CSRF ve opt-in API; yerel sekiz eksenli radar arayüzü.
4. CI, testler, sürümlü sözleşme, kararlara işleme ve bağımlı Draft PR.
