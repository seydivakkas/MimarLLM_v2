# İşlem 016 — Özgün mevzuat PDF görsel kanıt incelemesi ve tarihsel sürüm inceleme iş akışı

- **Tarih:** 2026-10-14
- **Durum:** UYGULANDI — kaynak PDF görsel vurgulama + değişiklik PDF kıyas + imzasız kayıt zinciri; Linux/Windows sentetik CI PASS. Resmî kaynak/yürürlük/uzman imzası ve gerçek saha kabulü HOLD.
- **Ön koşullar:** 013 PDF→LegalAST (UNREVIEWED); 014 SQLite FTS5/RRF; 015 kaynak kimliği, amendment claim, proje uygulanabilirlik bağı. 001–015 işlem kayıtları değiştirilmez.
- **Çevrimdışı:** Yerel orijinal PDF, `pypdfium2`/PDF render, yerel HTML/SVG; bulut/ücretli API veya model gerektirmez.
- **Hukukî sınır:** Görsel kanıtı görüntüleme/manuel inceleme **resmî yayımlanma, normun yürürlükte olması veya `APPROVED_FOR_CHECK` değildir**. `RuleEngine` tüm `REGULATORY` kuralları `INSUFFICIENT_EVIDENCE` kilidinde tutulacak.

## 1. Uygulanacak modüller

1. `src/mimarllm/legal/review.py`: incelenecek LegalAST düğüm, tablo hücresi, değişiklik ifadesi ve `AmendmentClaim`'in kaynak PDF SHA/node/line/cell/page/quad ile **değiştirilemez inceleme referansı**; manuel `VISUALLY_MATCHED`, `CORRECTION_REQUIRED`, `UNREVIEWED` kayıtları. Kararı kullanıcı seçimi, gözlem türü ve notla açıkça ayrıştır; kullanıcının seçimi dijital imza değildir. İmzalanmış/kurumsal belge iddiası yasak.
2. `src/mimarllm/legal/review_viewer.py`: seçilen özgün PDF sayfalarını güvenli `pypdfium2` ile görüntüye dönüştür; **orijinal sayfa üst-sol PDF point koordinatında SVG polygon** ile gerçek hücre/metin kutusuna sarı vurgu; kaynak kimliği, sayfa, metin, ilgili madde/fıkra, değişiklik hedefi ve bağlayıcının HOLD uyarılarını gösteren yerel bağımsız HTML. Görüntü render/coordinate/hash yanlışsa fail-closed ve PDF bağlantısı üretme. HTML içinde dosya/içerik metni güvenli kaçış.
3. `src/mimarllm/legal/review_ledger.py`: kullanıcının indirdiği/doldurduğu inceleme kararlarını kaynak `ReviewTask` ile yeniden doğrulayarak yerel append-only hash-chain JSONL kayıt/okuma; bu **kriptografik imza veya dosyanın dışarıdan değiştirilmediği garantisi değildir**.
4. `src/mimarllm/legal/version_workflow.py`: hedef/müdahil amendment LegalAST'in **ayrı** özgün PDF sayfalarını görsel inceleme kuyruğuna eşleştir, iki tarafa ilişkin değişiklik beyan kimliği/dönemini sakla; `assess_version_chain` sonucunu göster; otomatik konsolide hüküm veya resmî yürürlük tarihi oluşturma.
5. `tests/test_legal_review.py`: ReportLab sentetik özgün + amendment iki PDF, madde/fıkra/hücre/quad, doğru SVG koordinat skalası, file SHA ret, bozuk bbox, HTML escaping, elle review durumları, ledger bütünlüğü ve değiştirilmiş kayıt; değişiklik dönemi çakışması ve orijinal PDF eksikliği.
6. `.github/workflows/core-contracts.yml` Ubuntu + Windows test matrisi; `docs/specs/legal-review-v0.1.md`, README, F15/F16 envanter, yol haritası ve kararlar.

## 2. Önleyici teknik ve hukukî koşullar

