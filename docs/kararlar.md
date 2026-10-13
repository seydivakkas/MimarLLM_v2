# MimarLLM V2 — Karar Defteri
Bu belge kesin kararları önerilerden ayırır. Her değişiklik işlem kaydıyla izlenir.
| Kod | Karar | Durum | Kaynak |
| --- | --- | --- | --- |
| K-001 | V1'den bağımsız `seydivakkas/MimarLLM_v2` deposunda geliştirme | KESİN | islem_001 |
| K-002 | Tek bilgisayarda Windows odaklı yerel çalışma | KESİN | islem_001 |
| K-003 | Hiçbir bulut yapay zekâ API'si kullanılmaması | KESİN | islem_001 |
| K-004 | Hedef kaynak sınırı 8 GB VRAM / 32 GB RAM | KESİN | islem_001 |
| K-005 | Gereksiz agent altyapısı olmadan sade modüler mimari | KESİN | islem_001 |
| K-006 | Her geliştirme isteğinden önce sıralı `docs/islem_NNN.md` kaydı | KESİN | islem_001 |
| K-007 | Ana ürün: **mimari teknik çizim analizi ve hata tespiti** | **KESİN** | islem_002 |
| K-008 | **Pedagojik eğitim portalı, LMS, sınıf/öğrenci takibi ilk ürün kapsamında yok** | **KESİN** | islem_002 |
| K-009 | İlk girdi formatları: DXF / vektörel PDF / raster PDF / DWG / IFC sırası | TARTIŞILIYOR | islem_002 |
| K-010 | Arayüzün masaüstü / localhost web biçimi | TARTIŞILIYOR | islem_002 |
| K-011 | Yerel OCR ve VLM modelleri/sürümleri | TARTIŞILIYOR | islem_002 |
| K-012 | Mevzuat denetiminin kapsamı ve geçerli kaynaklar | TARTIŞILIYOR | islem_002 |
| K-013 | Jüri karakterleri ve otomatik öğrenci puanlaması ilk ürünün parçası olmayacak | **KESİN** | islem_002 |
| K-014 | Geometrik ölçüm ve kural denetimi deterministik çekirdekte; VLM yalnız yardımcı | **KESİN** | islem_002 |
| K-015 | İlk 5–10 hata kontrolünün ayrıntılı tanımı ve toleransları | TARTIŞILIYOR | islem_002 |
| K-016 | İlk kullanıcı profili: teknik ofis / mimar / öğrenci | TARTIŞILIYOR | islem_002 |
## Kesinleştirilen kapsam gerekçesi
V1'deki eğitim/portal/jüri/çoklu AI servislerini sürdürmek yerine kullanıcıya ölçülebilir teknik çizim hata bulgularını **kaynak konumu ve kanıtıyla** gösteren tek bilgisayarlık uygulama üretmek. Ürün özellikleri olmayan klasör veya menü şablonları eklenmez. Gelecekte kapsam değişirse yeni işlem kaydı ve kullanıcı kararı gerekir.
## Başlangıç önerileri, henüz karar değil
- **Öneri:** İlk vektör formatı DXF; sonraki aşamalar dijital PDF ve raster PDF.
- **Öneri:** Önce `DrawingIR` + geometri + deterministik kontroller; OCR ve VLM daha sonra.
- **Öneri:** Önce Python çekirdeği ve tek bir yerel arayüz; UI teknolojisi ayrı seçilir.
- **Öneri:** Mevzuat kuralları yalnız kaynak ve yürürlük bilgisi doğrulandığında eklenir.
**İş kuralı:** Kesin olmayan seçenekler fiili iş veya doğrulanmış sonuç gibi gösterilmez. Bir sonraki geliştirme isteğinin kaydı `docs/islem_003.md` olacaktır.
**Depo durumu:** 2026-10-12 tarihinde depo **public** olarak doğrulandı; özel kullanıcı çizimleri, veritabanları, anahtarlar ve model ağırlıkları depoya yüklenmez.
## İşlem 003 — Mimari ve mevzuat doğrulama kararları (2026-10-12)
| Kod | Karar | Durum | Kaynak |
| --- | --- | --- | --- |
| K-017 | Mimari hata kontrolüne **hiyerarşik/hibrid yerel mevzuat RAG** eklenecek | **KESİN** | islem_003 |
| K-018 | Hata bulgusunda **özgün mevzuat sayfası + metin bbox / tablo hücresi** gösterilecek; satır ID'si türetilmiş olarak etiketlenecek | **KESİN** | islem_003 |
| K-019 | Mevzuat erişimi; madde, fıkra, bent, tablo, ek ve değişiklik/yürürlük sürümüyle tutulacak | **KESİN** | islem_003 |
| K-020 | Mevzuat RAG **arama adayı** döndürür; kural motorunun deterministik hükmünün yerini almaz | **KESİN** | islem_003 |
| K-021 | Yerel OCR kullanımı zorunlu; OCR CPU'da RapidOCR ile yapılır | **KESİN; islem_005 ile güncellendi** | islem_003/005 |
| K-022 | Önceki ağır OCR araştırmasının iptal edilmesi | **İPTAL** | islem_005 |
| K-023 | Ağır GPU OCR ve VLM aynı anda çalışmayacak; süreç izolasyonlu phase-lock | **KESİN** | islem_003 |
| K-024 | İlk 5 mevzuat ailesi: Planlı Alanlar, Yangın, Otopark, Sığınak, BEP | **KESİN (hedef korpus)** | islem_003 |
| K-025 | Mevzuatın özgün yürürlük/değişiklik kronolojisinin ve kuralların sayısal eşiklerinin doğrulanması | **İNCELEME BEKLENİYOR** | islem_003 |
| K-026 | SQLite FTS5 + yerel CPU embedding + RRF; vector DB sunucusu zorunlu değil | **KESİN (başlangıç mimarisi)** | islem_003 |
| K-027 | Kullanıcı arayüz teknolojisi, DWG/IFC ve ilk uygulanacak kesin mevzuat eşikleri | **AÇIK** | islem_003 |
Ayrıntılar: [Sistem mimarisi](sistem-mimarisi.md) · [OCR/bellek](ocr-ve-bellek.md) · [Mevzuat RAG](mevzuat-rag.md).
**K-012 güncellemesi:** Önceden tartışılan mevzuat desteği K-017 ile çekirdek ürüne eklendi. Ancak **hukukî denetimin hangi maddelerle ve hangi projelerde uygulanacağı** hâlâ ayrı mevzuat ve proje bağlamı incelemesine bağlıdır.
## İşlem 004 — OCR strateji revizyonu (2026-10-12)
**K-021/K-022/K-023 güncellemesi:** PDF/OCR motoru [ADR-002](adr/ADR-002-PDF-Engine-License.md) ile kesinleştirildi; önceki ağır OCR alternatifleri kapsam dışıdır.
| Kod | Karar | Durum | Kaynak |
| --- | --- | --- | --- |
| K-028 | DXF CAD veya pdfplumber native PDF metni, eksik bölgede RapidOCR CPU | **KESİN** | islem_005 |
| K-029 | Birincil yerel OCR: `rapidocr` + `onnxruntime` CPU | **KESİN** | islem_005 |
| K-030 | OCR için ikinci büyük model seçeneği desteklenmeyecek | **KESİN** | islem_005 |
| K-031 | Native metin de kusurlu olabilir; SHX/kontur metin ve kısmi raster için ROI kalite kapısı | **KESİN** | islem_004 |
| K-032 | Döndürülmüş yazılarda quad/homografi + sayfaya geri dönüş; RapidOCR cls yalnız 0°/180° | **KESİN (yöntem)** | islem_004 |
| K-033 | Türkçe/mimari simgelerin RapidOCR ile gerçek doğruluğu ve Windows CPU RAM/latency | **ÖLÇÜM BEKLENİYOR** | islem_004 |
| K-034 | Mevzuat OCR/tabloları çizim analizinden **ayrı offline ETL** hazırlanacak | **KESİN** | islem_004 |
| K-035 | Mevzuat tabloları ve hücre geometrileri pdfplumber ile çıkarılacak; doğruluk manuel kontrol kapısından geçecek | **KESİN** | islem_005 |
| K-036 | Kaynak paket adı `src/mimarllm/` olarak korunur; ikinci `src/mimar/` paketi açılmaz | **KESİN (repo bütünlüğü)** | islem_004 |
Kaynak: [İşlem 004](islem_004.md) · [OCR mimari sözleşmesi](ocr-mimari-pafta.md).
| K-037 | PDF/OCR teknoloji yığını yalnız ADR-002'deki seçili üç bileşendir; diğer motorlar kullanılmaz | **KESİN** | islem_005 |
| K-038 | Kapalı kaynak, ücretsiz yeniden dağıtım alternatifi olarak pypdfium2 ve pdfplumber kıyaslanacak | **İNCELEME BEKLENİYOR** | islem_004 |
[PDF lisans ve backend karşılaştırması](pdf-lisans.md).

