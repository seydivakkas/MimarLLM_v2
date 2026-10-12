# İşlem 008 — Deterministik DXF ayrıştırıcısı ve DrawingIR köprüsü

- **Tarih:** 2026-10-13
- **Durum:** UYGULANDI — gerçek DXF kaynak kodu + sentetik GitHub CI PASS; gerçek Windows/saha paftası kabulü HOLD.
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

## 5. Tamamlanan işlemler ve commit kanıtı

**Ön-kayıt ilk commit:** `173a3cea611c7d26eeda6b970536895b9f1332b0`. Kod değişikliklerinden **önce** `docs/islem_008.md` oluşturuldu.

| Dosya | Gerçek uygulama | İlk/son ilgili commit |
| --- | --- | --- |
| `src/mimarllm/importers/dxf.py` | ezdxf readfile/audit, çizgi/yay/çember/LWPOLYLINE, TEXT/MTEXT/DIMENSION, INSERT/nested INSERT/MINSERT, orijinal CAD handle ve `DrawingIR` | `0b22f566`; sertleştirme `49839719`, `e4b46bfc` |
| `src/mimarllm/importers/layers.py` | Duvar/kapı/pencere/mahal/ölçü için kesin olmayan token tabanlı katman adayları | `fce9c9ba` |
| `pyproject.toml` | `ezdxf>=1.4,<2` ana bağımlılığı | `26ac6fc4` |
| `tests/test_dxf_parser.py` | Kaydedilip tekrar açılan sentetik DXF, tüm hedef entity türleri, nested insert/rotasyon, MINSERT, bulge, kritik limitler ve XREF | `f905f97f`; `0a85fe67`; `63b5fce2` |
| `.github/workflows/core-contracts.yml` | Mevcut Pydantic/PDF testlerine DXF testini ekle; ezdxf CI kurulumu | `bd338321` |
| `docs/specs/dxf-import-v0.1.md` | API, kaynak izi, açıklıklar, MINSERT ve tessellation/XREF sınırları | `7f553f46`, `af7a6da2` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | Kod ile hedef kapsam ayrımı, F02 `KISMI/MEVCUT_KOD`, sonraki işlem 009 | `e0456b7a`, `6b283b66`, `a0a093f7`, `ea8bba3` |

### Doğrulanan test sonucu

- **Nihai kaynak kodu `e4b46bfc`, testleri `63b5fce2`** içeren [GitHub Actions çalışması 38314925779](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38314925779): **73 test PASS, 0 FAIL, 1.68 saniye test süresi**, Ubuntu/Python 3.11.
- Bütün testler GitHub runner üzerinde gerçek `ezdxf.new` ile DXF üretir, dosyayı kaydeder ve `ezdxf.readfile` üzerinden geri açar; uçtan uca veri kontratı test edilir. Bunlar **sentetik DXF dosyalarıdır**, gerçek müşteri/ruhsat paftaları değildir.
- DXF source identity, nested block path, MINSERT instance ID, nonuniform scale + flattened curve, `$INSUNITS` onaysızlık, TEXT/MTEXT/DIMENSION kaynakları, bilinmeyen geometri ve kontrollü hata doğrulandı.
- PDF/OCR/VLM inference ve Windows gerçek donanım benchmark'ı bu test kapsamına girmez.

### Mühendislik sınırları ve sonuç

- Kural sonucu, semantik duvar/kapı/oda sınıfı veya metre cinsinden mevzuat PASS **üretilmedi**. `DrawingIR.findings` boştur.
- `LWPOLYLINE`, ARC ve CIRCLE path flattening eğri kaynak geometrisini **örnekleyerek** aktarır, gerçek matematiksel yay analizinin yerini almaz. Source handle korunur.
- `DIMENSION` etiketi ham `DxfAnnotation` değeridir; sayısal CAD ölçüsü ve displayed override/style tartışması ayrı onaylanmadan fiziksel metre olmaz.
- `XREF` otomatik dış ağ/disk kaynağından okunmaz; `XREF_UNRESOLVED` uyarısı vardır.
- Özellikle büyük gerçek mimari dosyalar, 3B OCS, karmaşık nonuniform nested blocks, dynamic blocks, xclip, MINSERT attributes ve Windows 10/11 hedef makine testi **HOLD**.

**Sonuç:** `F02` için **kod ve sentetik CI PASS**; gerçek Windows ve kapsamlı CAD saha kabulü `KISMI/HOLD`. Sıradaki uygulama `islem_009`: PDF glyph/ROI ve RapidOCR kaynak koordinatlarını `DrawingIR`'ye güvenilir şekilde bağlamak.
