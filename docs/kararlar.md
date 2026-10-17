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


## İşlem 014 — Lokal RAG indeks/kanıt kararları (2026-10-13)

| Karar | Mühendislik uygulaması | Durum |
| --- | --- | --- |
| K-101 | SQLite FTS5/BM25 lexical arama; kaynak metni ayrı korunur, Türkçe Unicode normalize indeks kullanılır | KODLANDI |
| K-102 | LegalAST düğüm, parent, madde/fıkra/bent ve tablo hücre row/column orijinal PDF span + SHA kimliğiyle dizinlenir | KODLANDI |
| K-103 | SQL/MATCH girdi escape + parametrik filtre ve sorgu sınırı; yeniden indeksleme transaction içinde | KODLANDI |
| K-104 | Dense embedding yalnız açıkça sağlanan **yerel** SentenceTransformer klasöründe CPU, `local_files_only` ve `trust_remote_code=False` | KODLANDI; gerçek model kabulü HOLD |
| K-105 | Dense v0.1 SQLite JSON ve bounded exact cosine; ANN/FAISS/servis bağımlılığı yok | KODLANDI / BÜYÜK CORPUS PERF HOLD |
| K-106 | RRF 1/(k+rank), aynı passage kimliğinin FTS/dense birleştirilmesi; skor mevzuat geçerlik puanı değildir | KODLANDI |
| K-107 | Kaynak PDF sağlanırsa aynı SHA ve sayfa sınırları doğrulanır; dosya artık yok/bozuksa `source_pdf_available=False` | KODLANDI |
| K-108 | `RagHit` `UNREVIEWED`, `legal_compliance_certified=False`; yasal RuleEngine REGULATORY kilidi açılmaz | KESİN |
| K-109 | Sentetik dense stub CI, gerçek öğrenilmiş Türkçe embedding doğruluk testi veya milyarlarca parçacıklı RAG benchmarkı değildir | HOLD |
| K-110 | Gerçek mevzuat PDF corpus, konsolidasyon, hukukî yürürlük, belediye/yapı istisna bağları yapılmadı | HOLD |

[İşlem 014](islem_014.md) · [RAG v0.1 teknik şartnamesi](specs/rag-v0.1.md).


## İşlem 015 — Kaynak/versiyon/proje bağlayıcı kararları (2026-10-13)

| Karar | Mühendislik sözleşmesi | Durum |
| --- | --- | --- |
| K-111 | `LegalAST` ve fiziksel yerel PDF SHA256+sayfa sayısı+polygon bounds karşılaştırılır; resmî yayımlanma iddiası üretilmez | KODLANDI |
| K-112 | Kural `LegalSourceLocator` SHA/regulation/article/clause/page tam LegalAST ancestry ile eşleşmeli | KODLANDI |
| K-113 | RAG skorları hiçbir onay kapısını açmaz; hit node/text/spans tam AST ile karşılaştırılır | KODLANDI |
| K-114 | Amendment'ın kendi MADDE numarası hedef hüküm değildir; `target_node_id` ve `amending_node_id` ayrı gerekir | KODLANDI |
| K-115 | Değişiklik PDF'lerinin fiziksel dosya/hash/source polygon'u ayrıca doğrulanır; eksikse `HOLD_AMENDMENT_CHAIN` | KODLANDI |
| K-116 | Tarih sırası, çakışma, eksik proje/ruhsat/kullanım ve istisna `REVIEW_REQUIRED/INSUFFICIENT_EVIDENCE` olur | KODLANDI |
| K-117 | Teknik kaynak bütünlüğü resmî yayımlanma/dijital imza/hukukî sürüm konsolidasyonu veya geçerli madde incelemesi değildir | KESİN |
| K-118 | Tüm `REGULATORY` `RuleEngine` kararları kilitli; `APPROVED_FOR_CHECK` alanı üretilmez | KODLANDI |
| K-119 | Gerçek tüm yıl Resmî Gazete incelemesi, uzman hukukî değerlendirme, gerçek müşteri Windows kabulü | HOLD |

[İşlem 015](islem_015.md) · [Kanıt bağlama sözleşmesi](specs/legal-binding-v0.1.md).


## İşlem 016 — PDF üzerinde kaynak inceleme kararları (2026-10-14)

