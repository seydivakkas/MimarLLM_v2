# İşlem 018 — Çevrimdışı Bütünleşik Analiz Pipeline ve CLI

- **Tarih:** 2026-10-14
- **Durum:** ÖN KAYIT — İşlem 018 kapsamındaki **ilk GitHub yazımı**; hiçbir kod/değişiklik önce yapılmadı.
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

## 3. Son güncellemede doldurulacak kanıt

Gerçek oluşturulan dosyalar/commit SHA zinciri, pytest Ubuntu+Windows sonuçları ve başarısız düzeltme geçmişi, F16/F17/F18 kısmi durumu, hukukî/geometrik/kamera/Windows acceptance HOLD sınırları **bu aynı dosyanın son GitHub yazımında** eklenecek.