## İşlem 005 — Kesin teknoloji kararı

| Kod | Karar | Durum | Kaynak |
| --- | --- | --- | --- |
| K-039 | PDF native metin/geometri yalnız `pdfplumber` | **KESİN** | islem_005 / ADR-002 |
| K-040 | PDF görüntü/ROI render yalnız `pypdfium2` | **KESİN** | islem_005 / ADR-002 |
| K-041 | OCR yalnız `rapidocr` + `onnxruntime` CPU | **KESİN** | islem_005 / ADR-002 |
| K-042 | Eski PDF/OCR motorları ve seçenekleri güncel repo içerik ve bağımlılıklarından kaldırıldı | **KESİN** | islem_005 |
| K-043 | Transitif lisans/SBOM/Windows offline kabulü | **HOLD** | islem_005 |

[ADR-002](adr/ADR-002-PDF-Engine-License.md) kesin teknik seçimdir; tarihsel işlem kayıtları güncel bağımlılık kararlarını geçersiz kılamaz.



## İşlem 006 — Hedef kapsam ve dürüst kabul politikası (2026-10-13)

| Kod | Karar | Durum | Kaynak |
| --- | --- | --- | --- |
| K-044 | Yüklenen tüm taslaklar V2 için **hedef özellik** olarak F01–F24 envanterine dahil | KESİN | islem_006 |
| K-045 | `src/mimarllm/` tek paket; `src/mimar/` ikinci paket olmayacak | KESİN | islem_006 |
| K-046 | İşlem numaraları 001–005 tarihsel; şimdi 006; sonraki gerçek iş 007 | KESİN | islem_006 |
| K-047 | Yangın/Otopark/Sığınak/BEP/İmar hukukî sabitleri kaynak ve yürürlük doğrulanmadan gerçek PASS/FAIL üretmez | KESİN | ADR-003 |
| K-048 | Topolojik centroid uzaklığı yangın kaçış yürüme mesafesi değildir | KESİN | islem_006 |
| K-049 | run.bat ve PyInstaller `onedir` hedef kapsam; gerçek CLI/UI/Windows kabulü olmadan tamamlanmış sayılmaz | KESİN | islem_006 |
| K-050 | Mevcut PDF/OCR yığını değişmedi: pdfplumber + pypdfium2 + RapidOCR CPU | KESİN | ADR-002 |
| K-051 | İnsan hukukî incelemesi, özgün PDF source span ve amendment graph olmadan mevzuat etiketi `APPROVED_FOR_CHECK` olmaz | KESİN | ADR-003 |