| Karar | Mühendislik sözleşmesi | Durum |
| --- | --- | --- |
| K-120 | HTML öncesi LegalAST kaynak metni, quad ve PDF SHA yeniden doğrulanır; sahte vurgu reddedilir | KODLANDI |
| K-121 | pypdfium2 sayfa bitmap'i üstünde SVG sarı PDF üst-sol kaynak polygonu; bozuk CropBox/ölçümde fail closed | KODLANDI |
| K-122 | NODE, TABLE_CELL, CHANGE_MENTION ve AMENDMENT_SIDE ayrı inceleme task türleridir | KODLANDI |
| K-123 | Ana/orijinal ve değişiklik PDF'si ayrı gösterilir, aynı madde numarasından konsolidasyon yoktur | KODLANDI |
| K-124 | VISUALLY_MATCHED kullanıcı görsel eşleşme beyanıdır; resmî doğrulama veya hukukî uzman imzası değildir | KESİN |
| K-125 | Browser JSON taslağı task ID + kaynak digest ile Pydantic doğrulanır; yerel JSONL SHA-chain kayıt | KODLANDI |
| K-126 | Yerel SHA-chain haricî anchor/e-imza olmadan tüm geçmişin yeniden yazılmasını engellemez | KESİN |
| K-127 | Gerçek RG külliyatı, resmî belge imzası/yürürlük zinciri, bağımsız uzman ve son müşteri Windows testi | HOLD |

[İşlem 016](islem_016.md) · [Görsel kanıt inceleme şartnamesi](specs/legal-review-v0.1.md).


## İşlem 017 — Raporlama ve çift yönlü kanıt kararları (2026-10-14)

| Karar | Mühendislik uygulaması | Durum |
| --- | --- | --- |
| K-128 | DrawingIR/RuleResult raporu kaynak SHA/entity/frame ve ölçüm IDs ile oluşturulur | KODLANDI |
| K-129 | CAD layout/frame ve PDF page farklı koordinat sistemleri; kaynak CAD Y-up SVG dönüşümü fiziksel ölçek anlamına gelmez | KODLANDI |
| K-130 | Teknik COMPLIANT/NON_COMPLIANT yalnız RuleDomain.TECHNICAL; mevzuat REGULATORY sonucu kilitli | KODLANDI |
| K-131 | Bulgu→SVG kaynak entity, kaynak→bulgu; mevzuat kaynak adayı varsa legal PDF→bulgu HTML anchor | KODLANDI |
| K-132 | Gerçek orijinal PDF SHA ve LegalAST kaynak node/quad uyuşması yoksa sarı hukukî PDF görseli üretilemez | KODLANDI |
| K-133 | F17 JSON/Markdown/HTML/ReportLab PDF; PDF sadece özet, HTML interaktif kaynak bağlantılı | KODLANDI / KISMI |
| K-134 | Shapely yüzeyi yalnız UNCLASSIFIED_FACE, topology hop sayısı gerçek kaçış mesafesi sayılmaz | KESİN |
| K-135 | SVG DrawingIR CAD source geometri gösterimi, tam DXF/DWG plot veya paftanın tasarım görseli değildir | KESİN |
| K-136 | F16 CLI, F19 GUI, hukukî resmiyet/konsolidasyon, gerçek Windows kullanıcı acceptance | HOLD |

[İşlem 017](islem_017.md) · [Analiz raporu v0.1 şartnamesi](specs/analysis-reports-v0.1.md).


## İşlem 018 — Bütünleşik pipeline + CLI sözleşme kararları (2026-10-14)

| Karar | Mühendislik kuralı | Durum |
| --- | --- | --- |
| K-137 | Yalnız kaynak local .dxf/.pdf ve explicit local JSON, uzak/ücretli API yok; source SHA değişmeden pipeline boyunca korunur | KODLANDI |
| K-138 | Çoklu PDF page/CAD layout ayrı coordinate frame; Shapely analizleri frame bazlı, rapor birleştirir ama odaları birleştirmez | KODLANDI |
| K-139 | `$INSUNITS` otomatik onay değil; fiziksel `CalibrationReference` için native line entity, bilinen metre ve kullanıcı etiketi şart | KODLANDI |
| K-140 | DIMENSION/GRAPHIC_SCALE doğrulama modülü olmadan o kaynak yöntemlerinin `CONFIRMED` etiketini üretmek yasak | KODLANDI |
| K-141 | Kullanıcı `ReviewedTopology` beyanı yoksa `TOPOLOGY=SKIPPED`, yangın kaçış rotası veya gerçek kapı tahmini yok | KODLANDI |
| K-142 | Alan ve teknik kural ancak gerçek source ID/yöntem/geometri ile, mevzuat otomatik hükmü olmadan değerlendirilir | KODLANDI |
| K-143 | `COMPLETE/REVIEW_REQUIRED/SKIPPED/ERROR` manifesti; stage ERROR `PARTIAL_WITH_ERRORS` exit 4, kaynak parse/config exit 2, iptal 130 | KODLANDI |
| K-144 | HTML raporda bulgu olmasa da kaynak vektörünü göster; asla bulgu veya hukukî uygunluk uydurma | KODLANDI |
| K-145 | CLI yeni çıktı dosyası, mevcut dosya overwrite yok; ihracat hatası/iptalde sadece bu koşu dosyalarını temizle | KODLANDI |
| K-146 | Gerçek kanun yürürlük/Resmî Gazete doğrulaması, lokal Windows müşteri kabulü ve F19 GUI | HOLD |

[İşlem 018](islem_018.md) · [Pipeline/CLI v0.1 şartnamesi](specs/pipeline-cli-v0.1.md).


