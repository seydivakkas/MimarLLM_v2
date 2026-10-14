# İşlem 018 — Çevrimdışı Bütünleşik Analiz Pipeline ve CLI

- **Tarih:** 2026-10-14
- **Durum:** UYGULANDI — çevrimdışı DXF/PDF→DrawingIR→Shapely/NetworkX→RuleEngine→kaynaklı rapor pipeline ve CLI. **279/279 Linux + 279/279 Windows sentetik CI PASS.** F16 KISMI/MEVCUT_KOD; gerçek Windows cihaz ve hukukî uygunluk HOLD.
- **Önceki kayıt:** `docs/islem_001.md`–`docs/islem_017.md` değiştirilmeyecek.
- **Önkoşul:** 008–009 DXF/PDF→DrawingIR, 010 Shapely geometri, 011 NetworkX topoloji, 012 RuleEngine (REGULATORY kilitli), 013–016 LegalAST kanıt, 017 kaynak bağlı rapor/HTML/PDF.
- **Dağıtım:** Windows-first, internet/abonelik/ücretli API gerektirmeyen yerel Python/CLI. GitHub-hosted Linux/Windows sentetik testler; gerçek kullanıcı Windows/saha kabulü finalde.

## 1. Geliştirme paketi — kayıtlanan kapsam