[Özellik envanteri](ozellik-envanteri.md) · [Uygulama yol haritası](uygulama-yol-haritasi.md) · [Mevzuat doğrulama](mevzuat-dogrulama-protokolu.md).


## İşlem 008 — DXF gözlem motoru kararları (2026-10-13)

| Kod | Karar | Durum |
| --- | --- | --- |
| K-052 | DXF `ezdxf` ile yerel okunur, dosya aslı değiştirilmez | KESİN / KODLANDI |
| K-053 | `LINE/LWPOLYLINE/ARC/CIRCLE/TEXT/MTEXT/DIMENSION/INSERT` gözlemleri ve nested handle yolu | KODLANDI / sentetik CI kabulü |
| K-054 | Kaynak layer yalnız sınıf adayı; gerçek mimari duvar/kapı semantiği değildir | KESİN |
| K-055 | `$INSUNITS` ve DIMENSION onaysız iken `CONFIRMED` metre kullanılmaz | KESİN |
| K-056 | XREF dış bağlantı otomatik çözülmez, diagnostik oluşturulur | KESİN |
| K-057 | DXF curve tessellation CAD kaynak birimi toleransına ve çıktı affine stretch'e bağlıdır | KODLANDI / sentetik test |
| K-058 | Gerçek Windows, büyük pafta, dinamik blok, tüm OCS, DWG ve DXF mevzuat kabulü | HOLD |

[islem_008.md](islem_008.md) · [DXF source sözleşmesi](specs/dxf-import-v0.1.md).