## İşlem 019 — Offline tarayıcı UI / sunucu güvenlik kararları (2026-10-14)

| Karar | Uygulanan teknik sözleşme | Durum |
| --- | --- | --- |
| K-147 | FastAPI yalnız 127.0.0.1 Uvicorn; keyfi remote host parametresi ve forwarded proxy headers kapalı | KODLANDI |
| K-148 | Host, peer loopback IP, isteğe bağlı Origin, POST CSRF token, CSP, nosniff ve no-store denetimi | KODLANDI |
| K-149 | HTTP yolu yerel sunucu dosya yolu seçmez; yalnız 32 karakterli opaque UUID proje/run ID ve statik rapor allowlist | KODLANDI |
| K-150 | DXF 25 MB, PDF 50 MB, JSON 256 KB; kaynak SHA yeniden doğrulanmadan analiz çalışmaz | KODLANDI |
| K-151 | Şirket/LAN'a dışa açık API/çok kullanıcı/auth iddiası yok; localhost CSRF yerel kötü niyetli process'e mutlak koruma değildir | KESİN |
| K-152 | Aynı anda tek analiz, tüm raporlar ayrı run dizini; incomplete/error sonuçların kullanıcıya gizlenmesi yasak | KODLANDI |
| K-153 | Kullanıcı yalnız gerçek native LINE entity ID ve bilinen metreyle fiziksel ölçek istenir; CAD INSUNITS otomatik ölçek PASS değildir | KODLANDI |
| K-154 | UI HTML source CSS/JS tamamen yerel; kaynak layer/rule metinleri textContent ile gösterilir, harici CDN yok | KODLANDI |
| K-155 | Teknik PASS yalnız teknik senaryo, hukukî sürüm/Resmî Gazete/yürürlük doğrulaması ayrı HUKUKI_HOLD | KESİN |
| K-156 | Gerçek Windows Edge görsel kullanıcı kabulü, dağıtım installer, SBOM, sızma testi ve gerçek kanun kabulü | HOLD |

[İşlem 019](islem_019.md) · [F19 Dashboard şartnamesi](specs/dashboard-v0.1.md).


## İşlem 020 — ARCH-CORE Local master kapsam ve mühendislik kararı (2026-10-15)

**Kayıt:** [İşlem 020](islem_020.md) · [ADR-004](adr/ADR-004-ARCH-CORE-Local-Kapsam-Genislemesi.md) · [Master Mimari](master-mimari-arch-core-local.md).

| Karar | Mühendislik kuralı | Durum |
| --- | --- | --- |
| K-157 | Tek gerçek Python package `src/mimarllm/` korunur; ARCH-CORE/backend, ikinci DrawingIR veya bulut-API microservice açılmaz | **KESİN / DOKÜMAN KARARI** |
| K-158 | İlk teknik analiz Engineering Core mevcut ürün; ARCH-CORE Studio/Education yalnız **opsiyonel ileri-sürüm ek paket** | **KESİN MİMARİ / İLERİ SÜRÜM PLAN** |
| K-159 | Kaynak CAD/PDF koordinat ve SHA kanıtı, türetilmiş SI, repair-overlay, 2.5D/VLM/persona yanında değişmez | **KESİN / MEVCUT ÇEKİRDEĞİN KORUNMASI** |
| K-160 | Unit histogramı/door median/Dimension aday birimi `INFERRED`; kullanıcı kaynak segmenti + gerçek metre olmadan `CONFIRMED` değil | **KESİN / YENİ ALGORİTMA PLAN** |
| K-161 | Açık poligon/snap/virtual door bridge orijinal geometriyi düzeltilmiş gibi sunmaz; review alt katmanı `CANDIDATE` | **KESİN / GELİŞTİRME PLAN** |
| K-162 | Layer0 heuristiği/HATCH/ARC tek başına doğrulanmış duvar/kapı/kolon veya mevzuat ölçümü değildir | **KESİN / PLAN** |
| K-163 | A0 tiled OCR gerçek PDF SHA/page/quad geri dönüşümü ve bellek bütçesiyle; vektör PDF eksik ROI hâlâ OCR gerektirebilir | **KESİN / PLAN** |
| K-164 | RAG synonym ve statik legal madde identity arama iyileştirir, hükmün yürürlük/onayını otomatik kanıtlamaz | **KESİN / PLAN** |
| K-165 | 2.5D extrude ancak incelenmiş polygon + explicit height; gerçek 3D strüktür/yangın/çatı kanıtı değildir | **KESİN / PLAN** |
| K-166 | Yerel GGUF/mmproj/VRAM/structured output lisans ve donanım kabulü olmadan sabit performans/kararlı model iddiası yok | **AR-GE / PLAN** |
| K-167 | Rubrik score-in-code; persona çıktısı eğitsel öneridir, 10 ayrı bağımsız gerçek uzman oyu veya otomatik resmî akademik not değil | **KESİN / EĞİTİM PLAN** |
| K-168 | 2209-A κ/ICC, Recall, SUS, IoU, OCR CER, GPU VRAM, 60FPS vb iddialar **hipotez/ölçüm hedefidir**, test PASS değil | **KESİN / BİLİMSEL SON KABUL PLAN** |
| K-169 | İşlem 020 yalnız plan revizyonu; Windows paketleme 021, kırık CAD/OCR/ RAG/UI/3D/VLM/jüri 022–030, gerçek kabul 031 | **KESİN YENİ YOL HARİTASI** |
| K-170 | F08–F12 resmî mevzuat sürüm/yerel istisna/uzman doğrulama tamamlanmadan `REGULATORY_LOCKED` kalır; model/Jüri bu kilidi açamaz | **HUKUKI_HOLD** |
| K-171 | Windows offline dağıtım ve 3D/LLM/model transitive ve TS belge hakları SBOM/yeniden dağıtım incelemesine tabidir | **LİSANS KABULÜ HOLD** |

