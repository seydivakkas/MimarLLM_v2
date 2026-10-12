# DrawingIR v0.1 — Kaynak Geometri ve Kalibrasyon Sözleşmesi

- **İşlem:** [islem_007.md](../islem_007.md)
- **Kod:** [ir.py](../../src/mimarllm/core/ir.py), [units.py](../../src/mimarllm/core/units.py)
- **Durum:** Pydantic V2 modelleri GitHub'da; otomatik test ve hedef Windows kabulü ayrı izlenir.
- **Amaç:** CAD/PDF ve raster kaynağın **neyi gerçekten gösterdiği** ile fiziksel ölçüm ve hukukî yorumun birbirinden ayrılması.

## 1. Veri hiyerarşisi

```text
DrawingIR (schema_version=0.1)
├── source_sha256 + source_kind + parser_version
├── frames[]: CoordinateFrame(kind, y_direction, view/page)
├── transforms[]: Transform2D(source_frame, target_frame, six affine terms)
├── calibration: UnitCalibration(state, method, metres_per_unit, evidence_ids)
├── entities[]:
│   ├── GeometryPrimitive(POINT/SEGMENT/POLYLINE/POLYGON)
│   ├── SourceReference(file hash, page/view, CAD handle / block path / PDF polygon)
│   └── EvidenceOrigin(CAD/PDF/OCR/VLM/USER)
├── measurements[]: method, source_value, tolerance, entity IDs,
│                    optional physical_value + unit (CONFIRMED required)
└── findings[]: PASS/FAIL/REVIEW_REQUIRED/INSUFFICIENT_EVIDENCE/
                NOT_APPLICABLE/ERROR with referenced entity/evidence IDs
```

**Bu modül henüz DXF/PDF dosyasını kendisi okumaz.** Var olan `core/models.py` PDF kaynak karakter gözlemi için ayrı sözleşmedir. İleride `islem_008` DXF parser ve `islem_009` PDF adaptor bu şemaya dönüştürecek.

## 2. Koordinat sözleşmesi

| Frame türü | Birim | Y yönü | Zorunlu kaynak | Fiziksel ölçüm şartı |
| --- | --- | --- | --- | --- |
| `CAD_UNIT` | Çizim kaynak birimi | Tipik `UP`; dosyaya göre deklaratif | `view_id` / modelspace-layout | `UnitCalibration` CONFIRMED |
| `PDF_POINT` | 1/72 inç **sayfa uzayı**, mimari dünya birimi değil | Genelde `DOWN` | PDF `page_index` | Pafta ölçek/ölçü kalibrasyonu |
| `PIXEL` | Raster piksel | Genelde `DOWN` | Görüntü `page_index` | Grafik ölçek veya onaylı fiziksel referans |
| `METRE` | Fiziksel metre, normalize çıktı | açık tanımlanmış | Güvenilir dönüşüm | Kaynak geometri ve kalibrasyon |

`Transform2D` şu 6 affine katsayıyı saklar:

```text
x_target = a*x_source + b*y_source + c
y_target = d*x_source + e*y_source + f
coefficients = (a, b, c, d, e, f)
```

Singular, nonfinite veya başka frame'e bağlanmayan matris kaydedilmez. Ters dönüşümden sonra orijinal nokta tolerans içinde bulunmalı. PDF rotation/crop, OCR ROI homography veya CAD blok matrislerinin birleşmesi **henüz tam uygulanmış değildir**; yalnız affine çekirdek hazır. Kompleks perspektif/homografi için daha sonra ayrı sürüm gerekir.

## 3. Ölçek ve fiziksel ölçüm güven modeli

- `UNKNOWN`: birim bilinmiyor; `metres_per_unit=None`.
- `CONFLICT`: çelişen birim kanıtları var; `metres_per_unit=None`.
- `INFERRED`: header veya referans hesabından ölçek adayı var fakat fiziksel ölçüm için yetkili değil.
- `CONFIRMED`: kaynak referans kimliği + açık kullanıcı onayı / uygun kalibrasyon doğrulaması var. **Yalnız bu durumda** SI dönüşüm yapılabilir.

`UnitCalibration.from_dxf_insunits(4)` (mm) varsayılan **INFERRED**; `user_confirmed=True` ile **CONFIRMED**. Kodlanan header ID'leri: `1=in`, `2=ft`, `4=mm`, `5=cm`, `6=m`. Desteklenmeyen kodlar `UNKNOWN`.

`UnitCalibration.from_reference(source_distance, known_distance_metres, evidence_id, method, user_confirmed)`: `DIMENSION`, `GRAPHIC_SCALE` veya `USER_REFERENCE` için kullanılır. Gerçek fiziksel referansın doğruluğu otomatik kanıtlanmaz; kullanıcı/denetçi onayı gerekir. `source_distance` ve `known_distance_metres` pozitif/sonlu olmalıdır. **Çizimin bounding box'ından otomatik birim veya ölçek çıkarılmaz**.

