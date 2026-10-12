# MimarLLM V2 — Kapsam ve Gerçekleşme Envanteri v0.1

- **Kayıt:** [islem_006.md](islem_006.md) · **Tarih:** 2026-10-13
- **Tanım:** Yüklenen taslak ve kod örneklerinin **tamamı hedef özelliklerdir**, doğrudan uygulanmış commit sayılmaz.
- **Durumlar:** `MEVCUT_KOD` = GitHub'da kod mevcut ama kabul zorunlu; `KISMI` = başlangıç var, hedef işlev eksik; `PLANLANDI` = kaynak/ürün henüz yok; `HUKUKI_HOLD` = mevzuat sürümü, dayanak ve uygulanabilirlik doğrulanana kadar etkinleştirilemez.

## Fonksiyonel özellik ve geliştirme takip matrisi

| Kimlik | Gerekli işlev | Hedef kod / bileşen | Mevcut durum | Kabul için somut kanıt | Kullanıcı taslağı |
| --- | --- | --- | --- | --- | --- |
| F01 | Birim, ölçek, CAD/DXF veri modeli `DrawingIR` | `core/ir.py`, `core/units.py` | PLANLANDI; PDF gözlem modelleri mevcut | Birim bilinmiyorsa kalibrasyonsuz gerçek ölçüm yok | Genel kapsam |
| F02 | DXF ayrıştırma, block/nested INSERT ve layer sinyali | `importers/dxf.py`, `importers/layers.py` | PLANLANDI | Katman/handle/transform ve bozulan bloklarda güvenli hata | (2) / eski 003 |
| F03 | PDF native vector + ROI + source provenance | `importers/pdf.py` | **MEVCUT_KOD, kabul bekler** | PDF char/line/curve/rect; dönüş/limit/görsel bbox ölçümü | İlk PDF kararları |
| F04 | OCR ve pafta layout (antet, mahal, kot, tablo) | `ocr/rapid_engine.py`, `ocr/layout.py` | **KISMI** (adapter) | CPU provider, Türkçe/simge CER, bbox + doğru yöne dönüş | (6) / eski 007 |
| F05 | Oda/duvar/poligon ve net-brüt alan, snap | `geometry/spatial.py`, `geometry/walls.py` | PLANLANDI | İki oda, açık sınır ve wall-inner-boundary referans alanı | (3) / eski 004 |
| F06 | Mekânsal topoloji, kapı bağlantısı, geçiş grafı | `geometry/topology.py` | PLANLANDI | Unreachable ve articulation; dış kapı/balkon ayrımı | (4) / eski 005 |
| F07 | Deterministik rule engine + altı durum ve kanıt | `rules/base.py`, `rules/engine.py` | PLANLANDI | PASS/FAIL/REVIEW/INSUFFICIENT/NA/ERROR; hesap izi | (5) / eski 006 |
| F08 | Planlı Alanlar İmar Yönetmeliği denetimi | `rules/registry/tr_imar.py` | **HUKUKI_HOLD** | Onaylı madde-fıkra-eşik, tarih, proje kapsamı ve bbox | (5) / eski 006 |
| F09 | BYKHY kaçış, kapı, çıkmaz koridor, sirkülasyon | `rules/registry/tr_yangin.py` | **HUKUKI_HOLD** | Ek-5/B doğru sürüm; yürünebilir yol/exit/sprinkler/occupancy | (12) / eski 014 |
| F10 | Otopark adedi, boyut, rampa ve manevra | `rules/registry/tr_otopark.py` | **HUKUKI_HOLD** | Kullanım/konum/tarih, gerçek kural, 3B rampa bilgisi | (13) / eski 015 |
| F11 | Sığınak ihtiyacı, kapasite, alan, kapı/çıkış | `rules/registry/tr_siginak.py` | **HUKUKI_HOLD** | 2025 değişikliklerinin sürüm zinciri; ek proje verisi | (14)=(15) / eski 016 |
| F12 | BEP/TS 825 pencere, enerji ve kabuk verileri | `rules/registry/tr_bep.py` | **HUKUKI_HOLD** | TS hakları + U/hesap/iklim/3B veri; 2B'den sahte PASS yok | (16) / eski 017 |
| F13 | Hiyerarşik mevzuat AST ve değişiklik/yürürlük | `regulations/parser.py`, `versions.py`, `citations.py` | PLANLANDI | Kaynak hash + madde/fıkra/ek + gerçek PDF page/quad | (7) / eski 008 |
| F14 | SQLite FTS5 ve CPU dense hibrit RAG, RRF | `regulations/store.py`, `retrieval.py` | PLANLANDI | Kaynak/version ID, exact match ve lexical fallback | (7) / eski 008 |
| F15 | RuleResult–LegalNode kaynak bağlama | `rules/evidence.py`, `evidence/` | PLANLANDI | Exact verified binding; arama benzerliği asla hukukî PASS değil | (8) / eski 009 |
| F16 | Analiz hattı + CLI | `pipeline.py`, `cli.py` | PLANLANDI | Sentetik DXF -> geometrik bulgu -> rapor; hata/iptal | (9) / eski 010 |
| F17 | JSON/Markdown/HTML/PDF rapor | `reports/exporter.py` | PLANLANDI | Ölçüm ve kaynak iki yönlü izlenebilir; sahte hüküm yok | (8) / eski 009 |
| F18 | SVG/HTML koordinatlı işaretleme | `reports/visualizer.py` | PLANLANDI | Offline, X/Y dönüşümü, hata pinine tıklayınca kaynak | (10) / eski 011 |
| F19 | Tek kullanıcılı localhost dashboard | `app/server.py`, `app/static/` | PLANLANDI | Sadece 127.0.0.1; izinli dosya; CDN yok, upload sınırı | (11) / eski 012 |
| F20 | Windows `run.bat`, `build_exe.bat`, `mimar.spec` | Root / `scripts/` | PLANLANDI | Sonraki gerçek CLI/dashboard entrypoint ile offline onedir | Sohbet / eski 013 |
| F21 | Yerel Qwen-VL ile aday sınıflandırma | `vision/vlm.py`, `vision/prompts.py` | PLANLANDI | GGUF + mmproj/Windows ölçümü; 8 GB peak VRAM | (17) / eski 018 |
| F22 | VLM adayını etiketleme, no-overwrite | `vision/semantic.py` | PLANLANDI | Native/certified kanıt ezilmez; belirsiz REVIEW | (18) / eski 019 |
| F23 | Çapraz modül benchmark, QA ve CI | `scripts/benchmark_audit.py`, `tests/`, `.github/workflows/` | PLANLANDI | Windows gerçek ölçüm, sentetik baseline, CPU/GPU peak | (19) / eski 020 |
| F24 | Dürüst README, kurulum ve işletim kılavuzu | `README.md`, `docs/` | KISMI | Gerçek özellik durumu, bağımlılık/kurulum ve lisans gerçeği | (20) |