**Güvenlik notu:** İşlem 020 diğer İşlem 001–019 karar ve tarihsel kayıtlarını silmez veya geriye dönük kod değiştirmez; gerçek kaynak modüllerine dokunmadan gelecek modüllerin giriş/çıkış sözleşmeleri ve önceki planın eksikleri yeniden tarif edildi.


## İşlem 021 — Windows offline onedir / wheelhouse / lisans envanteri kararları (2026-10-15)

| Karar | Mühendislik sınırı | Durum |
| --- | --- | --- |
| K-172 | Mevcut `src/mimarllm`, `app.launch` ve yerel static UI kullanılır; paralel `src/mimar` eski entrypoint yok | KODLANDI |
| K-173 | `run.bat` yalnız hazır ortamı başlatır; otomatik pip/ağ yok | KODLANDI |
| K-174 | Kurulum `install_offline.bat` ayrı bilinçli adım; hash verified wheelhouse ve `--no-index` fail closed | KODLANDI |
| K-175 | Wheel cache internet kullanımı **yalnız hazırlama** `-AllowNetwork`; runtime ağ gerektirmeyecek politika korunur | KODLANDI / GERÇEK OFFLINE ACCEPTANCE HOLD |
| K-176 | `mimar.spec` Win32, `onedir`, `console=True`, `upx=False` ve gerçek PDF/OCR/GEOS/UI bağımlılığı | KODLANDI / ONEDIR BINARY BUILD HOLD |
| K-177 | Frozen `--self-check` yerel UI asset, PDF/OCR/GEOS/ONNX CPU import sözleşmesi; tam kullanıcı tıklama/temiz PC testi değildir | KODLANDI / WINDOWS SMOKE HOLD |
| K-178 | Paket payload SHA manifesti yerel bytes/size; harici imza olmadan dosya kökeni veya tamper-proof garanti değil | KODLANDI / SIGNATURE HOLD |
| K-179 | SBOM metadata'da `declared_license` kullanıcı/dağıtıcı hukuki izin doğrulaması değildir; DLL/NOTICE/UCRT hakları bağımsız inceleme | HOLD |
| K-180 | Kullanıcı workspace dist altına değil `LOCALAPPDATA`; dashboard sadece `127.0.0.1` ve kaynaklı rapor pipeline aynı | KODLANDI |
| K-181 | `F20` kısmi kaynak ve sentetik CI kabulü; gerçek Windows exe, installer/MSI, cihaz/Edge ve lisans kabulü final | HOLD |

[İşlem 021](islem_021.md) · [Windows offline paket v0.1](specs/windows-offline-package-v0.1.md).


## İşlem 022 — Onarım adayı, Layer0 ve SI ipucu güvenlik kararları (2026-10-16)

| Karar | Sözleşme | Durum |
| --- | --- | --- |
| K-182 | `RepairOverlay` `DrawingIR` entity/geometry/handle/block_path/source SHA'yı hiçbir zaman değiştirmez | KODLANDI |
| K-183 | Sanal köprü/snap, çakışan/duplicate çizgiler yalnız `REVIEW_REQUIRED` ve `VIRTUAL_CANDIDATE`; otomatik oda/net alan yok | KODLANDI |
| K-184 | Her onarım adayı iki orijinal kaynak entity ve CAD SourceReference taşır, farklı PDF/frame/katman birleştirilmez | KODLANDI |
| K-185 | Kasıtlı kapı açıklığı olabilecek boşlukta sadece turuncu kesikli overlay; NetworkX/RuleEngine kanıtı olmaz | KODLANDI |
| K-186 | Çoklu makul endpoint eşleşmesinde seçme yerine `AMBIGUOUS_ENDPOINT_MATCH`; kaynak segment/aday bütçesi fail closed | KODLANDI |
| K-187 | `$INSUNITS` fiziksel metreye otomatik `CONFIRMED` dönüşmez; gerçek DIMENSION/door histogramı ayrı paket | KISMI |
| K-188 | Layer0 tek başına WALL/DOOR/COLUMN sınıfını vermez; gerçek ARC/HATCH incelemesi ayrı | KISMI |
| K-189 | Onarım SVG yalnız kullanıcı için kaynak-vs-sanal aday görünümü; asıl CAD plot/Windows kullanıcı görsel kabulü henüz yok | KISMI |
| K-190 | Gerçek saha CAD, fiziksel ölçüm, onaylı Resmî Gazete kaynak zinciri ve ticari Windows yeniden dağıtım kabulü | HOLD |

