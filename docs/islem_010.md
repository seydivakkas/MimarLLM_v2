# İşlem 010 — Shapely geometri, oda yüzey adayları ve duvar aralığı kanıtları

- **Tarih:** 2026-10-13
- **Durum:** UYGULANDI — Shapely geometri çekirdeği ve Ubuntu/Windows sentetik test kabulü. Gerçek mimari saha/kişisel Windows kabulü ve otomatik duvar/oda semantiği HOLD.
- **Depo:** `seydivakkas/MimarLLM_v2`; önceki 001–009 geçmişi korunur.
- **Hedef özellik:** F05; DrawingIR v0.1, islem_008 DXF ve islem_009 PDF source bağlarına dayanır.
- **Donanım:** i7 14. nesil/32 GB RAM/RTX 4070 8 GB. Shapely CPU üzerinde ve harici AI API'si olmadan çalışır.

## 1. Uygulama sözleşmesi

1. `src/mimarllm/geometry/spatial.py`: DrawingIR'ye doğrudan bağlı, **tek coordinate frame** içinde gerçek SEGMENT/POLYLINE/POLYGON'dan çizgisel boundary gözlemleri; intersection/noding, `unary_union`, `polygonize_full`. Bütün olası yüzeyler `ROOM_CANDIDATE`, kesin oda veya net alan değildir.
2. Boşluk, T junction, fazladan çizgi, self-intersection, çakışan/coincident segment, çift çizgi, desteklenmeyen semantik ve geometri sınırı için tanı kayıtları. Varsayılan snap **kapalı**; toleransla snapped topoloji kullanılırsa yalnız revize edilmiş aday olarak sınıflandırılacak.
3. `src/mimarllm/geometry/walls.py`: paralel çizgi çiftlerinin yön, projeksiyon örtüşmesi, dik uzaklık ve source handle/entity ID ile `WALL_THICKNESS_CANDIDATE` üretimi. Katman ipucu ve çizgi aralığı duvar kesinliği sağlamaz.
4. `confirmed` seçilmiş kaynak entity kimlikleriyle ayrı **interior/outer envelope** yüzey sözleşmesi. Net alan **iç sınırların doğrulandığı** ve tek kapalı yüzeyin bulunduğu zaman aday çizim alanı; fiziksel m² değeri **yalnız aynı frame'e bağlı CONFIRMED UnitCalibration** varsa. Otomatik `buffer` ile duvar kalınlığı düşüp sahte net alan yok.
5. Negatif alan, açık/çelişkili sınır, farklı page/layout/frame, onaysız fiziksel ölçek, çakışma, clip/rotasyon kaynak belirsizliğinde kesin hesap yok; `INSUFFICIENT_EVIDENCE` veya `REVIEW_REQUIRED` açık durumları.
6. `DrawingIR.findings` veya hukukî `PASS` üretmeyecek. Üretilen geometrik `surface_area_source_units` metre kare değil, frame birimi karesidir.
7. Belirgin **max_entities/max_segments/max_faces/max_pairs**, snaptolerance ve minimum yüzey eşiği. GPU veya network çağrısı yok.
8. Gerçek `ezdxf` ile sentetik 2 oda kapalı/açık/çakışan/çift çizgi ve net-brüt dış kabuk fikstürleri, PDF source frame, çapraz frame reddi, kalibrasyon ve source IDs; Linux ve Windows CI.

## 2. Beklenen dosyalar

- `src/mimarllm/geometry/__init__.py`, `spatial.py`, `walls.py`
- `tests/test_geometry.py` ve gerekirse `tests/test_geometry_integration.py`
- `pyproject.toml` Shapely (BSD-3-Clause; binary/GEOS lisansı SBOM ayrı)
- `.github/workflows/core-contracts.yml` Linux/Windows sentetik test matrisine geometri testleri
- `docs/specs/geometry-v0.1.md`, `README.md`, `docs/ozellik-envanteri.md`, `docs/kararlar.md`, `docs/uygulama-yol-haritasi.md`

## 3. Semantik ve kabul sınırı

- Bir polygonize sonucu geometrik yüzeydir; **oda duvarı / net yaşam alanı** kanıtı değildir.
- Dıştan içe `buffer(-thickness)` ile otomatik net alan ve çizgi merkezleri üzerinden kesin duvar kalınlığı üretmek **yasaktır**.
- Algoritmik `snap` sonucu onaylı geometri değil, alternatif aday; kullanıcı/otorite doğrulaması ister.
- Çapraz PDF sayfasındaki veya DXF layout'undaki çizgiler birlikte çözülmez.
- Yangın mesafesi, topoloji, mevzuat kuralları ve mimari uygunluk **bu işlemde uygulanmaz**.
- Windows-hosted CI, kullanıcının gerçek i7/4070 Windows makinesinde saha kabulü değildir.

## 4. Gerçek GitHub uygulaması ve commit zinciri

**Ön kayıt:** `docs/islem_010.md` commit **`d0e0e92924799ba4c2000b89ec1444b123fdc8e5`**. Bu kayıt herhangi bir uygulama modülünden önce oluşturuldu.

