# MimarLLM V2 × ARCH-CORE Local — Risk, B Planı ve Bilimsel Doğrulama Matrisi

**İşlem:** [020](islem_020.md) · [Master mimari](master-mimari-arch-core-local.md). Kaynak: kullanıcının “7 kritik mühendislik darboğazı” metni ve 2209-A birleşim taslağı; risk/süre/başarı sayıları **kaynak metindeki varsayımlar veya hedeflerdir, mevcut GitHub'da doğrulanmış mühendislik sonuçları değil**.

| Risk | Kök neden | Uygulama (kaynak koruyan yaklaşım) | B planı / açık HOLD | Ölçülecek gerçek metrik |
| --- | --- | --- | --- | --- |
| R1 Kirli CAD ve açıklık | Undershoot, çakışma, açık duvar/kapı çizgisi | Shapely native linework sorunlarını işaretle; snapping/ray extension/virtual door bridging **önerilen alternatif katmanda** ve explicit toleransla oluştur; orijinal entity/handle/geometriye dokunma | Yalnız kaynağı incelemeci tarafından onaylanmış açıklıklarla topoloji; aksi halde oda/alan/geçiş **REVIEW_REQUIRED** | Açık/çakışan segment tanıma precision/recall, doğru yüz sınırı IoU, aşırı-kapatma false positive |
| R2 $INSUNITS, mm/cm/m, DXF dimension | Birimsiz/yanlış header, sahte insan ölçüsü | Kaynak çizgi/dimension/kapı histogramıyla **UnitHypothesis** öner; güven ve çelişki listesi; `UnitCalibration.CONFIRMED` ancak birebir kaynak referansı + gerçek metre + kullanıcı incelemesi | Çelişki halinde `CONFLICT/INSUFFICIENT_EVIDENCE` ve m/m² uygunluk üretilmez | Kaynak birim classification accuracy, yanlış kesin fiziksel ölçü oranı (hedef 0), tolerans |
| R3 Layer0, kirli layer | Etiket yok, AIA/Türkçe layer yok | Paralel çizgi, HATCH, ARC eğriliği gibi geometrik özelliklerle `SemanticCandidate(WALL/DOOR/COLUMN)`; destekleyen native ID ile güven ve karşı-kanıt | Manuel layer/space/portal seçim iş akışı; heuristik kendiliğinden authoritative DrawingIR semantics yapmaz | Wall/door/column aday precision/recall, native source coverage |
| R4 A0/A1 taranmış PDF OCR | Tam sayfa yüksek DPI RAM/latency, küçük metin | `pdfplumber` vektör + eksik ROI için `pypdfium2` tile; overlap, dönme, DPI, crop, source PDF point quad geri dönüşü ve dedup; `RapidOCR CPU` | Kullanıcı ROI seçsin, düşük DPI uyarısı; bütçe aşımında `SKIPPED/REVIEW_REQUIRED`; taranmış sayfaya zorunlu full-page OCR yok | Peak RSS, p50/p95 süre, CER/WER, bbox IoU, text provenance |
| R5 8GB VRAM + JSON kırılması | Uzun multimodal context, GGUF/MMProj/llama.cpp uyumu, persona drift | Yerel tek VLM instance/opsiyonel, VRAM guard/preflight, structured JSON+Pydantic; rubrik puanı **code-owned**; persona görevleri sequential | GPU OOM riskinde kullanıcıya bilgi ver ve VLM OFF/CPU-only fallback *ölçülmüşse*; model re-init etmeden otomatik n_gpu_layers transfer garantisi verme | VRAM peak, başarı/timeout, schema-valid output, GPU→CPU hız |
| R6 Mimari jargon vs mevzuat dili | “EBEV.”/“HOL” ile resmî hukukî terim ayrımı | Sürüm kontrollü küçük Türkçe mimari synonym sözlüğü; tekil exact article ID ve FTS5/BM25; base RRF ile karşılaştırma | Synonym eşleşmesi belirsizse arama sonucunu ayrı aday göster, hukukî hükme “mühür” vurma | Recall@k, MRR/nDCG, yanlış doküman/hüküm eşleştirme |
| R7 UI kilitlenmesi / 3D kalabalığı | CPU parse, OCR ve GPU VLM isteği event-loop üzerinde, HATCH mesh artışı | Worker queue + sınırlı concurrency + SSE stage events; Three.js yalnız onaylanmış 2.5D strüktürel mesh; LOD/simplify tolerans ve kaynak-bağlı pin | SSE koparsa polling, GPU sahne kapanırsa 2D source SVG, VLM gecikirse çekirdek rapor hemen kalır | İlk anlamlı ekran süresi, event latency p95, FPS p5, RAM/VRAM, kaynak-pin kayma oranı |

## Geri döndürülemez hataya karşı açık güven sınırları