[İşlem 022](islem_022.md) · [Onarım overlay v0.1](specs/source-preserving-repair-v0.1.md).


## İşlem 023 — Tiled OCR / kaynak dörtgeni / antet aday kararları (2026-10-16)

| Karar | Uygulanan kural | Durum |
| --- | --- | --- |
| K-191 | OCR ancak explicit PDF page-point ROI ve yerel RapidOCR CPU reader ile; A0 sayfada tam bitmap arka kapısı yok | KODLANDI |
| K-192 | Her tile source SHA/page/rotation/ROI ve pixel-to-source transform kaydına bağlı; nondefault CropBox/unsafe rotation fail-closed | KODLANDI |
| K-193 | Max tile, per-tile ve toplam pixel, OCR candidate ve pipeline global budget render öncesi denetlenir | KODLANDI |
| K-194 | Overlap dedup hem normalize metin hem source bbox IoU ≥0.50; farklı konumdaki aynı yazı saklanır | KODLANDI |
| K-195 | `OCR_CANDIDATE` ve `REVIEW_REQUIRED` Pydantic güven kapısı, fiziksel ölçüm, onaylı room/wall/door / hukukî PASS üretilmez | KODLANDI |
| K-196 | Olası antet sadece sağ-alt text cluster source polygon; kesin mimar/ölçek/mahal/kot/ruhsat metaverisi değil | KODLANDI / SEMANTİK HOLD |
| K-197 | Gerçek A0/A1 OCR model, Türkçe CER/WER, peak RSS, rotasyon/CropBox farkları, Windows offline kullanıcı kabulü | HOLD |
| K-198 | F08–F12, resmî hukukî kaynak/yürürlük ve `RuleEngine.REGULATORY` kilidi değişmez | HUKUKI_HOLD |

[İşlem 023](islem_023.md) · [Karo OCR v0.1](specs/tiled-ocr-v0.1.md).


## İşlem 024 — Türkçe mimarlık sorguları ve RAG kaynak-cache kararları (2026-10-16)

| Karar | Sözleşme | Durum |
| --- | --- | --- |
| K-199 | Mimari jargon yalnız sürümlü, opt-in arama ipucu; kaynak LegalAST metnini/hükmünü değiştirmez | KODLANDI |
| K-200 | Özgün BM25 sorgu sonuçları lexical-only durumda genişletilmiş ilişkili terimlerin önünde kalır; dense sorgu özgün cümleyledir | KODLANDI |
| K-201 | Kullanıcı query/alternatif FTS5 MATCH operatörleri parametre ve token sınırından geçer | KODLANDI |
| K-202 | SQLite query cache yalnız SHA anahtar ve pasaj ID; PDF metni/görseli veya kullanıcı raw sorgusu cache'e yazılmaz | KODLANDI |
| K-203 | Document SHA ve regulation filtresi hem özgün hem genişletilmiş aday aramada ayrı SQL koşullarıdır | KODLANDI |
| K-204 | Re-index transaction ve SQL passage update/insert/delete trigger ile cache invalidation; dış PDF hash her sonuçta yeniden denetlenir | KODLANDI |
| K-205 | 128 anahtar sınırı, SQLite lokal kalıcılık; genel analitik workspace WAL/retention çok kullanıcılı senaryo değil | KISMI |
| K-206 | Eşanlamlı mimari kelimeler mevzuatta hukuken eşdeğer hüküm diye sunulamaz, uzman değerlendirmesi gerekir | KESİN |
| K-207 | Türkçe gerçek embedding model kalite ölçümü, resmî mevzuat sürüm/yürürlük, kullanıcı Windows saha benchmark ve lisanslı sözlük kabulü | HOLD |
| K-208 | `RuleEngine.REGULATORY` sonuçları INSUFFICIENT_EVIDENCE ve F08–F12 HUKUKI_HOLD | DEĞİŞMEDİ |

[İşlem 024](islem_024.md) · [Türkçe RAG/CACHE v0.1](specs/rag-lexicon-v0.1.md).


## İşlem 025 → 031 — Fiziksel kabulü sona erteleme kararı (2026-10-16)

Önceki İşlem 025 duraklatma kuralı, kullanıcı talebiyle **bu bölüm kapsamında ileriye dönük olarak değiştirilmiştir**. Tarihsel kararlar silinmez; bunlarla çelişen eski "026'ya geçilemez" ifadeleri bu kararın tarihinden sonra geçerli değildir.

