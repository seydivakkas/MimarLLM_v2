# İşlem 030 — Yerel ve rızaya bağlı sekiz eksenli analitik v0.1

**Sürüm:** 030.0.1 · **Temel:** 028.0.1 rubrik ve 029 pedagojik jüri; ancak **rubrik veya jüri sonuçları otomatik history yazmaz**. **Son fiziksel/insan kabulü:** İşlem 031 / HOLD.

## 1. Mahremiyet tehdidi / veri minimizasyonu

İsim, soyadı, e-posta, TC/öğrenci numarası, okul kayıtları, çizimin tam SHA'sı, orijinal CAD/PDF, DrawingIR/pafta, insan değerlendirme gerekçeleri ve AI/VLM yorumları **analitik SQLite veri tabanına yazılmaz**. Saklananlar:
- 128 bit rastgele koleksiyon erişim anahtarının **SHA-256 özeti** (ham anahtar yalnız oluşturma yanıtında kullanıcıya gösterilir).
- Kaydın bağımsız rastgele ID'si, \`created_utc\`, doğrulanmış **YYYY-GUZ/BAHAR/YAZ** kodlu dönem etiketi; keyfî kişi adı serbest metni yasak.
- Yerel 32 hex proje/run ID (aynı çalışma alanındaki kaynak raporla ilişkilendirilebilir metadata), rubrik sürümü, pilot sınıf, değerlendirilmiş ölçüt adedi, **sekiz eksenin nullable sayısal taslak yüzdesi**, varsa nullable toplam taslak puan. Veri kaynağının görüş notu veya çizim içeriği kopyalanmaz.

Bu, tam anonimlik garantisi **değildir**: yerel proje/run kimlikleri başka dosyalarla ilişkilendirilebilir. Diske yazılan SQLite **şifreli değildir**; dosya ilk oluştuğunda 0600 izin denemesi uygulanır. Windows ACL, başka yerel kullanıcı süreçleri, OS backup/restore, disk şifreleme, güvenli silme ve gerçek öğrenci izinlerinin doğruluğu son İşlem 031'de ayrıca denetlenir. Uygulama tek kullanıcı localhost + CSRF modelidir; çok kiracılı ya da öğrenci hesabı yönetimi değildir.

