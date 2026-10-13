# İşlem 016 — Özgün mevzuat PDF görsel kanıt incelemesi ve tarihsel sürüm inceleme iş akışı

- **Tarih:** 2026-10-14
- **Durum:** ÖN KAYIT — İşlem 016 kapsamındaki **ilk GitHub yazımı**, kod değişikliğinden önce.
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

## 3. Gerçek commit/CI sonuçları

Kod/test tamamlandıkça buraya gerçek commit, CI run, başarısız deneyler, PASS/FAIL ve açık eksikler kaydedilecek.
