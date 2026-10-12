# İşlem 007 — DrawingIR v0.1, CAD birimleri ve kaynak kanıt sözleşmeleri

- **Tarih:** 2026-10-13
- **Durum:** UYGULANDI — sözleşme ve sentetik CI kabulü; gerçek Windows/DXF ve tümleşik sistem kabulü açık.
- **Repo:** `seydivakkas/MimarLLM_v2`
- **Önceki kayıtlar:** `islem_001`…`islem_006` korunur. İşlem 007'nin kapsamı [uygulama yol haritasındaki F01](uygulama-yol-haritasi.md) ile sınırlı.
- **İstek:** `DrawingIR` şeması, kalibre edilebilir birim/ölçek modeli, CAD/PDF referans koordinatları, native geometrik varlıkların kaynak kimliği ve izlenebilir geometri/bulgu kanıtını Pydantic V2 ile kodlamak; sentetik testler oluşturmak ve gerçek sonuçları kaydetmek.

## 1. İnceleme ve mimari sınır

Mevcut `src/mimarllm/core/models.py` yalnız PDF source observation sözleşmesidir. Silinmeyecek veya kırılmayacak. Yeni modeller `core/ir.py` ve `core/units.py` içine gelecek. İlk iş **DXF parser değil**: `ezdxf` ile geometri alma sonraki `islem_008` işidir.

## 2. Sözleşme kararları

- Dosya hash'i SHA-256; kaynak `DXF/PDF/IMAGE`; referans, katman, kaynak DXF handle/blok yolu veya PDF sayfa + polygon.
- Ayrı bir `CoordinateFrame`: `CAD_UNIT`, `PDF_POINT`, `PIXEL`, `METRE`; `Y_UP/Y_DOWN` ve koordinat sistemi kimliği.
- `Transform2D`: explicit affine 2×3 katsayı + kaynak/hedef frame; determinant=0 reddi; inverse/roundtrip; başka frame'e doğrudan geçiş uydurulmaz.
- CAD header `$INSUNITS` biliniyorsa `HEADER_UNITS` ile fiziksel dönüşüm kayıtlı; UNKNOWN/CONFLICT/INFERRED otomatik SI hükmü veremez.
- Ölçü çizgisi veya grafik ölçek ile kalibrasyon, **bağımsız onay** ve kaynak referans ID gerektirir. Çizim boyutundan/alanından ölçek çıkarma yasak.
- `GeometryPrimitive` kaynak geometri olarak saklanır; `WALL/DOOR/ROOM` sınıfı ancak kanıtlanmış sonraki geometri ve kullanıcı inceleme süreciyle verilir.
- Bulguda `PASS/FAIL/REVIEW_REQUIRED/INSUFFICIENT_EVIDENCE/NOT_APPLICABLE/ERROR`; dayanak varlığı ile hukukî uygunluk iddiası ayrılır.
- Teknik veya hukukî `PASS` kararı bu işlemde üretilmez: yalnızca **şema ve kapı** tasarlanır.

## 3. Planlanan kaynak dosyalar

- `src/mimarllm/core/units.py`: `LengthUnit`, `CalibrationState`, `CalibrationMethod`, `UnitCalibration`, CAD header birim çözümleme, explicit reference calibration.
- `src/mimarllm/core/ir.py`: `DrawingIR`, `CoordinateFrame`, `Transform2D`, `SourceReference`, `GeometryPrimitive`, `DrawingEntity`, `MeasurementEvidence`, `Finding`, provenance/status ayrımları.
- `tests/test_units.py`, `tests/test_drawing_ir.py`: sentetik header, ölçek, matris, kaynak hash, statü, belirsizlik, hata örnekleri.
- `docs/specs/drawingir-v0.1.md`: veri sözleşmesi, güven kapıları ve test sınırlamaları.
- `docs/ozellik-envanteri.md`, `README.md`: gerçek uygulama durumunun güncellenmesi.

## 4. Kapsam dışı ve doğrulama sınırı

DXF okunması, alan/oda/duvar tespiti, Shapely/NetworkX, OCR görüntü çıkarımı, mevzuat veya arayüz kodu bu işlemde uygulanmayacak. GPU veya haricî AI API'si gerekmiyor. Yerel sentetik test sonucu, GitHub CI ve kullanıcının Windows kabulü ayrı durumlar olacak.

## 5. Sonuç / gerçek GitHub işlem kaydı

**İşlem kaydı önceliği:** `docs/islem_007.md` ilk olarak commit `13d2226` ile açıldı; bundan sonra kod yazıldı.