**Eksik olarak bırakılmayacak iki denetim:** yapısal kaynak RAG'de *taranan özgün mevzuat sayfası ve satır/blok/quad* gösterimi; çizimde *ölçümün gerçek source entity/geometriye dönmesi*. Her ikisi de hukuken ve teknik olarak sahici kanıt için gereklidir.

## Taslaklardan taşınmayacak yanlış varsayımlar

- `src/mimar/` yerine **yalnız mevcut `src/mimarllm/`**.
- `rapidocr_onnxruntime` yerine **`rapidocr + onnxruntime CPU`**.
- PDF: yalnız **pdfplumber + pypdfium2**, başka motor ve genel doküman OCR paketi yok.
- “Dört köşeli OCR poligonu varsa 45°/90°/270° kusursuz okunur” geçersiz.
- “En yakın merkezler arasında Dijkstra yangın yürüme mesafesidir” geçersiz; yürüme ağı modelleme şart.
- “Odanın minimum rotated rectangle dar kenarı gerçek net geçiştir” geçersiz; gerçek kesit/geçiş ölçümü farklıdır.
- “Poligona buffer uygulamak duvar kalınlığını doğru düşer” her planda doğru değil.
- Örnek ölçü eşikleri kaynak/onay/yürürlük olmadan üretim kuralı değil.
- “0ms”, “%100 doğruluk”, “maksimum 2.5 GB VRAM” gibi test edilmemiş iddialar kabul değil.
- Kullanıcıların sağladığı yapıştırma dosyaları **telif ve özel veri kontrolünden geçirilmeden olduğu gibi public depoya yüklenmeyecek**.

## Durumun güncellenmesi

Her yeni `docs/islem_NNN.md` dosyasında Fxx kimlikleri korunur. Kod + sentetik test + hedef donanım kabulü + varsa hukukî inceleme sonrasında ayrı `PASS` verilir. Bir özellik yalnız başlığının veya Markdown örneğinin bulunmasıyla tamamlanmış sayılmaz.
