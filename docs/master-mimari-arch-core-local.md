# MimarLLM V2 × ARCH-CORE Local — Birleştirilmiş Master Mimari v1.0

**Durum:** 2026-10-15 güncel mühendislik planı; yeni özelliklerin çoğu PLAN. **Kayıt:** [İşlem 020](islem_020.md). **Karar:** [ADR-004](adr/ADR-004-ARCH-CORE-Local-Kapsam-Genislemesi.md). **Rota:** [güncel yol haritası](uygulama-yol-haritasi.md). **Risk:** [risk ve doğrulama](risk-ve-dogrulama-matrisi.md). **2209-A:** [araştırma iş paketleri](tubitak-2209a-is-paketleri.md).

Bu belge, kullanıcının üç metnindeki (ARCH-CORE yerel birleşim, yedi teknik darboğaz, önerilen dizin mimarisi) hedefleri **İşlem 001–019 sonunda gerçek GitHub ağacındaki kodla** karşılaştırır. Metinlerdeki tahminî benchmark süreleri ve önerilen dosyalar uygulanmış kod sayılmaz.

## 1. Ürün kararı — iki kapsam, tek modüler monolit

**A — MimarLLM V2 Engineering Core (mevcut, öncelik):** Yerel Windows-first DXF/PDF okuma, DrawingIR, kaynak/koordinat ve kanıt, Shapely geometri adayı, NetworkX yalnız incelenmiş geçit grafı, teknik RuleEngine, LegalAST + SQLite FTS5/RRF, özgün PDF üzerinde sarı kaynak konumu, HTML/JSON/Markdown/PDF, CLI ve yerel tek kullanıcı FastAPI dashboard. Bu çekirdek GPU, VLM, pedagojik persona ve sunucu hizmeti olmadan çalışmalıdır.

**B — ARCH-CORE Studio/Education (ileri-sürüm opsiyonel modüller):** DrawingIR kanıtından kaynaklı 2.5D WebGL görünüm, yerel GGUF/VLM ile *yalnız* semantik adaylar, sekiz boyutlu deterministik eğitim rubriği, tek model üzerinde sıralı pedagojik bakış açısı yorumları ve isteğe bağlı öğrenci gelişim analitiği. **Şu anda uygulanmadı**; eski İlk Ürün kapsamının eğitim/jüri dışlaması yeni çekirdekte korunurken **ileriki sürüm genişleme adayı** olarak yeniden açılır. Eğitimciler ve kullanıcılar gerçek pedagojik geçerliliği ayrı onaylamalıdır.

**Kanonik Python paketi yalnız `src/mimarllm/`.** İkinci bir `ARCH-CORE/backend/`, `src/mimar_core/`, `src/arch_jury/` veya paralel `schema/drawing_ir.py` açılmaz. FastAPI `app/`, kaynaklı raporlar `reports/`, hukukî arama `legal/ + rag/` kullanır. Çok sayıda Docker microservice, zorunlu Next.js ve çoklu GPU modeli ürüne temel bağımlılık olarak sokulmaz.

## 2. Mevcut kod ↔ ek metinler karşılaştırma

| Alan | GitHub'da mevcut ve gerçek | Ek metnin yeni talebi | Karar ve durum |
| --- | --- | --- | --- |
| Kaynak model | `core/ir.py` ve `units.py`, SHA/entity/frame | Tüm çizimi SI metreye normalize etmek | **RED**: özgün CAD/PDF koordinatı korunur; SI ayrı kalibrasyon katmanı |
| DXF/PDF | `importers/dxf.py`, `pdf_ir.py`, `layers.py` | Kirli CAD, Layer0, dev OCR | **KISMI + PLAN:** yeni adayı kaynakla birlikte tut |
| OCR | `pdfplumber + pypdfium2 + RapidOCR CPU` ve explicit ROI | Vektör kısayolu ve tiled OCR | **PLAN:** eksik raster/SHX metin ihtimali nedeniyle vektör PDF'yi toptan OCR'dan muaf tutma |
| Geometri | `geometry/spatial.py`, `walls.py`; unclassified face, issue | otomatik virtual door bridging, poligon onarımı | **PLAN, VIRTUAL_CANDIDATE**: orijinali değiştirme; kesin oda/PASS üretme |
| Topoloji | `geometry/topology.py`; reviewed room/passage | Dijkstra yangın kaçış metreleri | **RED:** grafik hop gerçek yürüme uzunluğu değildir; çok kat/engeller ayrı modeller ister |
| Teknik kurallar | `rules/base.py`, `engine.py` | Beş mevzuat ailesi ve sabit eşikler | **HUKUKI_HOLD:** hukukî PDF/sürüm/proje istisna/onay olmadan mevzuat eşiği aktifleştirme |
| Mevzuat ve RAG | `legal/` + `rag/` LegalAST, FTS5, RRF, PDF page quad | mimari jargon query expansion, statik madde | **KISMI + PLAN**: retrieval adayı resmî yürürlük değil |
| Rapor ve UI | `reports/`, `pipeline.py`, `cli.py`, `app/server.py`, `app/static/` | SSE, 3D, öğrenci dashboard'u | **KISMI + PLAN**: mevcut tek kullanıcı UI genişler |
| Dağıtım | `pyproject.toml`, CLI/localhost launcher | offline onedir + wheelhouse + SBOM | **PLAN**; GitHub-hosted CI gerçek paket kabulü değildir |
| VLM, GPU | Bu depoda GGUF/llama.cpp multimodal entegrasyonu yok | tek VRAM modeli, strict schema, persona | **AR-GE / OPSİYONEL**; sürüm/model/VRAM henüz doğrulanmadı |
| Eğitim | jüri, rubrik, ton profili, analitik yok | 10 uzman, 15 mimar, 21 ton, 8 rubrik | **KAPSAM GENİŞLEME ADAYI**; bağımsız uzman görüşü/otomatik not iddiası yasak |

