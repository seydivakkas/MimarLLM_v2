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


## Gerçekleştirilen kod ve sentetik CI kanıtı

- `analytics/models.py`: zorunlu `consent:true` CREATE ve ADD; 30/90/180 günlük saklama, 128-bit özel erişim token'ı, `YYYY-GUZ/BAHAR/YAZ` kimliksiz dönem etiketleri, `CompareSnapshots` ve sekiz eksenli `TrendComparison`. Resmî akademik not ve doğrulanmış pedagojik gelişim: **false**.
- `analytics/store.py`: hiçbir analitik history çağrısı gelmeden DB yaratılmaz. Yalnız SHA256-token digest, yerel proje/run UUID, dönem ve sekiz nullable 028 rubrik insan-taslak puanı saklanır; insan notu, isim, e-posta, öğrenci numarası, kaynak çizim/rapor veya VLM/Jury metni saklanmaz. SQLite `secure_delete=ON`, `VACUUM` silme, ilk dosya izni `0600`. Yetki/capability token kaybolunca server üzerinden listelenip kurtarılamaz. SQLite **disk şifrelemesi değildir** ve OS yedekleri temizlenmez.
- `analytics/trends.py`: aynı sınıf/rubrik sürümü + her iki tam değerlendirmede `COMPARABLE_DRAFT_ONLY`; aksi `NOT_COMPARABLE`, farklar/null. Sekiz eksen, 1. sınıfta strüktür/iklim N/A. Taslak puan farkı gerçek pedagojik ilerlemenin kanıtı değildir.
- `app/server.py`: `POST /api/analytics/history/{create,list,add,compare,delete,revoke}` tamamı mevcut loopback CSRF/Origin/Host politikasıyla. ADD önce gerçek run'ın özgün DrawingIR SHA/frame/native entity ve 028 insan rubrik incelemesini doğrular. Silme, revocation ve süre aşımı erişim-temellidir; hiçbir varsayılan background silme hizmeti yok.
- `app/static/index.html`, `dashboard.js`, `dashboard.css`: izinle açılan tarihçe, gizli token (browser kalıcı depolaması yok), yeni dönem kaydetme (her seferinde açık onay), kayıt silme/izni geri çekme, yerel SVG sekiz eksenli radar ve ayrıntılı erişilebilir değer tablosu. Tam sekiz eksen yoksa kapalı grafik çizilmez, N/A=0 uydurulmaz. Rıza iptali orijinal CAD/PDF/raporları silmez.
- `tests/test_analytics_030.py`: rıza yokken veritabanı yaratmama, SHA ile anahtar kimliği, kişisel not/kimlik yazılmaması, same-scope/different-year/partial sınırlamaları, JSON schema source/AI sahteciliği, CSRF/413/422, saklama süresi ve revocation, immutable DrawingIR/analiz, HTML ve SVG.
- `scripts/windows/edge_smoke_025.py`: 030 HTML kontrolleri, geçmiş oluşturma izni ve radar panelinin varlığı, varsayılan DB yokluğu.
- `docs/specs/private-analytics-030-v0.1.md`: kabul ve gerçek mahremiyet kısıtları.

### Gerçek CI durumu

Önceki `6bb73e33`/ara UI commit'leri **JavaScript `SyntaxError: missing )`** nedeniyle Core CI başarısızdı; hata `67d0c853` commit'iyle düzeltilip gerçek GitHub-hosted Windows/Ubuntu tekrar koşuldu. [Core CI #38989925319](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38989925319) **SUCCESS**: Windows **404 passed**, Ubuntu **403 passed, 1 skipped** ve `node --check dashboard.js` PASS. Dolayısıyla sentetik sözleşme kabulü bu **düzeltilmiş commit** ve sonraki HEAD doğrulamasına dayanır; erken kırmızı sonuçlar saklanıp doğru biçimde açıklanmıştır.

[Bağımlı Draft PR #8](https://github.com/seydivakkas/MimarLLM_v2/pull/8): `feature/islem-030-private-analytics` → 029 dalı (PR #7); PR #2/#4/#5/#6/#7 Draft kalır. `main` ve üretim değişmedi.

**Son karar:** `030_MÜHENDİSLİK_KOD_ADAYI / SENTETİK_CI_PASS`; `REAL_STUDENT_CONSENT_HOLD`, `ACADEMIC_FAIRNESS_AND_VALIDITY_HOLD`, `WINDOWS_EDGE_EXE_PHYSICAL_UAT_HOLD`, `LEGAL_F08_F12_HOLD`. Geçerli rızanın gerçekten öğrenciye ait olması, örneklem/adalet, uzmanlar arası kıyas, Windows ACL/backup ve offline paket son İşlem 031'de değerlendirilecek.

**Sıradaki tek geliştirme aşaması:** İşlem 031 — fiziksel Windows 10/11 + gerçek Edge, gerçek mimari DXF/PDF, çevrimdışı .exe, 2.5D GPU/VRAM, MMProj model uygunluğu, uzman pedagojik doğrulama, hukuki kaynak bağlantısı ve kişisel veri koruma nihai kabul kapısı. `docs/islem_031.md` yeni dalın koddan önceki ilk kaydı olacaktır.
