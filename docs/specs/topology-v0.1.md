# Mekânsal Topoloji v0.1 — NetworkX + Shapely Kanıtlı Bağlantı Sözleşmesi

- **İşlem:** [islem_011.md](../islem_011.md)
- **Kod:** `src/mimarllm/geometry/topology.py`
- **Hedef:** Tek CAD layout veya PDF sayfasında **inceleme kanıtına bağlanmış** oda/koridor/balkon/sahanlık/merdiven ve geçiş topolojisi; *yangın kaçış mesafesi değildir*.
- **Durum:** Ürün çekirdeğinde Pydantic veri ve NetworkX `MultiGraph` uygulaması; gerçek insan incelemesi, otomatik kapı bulma ve gerçek Windows saha kabulü ayrı.

## 1. Sözleşme ve API

```python
from mimarllm.geometry.spatial import analyze_geometry
from mimarllm.geometry.topology import (
    SpaceKind, SpaceReview, PassageKind, PassageReview,
    build_topology, shortest_passage_path, EXTERIOR_ID,
)

analysis = analyze_geometry(drawing_ir, frame_id="cad:Model")
# analysis.faces[]: UNCLASSIFIED_FACE; otomatik oda değildir

spaces = [
    SpaceReview(
        space_id="room1", face_id=analysis.faces[0].face_id,
        kind=SpaceKind.ROOM, reviewer_id="review-2026-01",
    ),
    SpaceReview(
        space_id="corridor1", face_id=analysis.faces[1].face_id,
        kind=SpaceKind.CORRIDOR, reviewer_id="review-2026-01",
    ),
]
portals = [
    PassageReview(
        passage_id="door-01",
        from_space_id="room1", to_space_id="corridor1",
        kind=PassageKind.DOOR, reviewer_id="review-2026-01",
        supporting_entity_ids=("cad:door-block-or-line-entity-id",),
        path_endpoints=((4.0, 3.0), (6.0, 3.0)),
    ),
]
network = build_topology(
    drawing_ir, analysis, spaces, portals,
    coordinate_tolerance=1e-7,
    support_distance_source_units=.1,
)
possible_path = shortest_passage_path(network, "room1", "corridor1")
# possible_path.note == TOPOLOGICAL_HOPS_NOT_WALKING_DISTANCE
```

`supporting_entity_ids` öğeleri `DrawingIR.entities[].entity_id` değerleridir, DXF handle doğrudan değildir. Bu entity, orijinal CAD `SourceReference.cad_handle/block_path` veya PDF source `polygon/page` bağlantısını taşır. Marker `INSERT`, `LINE` veya benzeri *native kaynak* olabilir; tek başına kapı değildir.

**İnceleme kaydı güvenliği:** `reviewer_id` ve `opening_reviewed` bu sürümde kullanıcıdan gelen **beyan** alanlarıdır. Kullanıcı kimliğinin doğrulandığı, mimarın imzası veya resmî inceleme yapıldığı garanti edilmez. UI daha sonra kimlik, onay, sürüm ve imza/audit kaydını gerçek kullanıcı işlemine bağlayacak.

## 2. Düğümler ve kenarlar

`SpaceKind`: `ROOM`, `CORRIDOR`, `BALCONY`, `STAIR`, `LANDING`. Dış ortam `EXTERIOR_ID="__EXTERIOR__"`, aynı çizim için soyut düğümdür. Her `SpaceReview.face_id`, `GeometryAnalysis.faces[].face_id` içindeki gerçek yüzeyle eşleşir; `floor_label` birden fazla farklı kat iddiası içerirse bu v0.1 **reddeder**. Katlar arası gerçek erişim henüz yoktur.

`PassageKind`: `DOOR`, `ARCHWAY`, `OPEN_PASSAGE`, `EXTERIOR_DOOR`. Kapı, kemer ve açık geçişler kullanıcı incelemesiyle belirtilir. `EXTERIOR_DOOR` yalnız `__EXTERIOR__` düğümüne; yanlış yönlü etiket açık ret. `MultiGraph` iki mekân arasında iki ayrı kapı bulunduğunda iki kenarı da saklar.

