# MimarLLM V2 — Sade Tek Paket Dizin Mimarisi

**İşlem:** [islem_006](islem_006.md) · **Durum:** PLANLANAN DİZİN; aşağıdaki modüllerin çoğu henüz oluşturulmadı.

```text
MimarLLM_v2/
├── README.md
├── pyproject.toml                  # Tek Python bağımlılık kaynağı
├── .gitignore
├── run.bat                         # Plan: geliştirici/yerel wheelhouse başlangıç
├── build_exe.bat                   # Plan: Windows PyInstaller
├── mimar.spec                      # Plan: onedir standalone
├── docs/
│   ├── islem_001.md ... islem_006.md    # Mevcut, sıralı gerçek kayıtlar
│   ├── ozellik-envanteri.md
│   ├── uygulama-yol-haritasi.md
│   ├── mevzuat-dogrulama-protokolu.md
│   ├── planlanan-dosya-yapisi.md
│   ├── windows-dagitim-plani.md
│   ├── adr/
│   │   ├── ADR-002-PDF-Engine-License.md
│   │   └── ADR-003-Kapsam-Kanit-ve-Kabul-Kapilari.md
│   └── specs/                       # Henüz yok: alt şemalar
├── src/
│   └── mimarllm/                    # TEK mevcut paket adı
│       ├── __init__.py
│       ├── core/
│       │   ├── models.py            # MEVCUT: PDF source observation
│       │   ├── ir.py                # PLAN: CAD DrawingIR
│       │   └── units.py             # PLAN: SI kalibrasyon
│       ├── importers/
│       │   ├── pdf.py               # MEVCUT: pdfplumber+pypdfium2
│       │   ├── dxf.py               # PLAN: ezdxf
│       │   └── layers.py            # PLAN: lexicon/regex aday
│       ├── ocr/
│       │   ├── rapid_engine.py      # MEVCUT: CPU RapidOCR adapter
│       │   ├── text_extractor.py    # PLAN: ROI kalite kapısı
│       │   ├── layout.py            # PLAN: mahal/kot/antet
│       │   └── box_utils.py         # PLAN: transform/quad
│       ├── geometry/
│       │   ├── spatial.py           # PLAN: room polygon, net/brut
│       │   ├── walls.py             # PLAN: double-wall ve openings
│       │   └── topology.py          # PLAN: NetworkX access/egress
│       ├── regulations/
│       │   ├── extraction.py        # PLAN: OFFLINE PDF/HTML ETL
│       │   ├── parser.py            # PLAN: LegalAST
│       │   ├── store.py             # PLAN: FTS5, indexed versions
│       │   ├── retrieval.py         # PLAN: dense CPU + RRF
│       │   ├── versions.py          # PLAN: amendments and validity
│       │   └── citations.py         # PLAN: original page and quad
│       ├── rules/
│       │   ├── base.py              # PLAN: rule contracts
│       │   ├── engine.py            # PLAN: deterministic checks
│       │   ├── evidence.py          # PLAN: verified legal binding
│       │   └── registry/
│       │       ├── tr_imar.py       # PLAN/HUKUKİ HOLD
│       │       ├── tr_yangin.py     # PLAN/HUKUKİ HOLD
│       │       ├── tr_otopark.py    # PLAN/HUKUKİ HOLD
│       │       ├── tr_siginak.py    # PLAN/HUKUKİ HOLD
│       │       └── tr_bep.py        # PLAN/HUKUKİ HOLD
│       ├── evidence/
│       │   └── findings.py          # PLAN: geometry+legal source chain
│       ├── reports/
│       │   ├── exporter.py         # PLAN: JSON/Markdown/HTML/PDF
│       │   └── visualizer.py       # PLAN: SVG + original PDF highlight
│       ├── vision/
│       │   ├── vlm.py              # PLAN: local GGUF/ROI inference
│       │   ├── semantic.py         # PLAN: non-overwriting predictions
│       │   └── prompts.py          # PLAN: strict output schema
│       ├── app/
│       │   ├── server.py           # PLAN: localhost FastAPI
│       │   └── static/             # PLAN: no-CDN UI
│       ├── pipeline.py             # PLAN: staged analysis
│       └── cli.py                  # PLAN: Python -m mimarllm.cli
├── scripts/
│   └── benchmark_audit.py          # PLAN
└── tests/
    ├── test_pdf_contract.py         # MEVCUT, sonuç bağımsız teyide muhtaç
    ├── test_dxf_parser.py           # PLAN
    ├── test_geometry.py             # PLAN
    ├── test_topology.py             # PLAN
    ├── test_rules.py                # PLAN
    ├── test_rag.py                  # PLAN
    ├── test_pipeline.py             # PLAN
    └── fixtures/                    # PLAN: tamamen sentetik/lisanslı
```

**Gerçek dosya ağacına yeni boş python modülleri oluşturulmayacak.** Her modül ilk kez geliştirildiğinde kendi işlem kaydı ile commit edilir. `src/mimar/` ikinci bir package olarak açılmaz; `src/mimarllm/` sabittir.

### Git dışı veriler

```text
local_data/
  projects/              # gerçek müşteri çizimleri
  regulations/raw/       # özgün ve lisanslı mevzuat PDF/HTML
  regulations/parsed/    # structural AST
  regulations/index/     # local FTS5/dense
  models/                # GGUF / ONNX weights
  runs/                  # local metrics/temp
```

PDF/original document dosyaları public depoya otomatik kopyalanmaz. Hiçbir fonksiyon internet API'ye bağımlı olmaz.

**Önemli:** Aşağıdaki `run.bat` ve `.spec` dosyaları bir tasarım hedefidir. Gerçek CLI/app oluşturulmadan paketleme tamamlandı ve hazır masaüstü uygulaması iddiası yoktur.
