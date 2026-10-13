# İşlem 011 — NetworkX mekânsal geçiş topolojisi ve kanıtlı bağlantılar

- **Tarih:** 2026-10-13
- **Durum:** UYGULANDI — NetworkX + Shapely tek-plan topoloji motoru, Linux/Windows sentetik CI PASS; gerçek saha/geçilebilirlik ve yangın mevzuatı HOLD.
- **Depo:** `seydivakkas/MimarLLM_v2`; `islem_001`–`islem_010` kayıtları korunur.
- **Özellik:** F06 — mekân ilişki grafı, yalnızca kullanıcı tarafından incelenmiş yüzey ve geçiş kanıtlarına dayanır.
- **Kısıt:** Windows-first, CPU, offline; 8 GB VRAM'i kullanmaz. Teknik topoloji ile yangın mevzuatı/yürüme mesafesi ayrılır.

## 1. Mühendislik hedefleri

1. `src/mimarllm/geometry/topology.py`: oda, koridor, balkon, merdiven, sahanlık ve dış alan için türleri belirli `SpaceReview`, kapı/kemer/açık geçiş için `PassageReview`, bağlantı kanıtı ve `NetworkX` multigraph. Her düğüm gerçekten `GeometryAnalysis.faces` içinde bulunan, aynı drawing hash/frame'e ait yüzeyin bir **inceleme kararıyla** eşleşmesi olacak. Sentetik kaynak çizgi etiketinden oda semantiği çıkarılmayacak.
2. Aynı plan düzleminde bağlantı kurulması için iki farklı geometrik yüzeyin gerçekten **pozitif uzunluklu ortak sınırı** olması; geçişin açıkça seçilmiş iç-dış konumlarının bu yüzeylerde bulunması ve geçiş segmentinin bu sınırı geometrik olarak tek kez aşması gerekli. `PassageReview` üzerinde doğrulanmış açıklık kaynağı/manuel inceleme izinin ayrı ve bağlayıcı olması istenir.
3. Dış alana geçiş için ayrı `EXTERIOR` düğümü; kapı/giriş açıklığının bir ucu iç yüzeyde, diğer ucu seçili yüzeylerin tamamen dışında olmalı. Duvar çizgisi, TEXT, OCR veya kapı etiketini kendiliğinden kapı olarak kabul etmek yasaktır.
4. Belirsiz yüzey, çapraz PDF sayfası/layout, eksik kaynak, duvar üzerinde bulunmayan geçiş, sahte komşuluk, graf erişim eksikliği ve döngü/çift kimlik/safety budget için açık ret veya `REVIEW_REQUIRED` tanısı üretilecek. Belirsiz bağlantı **kenar olarak kullanılmayacak**.
5. Aynı iki düğüm arasında birden fazla bağımsız geçişi `MultiGraph` ile tutmak; `reachable`, `connected_components`, `articulation_points`, `bridges` ve erişim yollarını deterministik kaynak `passage_id` dizisiyle raporlamak.
6. Yangın kaçış mesafesi hesaplanmayacak: oda merkezi mesafesi yürüme mesafesi değildir. Sprinkler/kaçış yönü, kapı açık yönü, gerçek walkable polygon/navmesh ve katlar arası 3B bağlantı sonraki geliştirmedir. `STAIR` etiketi bu aşamada **kat geçişi veya yangın uygunluğu** değildir.
7. `tests/test_topology.py`: kullanıcıca onaylanmış sentetik iki oda-koridor-balkon ağı; dış çıkış, çoklu kapı, yanlış kapı, yanlış frame, kopuk mekân, kesişen/örtüşen yüzey ve belirsiz şemalar. Gerçek `ezdxf` dosyasını kaydet/oku ve Shapely→NetworkX zinciri, Linux+Windows CI.
8. `pyproject.toml`: `networkx` ana bağımlılığı ve GitHub CI; `docs/specs/topology-v0.1.md`, `README.md`, `docs/ozellik-envanteri.md`, `docs/kararlar.md`, `docs/uygulama-yol-haritasi.md` ilerleme kayıtları.

## 2. Kesin güven ve kaynak koşulları

- `SpaceReview`, analiz motorunun orijinal `FaceCandidate` kimliğini, `boundary_entity_ids` ve `source_sha256` korur; onaylayan kimlik açıkça tanımlanır, fakat bu kimlik tek başına bağımsız yetki doğrulaması değildir.
- `PassageReview` semantik kararını, bağımsız kaynağı, geçiş geometrisini ve onaylayanı saklar. DXF `INSERT` veya `LINE` tek başına `DOOR` kararı değildir.
- Fiziksel kapı genişliği, yükseklik, yürüme mesafesi veya hukukî `PASS` çıkışı yoktur.
- Kaynak/geometry frame uyuşmazlığına **fail closed**; tutarsız girişten yaratılmış sahte erişim bağlantısı yok.
- Maksimum düğüm/kenar, aday eşleşme ve spatial geometry limitleri olacak.

## 3. Beklenen gerçek dosya yolları

- `src/mimarllm/geometry/topology.py`
- `tests/test_topology.py`
- `pyproject.toml`, `.github/workflows/core-contracts.yml`
- `docs/specs/topology-v0.1.md`, `README.md`, `docs/ozellik-envanteri.md`, `docs/kararlar.md`, `docs/uygulama-yol-haritasi.md`.