| Dosya | Gerçek değişiklik | GitHub commit |
| --- | --- | --- |
| `src/mimarllm/core/units.py` | CAD `$INSUNITS`, fiziksel birim, referans kalibrasyonu, UNKNOWN/INFERRED/CONFIRMED/CONFLICT | `a66aba6` |
| `src/mimarllm/core/ir.py` | DrawingIR, frame, affine+inverse, entity/source, geometry, measurement, finding | `0036142` |
| `src/mimarllm/core/ir.py` | SI ölçüm/katsayı eşitliği, frame bazlı kalibrasyon ve doğrulama hızı düzeltmeleri | `37936b1`, `fb9efe3`, `a0d4790` |
| `tests/test_units.py` | Yerel sentetik birim/reference testleri | `3ae8537` |
| `tests/test_drawing_ir.py` | Frame/source/geometry/evidence/testler; CI sonrası test onarımı | `c13d9bb`, `2e4ca48`, `af1ebd7` |
| `docs/specs/drawingir-v0.1.md` | Gerçek kaynak/koordinat/kalibrasyon sözleşmesi | `9c957d5`, `f8fd463` |
| `.github/workflows/core-contracts.yml` | Ubuntu/Python 3.11 sentetik sözleşme test workflow | `feba2cd` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md` | F01 kısmi kod durumu, sonraki islem_008 işi ve bağlantılar | `31cc938`, `919c07b`, `0b1bdc3` |

### Gerçek otomatik test raporu

- İlk CI çalışması [run 38313212456](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38313212456): **46 PASS, 1 FAIL**. Testte `frame_id` senaryosu yanlış kurulmuştu; test düzeltildi.
- Sonraki aşamada `calibration_frame_id` güven kapısı eklendi ve fiziksel ölçümsel sonuç `source_value * scale` ile `area * scale²` olarak kontrol edildi.
- **Nihai kod commit `a0d4790`** için [CI run 38313585310](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38313585310): **49 PASS / 0 FAIL**, **Ubuntu Linux + Python 3.11**, pytest; 0.57 s test süresi (GitHub Actions logu). Bu sonuç gerçek hedef Windows bilgisayarındaki CPU/GPU benchmark değildir.
- CI yalnız seçili bağımlılıkları ve sentetik PDF/IR testlerini kurdu; RapidOCR model inference yürütülmedi. `pyproject.toml` OCR paketlerini ana bağımlılık olarak listeler, ancak bu sentetik CI işinde performans ve model testleri yapılmadı.
- Birim/kalibrasyon/transform modelleri saf CPU/Pydantic olup haricî AI API veya VRAM gerektirmez.

### Güvenlik ve performans sınırı

- `UnitCalibration` onaysız `INFERRED` ise gerçek metre/metrekare dönüşümü reddedilir.
- Her fiziksel ölçüm `calibration_frame_id` ile aynı coordinate frame'e bağlı olmak zorundadır. Belgede birden fazla farklı pafta ölçeği bulunursa bu v0.1 şemasında ayrı DrawingIR gerekir veya gelecekte frame başına kalibrasyon şeması gerekir.
- `DrawingIR.check_graph` entity lookup artık tüm entity listesini her ölçüm için yeniden taramaz; kimlik sözlüğü ile eşler.
- `Finding` `legal_compliance_certified=True` kabul etmez. RAG/hukukî onay modülü bu işlemde yoktur.

### Kalan işler — bu işlemin PASS dışı

- `ezdxf` üzerinden gerçek DXF okuma, blokların doğru WCS dönüşümü ve DIMENSION kaynaklarının kalibrasyonu **henüz yok**.
- Çok sayfalı farklı ölçek, PDF CropBox/rotasyon, homografi, CAD XREF, DUVAR/KAPI/ODA gerçek semantik/geometri analizi sonraki işlemlerdir.
- **Windows 10/11 i7 14. nesil / RTX 4070 8 GB** gerçek cihaz kabulü yapılmadı; saha verisi ve hukukî inceleme yok.
- Vektör/PDF geometrisiyle arayüz, gerçek yönetmelik PASS ve AI modeli bu işlemde oluşturulmadı.

**Sonuç:** F01 için çekirdek veri sözleşmesi **MEVCUT_KOD + CI sentetik PASS**; F01 entegre gerçek DXF/Windows kabulü **KISMI**. Sonraki kaynak geliştirme işi **`docs/islem_008.md` (ezdxf DXF ayrıştırıcısı ve DrawingIR köprüsü)** olarak açılacak.