Bir iç geçişin ağ kenarı olabilmesi için:
1. Her iki mekânın aynı DrawingIR SHA/frame'de, **yeniden DrawingIR'den hesaplanan** yüzey adaylarıyla eşleşmesi. Salt aynı hash ile gelen uydurma polygon geçmez.
2. Poligon iç bölgeleri örtüşmez; pozitif uzunluklu ortak sınır vardır. Yakın odalar ve sadece köşede dokunan odalar komşu değildir.
3. Kullanıcının seçtiği `path_endpoints` kaynağın/destinasyonun **içerisinde** olmalı, gerçek ortak sınırı **tek POINT** noktasında kesmeli; üçüncü bir mekânın içinden geçmemeli.
4. Yerel native CAD/PDF kaynak çizimindeki açıkça seçilmiş marker, geçişin sınırla kesiştiği noktaya `support_distance_source_units` yakın olmalı. Bu tolerans **kaynak CAD/PDF birimindedir**, metre değildir.
5. `opening_reviewed` ve kullanıcı inceleme kimliği olmalı. Fakat gerçek CAD duvar çizgisinde boşluk veya kapı kanadının çalışır durumda olması **otomatik olarak ispatlanmaz**.

Dış geçiş için kaynak mekânın iç noktası ve bütün seçili mekânların dışındaki nokta ile **tek kaynak dış sınırı kesişimi** gerekir. Bu yalnız incelenen planın **potansiyel dış bağlantısıdır**; erişilebilir giriş, tahliye veya güvenlik çıkışı olduğunu göstermez.

## 3. Dönüş alanları ve sorgular

- `TopologyResult.nodes`: `space_id`, `kind`, `face_id`, `boundary_entity_ids`, `reviewer_id`
- `TopologyResult.edges`: `passage_id`, iki space ID, tür, source marker entity ID, reviewer, `boundary_crossing_point`.
- `TopologyResult.issues`: reddedilen geçiş kimliği ve gerekçe. **Reddedilen geçiş graf kenarı olamaz**.
- `components`: NetworkX bağlı bileşenler.
- `articulation_space_ids`: bir düğüm silindiğinde topolojiyi parçalayabilen düğümler (yangın tahliye hükmü değil).
- `bridge_passage_ids`: bir bağımsız geçişi kaldırmanın grafı böldüğü kenarlar; iki paralel kapıda bir kapı silmek grafı bölmez.
- `exterior_reachable_space_ids`: incelenmiş bağlantılardan `__EXTERIOR__` düğümüne topolojik yolla erişilebilen mekânlar.
- `no_confirmed_exterior_path_space_ids`: **mevcut kanıtla** dış bağlantı kurulmamış mekânlar; gerçek yapıda hiç çıkış olmadığı anlamına gelmez.
- `shortest_passage_path`: en az **kenar sayısıyla** yürütülebilecek topolojik bağlantı dizisi; gerçek yol metre cinsinden hesaplanmaz, `TOPOLOGICAL_HOPS_NOT_WALKING_DISTANCE` etiketi zorunlu.

## 4. Geçersiz/eksik kanıt kapıları

- `TopologyInputError`: yanlış SHA/frame, uydurulmuş/çakışan kaynak poligon, aynı face'in iki farklı node'a atanması, farklı floor id, snapped geometri veya bütçe aşımı. Graf yayımlanmaz.
- `UNKNOWN_SPACE`, `OPENING_UNREVIEWED`, `UNSUPPORTED_OPENING_SOURCE`, `NO_SHARED_BOUNDARY`, `INVALID_PASSAGE_CROSSING`, `THIRD_SPACE_CROSSING`, `OPENING_SOURCE_TOO_FAR`: bu tekil geçiş **reddedilir**, diğer incelenmiş geçişler korunabilir.
- `max_spaces`, `max_passages`, `max_space_pairs`, `coordinate_tolerance`, `support_distance_source_units`: O(n²) yüzey çift karşılaştırma ve Shapely analiz bütçesi ile CPU güvenlik sınırları.

## 5. Sentetik testler ve bilimsel sınırlar

`tests/test_topology.py`: iki oda ve dört alanlı linework, koridor/sahanlık/balkon, `EXTERIOR`, kopuk alan, aynı iki mekânda iki kapı, kaynağı uzakta kapı, sahte OCR kaynak, uydurma geometry face, yanlış kat kimliği, çapraz frame, yanlış exit, belirsiz kaynak ve kaydedilip `ezdxf.readfile` ile açılan gerçek sentetik DXF.

**HOLD:** CAD kapı çizimi/ARC/bulge ve door width geometri üzerinden **otomatik kapı tespiti**, duvar boşluğunun gerçekten geçilebilir olduğunu gözlemleme, 3B merdiven bağlantısı, kat değişimi, yürüme çokgeni ve Dijkstra/A* metre ağı, çıkış/kapı açılış yönü, engelli erişimi, yangın/imar mevzuatına uygunluk.

`room centroid distance` **kaçış mesafesi değildir**. NetworkX en az geçiş sayısı, fiziksel en kısa yol uzunluğu veya mevzuat izin sınırı değildir. Bu aşamada `DrawingIR.findings` ve hukukî kural sonucu oluşturulmaz; yüzey/kapı beyanı otomatik ruhsat kararı değildir.