## 3. Değişmeyen kanıt ve ölçü sözleşmesi

```text
DXF / PDF (orijinal baytlar + SHA256)
  |
  v
DrawingIR v0.1: source entity, CAD handle, block_path / PDF page, native quad
  |-- GeometryAnalysis (kesişim, unclassified face, kaynaklı sorun)
  |      |-- ProposedRepairOverlay [PLAN]      ≠ özgün geometri
  |      |-- UnitHypothesis [PLAN]              ≠ CONFIRMED ölçek
  |      |-- Layer0SemanticCandidate [PLAN]     ≠ kesin Wall/Door/Column
  |-- TopologyResult: SADECE REVIEWED native marker/room/passages
  |-- RuleEngine: yalnız kaynaklı teknik senaryo, mevzuat LOCKED
  |
  +--> LegalAST: orijinal mevzuat SHA/page/quad
         +--> SQLite FTS5, RRF, synonym [PLAN]
         +--> tarih/sürüm/manual source review
         +--> REGULATORY_LOCKED, HUKUKI_HOLD
  |
  v
AnalysisReport: Finding ↔ çizim kaynağı ↔ özgün mevzuat PDF adayı
  +--> CLI/localhost dashboard [MEVCUT KOD, KISMI]
  +--> 2.5D/3D önizleme [PLAN]
  +--> yerel VLM ile semantik aday [PLAN]
  +--> 8D rubric + pedagojik persona yorumu [PLAN]
  +--> gerçek saha, hukukî, Windows, TÜBİTAK bilimsel kabul [SON]
```

**Kırmızı çizgiler:**

- Oda merkezi, sanal geçit çizgisi, yan yana iki duvar çizgisi veya tahminî kapı boyu **asla** doğrulanmış net alan, kapı temiz geçişi, yangın kaçış mesafesi, mevzuat `PASS` değildir.
- `$INSUNITS` ve histogram ancak `INFERRED`; fiziksel metre ölçümü için kaynak native çizgisi, kullanıcı referansı, aynı frame ve tolerans gereklidir. PDF/SVG asıl koordinatları korunur.
- Kaynak belge üzerinde meta veri çıkarımı veya onarım yapıldıysa **yeni türetilmiş belge SHA** ile orijinal hash ayrı saklanmalı; orijinal kanıt sessizce bozulmamalı.
- RAG relevancy ve expert/pedagogical "jüri" yorumu resmî mevzuat doğruluğu değildir; VLM kaynak koordinat/ölçü değiştiremez.
- Otomatik `3D extrude` ancak incelemeci onaylı 2B polygon ve **beyan edilmiş kat yüksekliği** ile kütle adayıdır; organik strüktür, gerçek kesit veya yangın ihlali 3D konumu uydurulmaz.

## 4. Kanonik gelecek kod ağacı — varlıkları dürüstçe ayır

```text
MimarLLM_v2/
  pyproject.toml                                  [MEVCUT]
  README.md                                       [MEVCUT]
  docs/                                           [MEVCUT, islem_NNN + ADR + specs]
  src/mimarllm/                                   [MEVCUT, TEK PYTHON PAKETİ]
    core/ir.py, core/units.py                     [MEVCUT]
    importers/{dxf,pdf_ir,pdf,layers}.py          [MEVCUT]
    ocr/rapid_engine.py                           [MEVCUT]
    geometry/{spatial,walls,topology}.py          [MEVCUT]
    legal/ ; rag/ ; rules/                        [MEVCUT]
    reports/ ; pipeline.py ; cli.py               [MEVCUT]
    app/{server,launch,static/}                   [MEVCUT]
    core/calibration_candidates.py                [PLAN — kaynaklı INFERRED]
    geometry/{repair,heuristics}.py               [PLAN — overlay, Layer0 aday]
    ocr/tiled_regions.py                          [PLAN — kaynak coord dönüşümlü]
    rag/synonyms.py                               [PLAN — jargon query expander]
    storage/workspace.py                          [PLAN — yerel WAL/cache/history]
    app/jobs.py                                   [PLAN — bounded jobs / progress]
    geometry/massing.py                           [PLAN — kaynaklı 2.5D mesh]
    app/static/scene3d.js                         [PLAN — yerel Three.js, build sonrası]
    vision/{local_vlm,grammar,semantic}.py         [PLAN — offline opt-in GPU]
    rubric/{ontology,grading}.py                  [PLAN — score-in-code]
    jury/{schema,personas,runner}.py               [PLAN — sequential model commentary]
    analytics/{trend,feedback}.py                 [PLAN — açık rızalı öğrenci takibi]
  scripts/windows/                                [PLAN — wheelhouse/onedir/SBOM]
  benchmarks/                                     [PLAN — doğru baseline ölçümleri]
  tests/                                          [MEVCUT, yeni modülle büyüyecek]
  local_data/                                     [GIT DIŞI, kullanıcı projesi/model/DB]
```

