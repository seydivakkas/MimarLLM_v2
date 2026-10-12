# DXF Import v0.1 — DrawingIR veri sözleşmesi ve dürüst destek matrisi

- **İşlem:** [islem_008.md](../islem_008.md)
- **Kaynak:** `src/mimarllm/importers/dxf.py` ve `layers.py`.
- **Kapsam:** Yerel DXF modelspace; onaylı parametre ile paper layout; ezdxf native entity source handles, nested block insertion ve curved geometrinin kontrollü düzleştirilmesi.
- **Güven:** Bu kod ölçüleri ve semantiği kanıtlayamaz; geometrik gözlemleri kaynak dosyaya bağlar. Windows gerçek pafta kabulü ayrıca.

## 1. Aktif API

```python
from mimarllm.importers.dxf import parse_dxf

result = parse_dxf(
    "plan.dxf",
    max_file_bytes=25_000_000,
    max_entities=100_000,
    max_block_depth=8,
    max_points_per_entity=8_000,
    curve_flatten_distance=0.05,  # CAD source units, NOT metres!
    include_paperspace=False,
)

drawing_ir = result.drawing    # DrawingIR v0.1
annotations = result.annotations  # TEXT/MTEXT/ATTRIB/DIMENSION candidates
issues = result.issues        # quality + unsupported + approximation
layers = result.layers        # names and unverified lexical hints
```

## 2. Kaynak format ve geometrik durum

| DXF türü | v0.1 uygulama rolü | Kritik sınır |
| --- | --- | --- |
| LINE | WCS 2B SEGMENT | 3B/elevated olan reddedilir |
| LWPOLYLINE | WCS, bulge dahil `ezdxf.path.make_path(...).flattening(...)` | Tessellation approximation; OCS -> WCS ezdxf path; yakınlık toleransı CAD birim |
| ARC | Flattened POLYLINE | Gerçek eğrilik/radius analizi üretilmez |
| CIRCLE | Flattened POLYGON | Doğrudan ROOM/usable polygon kabul edilmez |
| TEXT, MTEXT | POINT anchor + native text `DxfAnnotation` | Yazı çevresinin gerçek quad'ı henüz yok |
| DIMENSION | POINT anchor + style/override doğrulanmamış `raw_dimension_value` | Ölçek kalibrasyonu ve fiziksel doğruluk çıkarılmaz |
| INSERT | POINT anchor + nested child expansion | Orijinal INSERT handle, kaynak BLOCK child handle ve insert path korunur |
| MINSERT | Her instance için farklı source path | `ATTRIB` bütün MINSERT örnekleri için otomatik çoğaltılmaz |
| Unsupported | `DxfIssue` | Silent PASS yok |

**Önemli:** `LWPOLYLINE` kalınlık, genişlik ve CAD linetype v0.1'de semantik geometri üretmez. `arc` ve `circle` gerçek mühendislik çizimi yerine kaynak birimi bazlı tessellation yaklaştırmasıdır. Sınırlı 2D düzlemsel çıktı doğrudan mimari uygunluk raporu değildir.

## 3. Örnekleme ve nested dönüşümler

Bir iç blok `LWPOLYLINE` veya `LINE` içerdiğinde, orijinal block definition **değiştirilmez**, yeniden kaydedilmez. `child.matrix44() @ parent_matrix` bileşkesi her instance için uygulanır. Böylece aynı kaynak child CAD handle birden fazla yerleşimde görünse bile `DrawingEntity.entity_id` ve `SourceReference.block_path` farklıdır.

```text
entity_id: Model|34:OUTER:instance0|22:INNER:instance0|1B|LINE
source.cad_handle: 1B
source.block_path:
  - 34:OUTER:instance0
  - 22:INNER:instance0
source.frame_id: cad:Model
source.document_sha256: original local file SHA-256
```

Örnek kimlikler sentetiktir. Gerçek DXF handle'ları dosyanın kendisinden alınır.