| Dosya | Uygulanan gerçek kod/dokümantasyon | İlgili commit |
| --- | --- | --- |
| `src/mimarllm/geometry/spatial.py` | Shapely linework source filtering, unary_union noding, polygonize_full, faces, duplicate/open/hole diagnostikleri, explicit area assessment | `24e76ceb` |
| `src/mimarllm/geometry/walls.py` | Paralel kenar aralığı kaynak ID'li REVIEW_REQUIRED adayları, overlap ve limitler | `df6f91c0` |
| `src/mimarllm/geometry/__init__.py` | Tek Python paketine geometri modülü | `2a111c6a` |
| `pyproject.toml` | Shapely `>=2.0,<3` bağımlılığı | `528d3634` |
| `tests/test_geometry.py` | İki oda, DXF file read, PDF rectangle, open/overlap/bowtie, frame, scale, area/net-vs-footprint, wall-gap, budgets | `68a11c2e`, `76c2508b`, `07039f5d` |
| `.github/workflows/core-contracts.yml` | Shapely kurulum + tests/test_geometry.py Ubuntu/Windows CI matrisi | `20d9a33e` |
| `src/mimarllm/geometry/spatial.py`, `walls.py` | PDF glyph tarama performansı, açık kaynak seçimi diagnostik, kesişim X/Y ve source ID, her alan/gap raporunda source_sha256 | `7a9944c7`, `ebe4a62b`, `b57ea23d`, `50448969` |
| `docs/specs/geometry-v0.1.md` | Bilimsel sınır, kaynak birimi ve alan semantiği, doğrulama kapıları, test matrisi | `d2084ba0` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F05 kısmi kod statüsü, iş sırası ve K-066…K-074 kararları | `0691e32e`, `23fcd353`, `c4be6205`, `e8179baf` |

## 5. CI testleri — gerçek sonuç

- İlk yeni geometri CI [38361126179](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38361126179): **Ubuntu 107 PASS**, **Windows 107 PASS**, GitHub-hosted Python 3.11. Önceki 88 PDF/DXF/IR sözleşme testleri de içerildi.
- Geniş PDF'lerde gereksiz glyph uyarılarını azaltırken bir eski testin “OCR seçilmemişken de uyarı üretir” beklentisi yeni politikayla çelişti. [38361425260](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38361425260) ve [38361442436](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38361442436) ara koşuları FAIL oldu. Test açıkça seçilen OCR kaynağını reddetme ve genel taramadan ilgisiz glyph'leri filtreleme olarak düzeltildi.
- **Nihai kod commit `07039f5d`** için [CI 38361902512](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38361902512): **Ubuntu Python 3.11 — 112/112 PASS, 1,05 s**; **GitHub-hosted Windows Python 3.11 — 112/112 PASS, 5,56 s**. Job logları ayrı ayrı kontrol edildi. **Bu test kullanıcının gerçek i7/RTX 4070 Windows bilgisayarında çalıştırılmadı**.

## 6. Geometrik doğruluk ve limitler

**Kodlanan kanıtlar:** Frame ID ve `DrawingIR.source_sha256`, orijinal entity ID'leri, kapalı `UNCLASSIFIED_FACE`, kaynak entity çiftleriyle SHARED_ENDPOINT/T_JUNCTION/CROSSING kesişimleri, açık/çakışma/self-intersection diagnostikleri, paralel çizgi aralığı `REVIEW_REQUIRED` adayı. Kaynak CAD ölçü birimi, `snap_tolerance` ve alan `source_area_squared` **metrik kabul edilmez**.

**Fiziksel alan şartı:** `assess_area` yalnız seçilmiş gerçek sınır ID'leri + tek ambiguitiesiz kapalı Shapely yüzeyi + kullanıcı reviewer kaydı + aynı source frame CONFIRMED calibration olduğunda `physical_area_m2` üretir. Çizimde gerçek duvar iç yüzü seçilmemişse kullanıcı onayı bile mimarî net alan kanıtı sayılmaz. Dış zarf sonucu *footprint*'tir, yönetmeliğe göre brüt kat alanı değildir.

**HOLD:** Otomatik oda/duvar gerçek semantik sınıflandırma, PDF raster/OCR duvar geometri tespiti, açık kapı boşlukları üzerinden topolojik oda tamamlama, duvar iç/dış yüzü çıkarımı ve net/brüt yasal toplam, gerçek saha Windows testleri, büyük DXF çok binlerce segment için STRtree/spatial-index optimizasyonu, gerçek yangın kaçış yürüyüşü ve mevzuat karşılaştırması.

## 7. Sonuç ve sonraki mühendislik paketi

**F05 `MEVCUT_KOD + SENTETİK CI PASS / KISMI`**. Bu iş paketi mimarî `PASS` veya `MEVZUATA UYGUN` üretmez; Shapely kaynak kanıtı, çizim tutarlılığı ve onay şartlı alan sözleşmesini gerçek kodla oluşturur.

**Sıradaki işlem: `docs/islem_011.md`** (henüz oluşturulmadı): NetworkX oda geçiş topolojisi, kapı/açıklık kanıt modeli, dış mekân ve sahanlık ilişkileri. Bu da yangın kaçış mesafesi değildir; gerçek yürünebilir ağ ve mevzuat binding daha sonraki aşamalardır.