```python
from mimarllm.core.units import UnitCalibration

candidate = UnitCalibration.from_dxf_insunits(4)
# candidate.length_metres(1000) -> CalibrationError

confirmed = UnitCalibration.from_dxf_insunits(4, user_confirmed=True)
confirmed.length_metres(1000)         # 1.0 metre
confirmed.area_square_metres(1e6)     # 1.0 m2
```

Bu örnek `INSUNITS=4` bilgisinin doğru olduğu **varsayılarak kullanıcı onayı verildiği** senaryodur. Yanlış metadata'nın kullanıcıca yanlış onaylanması hâlâ risklidir; ikinci bağımsız doğrulama ilerideki geliştirme konusudur.

## 4. Kaynak referansı ve nesne güveni

- `SourceReference` kaynak SHA-256, DXF handle + layout + nested block ID veya PDF/raster page + 4 nokta ilişkisini tutar.
- `DrawingEntity` ilk okuma sırasında `type_candidate="UNCLASSIFIED"` kalır; `layer="A-WALL"` verilmesi duvar olduğunun kanıtı değildir.
- `CAD_NATIVE` veya `PDF_NATIVE` geometrinin kaynak türünü, `OCR_CANDIDATE`/`VLM_CANDIDATE` ise aday çıkarımın niteliğini belirtir. Kesin semantik ile bu adaylar çelişirse kullanıcı incelemesi gerekir.
- Degenerate segment geometrisi ilk ayrıştırmada atılmaz: sonraki geometri modülü **sıfır uzunluk/çift çizgi** sorununu tespit edebilsin.
- Farklı dosya SHA, olmayan entity/frame, çelişen PDF page/view veya yanlış kaynak türü **model_validation error**.
- Bulgu `FAIL`/`PASS` durumunu iddia ediyorsa var olan entity ve measurement evidence referansları zorunludur. Hukukî `PASS` üretilmez; `legal_compliance_certified=True` bu sürümde her zaman reddedilir.

## 5. Sentetik kabul örnekleri

| Alan | Test |
| --- | --- |
| INSUNITS | Bilinen kodlar, bilinmeyen kod ve ön onay yoksa ölçüm reddi |
| Reference calibration | 100 çizim birimi ↔ 2 m, kanıt ID, sonlu/belirli değer |
| Length vs area | 100 cm = 1 m; 10.000 cm² = 1 m² |
| Transform | Y tersleme, öteleme, ölçek ve 45° affine roundtrip |
| Kaynak SHA | Kaynak değişirse eski entity referansı reddedilir |
| Frame | PDF sayfası/CAD layout karışımı reddedilir |
| Kanıt | Olmayan entity/evidence referansı reddedilir |
| Semantik | VLM adayına verified flag konamaz |
| Belirsizlik | Unknown ölçüm otomatik metreye dönüştürülmez |
| Seri hale getirme | Aynı normalize şemanın JSON tekrarında sabit yapı |

**Limitler:** Pydantic model doğrulaması, CAD ölçülerin semantik gerçekliğini, kuralın kanunî doğruluğunu veya bir çizimin hatasız olduğunu kanıtlamaz. Fiziksel boyutun bağımsız doğrulanması sonraki adımlarda eklenecek.

## 6. Kapanmamış mühendislik maddeleri

- `islem_008`: `ezdxf` nested blocks/XREF/OLS/MINSERT, source handles, dimension style ve tolerans.
- `islem_009`: PDF layer/rotation/CropBox ve OCR bbox'ları gerçek source point sistemine bağlama.
- `islem_010`: Shapely geometri/topoloji ve alan hesaplarında interior boundary.
- F01 bütünleşik Windows/gerçek çizim kabulü tamamlanmadı.
- Modelin saf Pydantic/CPU sözleşmesinde bulut AI/VRAM ihtiyacı yok.

## 7. Uygulama sırasında güçlendirilen güven kapısı: frame-bound calibration

İlk model incelemesinde fiziksel kalibrasyonun farklı PDF sayfasına veya DXF layout'una yanlışlıkla taşınabileceği görüldü. Bunun için `DrawingIR.calibration_frame_id` alanı eklendi. `UnitCalibration` fiziksel oran içeriyorsa bu alan **zorunludur** ve `DrawingIR.frames[]` içindeki gerçek bir `frame_id` olmalıdır.

`MeasurementEvidence.physical_value` sadece `CONFIRMED` + **ölçümün frame'i = kalibrasyon frame'i** olduğunda kabul edilir. Ayrıca kaynak ölçüden SI dönüşüm matematiği yapılır; kaydedilen fiziksel değer, kalibrasyon çarpanına (`length: scale`, `area: scale²`) uymuyorsa reddedilir.

Bu **v0.1 tek kalibrasyon-frame** modelidir. Aynı belgede birden fazla pafta / view farklı ölçeğe sahipse ayrı `DrawingIR` işlenmeli veya gelecekte frame başına sürümlü `calibrations[]` şeması getirilmelidir. İlk sürüm aynı ölçeği otomatik tüm sayfalara uygulamaz.