- Görsel sayfa yalnız **gerçek SHA-256'sı LegalAST ile aynı** yerel PDF'den render edilir. Değişiklik belgesi ayrı PDF'dir; aynı madde numarasından birleştirme olmaz.
- Görsel kaynak alanı `LegalSourceSpan.page_index/polygon` ile aynı koordinat sisteminde olmalı. Yanlış CropBox/rotasyon/çözünürlük veya offpage quad'da yanlış vurgu üretmek yerine işlem reddedilir.
- Tablo hücresine denk gelen polygon ile fıkra/başlık kaynak alanı ayrı inceleme hedefleri olmalı. Bir satırın çok parça `spans` listesi ayrı ayrı vurgulanmalı.
- Manuel kararın `VISUALLY_MATCHED` olması yalnız **gösterilen metin/polygonun insan beyanına göre görsel örtüşmesidir**; hukukî uzman onayı, resmî PDF orijin teyidi, yürürlük/aşama onayı veya imza değildir.
- `HUKUKI_HOLD` ve `UNREVIEWED` LegalAST/RuleEngine sabit kalır; React/Windows tam uygulama bu işlemde iddia edilmez.
- Sentetik GitHub-hosted CI gerçek müşteri Windows sistemi, yıllara yayılan Resmî Gazete/ek tablosu ve gerçek insan incelemesi değildir.

## 3. GitHub'da gerçekten geliştirilen dosyalar

**Zorunlu ilk GitHub yazımı:** `docs/islem_016.md` oluşturma commit'i **`bf02e1871374dbc76768e4d8ba61484392d4b446`**. Diğer işlem 016 kodları/şartname bundan **sonra** oluşturuldu; 001–015 önceki işlem kayıtları yeniden numaralandırılmadı.

| Dosya | Gerçek uygulama | Commit |
| --- | --- | --- |
| `src/mimarllm/legal/review.py` | Kaynak kimlikli NODE/TABLE_CELL/CHANGE_MENTION/AMENDMENT_SIDE `ReviewSelection`, `ReviewTask`, `ReviewQueue` ve kaynak metin/poligon `task_digest`, kullanıcı beyanı `ReviewDecision` | `df2b1775` |
| `src/mimarllm/legal/review_viewer.py` | Yerel pypdfium2 / `render_region` sayfa bitmap + PDF üst-sol source polygon sarı SVG + offline HTML; JavaScript seçim/JSON taslak export; sahte metin/quad/hash ret | `ee0032a7` |
| `src/mimarllm/legal/review_ledger.py` | Tarayıcı JSON taslak import, orijinal kaynak task digest'e karşı validasyon ve yerel tek yazıcı SHA-chain JSONL geçmişi | `41684776` |
| `src/mimarllm/legal/version_workflow.py` | Asıl madde ve ilgili değişiklik beyanları için **iki farklı orijinal PDF** kaynaklı tarihsel kıyas paketi; `assess_version_chain` gerekçelerini koruma | `35ee7ecc` |
| `tests/test_legal_review.py` | Gerçek sentetik PDF SHA/source quad, SVG sarı highlight, OCR/native hücre, çok satırlı fıkra, XSS escaping, değişmiş dosya, bozuk kaynak, sürüm tarihi, ledger tamper ve kullanıcı JSON doğrulama | `0770d45d`, `79aad1eb` |
| `.github/workflows/core-contracts.yml` | `tests/test_legal_review.py` Ubuntu+Windows CI test matrisine eklendi | `780e701d` |
| `src/mimarllm/legal/review_viewer.py` | Eksik amendment-claim'i açık `VisualReviewError`; tarihsel \`claimed_effective_from\` görünür; `VersionReview.issues` (geç/farklı sürüm, çoklu ilişki) HTML uyarıları | `eeda5baa`, `a741887c` |
| `tests/test_legal_review.py` | Tarihsel uyarı kodlarının gerçek iki-PDF HTML içinde görünürlüğü | `38808285` |
| `docs/specs/legal-review-v0.1.md` | API, sınırlar, offline HTML, kullanıcı kararı JSONL ve tarihsel uyarılar | `f8e992c5`, `24e50c67` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F15 ve F18'in yalnız mevzuat PDF alt modülü için **kısmi** statüsü, K-120–K-127 kararları | `775c4a6f`, `c3937ca4`, `24c78b89`, `3726a990` |