## İşlem 009 — Kaynak-geometri bütünleştirme kararları (2026-10-13)

| Kod | Karar | Durum |
| --- | --- | --- |
| K-059 | PDF/ROI RapidOCR metinleri ayrı provenansla `DrawingIR` entity ve `SourceReference` içinde tutulur | KODLANDI |
| K-060 | Native glyph `bbox` gerçek rotated glyph dörtgeniymiş gibi sunulmaz; char.matrix korunur | KESİN |
| K-061 | PDF çizgisinde bbox diyagonali değil gerçek `line.pts`; cubic Bezier yaklaşıklaştırma uyarısı | KODLANDI |
| K-062 | Standart /Rotate 90/180/270: sınırlı full-page bitmap + ROI; bellek bütçesi aşılırsa ret | KODLANDI |
| K-063 | Non-default CropBox için pypdfium2–pdfplumber source mapping doğrulanana kadar OCR ROI açık ret | HOLD |
| K-064 | OCR engine açık verilmeden model yükleme, indirme veya haricî API çağrısı yapılmaz | KODLANDI |
| K-065 | Gerçek RapidOCR Windows inference, 45° Türkçe/simge CER ve karmaşık CAD PDF source yerleşimi | HOLD |

[İşlem 009](islem_009.md) · [PDF/OCR teknik şartname](specs/pdf-ocr-drawingir-v0.1.md).


## İşlem 010 — Shapely geometri ve alan kararı (2026-10-13)

| Kod | Karar | Durum |
| --- | --- | --- |
| K-066 | Shapely `unary_union + polygonize_full` tek frame native çizimden yalnız `UNCLASSIFIED_FACE` adayları üretir | KODLANDI |
| K-067 | Açık, fazla, çakışan veya kendiyle kesişen kaynakta kesinsiz alan m² verilmez | KODLANDI |
| K-068 | Bütünleşik kaynak entity ID+document hash ve kesişim noktası/T junction kaydı | KODLANDI |
| K-069 | Fiziksel iç alan ayrı gözden geçirilmiş iç sınır + onaylı aynı frame ölçek ister; metrik değilse `INSUFFICIENT_EVIDENCE` | KODLANDI |
| K-070 | Dış zarfın `EXTERIOR_FOOTPRINT_M2` hesabı yasal brüt kat alanı değildir | KESİN |
| K-071 | Paralel çizgi aralığı `WALL_THICKNESS` kanıtı değil `PARALLEL_EDGE_GAP_CANDIDATE` | KODLANDI |
| K-072 | `snap_tolerance>0` yalnız aday; kesin ölçüm snap kullanılmadan, seçili ham çizimde | KESİN |
| K-073 | CPU O(n²) segment/pair kontrolüne açık güvenlik üst limitleri, büyük pafta optimizasyonu sonraki iş | KODLANDI / PERF HOLD |
| K-074 | Gerçek Windows i7/4070 mimari çizimleri ve otomatik oda/duvar/kapı bağlantısı | HOLD |

[İşlem 010](islem_010.md) · [Geometry v0.1 sözleşmesi](specs/geometry-v0.1.md).


## İşlem 011 — NetworkX geçiş grafı (2026-10-13)

| Karar | Kural | Durum |
| --- | --- | --- |
| K-075 | Yalnız açık inceleme kaydı bulunan `FaceCandidate` düğüm; DrawingIR'den yeniden üretilemeyen yüzey reddedilir | KODLANDI |
| K-076 | Aynı frame/kattaki, iç bölgeleri örtüşmeyen mekânlar arası pozitif ortak sınır ve tek geometrik geçiş kesişimi gerekir | KODLANDI |
| K-077 | Yakın native source marker ve manuel açıklık inceleme beyanı yoksa graf kenarı kurulmaz; OCR/metin kabul edilmez | KODLANDI |
| K-078 | NetworkX `MultiGraph` ile birden fazla kapı, connected components, articulation, bridge ve passage-ID yolu | KODLANDI |
| K-079 | `EXTERIOR` düğümü bir mimari çıkış uygunluğu veya yangın kaçış kararı değildir | KESİN |
| K-080 | Centroid tabanlı kısa yol yalnız kenar sayısına göre topolojik ilişki; yürüme mesafesi değildir | KESİN |
| K-081 | `reviewer_id` güvenilir kimlik/onay kaydı olarak doğrulanmaz; UI audit ve gerçek kapı/boşluk belirleme ileride | HOLD |
| K-082 | Çoklu kat, 3B merdiven ve yangın yürünebilir yol sistemi `islem_011` kapsamında üretilmez | KESİN |

