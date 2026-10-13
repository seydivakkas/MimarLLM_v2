# Geometry Engine v0.1 — Shapely / DrawingIR

- **İşlem:** [islem_010.md](../islem_010.md)
- **Kod:** `src/mimarllm/geometry/spatial.py`, `walls.py`
- **Kaynaklar:** `DrawingIR` (işlem 007), DXF native (008), PDF native (009).
- **Yazılım bağımlılığı:** Shapely 2 / GEOS (CPU; yayın/NOTICE paket denetimi ayrıca).
- **Durum:** Sentetik geometrik analiz sözleşmesi. Oda sınıflandırması ve sahada net alan kabulleri ayrı.

## 1. Ana iş akışı

```text
DrawingIR [DXF or PDF] + one frame_id
   -> allowed native linework filter (LINE/LWPOLYLINE/PDF_LINE/PDF_RECT)
   -> per-segment source entity ID + original document SHA
   -> intersection: SHARED_ENDPOINT / T_JUNCTION / CROSSING
   -> overlap/duplicate checks
   -> unary_union (noding) + polygonize_full
   -> UNCLASSIFIED_FACE candidates + polygonize issues
   -> (optional) explicitly selected INTERIOR_ROOM / EXTERIOR_ENVELOPE
      -> exact one face + no ambiguity + reviewer selection
      -> CONFIRMED source scale bound to same coordinate frame?
         YES -> area m2 with role and source references
         NO  -> INSUFFICIENT_EVIDENCE (no physical area)
```

### Çalışan API

```python
from mimarllm.geometry.spatial import analyze_geometry, assess_area
from mimarllm.geometry.walls import find_parallel_edge_gaps

a = analyze_geometry(
    drawing_ir, "cad:Model",
    max_segments=1200, max_pairs=250_000, max_faces=300,
    snap_tolerance=0.0,
)
# a.faces: [] ya da kaynak boundary ID'li, sınıflandırılmamış poligonlar
# a.intersections: kaynak kimlikleriyle segment kesişim ve birleşimleri
# a.issues: open line, cut, invalid ring, overlapping segment

room = assess_area(
    drawing_ir, "cad:Model", source_entity_ids=["E1", "E2", "E3", "E4"],
    boundary_role="INTERIOR_ROOM",
    reviewer_id="review-session-id",
)
# role EXTERIOR_ENVELOPE da olabilir: yalnız footprint, legal gross GFA değil

walls = find_parallel_edge_gaps(
    drawing_ir, "cad:Model", min_gap=10, max_gap=400,
    min_overlap=100,
)
# Bütün mesafeler seçilen DrawingIR frame SOURCE UNIT birimindedir.
```

## 2. Kaynak ve birim koruma

`GeometryAnalysis.source_sha256`, `AreaAssessment.source_sha256` ve `WallGapResult.source_sha256` dosya SHA-256'sını korur. Her yüzey `boundary_entity_ids` listesiyle ilgili CAD handle/PDF sayfasına DrawingIR üzerinden dönebilir. Her kesişim `first_entity_id/second_entity_id`, nokta koordinatı ve `kind` saklar.

DXF'deki CAD çizim birimi veya PDF 1/72 inch **fiziksel mimari metre değildir**. Fiziksel `physical_area_m2` sadece bütün koşullarda üretilir:

1. Kullanıcı ayrı `source_entity_ids` listesini **iç yüz sınırı** veya **dış zarf** olarak doğrulamalı.
2. Seçim tek frame/page/layout içinde; ID'ler mevcut, benzersiz ve gerçek native sınır çizgisi olmalı.
3. Seçilen çizgiler tek, kendisiyle çelişmeyen ve **hiçbir dangling/overlap/cut olmayan** kapalı Shapely yüzeyi oluşturmalı. Snapping/algoritmik boşluk tamiri onaylı ölçü için kullanılmaz.
4. `UnitCalibration.state=CONFIRMED`, `calibration_frame_id` aynı `frame_id`; alan `source_area * metres_per_unit²`.
5. Yanlış veya eksik bilgi durumunda `REVIEW_REQUIRED` / `INSUFFICIENT_EVIDENCE` ve `physical_area_m2=None`.

**`reviewer_id` kimlik doğrulama değildir:** bu v0.1, dış uygulama tarafından sağlanan bir gözden geçirme alanıdır. Saha ölçüm yetkisini ve yapı hukuku geçerliliğini kanıtlamaz. UI gerçek reviewer kimlik/onay kayıtları ayrıca eklenecek.

## 3. Aday yüzey ve mimari anlam ayrımı

`UNCLASSIFIED_FACE` poligonun topolojik olarak kapandığını söyler; oda olduğunu veya m² mevzuatını sağladığını söylemez. İç poligon geometrisi, duvarın orta aksı veya dış bina kabuğu farklıdır. Kullanıcı **doğru iç duvar yüzeyi çizgilerini** seçmemişse `assess_area` görünürde sayısal ve kapalı olsa bile mimari gerçekliğe ilişkin garanti değildir.

