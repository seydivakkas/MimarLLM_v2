# MimarLLM V2 — Güncel Dosya Haritası ve Gelecek Modül Sözleşmeleri

**Revizyon:** İşlem 020, 2026-10-15 · **Tek gerçek paket:** `src/mimarllm`. [Master mimari](master-mimari-arch-core-local.md) · [Yeni sıra](uygulama-yol-haritasi.md) · [Özellik envanteri](ozellik-envanteri.md).

**Not:** Bu belge önceki İşlem 006'da çıkarılan yalnız plan niteliğindeki ağacı **yeniden baz çizer**. O eski belgede “PLAN” etiketli birden çok dosya (DXF, RuleEngine, LegalAST, RAG, CLI, dashboard vb.) artık GitHub'da **kısmen gerçek kod** olduğundan eski görünüme güvenilmemelidir. Hiçbir İşlem 001–019 tarihsel kayıt dosyası değiştirilmez.

```text
MimarLLM_v2/
├── README.md                                 [MEVCUT]
├── pyproject.toml                            [MEVCUT, tek Python bağımlılık kaynağı]
├── .github/workflows/core-contracts.yml     [MEVCUT, sentetik Linux/Windows CI]
├── docs/
│   ├── islem_001.md ... islem_020.md         [MEVCUT işlem kayıtları, 020 revizyon]
│   ├── master-mimari-arch-core-local.md      [YENİ DOKÜMAN]
│   ├── risk-ve-dogrulama-matrisi.md          [YENİ DOKÜMAN]
│   ├── ozellik-envanteri.md                  [MEVCUT, 020 revizyon]
│   ├── uygulama-yol-haritasi.md              [MEVCUT, 020 revizyon]
│   ├── specs/ ; adr/                         [MEVCUT kaynak/karar belgeleri]
│   └── planlanan-dosya-yapisi.md             [BU DOSYA]
├── src/mimarllm/                             [MEVCUT TEK KOD KÖKÜ]
│   ├── core/
│   │   ├── ir.py ; units.py                  [MEVCUT]
│   │   └── calibration_candidates.py         [PLAN: kaynaklı birim hipotezi]
│   ├── importers/
│   │   ├── dxf.py ; pdf.py ; pdf_ir.py       [MEVCUT]
│   │   └── layers.py                        [MEVCUT, layer adından aday]
│   ├── ocr/
│   │   ├── rapid_engine.py                  [MEVCUT, CPU OCR adapter]
│   │   └── tiled_regions.py                 [PLAN: A0/A1 bölgesel tile]
│   ├── geometry/
│   │   ├── spatial.py ; walls.py            [MEVCUT, geometri/duvar adayı]
│   │   ├── topology.py                      [MEVCUT, NetworkX reviewed geçit]
│   │   ├── repair.py                        [PLAN: virtual gap bridge/snap katmanı]
│   │   ├── heuristics.py                    [PLAN: Layer0 wall/door candidate]
│   │   └── massing.py                       [PLAN: kaynak-bağlı 2.5D]
│   ├── legal/
│   │   ├── models.py ; extractor.py         [MEVCUT]
│   │   ├── parser.py ; changes.py ; etl.py [MEVCUT]
│   │   ├── verification.py ; versions.py    [MEVCUT]
│   │   ├── applicability.py ; review.py     [MEVCUT]
│   │   ├── review_viewer.py                [MEVCUT]
│   │   └── review_ledger.py ; version_workflow.py [MEVCUT]
│   ├── rag/
│   │   ├── models.py ; store.py             [MEVCUT, SQLite FTS5]
│   │   ├── indexer.py ; retriever.py        [MEVCUT, lexical/RRF]
│   │   ├── embeddings.py                    [MEVCUT, opsiyonel local CPU]
│   │   └── synonyms.py                     [PLAN: mimari jargon dictionary]
│   ├── rules/
│   │   ├── base.py ; engine.py ; evidence.py [MEVCUT, REGULATORY kilitli]
│   │   └── registry/                        [PLAN / HUKUKI_HOLD: resmî teyitli aileler]
│   ├── reports/                              [MEVCUT]
│   │   ├── models.py ; builder.py           [MEVCUT]
│   │   └── exporter.py ; visualizer.py      [MEVCUT]
│   ├── pipeline.py ; cli.py                  [MEVCUT]
│   ├── app/
│   │   ├── server.py ; launch.py            [MEVCUT, 127.0.0.1]
│   │   ├── static/index.html                [MEVCUT]
│   │   ├── static/dashboard.css             [MEVCUT]
│   │   ├── static/dashboard.js              [MEVCUT]
│   │   ├── jobs.py                          [PLAN: bounded worker, SSE]
│   │   └── static/scene3d.js                [PLAN: yerel lisanslı Three.js]
│   ├── storage/workspace.py                 [PLAN: SQLite WAL source cache/history]
│   ├── vision/{local_vlm,grammar,semantic}.py [PLAN / AR-GE]
│   ├── rubric/{ontology,grading}.py         [PLAN, puan kodda]
│   ├── jury/{schema,personas,runner}.py      [PLAN, sıralı eğitim yorumu]
│   └── analytics/{trend,feedback}.py        [PLAN, kullanıcı izni]
├── tests/                                   [MEVCUT, 16 test modülü]
├── scripts/windows/                         [PLAN, paketleme/wheelhouse/SBOM]
├── benchmarks/                              [PLAN, gerçek QA/research]
└── local_data/                              [GIT DIŞI: ham çizimler, modeller, PDF'ler, DB]
```

