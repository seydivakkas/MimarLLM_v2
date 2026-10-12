# İşlem 007 — DrawingIR v0.1, CAD birimleri ve kaynak kanıt sözleşmeleri

- **Tarih:** 2026-10-13
- **Durum:** PLANLANDI; kod değişikliklerinden önce açılan işlem kaydı.
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

## 5. Sonuç / işlem kaydı

Gerçek commit, dosya, test sonuçları ve kalan hatalar iş sonunda eklenecektir.
