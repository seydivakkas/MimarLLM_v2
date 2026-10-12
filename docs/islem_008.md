# İşlem 008 — Deterministik DXF ayrıştırıcısı ve DrawingIR köprüsü

- **Tarih:** 2026-10-13
- **Durum:** ÖN KAYIT — kod değişikliklerinden önce açıldı.
- **Özellikler:** F02 (DXF okuma, geometri, INSERT, katman); F01 sözleşmeleri tekrar kullanılır.
- **Hedef platform:** Windows/i7 14. nesil/32GB/RTX 4070 8GB; parser sadece CPU, bulut AI API yok.
- **Kararlar:** `src/mimarllm/` tek paket; PDF/OCR ADR-002 kararı korunur.

## 1. Gerekli iş

1. `ezdxf.readfile()` ile yerel DXF (ASCII/binary uyumluluk araç yeteneğine bağlı); maksimum dosya boyutu, entity sayısı, blok derinliği ve tessellation nokta sınırlarıyla korumalı çözümleme.
2. Modelspace'te en az `LINE`, `LWPOLYLINE`, `ARC`, `CIRCLE`, `TEXT`, `MTEXT`, `DIMENSION`, `INSERT` okunmalı. Modelspace dışındaki paperspace başlangıçta açık kullanıcı seçimiyle ayrı frame olarak alınabilir.
3. Nested INSERT ve MINSERT için **orijinal kaynak CAD handle + tam blok örnekleme yolu + özgün layout/frame** korunmalı. Bloklar dosyanın üzerine fiziksel explode ile yazılmaz.
4. Yatay 2B WCS noktalara normalizasyon; `ezdxf.path.make_path(...).flattening()` ile eğri ve bulge tesselation. `curve_flatten_distance` kaynak CAD birimindedir, metre değildir; gerçek yay/radius semantiği ve approximation bilgisi ayrıca tutulur.
5. `$INSUNITS` bilgisi `UnitCalibration.INFERRED` olarak alınır. **Kullanıcı onayı veya bağımsız dimension/graphic scale verification olmadan** çizimin boyutu fiziksel metreye dönüştürülmez.
6. DXF TEXT/MTEXT/ATTRIB ve DIMENSION etiketi, sayı/ölçü iddiaları **separate annotation** olarak saklanır; DIMENSION measurement override ve style teyit edilmeden fiziksel kalibrasyon kanıtı sayılmaz.
7. Katman ipuçları **deterministik aday etiket** olabilir; doğrudan `WALL`, `DOOR`, `ROOM` onaylı sonucu sayılmaz.
8. Bozuk entity, desteklenmeyen 3B geometri, self-referencing/missing block, nonuniform scale ve limitler **açık diagnostics** olarak dönmeli; sessizce PASS/uygunluk üretilemez.
9. Kod, test, dokümantasyon ve CI logları aynı işlem günlüğünde gerçek durumuyla kaydedilmeli.

## 2. Somut dosyalar

- `src/mimarllm/importers/dxf.py`: `parse_dxf()`, `DxfImportResult`, `DxfAnnotation`, `DxfIssue`.
- `src/mimarllm/importers/layers.py`: katman adı ipucu; kullanıcı/semantik doğrulama gerek.
- `pyproject.toml`: `ezdxf` bağımlılığı.
- `tests/test_dxf_parser.py`: dosya oluşturup gerçekten kaydetme/okuma; nested INSERT, MINSERT, normal/yansıyan koordinat, bulge, ARC/CIRCLE, TEXT/MTEXT/DIMENSION, bilinmeyen `INSUNITS`, limitler ve bozuk dosya.
- `.github/workflows/core-contracts.yml`: DXF testleri CI içine alınır.
- `docs/specs/dxf-import-v0.1.md`: CAD source provenance, geometrik approximation ve kabul sınırları.
- `docs/ozellik-envanteri.md`, `README.md`: F02 ve gerçek kod/test statüsü.

## 3. Teknik kısıt ve risk kapıları

- ezdxf `INSERT.virtual_entities()` handle tutmaz; nested source identity için blok tanımındaki **gerçek entity** + `INSERT` yolu kullanılıp WCS matrisleri birleştirilecek. MINSERT örnekleri ayrı path kimliğine sahip olmalı.
- `LWPOLYLINE` raw `get_points()` OCS olabilir; tek başına WCS kabul edilmeyecek. Bulge/ARC/CIRCLE `ezdxf.path.make_path` ile örneklenecek; gerçek eğri ile yaklaşım farkı diagnostic/metadata halinde.
- Projeksiyon 2B ilk ürün: 3B/nonplanar kaynak 2B'ye sessizce yansıtılmaz. Kaynak varsa `UNSUPPORTED_3D` raporlanır.
- DXF DIMENSION türü metre cinsinden fiziksel değer değildir; style/`dimlfac`, text override ve block transform ayrı inceleme gerektirir.
- Layer adı “DUVAR” yazıyor diye nesne kesin duvar değildir.
- DXF parser raporunda hiçbir hukukî PASS/FAIL üretilmez.
- Gerçek Windows/AutoCAD export, XREF, dynamic block, OCS ve çok büyük pafta kabulü CI sentetikten ayrıdır.

## 4. Kabul

Kod CI üzerinde sentetik DXF'ler üzerinden geçerse `MEVCUT_KOD + SENTETIK_PASS`, Windows müşteri paftası denenmeden `WINDOWS_HOLD`.

## 5. Tamamlanan işlemler

Bu bölüm commitler ve CI sonucu doğrulandıktan sonra doldurulacaktır.