| Karar | Uygulanacak mühendislik kuralı | Durum |
| --- | --- | --- |
| K-209 | İşlem 025'te mevcut dar kapsamlı DXF LINE revizyon/undo, kaynaklı 2B önizleme ve bounded job kodu, sentetik CI başarılıysa **mühendislik aday teslimi** sayılır; fiziksel kullanıcı kabulü bundan bağımsızdır | KOD ADAYI / SENTETİK PASS |
| K-210 | Fiziksel Windows 10/11/Edge kullanıcı testi, gerçek kirli DXF ve A0/A1 PDF, p50/p95/peak RSS, Windows offline `onedir` exe/DLL, erişilebilirlik ve bağımsız uygulayıcı imzası **İşlem 031** birleşik kabulüne ertelenir | SON KABUL / HOLD |
| K-211 | 026–030 geliştirme işlemleri 025'in **fiziksel** kabulünü beklemez; yalnız CI/kaynak-provenance regresyonu, güvenlik ve yerel API sözleşmeleri korunur. CI FAIL olan kod bir sonraki özelliğe temel olamaz | İLERİYE DÖNÜK GELİŞTİRME KARARI |
| K-212 | Her işlemde hızlı sentetik Linux/Windows testleri ve sözleşme doğrulamaları devam eder. Gerçek saha/fiziksel testler son aşamada topluca yapılır; test kapsamı ve açık HOLD durumları kaybolmaz | ZORUNLU |
| K-213 | PR #2 mevcut Draft kalsa da yeni özellik için gerekiyorsa **ayrı feature dalı onun onaylanmış kod commit'inden** açılabilir. Draft/bağımlı PR açık etiketlenir; `main` merge'i ve üretim sürümü ayrı kod inceleme + CI kapısına tabidir | GÜVENLİ DAL YÖNETİMİ |
| K-214 | Fiziksel onay olmadan kullanılabilir müşteri paketi, mimari doğruluk sertifikası veya hukukî yönetmelik PASS iddia edilemez; F08–F12 HUKUKI_HOLD / REGULATORY_LOCKED aynı kalır | DEĞİŞMEDİ |

**Yeni yürütme sırası:** 025 mühendislik adayını koru → `islem_026` ilk GitHub kaydı → 026–030 özellikleri ve sentetik CI → 031 fiziksel/gerçek veri/kullanıcı/hukukî uzman kabulü → ancak sonrasında dağıtım kararı.

Bkz. [İşlem 025](islem_025.md), [yol haritası](uygulama-yol-haritasi.md) ve [final fiziksel test protokolü](specs/windows-acceptance-025.md).


## İşlem 026 — Kanıtlı 2.5D teknik kararları (2026-10-16)

| No | Karar | Durum |
| --- | --- | --- |
| K-215 | 2.5D yalnız aynı DXF SHA/frame'e bağlı, özgün direkt CAD Model LINE öğelerinden oluşan tek hatasız kapalı poligon kullanır | SENTETİK KOD |
| K-216 | Bağımsız CONFIRMED kalibrasyon yoksa metre cinsinden kütle yok; HEADER_UNITS tek başına yeterli değil | FAIL-CLOSED |
| K-217 | Yükseklik kullanıcı senaryosu; otomatik gerçek bina/kat/alan/hukukî onay iddiası yok | ZORUNLU |
| K-218 | Farklı frame/PDF, INSERT, delik, snap/onarım, belirsiz topoloji reddedilir | FAIL-CLOSED |
| K-219 | Three.js 0.160.1 yerel ESM SHA ile doğrulanır ve MIT metni paketlenir; CDN çalışma anında kullanılmaz | KOD ADAYI |
| K-220 | WebGL yoksa 2B kaynak inceleme korunur; orijinal DrawingIR/DXF/rapor revize edilmez | KOD ADAYI |
| K-221 | Sentetik Windows/Linux ve hosted Edge ara kontrol; fiziksel Windows/GPU/VRAM/A0/onedir kullanıcı kabulü 031'de | SON KABUL HOLD |

Bkz. docs/islem_026.md ve docs/specs/massing25d-v0.1.md. İşlem 026 PR #4, İşlem 025 PR #2 üzerine bağımlı Draft olarak tutulur. Main ve üretim değişmedi.


## İşlem 027 — GGUF/MMProj ve deterministik kanıt sınırları (2026-10-16)

