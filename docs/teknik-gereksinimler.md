# MimarLLM V2 — Teknik Gereksinimler v0.1
- **Bağlı işlem:** [islem_002.md](islem_002.md)
- **Tarih:** 2026-10-12
- **Durum:** **TASARIM / uygulama yok**
- **Çekirdek ürün (kesin):** Yerel mimari teknik çizim analizi ve hata tespiti
- **Kapsam dışı (kesin):** Pedagojik portal, LMS, sınıf/öğrenci yönetimi, otomatik jüri puanı, çoklu AI agent mimarisi
- **Hedef platform (kesin):** Windows, i7 14. nesil, RTX 4070 8 GB VRAM, 32 GB RAM; tek bilgisayar; çalışma anında bulut AI veya ücretli servis API'si yok
## 1. Ürün görevi ve ölçülebilir sınırlar
### Birincil kullanıcı işi
Mimar/teknik çizim hazırlayan kullanıcı, bir planı **yerelde** açarak tespit edilebilen teknik çizim kusurlarını ve ölçülebilir tutarsızlıkları dosya üzerinde işaretlenmiş konumları, verileri, açıklamaları ve güven/eksik veri durumlarıyla görmek ister.
İlk somut senaryo **önerisi**: tek kat mimari plan DXF dosyası -> ölçek/birim doğrulama -> duvar-açıklık/kapı/oda/ölçü adaylarını çıkarma -> seçili teknik kontroller -> görsel işaretleme -> JSON/HTML/PDF raporu. **DXF önceliği, çıktı biçimleri, kesin kural seti ve ilk kullanıcı profili henüz kullanıcı tarafından dondurulmadı.**
### Doğruluk ilkesi
- Çizimin geometri ve yazıları veri, modelin görsel yorumu ise **hipotez** olarak ele alınır.
- VLM bir elemanı “kapı” diye etiketledi diye kesin kapı sayılmaz. Geometrik ve/veya kullanıcı doğrulaması gerekir.
- Ölçek veya dönüştürme güvenilir değilse ölçüm sonucu kesin metre/m² olarak raporlanmaz.
- “Çizim kontrolü” ile “mevzuat/yönetmelik uygunluk sertifikası” farklı şeylerdir; ikincisi kapsam doğrulanmadan iddia edilmez.
- Bir uyum kararı yalnız doğru düzenleme sürümü, uygulama bağlamı, geometrik kanıt ve açık tolerans ile verilir.
- Algoritma `PASS` veremiyorsa veya gerekli veri eksikse bu açıkça belirtilir; sessiz başarı yok.
## 2. Fonksiyonel gereksinimler (FR)
| ID | Gereksinim | Öncelik | Kanıt / kabul gözlemi |
| --- | --- | --- | --- |
| FR-001 | Yerel dosyayı güvenli şekilde açma; tip, boyut ve format kontrolü | Çekirdek | Hatalı/bozuk dosyada kontrollü hata |
| FR-002 | Kaynak dosya için SHA-256, işleme kimliği, sürüm ve zaman damgası üretme | Çekirdek | Her raporda aynı girdiyle eşleşen hash |
| FR-003 | Vektör çizimde entity/katman, koordinat ve ilişki çıkarma | Çekirdek | Nesneler kaynak kimliğine/konumuna geri bağlanır |
| FR-004 | Ölçek, birim ve koordinat sistemi için açık `CONFIRMED/INFERRED/UNKNOWN/CONFLICT` modeli | Çekirdek | `UNKNOWN` iken ölçü mevzuat hükmü verilmez |
| FR-005 | Katman adı, blok ve geometri bazlı mimari eleman adayları üretme | Çekirdek | Her aday sınıflandırma kaynağıyla kayıtlı |
| FR-006 | Geometrik tutarlılık kontrolü: dejenere, kopuk, çakışık ve yinelenen eleman adayları | Çekirdek | Her bulgu için nesne/konum ve tolerans |
| FR-007 | Oda sınırı ve topoloji analizi; belirsiz duvar/kapı ilişkisini işaretleme | Çekirdek | Açık sınır otomatik “geçerli oda” sayılmaz |
| FR-008 | Ölçülebilir kontrol kuralı çalıştırma ve uygulanabilirlik değerlendirme | Çekirdek | Kural ID, sürüm, koşul ve hesap izi kaydedilir |
| FR-009 | Kanıt tabanlı durum sınıflandırması ve açıklama | Çekirdek | Her bulguda status+reason+evidence |
| FR-010 | Bulguları çizim üzerinde işaretleme; konuma geri gitme | Çekirdek | Rapor/arayüzden plan elemanı bulunur |
| FR-011 | İnceleme düzeltmesi: kullanıcı birim, eleman sınıfı ve belirsiz eşleştirmeyi onaylayabilir | Çekirdek | Onayın kim/ne/zaman/önce-sonra izi var |
| FR-012 | Bulguları yerel JSON ve okunabilir rapor olarak dışa aktarma | Çekirdek | Aynı analiz kimliği ve kaynak eşleşir |
| FR-013 | Görüntü/PDF üzerinde yerel metin ve ölçü anotasyonu çıkarma | Aşamalı | OCR bbox, metin, kaynak sayfa ve güven kaydedilir |
| FR-014 | Yerel VLM ile mimari nesne/etiket adayı çıkarma | Aşamalı | Model, sürüm, kaynak kırpım, aday ve doğrulama durumu |
| FR-015 | Çelişen kanıtları uzlaştırma; `REVIEW_REQUIRED` üretme | Aşamalı | VLM/çizim çelişkisinde otomatik kesin hüküm yok |
| FR-016 | Sürümlü, doğrulanmış mevzuat/standart kaynaklarına bağlanan kural havuzu | Sonraki | Resmî kaynak ve yürürlük teyidi olmadan “uyumlu” yok |
| FR-017 | Yerel geçmişte yeniden açma, tekrar değerlendirme ve rapor karşılaştırma | Sonraki | Rapor girdileri ve kural sürümleri geri izlenebilir |
| FR-018 | Tek kullanıcı yerel arayüz / ilerleme / iptal / hata bildirimi | Çekirdek | Görev iptal ve yetersiz VRAM durumu açıklanır |
**Girdi formatları için öneri (kesin karar değil):** P1'de DXF; P4'te vektörel PDF; P5'te taranmış PDF/PNG/JPEG. DWG/IFC, izinli dönüştürücü ve format doğrulaması sonrasında ayrı karar. CAD geometri nesnelerini bir metin modelinden üretmek ilk hedef değildir.
## 3. Veri sözleşmeleri — taslak
### DrawingIR v0
- `drawing_id`, `source_sha256`, `source_name` (özel yol/kimlik bilgisi dışa sızdırılmadan), `source_type`, `parser_version`
- `pages_or_views[]`: PDF sayfa no / DXF modelspace-layout, görüntü boyutları
- `coordinate_frames[]`: kaynak koordinat sistemi, birim, scale-to-metre, eksen yönleri, dönüşüm ve kalibrasyon durumu
- `entities[]`: `entity_id`, `source_ref` (DXF handle / PDF path / OCR bbox), `type_candidate`, `geometry`, `layer`, `attributes`, `provenance`
- `topology[]`: oda/duvar/kapı-aday ilişkileri, ilişkilerin dayandığı geometriler
- `annotations[]`: OCR text, image crop ref, konum ve doğrulama
- `issues[]`: parse/kalibrasyon/kanıt eksiklikleri
**Değişmezler:** tüm ölçümlerde açık birim; `entity_id` sabit ve çakışmasız; PDF piksel ve CAD dünya koordinatları birbirine dönüşümsüz karıştırılmaz; kaybolan kaynak bağlantısı kesin karar üretemez.
### Finding / Evidence v0
```json
{
  "finding_id": "f-0001",
  "check_id": "geometry.open-boundary",
  "check_version": "0.1",
  "status": "REVIEW_REQUIRED",
  "entity_ids": ["e-001", "e-002"],
  "source_locations": [{"view_id": "modelspace", "bbox": [10, 12, 15, 18], "unit": "drawing_unit"}],
  "measurements": [],
  "rule_inputs": {"tolerance": 0.001, "tolerance_unit": "drawing_unit"},
  "evidence": [{"type": "geometry", "ref": "e-001"}],
  "reason_code": "UNRESOLVED_GAP",
  "source_sha256": "<hex_sha256>",
  "confidence_kind": "measured_or_inferred",
  "review_required": true
}
```
Bu JSON yalnız sözleşme örneğidir; çalışır kod veya gerçek analiz çıktısı değildir.
### Durum sözlüğü
| Durum | Kesin anlamı |
| --- | --- |
| `PASS` | Bu **tanımlı ve uygulanabilir** kontrol, doğrulanmış girdilerle geçti |
| `FAIL` | Bu kontrol doğrulanmış verilerle ihlal belirledi |
| `INSUFFICIENT_EVIDENCE` | Ölçek, kaynak, ölçüm veya bağlam yetersiz |
| `REVIEW_REQUIRED` | Çelişen/olasılıklı bulgu, kullanıcı kararı gerekli |
| `NOT_APPLICABLE` | Kuralın açık uygulanabilirlik koşulları sağlanmıyor |
| `ERROR` | Parse, inference veya kural yürütme hatası; **PASS değildir** |
## 4. Fonksiyonel olmayan gereksinimler (NFR)
| ID | Kısıt | Ölçüm / geçiş şartı |
| --- | --- | --- |
| NFR-001 | Gerçek çevrim dışı çalışma | Model ağırlıkları önceden yereldeyken, ağ bağlantısı kapalı analiz tamamlanmalı |
| NFR-002 | Çalışma anında sıfır bulut AI API'si/telemetri | Kaynak taraması ve ağ çıkış gözlemiyle dış istek bulunmamalı |
| NFR-003 | RTX 4070 8 GB hedefi | Model ve görsel bellek bütçesi ölçülmeli; OOM'da kontrollü iptal/CPU yolu |
| NFR-004 | 32 GB sistem RAM hedefi | Bellek zirvesi ve veri seti büyüklüğü Windows'ta ölçülerek belgelenmeli |
| NFR-005 | Deterministik çekirdek | Aynı normalize girdi + kural sürümü + tolerans -> aynı geometrik bulgular |
| NFR-006 | Kaynak izlenebilirliği | `FAIL` bulgusu dosya, çizim konumu, ölçüm ve kural sürümüne bağlanmalı |
| NFR-007 | Güvenli yerel veri | Kullanıcı çizimleri ve çalışma DB'si public Git deposundan uzak |
| NFR-008 | Güvenli dosya işleme | Boyut/sayfa/nesne sınırları, dizin geçişi engeli, kontrollü parser hatası |
| NFR-009 | Tek kullanıcılı modüler monolit | Zorunlu bulut/Redis/Neo4j/Postgres/çok ajan hizmeti yok |
| NFR-010 | Lisans uygunluğu | Yerel VLM, OCR, kütüphane ve dağıtım lisansları yayınlamadan doğrulanacak |
| NFR-011 | Tutarlı karar raporu | Analiz kimliği, kullanılan sürümler, eksik kanıtlar raporda yer almalı |
| NFR-012 | Reproducibility | Deterministik modda sıralama, tolerans, model kimliği ve analitik parametreler kayıtlı |
**Henüz sayı sözü verilmeyen hedefler:** saniye/sayfa, VRAM zirvesi, geometrik precision-recall, oda tespiti başarısı, OCR doğruluğu ve LLM gecikmesi için ilk sentetik baseline ve hedef bilgisayardaki ölçümlerden sonra kabul eşiği belirlenecek. Sabit benchmark olmadan “optimize” ifadesi kullanılmaz.
## 5. Hata tespiti katmanları
1. **Seviye G0 — Geometri bütünlüğü:** sıfır uzunluk, aynı geometriyi tekrar etme, açık sınır, geçersiz poligon, kırık bağlantı; ölçülebilir ve CAD tabanlı.
2. **Seviye G1 — Mekânsal tutarlılık:** oda kapatma, kapı/duvar/açıklık ilişkisinde belirsizlik, erişim grafı; örneklerde doğrulama.
3. **Seviye G2 — Teknik kontrol:** kullanıcı tarafından onaylanmış kural setine göre ölçü ve eşiğe dayalı bulgu; proje tipi bağlamı gerekli.
4. **Seviye G3 — Görsel/OCR semantiği:** etiket, sembol ve sayı adayları; tek başına nihai `PASS` veya `FAIL` üretmez.
5. **Seviye G4 — Mevzuat:** doğru kaynak/sürüm/yürürlük doğrulaması gerçekleşirse sınırlı kural karşılaştırması; resmî onay değildir.
G0/G1 de hatalı çizimi kesin biçimde teşhis edeceğini iddia etmez; eşiğe ve sınıflandırma belirsizliğine göre `REVIEW_REQUIRED` üretebilir.
## 6. Güvenlik ve bağımlılık politikası
- Offline paket normal çalışmada internete bağlanmayacak; model indirme yalnız ayrı, açık kullanıcı kararıyla hazırlık sürecinde olabilir.
- `.env` / kullanıcı dosyaları / model ağırlıkları / SQLite verileri Git'e işlenmez; `.gitignore` tek başına güvenlik taraması yerine geçmez.
- Varsayılan `localhost` API gerekiyorsa loopback ile sınırlanır; yerel ağda servis açılmaz.
- Harici AI servisleri, çoklu model ajanları, uzaktan görev kuyruğu ve otomatik bulut fallback yok.
- Geometri ve rapor çekirdeğinin yerel VLM yokken de anlamlı sonuç üretmesi beklenir.
- Her modül erişilebilir olmama durumunu açık bildirir, hatayı gizleyip sessiz başarı döndürmez.
## 7. Kabul senaryoları (tasarım)
- S01: Birim bilgisi eksik DXF -> ölçüye bağlı `PASS`/`FAIL` yerine kalibrasyon uyarısı.
- S02: Çakışan çizgiler / kopuk oda kenarı -> koordinatlı bulgu veya inceleme isteği.
- S03: Aynı çizim ikinci kez -> normalleştirilmiş geometri ve kurallarda aynı bulgu seti.
- S04: VLM “kapı” diyor, vektör kanıtı yok -> aday ve `REVIEW_REQUIRED`.
- S05: Taranmış PDF'de OCR ölçü sayısı belirsiz -> kesin boyut hükmü yok.
- S06: Kuralın sürümü/yürürlüğü bilinmiyor -> yasal uyum `PASS` yok.
- S07: GPU belleği yetersiz -> OOM kaynaklı çökme yerine kontrollü alternatif/hata.
- S08: Ağ bağlantısı kesik -> yerel modeller önceden kurulmuşsa temel analiz sürer.
- S09: İçe alınan dosya bozuk/çok büyük -> uygulama hata bildirir, mevcut veri korunur.
- S10: Rapor bulgusu -> çizimde aynı kaynak koordinatı/nesneye geri dönüş.
**Not:** Bunlar uygulanmış veya çalıştırılmış testler değil, ilerideki kabul sözleşmeleridir.
## 8. Açık tasarım kararları
- İlk sürümün kullanıcısı: mimar/teknik ofis/öğrenci? Teknik çizim analizi amacı **kesin**, kullanıcı personası henüz kesin değil.
- Kesin ilk dosya formatı: DXF önceliği önerilir; vektörel PDF ve taranmış PDF faz sırası henüz dondurulmadı.
- Masaüstü `PySide6` veya localhost web UI tercihi açık; ikisi birden başlangıçta kurulmaz.
- İlk 5–10 ölçülebilir kontrolün tam tanımı ve toleransı sonraki işlemde tasarlanacak.
- Yerel OCR/VLM model sürümü, lisans, runtime, nicemleme ve VRAM benchmark'ı yapılmadan kesin seçim yapılmaz.
- DWG/IFC ve mevzuat uyumluluk kapsamı ayrı iş/karar konusu.
**Son durum:** Gereksinimler tanımlandı; uygulama, model kurulumu ve canlı performans kabulü başlatılmadı.
## 9. İşlem 003 — OCR ve hiyerarşik hukukî kanıt gereksinimleri (ek)
Önceki FR-001…018/NFR-001…012 gereksinimleri geçerlidir. Aşağıdakiler, tasarım kapsamına eklendi; **kodlanmış değil**:
| ID | Yeni gereksinim | Kabul niyeti |
| --- | --- | --- |
| FR-019 | DXF ve PDF için 2 ayrı source location / coordinate frame taşı | Bulgu hem çizimde hem kanıtta özgün koordinata geri gidebilsin |
| FR-020 | OCR çıktısında blok/satır/çokgen/okuma sırası ve tablo hücre koordinatları sakla | Aynı PDF hash'i ve sayfa alanı yeniden açılabilir |
| FR-021 | PDF'de önce native text, gerekiyorsa yerel OCR; aynı GPU'da çakışma yok | Çıktı modeli/motoru ve kaynak koordinatı kayıtlı |
| FR-022 | Özgün mevzuat belgesi için SHA-256, yayımlanma/yürürlük, menşe ve yetki meta-verisi tut | Farklı sürümler karışmaz |
| FR-023 | Bölüm, madde, fıkra, bent, geçici madde, ek, tablo/alt hücre AST kur | Her node `source_span` ve üst düğüme sahiptir |
| FR-024 | Değişiklik, yürürlükten kaldırma, istisna, atıf grafını tut | Çözümlenmemiş ilişki kaynak güvenini azaltır; PASS yok |
| FR-025 | SQLite FTS5 + CPU dense embedding + RRF hibrit arama | Adaylar kanıt ID ile dönmeli; retrieval score = legal confidence değil |
| FR-026 | Kural ile mevzuat kaynağı için onaylı binding: tarih/konum/kullanım kapsamı ve hesap | Hukukî PASS yalnız doğrulanmış sürüm ve kapsamla |
| FR-027 | Kullanıcı bulgusunda özgün kaynak PDF sayfa+bbox highlight ve değişiklik/istisna zinciri göster | Sayfa-satır iddiası sadece gerçek kaynak üzerine inşa edilir |
| FR-028 | Kaynak OCR'u belirsizse, sayfa span'i eşleşmiyorsa veya telif/izin uygun değilse güvenli fallback | Sahte atıf ve yanlış hukukî `PASS` yasak |
| ID | Ek fonksiyonel olmayan kısıt | Kabul niyeti |
| --- | --- | --- |
| NFR-013 | Heavy GPU model concurrency = 1; OCR ve VLM ayrı süreç yönetimi | Target GPU gerçek peak VRAM ve süreç kapanışı test edilir |
| NFR-014 | 100% yerel AI ve indeksleme; uygulama çalışma sırasında internete bağımlı değil | Offline testte dış bağlantı gözlenmez |
| NFR-015 | Yerel kullanıcı çizimi ve özgün mevzuat PDF/indeksleri public repo dışında | `.gitignore` + commit içerik denetimi |
| NFR-016 | PDF piksel/point dönüşümü ve OCR türetilmiş satır ID'si sürümlü | Rotasyon/crop/çok sütun ve tablo bbox regresyon testi |
**Kritik iki kapı:** (1) Geometri kanıtı sağlam olsa bile ilgili hukukî kaynağın sürüm ve uygulanabilirliği doğrulanmadıysa mevzuat `PASS` olmaz; (2) OCR “satır” gösterimi varsa bunun türetilmiş bir görüntüleme indeksi olduğu açıkça belirtilir. Asıl bağ madde/fıkra/bent + kaynak PDF sayfa/alanıdır.
Bkz. [Mevzuat RAG](mevzuat-rag.md) ve [Yerel OCR/bellek](ocr-ve-bellek.md).
## 10. İşlem 004 — PDF vektör önceliği ve CPU OCR ekleri
| ID | Gereksinim | Kabul/kanıt |
| --- | --- | --- |
| FR-029 | DXF CAD TEXT/MTEXT/ATTRIB/DIMENSION kaynak kimliği ve dönüşümüyle doğrudan çıkar | Native kaynağın handle/transform izlenebilirliği |
| FR-030 | PDF native text kalitesini sayfa **ve ROI** bazında değerlendir; metin varsa tüm sayfada OCR'ı kör kapatma | Kısmi raster/SHX örneklerinde eksik ROI seçimi |
| FR-031 | pdfplumber `char.matrix`/native bbox ile döndürülmüş yazı yönünü temsil et; gerçek quad için ek koordinat dönüşümü | 45/90/270° PDF fixture |
| FR-032 | RapidOCR ONNX Runtime **CPU** ile çalış; model/version ve confidence/raw text dört köşe polygon döndür | CPU provider doğrulaması, OCR JSON |
| FR-033 | 90/270 ve eğik metin crop/orientation düzeltmesi, inverse transform zinciri | Poligon roundtrip ve döndürülmüş OCR vaka testi |
| FR-034 | Türkçe ve özel mimari semboller `Ø ± ° ²`, rakam, kot ve ölçü değerlerini ayrı doğrula | Character-level CER + critical-token exact-match |
| FR-035 | Mevzuat hazırlığı ayrı offline ETL; OCR/table cell kaynak geometri ile hiyerarşik LegalAST | Orijinal PDF bbox/hücre görseli yeniden açılır |
| FR-036 | OCR motoru unavailable olduğunda native DXF/PDF yetenekleri çalışmaya devam eder | Açık `OCR_UNAVAILABLE` ve kapsamlı fallback |
| NFR-017 | Normal OCR GPU CUDA VRAM ayırmaz; ONNX CPU provider, bounded RAM/CPU thread | Windows'da provider, RAM/CPU, latency gözlemi |
| NFR-018 | Modeller önceden yerelde; çalışma esnasında hiçbir indirme/ağ bağımlılığı yok | İzole ağda OCR + rapor akışı |
| NFR-019 | Rotated text ve pafta dönüşümünden sonra kaynak koordinatını koru | Transform/quad property testleri |
| NFR-020 | Güncel `rapidocr + onnxruntime CPU` motorları kullanılacak | Sürüm/kilit/CPU provider ve model lisans kanıtı |
**Güncel:** PDF/OCR motorları işlem 005 ile kesinleştirildi: pdfplumber + pypdfium2 + RapidOCR CPU; sonuç doğruluğu ve Windows dağıtımı henüz HOLD.
| NFR-021 | PDF okuma ve render, seçili izinli motorlarla sınırlıdır | SBOM/binary yeniden dağıtım kabulü tamamlanmadan ticari PASS yok |
| FR-037 | pdfplumber native glyph+vector, pypdfium2 ROI render kaynağı korunacak | Kaynak PDF bbox/quad testleri |
**Lisans kapısı:** [ADR-002](adr/ADR-002-PDF-Engine-License.md) ve [pdf-lisans.md](pdf-lisans.md).