## Açılmaması gereken ikinci kökler

- `ARCH-CORE/backend/`, `src/mimar_core/`, `src/arch_jury/`, `src/server/` **aynı işin ikinci Python implementasyonu değildir**: bunların işlevleri yukarıdaki tek `src/mimarllm/` altına aktarılır.
- React/Next.js 16 veya ayrı Node server, yerel v0.1 dashboard'a zorunlu eklenmez. İleride UI ihtiyaçları ciddi büyürse tek paket içine statik build ve offline dağıtım ile, ayrı ürün kararıyla düşünülebilir.
- Yeni `legal_rag/`, ikinci `rules/engine`, yeni `src/mimar/schema/drawing_ir` açılmayacak. Çalışan `rag/`, `legal/` ve `core/ir.py` sözleşmeleri korunacak.
- `models/` içindeki GGUF/MMProj/ONNX, özel projeler, standartlar, SQLite veri ve müşteri/öğrenci kayıtları **public GitHub'a alınmayacak**. Yalnız nasıl temin edileceği lisans ve SHA manifestleriyle tarif edilebilir.

## Planlanan bağımlılık sırası

1. İşlem 021: Windows offline installer/onedir/wheelhouse/SBOM.
2. İşlem 022–024: Kirli CAD, Layer0/kalibrasyon adayı, A0 tiled OCR, jargon RAG ve local source cache.
3. İşlem 025–026: Dashboard gerçek evidence UX, bounded SSE/poll, onaylı 2.5D geometry.
4. İşlem 027: Opsiyonel yerel VLM/GGUF/GBNF benchmark; kesin ölçüm/kaynak değiştirme **yasak**.
5. İşlem 028–030: Rubrik/jüri/persona/öğrenci analitiği genişlemesi **opsiyonel, pedagojik geçerlilik HOLD**.
6. İşlem 031: Gerçek Windows/i7/8GB GPU benchmark, gerçek çizim verileri, eğitim uzmanı, UX, resmî hukuki kayıt/istisna incelemesi son kabul.

Dosyalar **yalnız implementasyon aşamasında** oluşturulmalı; sırf ağaçta var görünmeleri için boş modül açılmamalı. Takvime eklenmiş mevzuat eşikleri hukukî onaydan önce asla etkinleştirilmemelidir.