[islem_011](islem_011.md) · [Topology v0.1 sözleşmesi](specs/topology-v0.1.md).


## İşlem 012 — Deterministik RuleEngine ve mevzuat HOLD (2026-10-13)

| Karar | Kural | Durum |
| --- | --- | --- |
| K-083 | `RuleDefinition` yalnız Pydantic/JSON deklaratif kısıtlı `>= > <= < ==` operatörlerini kullanır; `eval/exec` yasak | KODLANDI |
| K-084 | Teknik sonuç 6 durum: COMPLIANT/NON_COMPLIANT/INSUFFICIENT_EVIDENCE/REVIEW_REQUIRED/NOT_APPLICABLE/ERROR | KODLANDI |
| K-085 | Segment uzunluğu native gerçek çizimden, alan Shapely'den, geçiş NetworkX'ten aynı kaynak ve frame ile **yeniden doğrulanır** | KODLANDI |
| K-086 | `COMPLIANT` ve `NON_COMPLIANT` yalnız teknik senaryo kıyasıdır; yapı hukuku sertifikası değildir | KESİN |
| K-087 | Bütün `REGULATORY` sonuçları bağımsız Resmî Gazete/versiyon/yürürlük/uygulanabilirlik kapısı kurulana kadar `INSUFFICIENT_EVIDENCE` | KODLANDI / HUKUKI_HOLD |
| K-088 | `LegalSourceLocator` kullanıcıdan gelen hash/madde bilgisiyle yasal onay açamaz | KODLANDI |
| K-089 | Hatalı kaynak, onaysız SI ölçek, sahte alan/graf, eksik kanıt veya belirsizlik bandından olumlu kural kararı çıkarılmaz | KODLANDI |
| K-090 | `NOT_APPLICABLE` yalnız technical reviewer declaration + DrawingIR SHA/entity bağı ile mümkündür, yasal uygulanabilirlik kararına dönüştürülemez | KODLANDI |
| K-091 | Resmî yönetmelik kuralları, bağımsız hukukî inceleme ve gerçek Windows saha kabulü bu aşamada yapılmadı | HOLD |

[İşlem 012](islem_012.md) · [Rule Engine v0.1 sözleşmesi](specs/rule-engine-v0.1.md).


## İşlem 013 — PDF LegalAST ETL kararları (2026-10-13)

| Karar | Uygulama | Durum |
| --- | --- | --- |
| K-092 | Resmî mevzuat PDF kaynak kimliği immutable SHA-256; özgün PDF sayfa/koordinat/çıkarım yöntemi LegalSourceSpan içinde | KODLANDI |
| K-093 | `pdfplumber` native kelime/hücre; `pypdfium2` render; `RapidOCR` CPU yalnız kullanıcının seçtiği OCR sayfalarında | KODLANDI |
| K-094 | BÖLÜM, MADDE, GEÇİCİ MADDE, (fıkra), bent ve devam metniyle LegalAST oluşturulur; belirsizlikler issue | KODLANDI / KISMI |
| K-095 | Tablo hücreleri PDF bbox ve row/column kimliğiyle tutulur; tablo–madde ilişkisi yalnız adaydır | KODLANDI |
| K-096 | Değişiklik, ilga, yürürlük ve istisna sözcükleri `LegalChangeCandidate` işaretidir, gerçek norm ilişkisi veya geçerli tarih değildir | KODLANDI |
| K-097 | Metadata `USER_ASSERTED_UNVERIFIED`; LegalDocument her zaman `UNREVIEWED`; hukuken `APPROVED_FOR_CHECK` çıkarılamaz | KODLANDI |
| K-098 | Bütün tarihsel yönetmelik sürümleri, iki sütun/karmaşık ekler, OCR doğruluk kabulü ve gerçek resmî PDF ayrıştırılması | HOLD |
| K-099 | F08–F12 hukukî uygunluk; RuleEngine REGULATORY kilidi islem_013'te açılmaz | KESİN |
| K-100 | Orijinal mevzuat PDF içerikleri ve modelleri GitHub'a yüklenmez, yalnız sentetik fixture | KESİN |

[İşlem 013](islem_013.md) · [LegalAST kaynağı](specs/legalast-v0.1.md).