1. `src/mimarllm/pipeline.py`: tek yerel `.dxf`/ `.pdf` girdisini doğrulanmış import üzerinden `DrawingIR`'ye dönüştüren, açık aşama/uyarı ve hata kodlarıyla geometri Shapely, sadece **açık ve kaynaklı** SpaceReview/PassageReview sunulmuşsa NetworkX, RuleEngine teknik senaryoları ve raporu koordine eden deterministik pipeline. Ortak drawing SHA, coordinate frame ve evidence ID denetimi şart. PDF'de OCR yalnız sağlanmış yerel motor+seçilmiş ROI varsa devreye girer.
2. `src/mimarllm/pipeline.py` konfigürasyon sözleşmeleri: frame seçimi (çok sayfalı PDF'yi birbirine karıştırma yok), isteğe bağlı *gerçek native çizgi entity* üzerinde kullanıcı beyanlı referans kalibrasyonu, fiziksel ölçüm isteği, açık topoloji node/door inceleme beyanları, seçili RuleDefinition ve RuleRequest kaynak kimlikleri. `$INSUNITS` tek başına CONFIRMED sayılmaz. Yanlış frame/kalibrasyon/source veya eksik geçişde `INSUFFICIENT_EVIDENCE`/`REVIEW_REQUIRED`; kapalı geçit/yangın kaçışı iddiası yok.
3. `src/mimarllm/cli.py`: `python -m mimarllm.cli analyze local.dxf --output-dir ... --config ...`; yalnız **yerel JSON** konfigürasyonu; JSON/Markdown/HTML/PDF raporu ve pipeline manifestini yeni dosyalara yazma, yinelenen çıktı üzerine yazma yok; anlamlı exit code ve gizli dosya yolu/OCR/pdf içeriğini traceback ile dökmeyen hata yönetimi.
4. `src/mimarllm/reports/builder.py` yalnız gerekirse çok frame'li geometry/topology toplu bağlamasını geriye uyumlu destekleyecek; farklı PDF sayfası/CAD layout varlıklarını asla tek frame'e zorlamayacak.
5. `tests/test_pipeline.py`, `tests/test_cli.py`: sentetik DXF/PDF; calib unknown / confirmed from exact line; açık ve hatalı teknik RuleEngine testleri; without reviewed topological evidence; multi-page PDF frame separation; kaynak integrity; belge desteklenmiyor, bozuk dosya, yanlış config, eksik dosya, file overwrite, no cloud; Linux/Windows pytest.
6. `pyproject.toml`, `.github/workflows/core-contracts.yml`, `README.md`, `docs/specs/pipeline-cli-v0.1.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md`.

## 2. Yasak olan sahte otomatik sonuçlar

- Geometri kapalı bir aday yüzey üretse de otomatik **oda/net/brüt metrekare hukukî kararı** yok. Scale calibration sadece açıkça seçilen native kaynak segment + fiziksel uzunluk + inceleme beyanıyla; yanlış/eksik metrikte fiziksel `PASS` yok.
- Ağ/Cloud API, web bazlı model indirme, renkli katman etiketinden oda tipi çıkarma, oda merkezlerinden kapı yangın kaçışı varsayımı yok.
- Mevzuat/LegalAST/RAG eşleşmesi hiç otomatik `RuleEngine.REGULATORY` kilidini açmaz. V0.1 CLI hukukî belgeleri otomatik konsolide etmeyecek; rapordaki hukukî source slot ayrıca insan kaynaklı İşlem 015/017 API'leriyle kullanılabilir.
- Bir dosyanın bazı aşamaları geçerse bile diğerleri HOLD/ERROR olabilir; aşama sonucu yoksa başarı yazmayacağız. CLI `exit 0` yalnız teknik pipeline'ın çıktı dosyalarını başarıyla oluşturduğunu ifade eder, *bina hukuken uygun* demek değildir.

## 3. Gerçek GitHub kod değişiklikleri, dosyalar ve commitler

**İlk GitHub yazımı**: `docs/islem_018.md` ön kayıt commit'i **`87df4fcaf8b83e0c507b7b07dabc2d453ada74de`**. Uygulama kodu ve diğer belgelerden **önce** oluşturuldu. Önceki `islem_001.md`–`islem_017.md` dosyaları yeniden yazılmadı.

| Dosya | Gerçek uygulama | Kod/örnek commit |
| --- | --- | --- |
| `src/mimarllm/pipeline.py` | PipelineConfig, explicit native-segment CalibrationReference, StageRecord, PipelineManifest, DXF/PDF import, multi frame Shapely, açık SpaceReview/PassageReview NetworkX, teknik RuleRun/RuleEngine ve kaynaklı rapor | `0c180b33` |
| `src/mimarllm/pipeline.py` | OCR ROI yalnız yerel açık okuyucuyla; kaynak type/coordinate limit; geometri/RuleEngine hata halinde `PARTIAL_WITH_ERRORS`; bulgusuz çizimde kaynak entity gösterimi | `1d7dcdae`, `b699c253`, `c323bb63` |
| `src/mimarllm/pipeline.py` | Başka DXF DIMENSION veya grafik ölçeği bağımsızca okunup doğrulanmadığı için `CalibrationReference.method=USER_REFERENCE` ile sınırla | `fd04e510` |
| `src/mimarllm/cli.py` | `mimarllm analyze` yerel JSON config, yalnız yeni rapor dosyaları ve pipeline-manifest JSON, JSON/HTML varsayılan; isteğe bağlı Markdown/PDF; eksik dosya, invalid config ve no overwrite açık ret | `785abefa` |
| `src/mimarllm/cli.py` | `exit 4` ile `PARTIAL_WITH_ERRORS`, `Ctrl+C exit 130`, tamamlanmayan export/iptalde sadece bu koşunun raporlarını geri alma | `43e6c8f5`, `69fed5c6`, `0212b3b1` |
| `src/mimarllm/reports/builder.py` | Multi-frame geometry/topology sonuçlarını tek çizim SHA altında rapora alma ve ilk koşuda bulgu olmasa dahi kaynak DrawingIR entity'lerini görsel panelde sunma | `65289244`, `c92408ce` |
| `tests/test_pipeline.py` | Native sentetik DXF segmenti üzerinden fiziksel kalibrasyon yok/HOLD ve kullanıcı beyanlı teknik kıyas, REGULATORY HOLD, iki sayfalı PDF, explicit reviewed topology, OCR opt-in, bozuk dosya ve geometri bütçesi ERROR | `4b668ce6`, `704c96c2`, `a9cdce55` |
| `tests/test_cli.py` | `python -m mimarllm.cli` subprocess, yerel PDF sayfa arka planı, config, no overwrite, gerçek source SHA manifest, PDF/MD, yasal kilit, partial exit 4, export rollback ve Ctrl-C | `1b14fb86`, `43914cab`, `e0a6ed14` |
| `pyproject.toml` | `[project.scripts] mimarllm = "mimarllm.cli:main"` | `932fad0c` |
| `.github/workflows/core-contracts.yml` | Pipeline ve CLI kaynak değişimlerine trigger, yeni testler Windows/Linux mevcut bütün testlere dahil | `d99362b3` |
| `docs/specs/pipeline-cli-v0.1.md` | Çevrimdışı kullanım, explicit inceleme JSON örneği, opt-in OCR, frame/ölçek ve exit 0/2/3/4/130, rapor güven sınırları | `9ec10a09` |
| `README.md` / `docs/ozellik-envanteri.md` / `docs/uygulama-yol-haritasi.md` / `docs/kararlar.md` | F16 KISMI/MEVCUT_KOD, F19 GUI plan, F17/F18 kısmi, HUKUKI_HOLD, K-137–146 | `7003da72`, `87aab027`, `b7033b98`, `4867347b` |

## 4. Gerçek sentetik CI kayıtları

- İlk pipeline/CLI test seti [GitHub Actions **38529603872**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38529603872): **271 PASS, 3 FAIL** Ubuntu. Hataların ikisi yalnız validator/overwrite çıktı metni beklentisiydi. Bir gerçek ürün eksikliği tespit edildi: rapor bulgusu yoksa kaynak DrawingIR entity paneli boş kalıyordu. `builder.include_unlinked_sources=True` ve pipeline bağlantısı eklendi; yanlış bir bulgu veya onay üretilmedi.
- [GitHub Actions **38530011720**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38530011720): **Ubuntu 276 PASS, Windows 276 PASS**. Hata toleransı ve manifest bir üst güven katmanıyla genişletildi.
- Sonrakilerde user kaynak referansı yöntemi `USER_REFERENCE`'a sınırlandı; geometri stage `ERROR` ise artık `PARTIAL_WITH_ERRORS` ve CLI exit 4; Ctrl+C/başarısız export'a özgü rollback ve regresyonları eklendi.
- **Son kod commit `a9cdce555c3801a70e97e4e74dc93a25310601a1`**: [GitHub Actions **38530537311**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38530537311) — **Ubuntu Python 3.11 279/279 PASS (6,26 s), GitHub-hosted Windows Python 3.11 279/279 PASS (15,36 s)**. Her iki job logları ayrı okundu; `failed` yok.
- CI testleri, yerel sentetik DXF (ezdxf), PDF (ReportLab), gerçek dosya import, çok sayfalı DrawingIR, Shapely ve NetworkX source bağları, RuleEngine teknik ve yasal kilit senaryoları, JSON/HTML/MD/PDF export, manifest status/exit, rollback ve kaynak SHA'yı doğruladı.
- CI yalnız sentetik Github-hosted Linux/Windows Python 3.11 içindir. Kullanıcının kendi Windows 10/11 Intel i7/RTX 4070 cihazında veya gerçek sahadan gelen mimari/Resmî Gazete verilerinde bağımsız kabul yapılmadı.

## 5. Tamamlananlar, kısmi kabul ve açık kalanlar

**F16 KISMI / MEVCUT_KOD**: yeni `pipeline.py`, `cli.py` ile farklı modüller tek dosya üzerinden çağrılıyor; kullanıcının seçtiği kaynak kimlikleri DrawingIR–RuleEngine–rapor arasında aynı SHA'ya bağlanıyor. `pipeline-manifest.json`'daki her `IMPORT/CALIBRATION/GEOMETRY/TOPOLOGY/RULES/REPORT` aşaması ayrı `COMPLETE/REVIEW_REQUIRED/SKIPPED/ERROR`. Varsayılan `COMPLETED_WITH_REVIEW_GATES` ifadesi bina uygunluğu anlamına gelmez; aşama ERROR olduğunda `PARTIAL_WITH_ERRORS` ve exit 4. İptal exit 130, hatalı kullanıcı girdisi exit 2, beklenmeyen istisna exit 3, rapor oluşturulan ama kaynak incelemesi bekleyen analiz exit 0.

**F17/F18 KISMI**: rapor yapısal kanıt ve SVG/yerel PDF görüntüleri artık bu pipeline'dan üretiliyor. PDF rapor interaktif değil; DXF SVG tam CAD plot değil. Çok sayfalı PDF kaynakları frame bazlı ayrılır; layout/çok sayıda entity üzerinde gerçek performans kabulü eksik.

**F08–F12 HUKUKI_HOLD:** RuleEngine `RuleDomain.REGULATORY` kullanıcı config/rule/effective_date ile `COMPLIANT/NON_COMPLIANT` veya `APPROVED_FOR_CHECK` üretmez. Tarihsel Resmî Gazete sürüm grafı, yetkili hukukî orijin kontrolü, yerel plan hükümleri/geçiş/istisna ve gerçek kurum uzman onayı ayrıca. Gerçek imar/yapı analizi için kullanıcı veya hukukçu asıl kaynağı incelemeli.

**Açık yazılım:** F19 yerel localhost dashboard **bu işlemde yok** (eski plan 018'den F16 CLI odağına daraltıldı). F20 Windows paketleme/installer, geniş CAD render, gerçek Windows kabulü ve gerçek bina PDF/DXF/insan inceleme ayrıca yapılacak.

**Sıradaki kayıt:** `docs/islem_019.md` henüz oluşturulmadı; sonraki kod değişikliğinden önce **ilk GitHub yazımı** olarak açılmalı. İşlem 019 kapsamı için F19 dashboard/Windows-first dağıtım önceliği ayrıca değerlendirilebilir; gerçekleştirilmeden tamamlandı denmemeli.