**Blok sınırları:** XREF, dynamic block, clipping path/XCLIP, complex OCS, nested MINSERT attribute duplication, 3D, nonuniform text geometry/kısıtlı DIMENSION, ACAD_PROXY_ENTITY kapsam dışı veya `DxfIssue` uyarı durumundadır. Aynı adı tekrar içeren blok referansı döngüsü `CYCLIC_BLOCK`; eksik kaynak `MISSING_BLOCK`; max depth `MAX_BLOCK_DEPTH`; aşırı tessellation `TESSELLATION_LIMIT`.

## 4. Birim ve ölçü kanıtı

- `header["$INSUNITS"]` → `UnitCalibration.INFERRED`; kullanıcı bağımsız doğrulamadan `CONFIRMED` değildir.
- Yanlış birim veya onaysız ölçü için `metres_per_unit` olsa dahi fiziksel metre dönüşümü reddedilir.
- DXF DIMENSION `get_measurement()` yalnız ham DXF sayısına adaydır; `DIMSCALE`, DIMLFAC, override, angular dimension, block transform ve gerçek referans noktaları kontrol edilmeden yönetmelik ölçümü olmaz.
- Bütün sonuç `DrawingIR.entities[]` içinde `is_verified_semantics=False`; `DrawingIR.findings=[]`.

## 5. Güvenli çalışma

- Girdi DXF uzantısı, dosya sınırı, `ezdxf.readfile` ve DXF auditor kontrolü.
- Entity sayısı, nested depth, curve point sayısı ve kaynak dosya boyutu için ret kapısı.
- Kaynağın SHA-256 değişirse eski entity'ler yeni kaynak kimliğine ait sayılmaz.
- OCR/VLM/RAG veya bulut API çağrısı yapılmaz; harici dosya/link çözümleme özelliği bu aşamada yok.
- Sınırlı parser, ancak tüm gerçek DXF saldırılarına karşı sandbox garantisi değildir: dışa açık sunucuya upload açmadan önce izolasyon ve güvenlik regresyonu gerekir.

## 6. Sentetik kabul

`tests/test_dxf_parser.py`: test sırasında `ezdxf.new()` ile oluşturulmuş DXF'lerin **diske kaydedilip tekrar gerçekten okunması**; LINE/LWPOLYLINE/ARC/CIRCLE/TEXT/MTEXT/DIMENSION, nested blok iki kez yerleştirme, MINSERT, katman adayı, unknown INSUNITS, invalid input, entity budget, 3D reject, paperspace opt-in.

**Başarı ve kalan sorunlar için nihai referans:** [islem_008.md](../islem_008.md) GitHub Actions CI günlüğü.

## 7. Sonraki adım

`islem_009`: PDF koordinat/rotasyon ve RapidOCR ROI'leri DrawingIR'ye tutarlı bağlamak. Ardından `islem_010`: Shapely duvar/oda/topoloji gerçek geometri çıkarmak; DXF kaynak içeriği **duvar** sayılmadan önce kurallı/kanıtlı doğrulama.


## 8. Son uygulama sertleştirmeleri (2026-10-13)

- MINSERT `mcount`, açılacak örnekler belleğe `list()` yapılmadan önce kontrol edilir; oluşturulan instance'lar generator ile gezilir.
- Block/nonuniform scale altında tessellation local toleransı, birikimli affine matrisin Frobenius üst sınırına bölünür; böylece blok ölçek büyütmesi nedeniyle çıktı CAD koordinatlarında yaklaştırma toleransı sessizce gevşemez. Bu algoritma daha yüksek hassasiyet gerektiren mühendislik analizinde yine bağımsız referans karşılaştırması ister.
- XREF flag alanı dış kaynak olarak işaretlendiğinde dosya açılıp getirilmez; `XREF_UNRESOLVED` diagnostic döner ve hatalı tamlık kabulü engellenir.
- `tests/test_dxf_parser.py` üzerinde bu üç sınır için sentetik regresyon örnekleri eklendi.