### Rıza ve saklama
- Varsayılan **OFF**: dashboard açılışı/read-only rubrik analizi bir analitik DB, çerez veya history kaydı oluşturmaz.
- \`POST /api/analytics/history/create\`: \`consent=true\` ve yalnız 30/90/180 gün. 128 bit koleksiyon token'ı kullanıcıya bir kez gösterilir; uygulama onu \`localStorage\`, \`sessionStorage\` veya başka sürekli browser deposuna **yazmaz**. Kullanıcı ayrı güvenli yerde saklar; kayıp token sunucudan geri alınamaz.
- \`POST /api/analytics/history/add\`: **her taslak için yeniden** \`consent=true\`; kullanıcı tarafından seçilmiş project/run'dan *aynı kaynağa bağlı* \`RubricSubmission\` → 028 \`evaluate_rubric\` → minimal veri kaydı. Yeni resmî not, öğrenci profili veya VLM alanı kabul edilmez.
- Limitler: en fazla 20 yerel koleksiyon, her koleksiyonda 24 snapshot, 180 gün maksimum saklama izni, 32 KiB add body. Diğer küçük isteklerde 1024 bayt.
- \`list\`/kayıt ekleme/silme/oluşturma erişiminde **süresi dolmuş koleksiyonlar temizlenir**. Bu erişim-temelli TTL'dir; arka planda zamanlayıcı, Windows hizmeti veya bilgisayar kapalıyken otomatik yürütme **yoktur**. Saklama süresi dolunca sonraki erişimde silinir. Uzun süre açılmayan veri tabanındaki kayıtlar eş zamanlı olarak kaldırılmayabilir; bu 031 veri koruma kabulünde ayrıca ele alınmalıdır.
- \`POST /api/analytics/history/delete\`: explicit confirm_delete=true ile sadece seçilen snapshot silinir.
- \`POST /api/analytics/history/revoke\`: explicit confirm_delete=true ile koleksiyon + kademeli cascade snapshot kayıtları silinir; SQLite \`secure_delete=ON\` ve \`VACUUM\` denenir. Silme **orijinal CAD/PDF/analiz dosyalarını, yedekleri veya dosya sistemi geçmişini silmez**. Adlî güvenli silme garantisi yoktur.
- Koleksiyon anahtarları genel listelenmez; tüm liste/compare/deletion POST gövdesinde doğru token gerektirir; GET URL'den token sızdırılmaz.

## 2. Güvenli kaynak ve skor köprüsü

- İşlem 028'deki \`RubricSubmission\` strict \`human_review_attested=true\`, 0–4 tam sayı/yerel native entity ID/frame/source SHA, rubrik sürümü, sınıf kapsamı ve okunur not sözleşmesi **kaydetmeden önce backend'de yeniden doğrulanır**. Bu, gerçek öğrenci veya öğretmen kimliğinin doğrulandığı anlamına gelmez.
- Yalnız \`evaluate_rubric\` sonucundaki \`AxisOutcome\` düzeylerinden \`DraftSnapshot.axes[Axis]\` elde edilir. 028'de \`NOT_SCORED\` ise genel puan \`null\`; \`NOT_APPLICABLE_BY_LEVEL\` eksenleri \`null\`, **sıfır değildir**. \`official_grade=false\`, \`pedagogical_progress_verified=false\`. "Gerçek iyileşme" veya akademik başarı yönlendirmesi yapılmaz.
- Orijinal DrawingIR, DXF/PDF, \`analysis.json\`, diğer resmî raporlar ve VLM/Jury çıktıları bu işlemle değişmez. Kayıt ayrı \`private-analytics-030.sqlite3\` dosyasındadır.

## 3. API sözleşmeleri

| Endpoint (hepsi POST) | Girdi | Beklenen davranış |
| --- | --- | --- |
| \`/api/analytics/history/create\` | \`consent:true\`, \`retention_days:30/90/180\` | 201, token; varsayılan geçmiş yok |
| \`/api/analytics/history/list\` | \`collection_token\` | 200, minimal snapshot listesi; başka token 404 |
| \`/api/analytics/history/add\` | \`collection_token\`, \`consent:true\`, \`project_id\`, \`run_id\`, \`period_label\`, \`assessment:RubricSubmission\` | 201, gerçek kaynaklı rubrik taslak snapshot; sahte SHA 409 |
| \`/api/analytics/history/compare\` | token + \`before_id\`, \`after_id\` | 200, \`TrendComparison\`; sahte snapshot 404 |
| \`/api/analytics/history/delete\` | token + snapshot ID + \`confirm_delete:true\` | yalnız o kayıt silinir |
| \`/api/analytics/history/revoke\` | token + \`confirm_delete:true\` | analitik koleksiyon iptal edilir |

Her POST mevcut localhost/Host/Origin/CSRF kurallarına tabidir. 413 gövde limiti, 422 şema/rıza, 404 erişim anahtarı veya snapshot bilinmiyor, 409 veri alanı/rubrik kanıt uyuşmazlığı; istemciye hassas yollar veya öğrencinin not metni hata mesajında dökülmez.

## 4. Dönem karşılaştırma ve sekiz eksenli radar

- \`COMPARABLE_DRAFT_ONLY\`: **aynı pilot sınıf ve aynı rubrik sürümü**, her iki kayıtta da bütün etkin kriterler incelenmiş ve 028 taslağı tamamlanmış. \`total_draft_delta\` ve her iki kaydın etkin eksen puan farkları \`Decimal\` ile üretilir. **Puan farkı öğrenme ilerlemesinin veya nedeni bir uygulamanın etkisinin kanıtı değildir**.
- \`NOT_COMPARABLE\`: farklı sınıf/sürüm veya kısmi insan incelemesi; **hiçbir sayısal delta veya karşılaştırma grafiği noktası yayımlanmaz**. Böylece farklı düzeylerin farklı aktif kriterleri yanıltıcı regresyon/ilerleme grafiği oluşturmaz.
- SVG radar: sekiz spokes/kısa ad + kullanıcı erişimine açık satır/tablo; 0–100 raster ölçeği, yerel DOM \`createElementNS\`, URL/CDN yok. **Tam sekiz eksen yoksa kapalı radar poligonu çizilmez**, yalnız mevcut eksen işaretleri çizilir; \`N/A\` asla sıfıra çevrilmez. Örn. 1. sınıfta strüktür ve çevre \`N/A\`.
- Değerler yalnız insan öz-beyanlı kod taslağıdır; resmî öğretim üyesi değerlendirmesi / bağımsız uzman güvenilirliği / hakiki akademik ilerleme doğrulanmış değildir.

## 5. CI ve fiziksel son kabul

\`tests/test_analytics_030.py\`: varsayılan DB yok, geçersiz rızayla DB yok, rastgele token hash only, isim/çizim/notun DB'de olmaması, 8 eksen doğru 0/null, yıl/rubrik/kapsama karşılaştırma ret, silme/rıza iptali, 30 günlük erişim TTL, CSRF, kaynak SHA, sahte VLM alanı, özgün DrawingIR/rapor immutable, local radar UI. Hosted Edge DOM testine analitik panel ve geçmişin başlangıçta boş olması kontrolü eklendi.

**Nihai 031/HOLD:** Gerçek öğrenciden geçerli rıza yönetimi, eğitim etiği, veri sorumlusu/işleme hukuku, kurum rubrik onayı, pedagojik güvenirlik ve adalet; fiziksel Windows 10/11 + Edge + offline EXE + gerçek öğrenci çizimleri. Sentetik CI bu sonuçların yerine geçmez. Üretim yayını ve resmî not oluşturma kapalı.