| Karar | Mühendislik sözleşmesi | Durum |
| --- | --- | --- |
| K-222 | Yerel VLM isteği varsayılan kapalı; GGUF, MMProj ve llama-server operatör tarafından konfigüre edilip SHA doğrulanmadan model çalışmaz | KODLANDI |
| K-223 | Yalnız aynı DrawingIR SHA/frame içindeki benzersiz native DXF/PDF LINE ID'leri 512 px lokal raster adayına seçilebilir | KODLANDI |
| K-224 | RAM/VRAM kullanılabilir değerleri kanıtlanamıyorsa GPU uydurulmaz; tek NVIDIA nvidia-smi, rezervli ağırlık hesabı ve yalnız izinli CPU fallback | TAHMİNİ BÜTÇE / GERÇEK DONANIM 031 |
| K-225 | Llama subprocess only localhost, `--fit off`, açık model/MMProj, tek iş, zaman/token/JSON sınırı; dış model URL/CDN/ücretli API yok | KODLANDI |
| K-226 | Model yanıtı `ModelOnlyPayload` extra-forbid ve yalnız izinli entity IDs; metre/m², mevzuat PASS, skor, new source veya DrawingIR değişikliği şema dışı | KODLANDI |
| K-227 | Kaynak SHA, çalışma tipi, model/MMProj SHA, hukukî kilit ve sonuç statüsü yalnız sunucu tarafından `UNVERIFIED_VLM_SUGGESTION` envelope'unda oluşturulur | KODLANDI |
| K-228 | VLM kapalı/eksik, başarısız veya belleği yetersizse deterministik pipeline ve değişmez dosyalar çalışmaya devam eder | KODLANDI |
| K-229 | Gerçek GGUF/MMProj model uyumluluğu, mimarî doğruluk, CUDA/VRAM, fiziksel Windows ve offline `onedir` kullanıcı kabulü yalnız İşlem 031'de doğrulanır | SON KABUL HOLD |
| K-230 | İşlem 028 rubrik puanı model metninden değil sürümlü deterministik kural ve uzman ölçütüyle hesaplanır; VLM yalnız açık denetim adayı sağlar | SONRAKİ İŞLEM SINIRI |

Bağımlılık: Draft PR #2 (025) → Draft PR #4 (026) → Draft PR #5 (027). `main` dalında değişiklik yok, üretim sürümü veya resmî hukukî PASS yok. [İşlem 027](islem_027.md) ve [VLM kaynak sözleşmesi](specs/local-vlm-027-v0.1.md).


## İşlem 028 — 8 eksenli sınıf-duyarlı rubrik kararları (2026-10-17)

| Karar | Bağlayıcı mühendislik kuralı | Durum |
| --- | --- | --- |
| K-231 | Sekiz tanımlı pedagojik eksen; `028.0.1` pilot rubrik, kodda sabit profil/ağırlık. Okulun resmî rubriği olduğu iddia edilmez | MÜHENDİSLİK_ADAYI |
| K-232 | 1/2/3/4. sınıfta aktif kriter sayısı 6/10/14/16. 1. sınıfta strüktür/çevre ileri hedefleri `NOT_APPLICABLE_BY_LEVEL`; sıfır not/yanlış FAIL değil | SENTETİK TEST |
| K-233 | AI/VLM `human_level` veya rubrik ağırlığı veremez. Sayısal taslak yalnız kodun `Decimal` ve `ROUND_HALF_UP` hesaplamasıyla, insanın açık değerlendirme öz-beyanı ile üretilir | KODLANDI |
| K-234 | Her kriter için aynı projeye/run'a bağlı native DXF/PDF entity kaynak SHA/frame/kind ve insan yorumu gerekir; uygunsuz veya sahte kaynakta `409`, eksik şemada `422` | KODLANDI |
| K-235 | Tek bir etkin kriter bile değerlendirilmemişse `NOT_SCORED` ve genel puan `null`. Aktif eksenler yeniden normalize edilir; üst sınıf boyutları yanlış puan düşürmez | KODLANDI |
| K-236 | Tamamı girilse bile `LOCAL_DRAFT_ONLY` + `official_grade=false`, çünkü `reviewer_label` öğretim üyesinin imzalı kimlik doğrulaması değildir ve ağırlıklar resmî onaylı değildir | KABUL SINIRI |
| K-237 | DrawingIR, gerçek DXF/PDF, pipeline raporu, RuleEngine, hukukî veri ve VLM çıktısı rubrik API tarafından değiştirilemez; rubrik sonucu ephemeral JSON | KODLANDI |
| K-238 | Gerçek öğretim üyesi/öğrenci onamı, kurumsal ölçüt onayı, uzmanlar arası güvenirlik/kappa ve fiziksel Windows/Edge saha kabulü yalnız İşlem 031'de | SON KABUL HOLD |
| K-239 | 029 çok kişilik jüri simülasyonu model/persona çıktıları bağımsız insan eğitmen oyu sayılmaz; önce 028'in kural/kaynak sınırı korunmalıdır | İLERİYE DÖNÜK |

Bağımlı Draft zinciri **PR #2 → PR #4 → PR #5 → PR #6**. `main` ve üretim sürümü değişmedi. [İşlem 028](islem_028.md) / [rubrik teknik sözleşmesi](specs/pedagogical-rubric-028-v0.1.md).


## İşlem 029 — Sıralı jürinin rol ve kaynak sınırı (2026-10-17)