1. **Virtual Bridge:** 2–10 cm boşluğu zorla birleştirme ve bir odayı diğerine ekleme riski. Kaynak geometri hiç değişmez; `ProposedRepairOverlay` altında orijinal/önerilen iki ayrı polygon; kullanıcı kabul etse bile değişiklik şeffaf. Açıklık kapanması otomatik kapı/yangın eşiği sağlamaz.
2. **Unit histogram:** “90 birim görüldü → santimetre” yalnız olasılıktır, CAD ölçü/ölçek kalibrasyonu değildir. DXF'yi import anında dönüştürürsen CAD handle→source polygon kanıtını bozarsın; iki ayrı transform tut.
3. **Tiled OCR:** Kapalı oda merkezleri bile `REVIEW_REQUIRED` yüzey adaylarıdır; ROI'yi sadece onları baz alarak hesaplamak etiketleri kaçırabilir. Önce PDF layout/yerel ROI ve seçili topolojik bölgeler; gerekirse kullanıcı manuel tile seçer.
4. **VLM grammar:** Syntax-valid JSON, içerik factually correct demek değildir. Ek numeric bounds, evidence ID whitelist, source bounding quad provenance ve native-core overwrite yasağı gerekir.
5. **Jüri puanı:** 10 persona aynı model çıktısı olduğundan “10 bağımsız uzman” değildir. Rubrik puanı ancak insan kalibrasyonlu/şeffaf deterministik algoritmadan gelir; modelden gelen ±10 bile kanıtsız şekilde geçerli akademik notu değiştirmemeli.
6. **Resmî hukuk:** TS 825/TS 9111 veya diğer standartlar, coğrafya/tarih/yapı türü dışında varsayılan sayısal eşiklerle yayımlanmaz; tam metin yeniden dağıtımı ayrıca telif hakkı gerektirir.
7. **Gizlilik:** Model prompt/cache'e gönderilen çizim üzerinde kişi/öğrenci kimliği olabilir. Varsayılan telemetry yok, local data at rest ve retention tasarımı, Git'e dış kaynak/metin eklememe.

## TÜBİTAK 2209-A bilimsel ölçüm taslağı (PLAN, gerçekleşmedi)

| Kategori | Metinlerde önerilen hedef (yeniden doğrulanacak) | Deney/raporlama disiplini |
| --- | --- | --- |
| Offline runtime | dış bulut AI çağrısı **0** | air-gapped gerçek Windows cihazda kaynak process egress ve bağımlılık kaydı |
| Geometri | `~94%` poligon başarısı, `≤300 ms` CPU | bağımsız gerçek DXF doğruluk/latency; cihaz, pafta karmaşıklığı, p50/p95, başarısız çizimler |
| Ölçek | yanlış ölçekten sahte PASS/FAIL **0** | gizli birimli mm/cm/m CAD fixture ve bilinmeyen durumları |
| OCR | `≤300MB` OCR RSS, `6x` throughput | A0/A1 raster, ROI tile boyutu/overlap ve CER/WER; kalite/süre trade-off |
| RAG | `Recall@10 ≥ .85 / .90` | yıl ve mevzuat kural ailelerine göre ayrı etiketlenmiş en az 200 soru, baseline lexical/dense/RRF/synonym |
| GPU/persona | `≤3GB VRAM`, `5 persona ≤30s` | GGUF/model-mmproj context+OS browser ve WebGL birlikte, VRAM peak, p95; CPU fallback ve OOM oranı |
| 3D/UI | `60 FPS`, ilk ekran `300ms` | gerçek düşük/yüksek yoğunluklu çizim, Chrome/Edge WebGL, p5 FPS ve semantik mesh onayı |
| Eğitim | `Cohen κ ≥ .60`, `SUS ≥70` | bağımsız mimar jüri/gözlemciler, etiketleme yönergesi, konsensüs etkisini ayrı göster, kör çalışma, gizlilik ve rıza |

**Bunların hiçbiri GitHub 295/295 sentetik CI ile kanıtlanmaz.** Ayrıca Cohen kappa nominal sınıflar için tanımlıdır; 8 boyutlu sürekli rubrik değerlendirmeleri için ICC veya uygun ordinal ağırlıklı kappa kullanılması metodolojik inceleme gerektirir. Makine ve insan puanlarını sırf birbirine yaklaştırmak yerine uyumsuz örnekler ve belirsizlik ayrı raporlanır.

## Kabul takvimi

Özellikler/modül entegrasyonu ve sentetik regresyonlar geliştirmenin içinde; **gerçek kullanıcı çizimleri, uzman gözden geçirme, gerçek GPU/Windows offline kabul ve TÜBİTAK bilimsel değerlendirme** ürün özellikleri tamamlandıktan sonra bağımsız son kabul aşamasında yapılır. Bu karara rağmen lisans, hukukî HOLD, güvenlik ve veri kaynağı kapıları geliştirmenin her aşamasında fail-closed tutulur.
