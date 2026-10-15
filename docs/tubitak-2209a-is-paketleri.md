# TÜBİTAK 2209-A — MimarLLM V2 × ARCH-CORE Local Araştırma / İş Paketi Taslağı

**Durum:** YALNIZ PROJE PLANI (resmî programa sunulmuş/uygunluğu teyit edilmiş başvuru, onaylı bütçe veya deney sonucu değildir). [İşlem 020](islem_020.md) · [Teknik master](master-mimari-arch-core-local.md) · [Riskler](risk-ve-dogrulama-matrisi.md).

## 1. Araştırma kapsamını yapılabilir tutma

**Önerilen temel bilimsel soru:** Mimari DXF/PDF planlarında kaynak SHA, koordinat ve insan ölçek/geçit incelemesiyle sınırlandırılmış deterministik kanıt motoru, sıradan otomatik sınıflandırma/katmansız çizim yaklaşımlarına kıyasla **yanlış kesin teknik hüküm vermeyi azaltırken** anlamlı geometrik geri bildirim sağlayabilir mi?

**Çekirdek teslim:** Kaynaklı DrawingIR, geometri/topoloji *aday* çıkarma, özgün mevzuat PDF üzerinde şeffaf kaynak inceleme (hukukî PASS değil), yerel rapor ve kullanıcının onayıyla doğrulama. **İkinci hipotez / esneme hedefi:** Kanıt üstünden yerel VLM ile açıklama, 2.5D ve pedagojik rubrik/jüri geri bildiriminin öğrencinin raporu anlamasını kolaylaştırıp kolaylaştırmadığını ölçmek. Yeterli süre/bütçe yoksa bu modüller çekirdek kabulü engellemez; bunların eksik olduğu açıkça belirtilir.

## 2. Kaynak taslaklardan uyarlanmış 12 aylık örnek takvim

Bu aylar **programa kabul veya proje başlangıç tarihi değildir**, proje başlatıldıktan sonraki göreli zaman çizelgesidir. Modül implementasyonu + sentetik regresyon gelişim sırasında; **gerçek insan/gerçek saha cihazı son aşamada** yapılır.

| İş Paketi | Görev | Aylar (göreli) | Çıktı kanıtı | Ölçüm/kapanış |
| --- | --- | --- | --- | --- |
| İP-1 | Var olan DrawingIR/RuleEngine pipeline source contract audit ve kapsam baz çizimi | 1–2 | kaynak hash/frame/check/CI envanteri | sentetik branch CI, yeni kaynak sürüm dosyası |
| İP-2 | Kirli CAD, Layer0 ve kaynak-koruyan repair overlay/kalibrasyon adayı | 2–4 | original vs suggestion overlay ve güven kanıtı | geometry IoU, false gap bridge, unit hypothesis error |
| İP-3 | A0/A1 ROI OCR + FTS5 terminoloji, kaynak sürüm ve uygunsuz mevzuat HOLD | 3–5 | text quad, native/OCR ayrımı, FTS5 glossary | CER/WER, source bbox IoU, Recall@k |
| İP-4 | Windows offline dağıtım, local user workflow, guarded background run, 2.5D opt-in | 4–7 | wheelhouse/SBOM, local HTML ve varsa 2.5D source linked model | packager smoke, UI error states, geometry pin consistency |
| İP-5 | Opsiyonel multimodal yerel VLM, code-owned 8D rubric ve sıralı eğitsel yorumlar | 6–10 | sürümlü JSON schema, explicit evidence referansı, model-card/license | GPU VRAM, JSON valid, rubrik tutarlılığı/uzman görüşü |
| İP-6 | Gerçek Windows cihazı, uzman ve öğrenci, kontrollü örneklem ile bağımsız geçerlik/UX | 10–12 | anonim etiketler, protokol, gerçek test ve olumsuz sonuçlar | p50/p95, κ/ICC, Recall, SUS, gerçek fail/hold dağılımı |

## 3. Başarının tarafsız gösterimi

**Geometri/ölçek:** native kaynak referans ile face/duvar aday IoU, kaç gerçek açık oda yakalandı, kaç yanlış sanal köprü önerildi, kalibrasyon çelişkilerinde ne kadar sıklıkla `INSUFFICIENT_EVIDENCE` döndü. “Yanlış ölçü %0” matematiksel garanti diye sunulmaz; örneklemle tahmin edilir.

**Mevzuat/RAG:** Dokümanların yayın/kaynak kimliği, yürürlük zinciri ve query match doğruluğu **farklı deney** olarak raporlanır. FTS5/BM25, dense/RRF, synonym ablation; gold etiket veri yoksa yüksek Recall iddia edilmez. Hukukî `APPROVED_FOR_CHECK` için bağımsız hukukî inceleme gerekir.

**Eğitim:** Sekiz boyutlu rubrik uzmanlar tarafından yazılacak; rubrik geçerliği, yorum faydası ve bağımsız jüri uyumu kör değerlendirmede ayrı ölçülecek. İkili/nominal etiketlerde κ, sürekli/ordinal puanlarda uygun ICC/ağırlıklı kappa; örneklem büyüklüğü, güven aralığı ve değerlendiriciler arası varyans raporlanır. Gerçek öğrenci sonuçları yalnız onam ve saklama/gizlilik protokolüyle kullanılabilir. Simüle edilmiş 10 persona “10 bağımsız eğitmen” sayılmaz.

**Kullanılabilirlik:** SUS, görev tamamlama, yanlış kaynağa tıklama, “yanlış hukukî PASS algısı”, kaynak açıklama süresi. Gerçek Windows/Edge ve tercihen birden fazla donanım profili raporlanır.

## 4. B Planı ve etik kapılar

- Gerçek resmî hukukî belgelere/tam TS standartlarına yasal erişim yoksa: hakları doğrulanmış sentetik/lisanslı metinlerde kanıt/arıma gösterimi; hukukî uygunluk `HUKUKI_HOLD` devam eder.
- GPU/MMProj uyumsuzluğu veya VRAM taşması: VLM/jüri opsiyoneli kapatılır, 2D source kanıt + deterministik rapor çalışır; “otomatik GPU fallback” garanti edilmez.
- Kapalı alan/door semantics yetersizse: poligonlar `UNCLASSIFIED_FACE`, Layer0 heuristik aday, doğru kaynağı kullanıcı seçer. Geçiş/yangın tahmini uydurulmaz.
- Bireysel öğrenci veya müşteri çizimi: açık izin yoksa kamuya açık repoya, prompt datasetine veya model eğitimine katılmaz.
- Personas ve yaşayan/tarihî mimarlar: eğitsel perspektifler temsilî sentetik içeriktir, gerçek kişinin tavsiyesi veya otorite iddiası yoktur.

**Resmî TÜBİTAK 2209-A programına başvuru biçimi, süre/bütçe/etik kurul yükümlülükleri bu belgeden otomatik doğrulanmaz; başvuru anındaki güncel resmî program şartlarına göre ayrıca kontrol edilir.**