| Karar | Zorunlu sözleşme | Durum |
| --- | --- | --- |
| K-240 | Dört sabit sıralı perspektif aynı tek kontrol motorudur; isimleri gerçek jüri üyeleri, bağımsız AI modelleri/oyları veya eğitmen kimlikleri değildir | KODLANDI |
| K-241 | Yalnız 028'in sınıfa uygun rubrik kriterlerinden source SHA/frame/native entity ile bağı insan tarafından öz-beyan edilmiş inceleme alınabilir. Model yorumları jüri puanı değildir | KODLANDI |
| K-242 | 1. sınıf yapım/iklim perspektifi `NOT_APPLICABLE_BY_LEVEL`. Eksik değerlendirme `REVIEW_REQUIRED` ve kaynak ID boş; kaynak uydurulmaz | KODLANDI |
| K-243 | Raporda `official_jury=false`, `independent_ai_votes=false`, `model_inference_used=false`, `real_faculty_approval=false`, `official_grade=false`, `numeric_score=null`, `passed=null` ve `REGULATORY_LOCKED` sabit | FAIL-CLOSED |
| K-244 | İnsan notu açıkça `doğrulanmamış öz-beyan` olarak tutulur, Markdown/HTML escape edilir; yeni tasarım, ölçü veya geçme sonucu türetilmez | KODLANDI |
| K-245 | Kontrol edilen kaynak ID SVG üzerinde odaklanabilir, gösterilemiyorsa kullanıcıya açıkça bildirilir. Markdown yalnız kullanıcı etkileşimiyle yerel indirilir | KODLANDI |
| K-246 | API proje/run/SHA/rubrik/CSRF ve 32 KiB sınırlı, sonucu transient. CAD, DrawingIR, RuleEngine, AI çıktısı ve analiz raporu değişmez | KODLANDI |
| K-247 | Uzmanlar arası güvenirlik, gerçek jüri/öğrenci görüşleri, offline EXE, fiziksel Windows/Edge ve gerçek mimari proje kabulleri İşlem 031'de | SON KABUL HOLD |

`docs/islem_029.md`, `docs/specs/sequential-jury-029-v0.1.md`. Bağımlı Draft PR zinciri 025 #2 → 026 #4 → 027 #5 → 028 #6 → 029 (yeni Draft). `main` değişmedi.


## İşlem 030 — Yerel taslak geçmişinde veri koruma kararları (2026-10-17)

| Karar | Bağlayıcı mühendislik sözleşmesi | Durum |
| --- | --- | --- |
| K-248 | History DB varsayılan yok; hem koleksiyon hem tekil kayıt için açık `consent=true` gerekir | KODLANDI |
| K-249 | 128-bit token'ın yalnız SHA256 özeti sunucuda tutulur, genel koleksiyon listeleme ve GET token URL yok, browser persistent storage yok | KODLANDI |
| K-250 | SQLite sadece yerel run/opaque project IDs, yapılandırılmış yıl-dönem, 8 nullable rubrik yüzdesi/metadata saklar; öğrenci adı/e-posta/not/çizim/AI metni depolanmaz | KODLANDI / KİŞİSEL VERİ TEHDİDİ 031 |
| K-251 | `028` kaynak SHA/frame/native entity ve insan öz-beyan rubriği tekrar kontrol edilmeden taslak snapshot kaydı yok | FAIL-CLOSED |
| K-252 | Farklı sınıf/sürüm ve eksik insan incelemesinde `NOT_COMPARABLE`, hiçbir delta yok. N/A radar ekseni 0 sayılmaz, eksik veride kapalı radar poligonu yok | KODLANDI |
| K-253 | Aynı sınıf/sürümde tam veri için yalnız taslak puan farkı; resmî not, akademik ilerleme veya nedensel gelişim sonucu değil | ZORUNLU |
| K-254 | 30/90/180 gün, en çok 20 koleksiyon/24 snapshot; TTL silme erişim-temelli; kullanıcı tek kayıt veya rızayı geri çekerek tüm koleksiyonu silebilir | KODLANDI |
| K-255 | SQLite `secure_delete=ON` + `VACUUM` ve ilk yaratımda 0600; şifreli-at-rest/OS ACL/backups/adli silme garantisi yok | 031 GÜVENLİK KABULÜ |
| K-256 | Kaynak DXF/PDF, DrawingIR, RuleEngine, analiz raporları, VLM ve 029 jüri dosyaları tarihçeden ayrı ve değişmez | KODLANDI |
| K-257 | Geçerli öğrenci onamı, küçük örneklem yanlılığı, uzman pedagojik geçerlilik, fiziksel Win10/11/Edge/onedir ve üretim kabulü son `islem_031` | SON FİZİKSEL KABUL HOLD |

Bağımlı Draft PR zinciri #2 → #4 → #5 → #6 → #7 → 030. `main` ve üretim değişmedi. [İşlem 030](islem_030.md), [gizlilik şartnamesi](specs/private-analytics-030-v0.1.md).
