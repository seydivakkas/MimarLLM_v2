# İşlem 011 — NetworkX mekânsal geçiş topolojisi ve kanıtlı bağlantılar

- **Tarih:** 2026-10-13
- **Durum:** ÖN KAYIT; bu işleme ait ilk GitHub yazımıdır.
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

## 4. Kabul ve bitiş

Sentetik CI Ubuntu/Windows kontrolü + gerçek commit SHA'sı, insan onaylı bağlantı sözleşmesi ve open issues burada tamamlanacak. Bu adım gerçek Windows kullanıcı PC'sinde 3B/yangın kabulü yerine geçmez.