## 4. CI ve gerçek test kaydı

- İlk CI [38472884993](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38472884993): Eksik değişiklik beyanı verilince beklenen özel `VisualReviewError` yerine genel `ReviewInputError` dönüyordu; sentetik test başarısız. Hata tipi düzeltilerek değişiklik kaydı eksikliği açık ret oldu.
- [38473010905](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38473010905): Ubuntu `230 PASS / 1 SKIP` ve Windows successful. SKIP olan çok satırlı fıkra testi, gerçekten ikinci kaynak span oluşturacak sentetik PDF fixture'ıyla değiştirildi.
- [38473139580](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38473139580): Ubuntu/Windows `231 PASS`, `0 SKIP`. Çoklu source span için her original polygon ayrı vurgulanabiliyor.
- **Son kod commit `38808285e28cd534fc9385e5829e10f7ee84c27a`:** [GitHub Actions 38473566992](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38473566992). **Ubuntu Python 3.11: 231/231 PASS (4,79 s); GitHub-hosted Windows Python 3.11: 231/231 PASS (9,69 s).** Her iki CI job logu ayrı incelendi. Son ek: `VersionReview.issues[]` görsel HTML'de ayrı belirsizlik alanı olarak gösterilir.
- Testler ReportLab ile **sentetik PDF oluşturup gerçekten PDFium bitmap render** ediyor, LegalAST kaynak koordinatlarını SVG HTML'de doğruluyor, ayrıca tarayıcıya aktarılan JSON taslağının kaynak task digest denetimini ve SHA-chain read-back'i test ediyor. Gerçek RG/hukukî onay/gerçek Windows kullanıcı bilgisayarında UI açma ve insan görsel kabulü **yapılmadı**.

## 5. Özellik, güvenlik ve hukukî kabul sınırları

**Gerçek kodlanan:** Native PDF metin/tablo hücresinin ve amendment claim'inin kaynak SHA/page/quad ile seçilip gerçek PDF sayfasına sarı poligonla vurgulanması; source PDF değişirse HTML export HOLD; offline tarayıcıda manuel görsel karar ve JSON draft; belirsizlik nedenleriyle base-amendment tarihsel iki-kaynak kıyası; kaynak task digest/JSONL geçmişi ve basit değişiklik tespiti.

**Mevcut olmayan:** Yıllara göre bütün Resmî Gazete dokümanlarını toplamak, resmî yayımlanma orijinini bağımsız doğrulamak, yürürlükteki konsolide hukukî normu çıkartmak, gerçek e-imzalı ve yetkili hukukçu audit, tüm mimari çizim bulgularının görsel işaretlenmesi, canlı React/Windows masaüstü UI, gerçek müşteri ve gerçek mevzuat kaynaklarıyla kabul.

**Hukukî durum:** `LegalAST.review_status=UNREVIEWED` ve `RuleEngine.REGULATORY=INSUFFICIENT_EVIDENCE` kilidi korunur. `VISUALLY_MATCHED` yalnız kullanıcının gördüğü metin/konum hakkında **imzasız beyanı**dır, `APPROVED_FOR_CHECK` veya hukuken yürürlük ve resmî kaynak ispatı değildir. SHA-chain **haricen imzalanmadıkça** tüm geçmişin kasıtlı yeniden yazımını ispatlamaz.

**F15 / F18 yalnız KISMI (mevzuat PDF alt kapsamı), F08–F12 HUKUKI_HOLD.** Sonraki sıra: özgün hukukî kaynak ve tarihsel norm inceleme eksiklerinin resmî belge/uzman kabul akışı; ardından genel mimari analiz raporları, çizimde çift yönlü kanıt vurgulama ve Windows UI paketleme. Bir sonraki kodlamada önce `docs/islem_017.md` oluşturulmalıdır; bu dosya henüz yoktur.

