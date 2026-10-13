# İşlem 010 — Shapely geometri, oda yüzey adayları ve duvar aralığı kanıtları

- **Tarih:** 2026-10-13
- **Durum:** ÖN KAYIT — diğer kod ve belge değişikliklerinden **önce** oluşturuldu.
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

## 4. Uygulama ve test sonuçları

Bu bölüm gerçek GitHub commitleri, CI sonuçları ve açık kalan sınırlamalarla güncellenecektir.