Boş klasör veya örnek sıfatlı Python dosyaları sırf ağaçta görünsün diye açılmayacak. İşlem 020 plan güncellemesi, yukarıdaki PLAN modüllerinin oluşturulduğu anlamına gelmez.

## 5. Donanım, lisans, gizlilik

**Hedef platform:** Windows 10/11, i7 14. nesil, 32 GB RAM ve RTX 4070 8 GB VRAM. Geometry, topology, OCR ONNX CPU, SQLite FTS5 ve RuleEngine GPU olmadan çalışır; VLM opsiyonel GPU, WebGL tarayıcı GPU'su tüketir. Yerel çalışma sırasında ücretli harici AI API, token ve Internet gerekmemeli. Offline kurulum için bağımlılıklar ve model ağırlıkları kullanıcının diskinde önceden sağlanmalı; **henüz bağımsız offline installer yok**.

Kaynak metinlerdeki “2.7 GB VRAM”, “0 OOM”, “300ms geometri”, “60 FPS”, “15–25 sn jüri”, “94% oda”, “Recall@10 %90”, “Cohen kappa .60”, “SUS 70” değerleri **ölçülmüş repo sonucu değil, önerilen test hedefi/hipotez** olarak risk dokümanında tutulur. GGUF/MMProj uyumluluğu, model/sürüm, Windows CUDA binary ve GPU peak ölçülmeden sabit model seçimi bağlayıcı olmaz.

**Lisans:** Bağımlılık üst lisansı “tümü %100 permissif” garantisi vermez. Native transitif kütüphaneler, model/merch, PDFium/Three.js, PyInstaller runtime hakları ve korunan TS standartları ile telifli Ching/Neufert içeriği, SBOM ve yeniden dağıtım incelemesi gerektirir. Public depoya hakları belirsiz tam standartlar, özel müşteri/öğrenci çizimleri, token/secret, model ağırlıkları alınmaz.

**Gizlilik:** Tek kullanıcılı localhost prototipi çok-kullanıcılı güvenli LMS değildir. Eğitim profil/analitik eklenecekse açık rıza, saklama/silme süresi, erişim kontrolü, anonimleştirme ve kaynak lisansı ayrı tasarlanmalıdır. SHA256 kanıt kaydı ≠ elektronik imza.

## 6. Ayrı kabul kapıları

- **Mevcut sentetik kod regresyonu:** İşlem 019 son GitHub Actions kaydı Ubuntu/Windows **295/295 PASS**. Bu gerçek müşteri Windows/Edge veya kurulu launcher testi değildir.
- **Gerçek çizim kabulü:** Layer0, zayıf CAD, açık odalar, A0/A1, bozuk ölçü ve ayrı PDF sayfa/topolojik açıklıklarda uzman gerçek değerlerle test — **HOLD**.
- **Windows/GPU performansı:** offline installer, model/mmproj CUDA, CPU fallback, bellek p95, görsel WebGL FPS, Edge etkileşimi — **HOLD**.
- **Hukukî:** Resmî Gazete asıl kaynak, yürürlükte konsolide sürüm, geçiş ve istisna, konum/proje uygulanabilirliği, hukukçu/alan uzmanı — **HUKUKI_HOLD**.
- **Pedagoji/2209-A:** Sekiz boyutlu rubrik bağımsız uzman/öğretim üyesiyle geçerlilik; kör uzman karşılaştırması, kappa/ICC uygunluğu, onam ve SUS gerçek kullanıcı değerlendirmesi — **PLAN/HOLD**.

**Ürün pozisyonu:** MimarLLM V2 kaynağa bağlı mimari analiz yardımcısıdır; ARCH-CORE Local yalnız bu kanıtlara dayalı ileri sürüm pedagojik yorum ve 2.5D simülasyon eklentisidir. Ne yazılım ne de metinsel jüri otomatik ruhsat, yapı güvenliği veya resmi akademik not onayı verir.