- `INTERIOR_ROOM`: kullanıcıca doğru iç yüz sınırı seçildiği varsayımıyla ilgili **tek oda iç alanı**; birden fazla oda için önce ayrı assessment, toplam için daha sonra ayrı ölçü denetimi.
- `EXTERIOR_ENVELOPE`: kullanıcıca doğru dış sınır seçimiyle **bina footprint alanı**; ruhsata esas emsal, toplam brüt kat alanı veya yönetmelik gross floor area değildir.
- **Duvar kalınlığı:** `find_parallel_edge_gaps` yalnız paralel ve projeksiyonda örtüşen iki kaynağın aralığını döndürür. Kapı çevresi, aks çizgileri, kolon/kiriş, bağımsız kaplama ve çizimdeki çizgilerin gerçek duvar yüzeyi olması doğrulanmadan kalınlık değildir.
- **Otomatik buffer yok:** Orijinal yüzeyden kabaca `buffer(-wall_thickness)` ile net alan uydurulmaz.

## 4. Çizim hataları ve tolerans politikası

| Kanıt / durum | Kaynak izleme | Mimari hüküm |
| --- | --- | --- |
| `DANGLING_OR_OPEN_EDGE` | frame + problem bileşen sayısı | Açık yüzey, kesin alan yok |
| `UNASSIGNED_CUT_EDGE` | frame | Fazla/kesit çizgisi olabilir; kesin sınır seçimi kontrolü |
| `OVERLAPPING_SEGMENTS` | iki kaynak entity ID | Çakışma; alan onayı bloklanır |
| `INVALID_RING` | frame | Geçersiz halka; kesin alan yok |
| `SELF_INTERSECTING_SOURCE` | tek kaynak entity ID | Kendiyle kesişme; kesin alan yok |
| `SHARED_ENDPOINT` | kaynak ID çiftleri ve X,Y | Kaynak segment uç birleşimi |
| `T_JUNCTION` | kaynak ID çiftleri ve X,Y | Bir çizgi başka çizginin iç noktasına bağlanır |
| `CROSSING` | kaynak ID çiftleri ve X,Y | Kaynak çizgiler birbirini içten keser |
| `SNAPPED_TOPOLOGY_UNVERIFIED` | frame | Yalnız alternatif yüzey adayları; ölçüm onayı değil |
| `UNSUPPORTED_BOUNDARY_SOURCE` | açıkça seçilen kaynak ID | OCR/metin/point kaynak duvar sınırı değildir |

Genel PDF taramasında glyph/point/INSERT gözlemleri sınır hesabından sessizce **filtrelenir**; yanlış bir kullanıcı seçimi yapıldığında kaynak ID ile diagnostic verilir.

`snap_tolerance=0` varsayılandır. Sıfırdan farklı snap ile elde edilen yüzey sadece `REVIEW_REQUIRED` sayılır; `assess_area` snap kullanmaz. Eşikleri doğru plan ölçeğine göre mühendis belirler; 1 CAD birimini 1 metre saymak yasaktır.

## 5. Kaynak/cpu limitleri

- `analyze_geometry`: max 1200 kaynak segmenti; varsayılan pair budget 250.000, en çok 1500 intersection ve 300 yüzey. Segment/pair/faces sınırı aşılırsa `GeometryInputError`. Bu başlangıç politikası büyük mimari paftalar için **ön işlem ve spatial-index tabanlı optimizasyon** gerektirir; büyük çizim otomatik kabul edilmez.
- `find_parallel_edge_gaps`: varsayılan 650 segment / 210.000 çift / 1000 aday güvenlik limitleri; CPU-only, çıkarım dış API yok.
- `min_face_area`, `min_gap/max_gap`, `min_overlap`, `snap_tolerance` seçili frame'in kaynak birimindedir. Bu parametreler yönetmelikteki asgari ölçüler değildir.
- Shapely polygonize üretimi geometrik sağlamlık kanıtıdır; katman adı `A-DUVAR` olsa bile oda ve duvar semantiği otomatik PASS değildir.

## 6. Test kapsamı ve kabul sınırı

`tests/test_geometry.py` sentetik DrawingIR, **diske yazılıp gerçekten yeniden açılan ezdxf iki odalı plan**, ReportLab ile oluşturulmuş PDF_RECT, iki oda, açık/duplicate/overlap/self-cross çizgi, kaynak SHA, frame karışması, onaysız ölçek, kullanıcı onayı, m², footprint, paralel çizgi aralığı, kalınlık false-positive, intersection T/cross ve güvenlik bütçesi senaryolarını içerir.

**Bu aşamada uygulanmayanlar:** Duvar çift çizgilerini global olarak eşleştirip dolu duvar poligonunu doğrulama, kapı/pencere açıklığına göre oda iç sınırı tamamlama, dış duvar-internal wall face ayrımı, sürekli kat alanı, CAD-layer güven modeli, geçiş grafı ve yangın yürüme ağı. Bunlar islem_011 ve daha sonraki paketlerin hedefleridir. Gerçek mimarî projelerde manuel kanıt değerlendirmesi gereklidir.
