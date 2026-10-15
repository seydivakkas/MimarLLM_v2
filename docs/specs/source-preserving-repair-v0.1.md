# Kaynak-Koruyan CAD Onarım Adayı v0.1 — İşlem 022

**Geliştirme kaydı:** [İşlem 022](../islem_022.md). **Modüller:** `src/mimarllm/geometry/repair.py`, `src/mimarllm/geometry/repair_viewer.py`.

## 1. Neden ayrı bir overlay?

İçe alınmış CAD dosyasının `DrawingIR` nesneleri özgün geometri, CAD handle, `block_path`, layer, koordinat frame ve kaynak dosya SHA-256 kimliğini taşır. Kirli CAD'de küçük çizgi boşlukları, aynı konumda tekrarlanan çizgiler ve katman 0'da belirsiz çizimler olabilir. **Bunları otomatik onarıp asıl DrawingIR'yi değiştirmek**, sonradan ölçüye, geçit tespitine veya hukukî rapora yanlış veri sızdırabilir.

Bu nedenle `propose_repair_overlay(...)` sadece **salt-okunur `RepairOverlay`** döndürür. `DrawingIR` olduğu gibi kalır; öneriler `assess_area`, `build_topology`, `RuleEngine` veya hukukî denetim girdisi sayılmaz.

## 2. API

```python
from mimarllm.importers.dxf import parse_dxf
from mimarllm.geometry.repair import propose_repair_overlay
from mimarllm.geometry.repair_viewer import render_repair_overlay_svg

drawing = parse_dxf(r"C:\projeler\kirli_plan.dxf").drawing
frame_id = "cad:Model"
overlay = propose_repair_overlay(
    drawing, frame_id,
    snap_tolerance=0.01,
    max_gap_source_units=0.15,
    max_segments=800,
    max_pairs=250_000,
    max_candidates=300,
)
svg = render_repair_overlay_svg(drawing, overlay)
# SVG, lacivert: asıl native CAD çizgileri / turuncu kesikli:
# yalnız kullanıcı incelemesi bekleyen sanal kısa bağlantılar.
# Yalnız kaynak koordinat birimleri kullanılır, metreye çevrilmez.
```

Buradaki tüm toleranslar **kaynak CAD birimidir**; millimetre, metre, plan ölçeği ya da fiziksel duvar/kapı bilgisi değildir. `$INSUNITS` metrik ipucu `INFERRED` olarak sunulabilir ancak onaylanmış fiziksel boyut üretmez.

## 3. Kaynak kanıtıyla sunulan nesneler

| Nesne | Anlamı | Güven sınırı |
| --- | --- | --- |
| `RepairCandidate.VIRTUAL_GAP_BRIDGE` | Yakın iki özgün CAD uç noktası arasında çizilen sanal kaynak-birimli bağlayıcı | Kasıtlı kapı veya açıklık olabilir; `REVIEW_REQUIRED` |
| `ENDPOINT_SNAP_CANDIDATE` | Çok yakın fakat aynı konumda olmayan iki uç arasındaki yalnızca önerilen bağ | Fiziksel geometriye uygulanmaz |
| `DUPLICATE_SEGMENT_CANDIDATE` | İki farklı kaynak CAD nesnesinin yaklaşık aynı çizgiyi tekrar etmesi | Hiçbir orijinal entity silinmez |
| `OVERLAPPING_SEGMENT_CANDIDATE` | Aynı doğrultudaki iki CAD çizgisinin kısmen örtüşmesi | Hat/sınır otomatik yeniden yazılmaz |
| `UnitHypothesis` | Çizimde zaten bulunan `calibration.state/source_unit/method` özeti | Onarım ölçeği onaylamaz, SI hesaplama üretmez |
| `Layer0SemanticCandidate` | Katman 0'daki doğrusal CAD nesnesini kaynaklı insan incelemesine sunma | Duvar/kapı/kolon/oda sınıfı kesin değildir |
| `RepairIssue` | Bir uç birden fazla komşuya uyarsa `AMBIGUOUS_ENDPOINT_MATCH` | Rasgele seçim yapıp bağ oluşturulmaz |

**Her `RepairCandidate`**: `source_sha256`, `frame_id`, iki gerçek `source_entity_ids`, kaynak `SourceReference` çiftleri ve dolayısıyla **CAD handle, layout, nested INSERT block_path**, durum `REVIEW_REQUIRED`, `overlay_kind=VIRTUAL_CANDIDATE` taşır. Yerel SVG, bunların gerçekte kaydedilmiş CAD onarımı olduğu izlenimini vermez.

Yalnız `CAD_NATIVE`, ilgili `CAD_UNIT` frame'i ve `SEGMENT/POLYLINE/POLYGON` kaynak çizgi parçaları işlenir. Her iki kaynak aynı layer'da değilse bunları tek duvar/açıklık sayıp bağlamaz. **Başka PDF sayfası veya DXF layout'u** `CAD_UNIT` frame'ine katılmaz.

## 4. Deterministik güven sınırları

- Orijinal DrawingIR tüm girişte tekrar doğrulanır; aynı SHA ve aynı frame dışındaki kaynak referansları reddedilir. Kaynak geometriye yazma yok.
- Boşluk önerisi yalnız kaynak çizgi uçları arasındadır ve `may_be_intentional_opening=True` taşır. Aynı orijinal geometriye zaten değen uçlar için bağ önerilmez. Birden fazla makul uç eşleşmesinde `AMBIGUOUS_ENDPOINT_MATCH` üretilir.
- Çizgi eşleşmesi iki gerçek `entity_id` gerektirir, aynı polyline içindeki komşu segmentleri dışarıdan farklı CAD nesnesi gibi göstermez.
- Önce orijinal tekrar/örtüşen çizgiler saptanır; üst üste çizilmiş hatlar silinmez.
- `max_segments`, `max_pairs`, `max_candidates`, `max_layer0`, `max_vertices` bütçeleri aşılırsa açık `RepairInputError`. Belirsiz veya aşırı karmaşık veri kesin sonuca çevrilmez.
- SVG gerçek kaynağı lacivert, öneriyi turuncu kesikli gösterir. SVG bağlantı/etiketleri CAD kaynağı kullanıcı metni için HTML escape uygular. Ölçek/koordinat yalnız ekran çizim dönüşümüdür.

## 5. Mevcut olmayan kabul

**KODLANDI/KISMI:** Kaynak-koruyan onarım adayı üretimi, Layer0 yalnız inceleme sınıflaması, SI onayı olmayan birim ipucu, CAD handle'lı SVG. **YAPILMADI:** Otomatik kaynak CAD dosyası kaydetme/otomatik “onarımı kabul et” işlemi; tüm CAD spline/hatch/polyline karmaşık kaynak onarımı; gerçek saha mimari semantik/kapı doğruluğu; metrik net/brüt alan; yangın kaçış rotası; gerçek Windows/Edge kullanıcı görsel kabulü. Gerçek hukuken yürürlükte mevzuat ve `F08–F12` hâlâ `HUKUKI_HOLD`. Dashboard'ta bu SVG için özel canlı onay editörü bir sonraki UI geliştirmesine bırakıldı.

**Sıradaki teknik paket**: `islem_023` A0/A1 doküman yerleşimi, PDF tile/ROI OCR, kaynak koordinat ve bellek bütçesi. Bu kod yazılmadan önce işlem kaydı oluşturulacak.