## 4. Gerçekleşen mühendislik işleri ve GitHub commit zinciri

**İlk commit:** `b7b34453994ac94523e13dfd1d49024181d2c098` — `docs/islem_011.md` önce oluşturuldu; ardından kod ve test dosyalarına geçildi.

| Dosya | Gerçek uygulama | İlk/son commit |
| --- | --- | --- |
| `src/mimarllm/geometry/topology.py` | Pydantic `SpaceReview`, `PassageReview`, `TopologyResult`, Shapely source-frame crossing doğrulama, NetworkX MultiGraph, connected components, articulation, bridges ve olası minimum-hop yollar | `20c8f62f` |
| `src/mimarllm/geometry/topology.py` | Serialized geometry face'leri DrawingIR native çiziminden yeniden üretip doğrulama; sahte polygon/source IDs ve farklı floor etiketlerinin reddi | `2296cc75` |
| `tests/test_topology.py` | Sentetik oda-koridor-sahanlık-balkon/exterior, bağımsız kapılar, gerçek DXF diske kaydet/oku, yanlış kapı/marker/hash/frame ve limitler | `08dc1f28` |
| `tests/test_topology.py` | Forged face/yanlış source IDs/farklı floor ve global kaynak değişmesi vs lokal geçiş hatası ayrımı | `1d172e0a`, `adc88ccc` |
| `pyproject.toml` | `networkx>=3.2,<4` ana bağımlılık | `2233ba49` |
| `.github/workflows/core-contracts.yml` | Ubuntu+Windows matrix'e `tests/test_topology.py` ve NetworkX yükleme | `7c8e4c61` |
| `docs/specs/topology-v0.1.md` | Sözleşme, kanıtlı sınır kesişimi ve fail-closed kararları | `91043c1a` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F06 kısmi kod ilerleme, K-075–082 kararları ve sonraki kayıt | `dc1948dd`, `414f5d69`, `93185c45`, `68ac1935` |

## 5. CI kabul raporu ve açıklanmış başarısız deneyler

- İlk NetworkX matrix [run 38363256745](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38363256745) **Ubuntu ve Windows başarı**; o sürümde dışarıdan verilen yüzeylerin hash tutsa bile geometrik olarak uydurulması ayrı kontrol edilmiyordu.
- Bu riski gidermek için kod `analyze_geometry` ile seçilen yüzeyleri tekrar kaynaktan üretmeye başladı. [Run 38363511357](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38363511357): **129 PASS / 2 FAIL** her OS; iki eski test güven kapısının yeni davranışını beklemiyordu.
- [Run 38363582064](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38363582064): **133 PASS / 1 FAIL** her OS; `GeometryAnalysis` üretildikten sonra mutate edilen marker için test lokal uyarı bekliyordu; artık kaynak analizi küresel olarak geçersiz sayılıyor.
- Test ayrıştırıldı: kaynak analizinde yer alan entity frame sonradan değiştirilirse tüm graf kapatılır; ayrı sonradan eklenmiş yanlış-frame marker ise yalnız o geçiş için `UNSUPPORTED_OPENING_SOURCE` döner.
- **Son doğrulanan kod commit `adc88ccc`: [GitHub Actions 38363772668](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38363772668) — Ubuntu Python 3.11: 134/134 PASS, 2,58 saniye; GitHub-hosted Windows Python 3.11: 134/134 PASS, 6,24 saniye.** İki işin sonucunu ayrı iş loglarında doğruladım.
- Bu gerçek kullanıcı i7 14. nesil/RTX 4070 8 GB cihazında veya bağımsız gerçek mimari projelerde saha kabulü değildir. RapidOCR/VLM ya da yasal kural motoru çalıştırılmadı.

## 6. Bilimsel ve ürün kabul sınırları

**Kod:** Tek frame/kattaki reviewed yüzeyleri yeniden DrawingIR'den hesaplamak; yüzeyden mekân beyanı, kaynak marker ve gerçek shared boundary crossing olmadan **graf kenarı vermemek**. Oda merkezlerinden veya katmanlardan otomatik kapı çıkarımı yapılmaz. Graph path minimum kapı sayısıdır, metre ölçüsü/yürüme rotası değildir. `__EXTERIOR__` bağlantısı mevzuata uygun çıkış sertifikası değildir.

**Açık:** CAD'de sürekli duvar çizgisi üzerinde bağımsız gerçek kapı boşluğu tespiti, dönük kapı kanadı ve net geçiş açıklığı, kullanıcı reviewer kimliğinin authentication/audit imzası, modelspace–floor gerçek 3B geçişi, yürüme poligonu, Dijkstra/A* metre rotası, engelli erişimi ve bağımsız yangın hukuku denetimi. Girilen `opening_reviewed=True` gerçek kapı varlığını otomatik kanıtlamaz; **beyan + yerel geometrik kaynak uyuşumu** anlamındadır.

**İşlem 011 sonucu:** F06 **KISMI / MEVCUT_KOD + Linux/Windows sentetik CI PASS**. Sonraki iş **`docs/islem_012.md`** olarak ilk commit öncesi yeni kayıt açılarak deterministik Rule Engine çerçevesini geliştirmek. Hukukî source binding / approved applicability olmadan hiçbir gerçek mevzuat PASS üretilmeyecek.
