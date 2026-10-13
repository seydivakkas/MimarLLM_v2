# İşlem 015 — Mevzuat kaynak doğrulama, sürüm ilişkisi ve RuleEngine kanıt bağlayıcısı

- **Tarih:** 2026-10-13
- **Durum:** UYGULANDI — kaynak/versiyon/proje ve RuleEngine kanıt bağlayıcısı; Linux+Windows sentetik CI 215/215 PASS. Resmî PDF kaynağı, yürürlükte konsolide hüküm, bağımsız hukukî onay ve kullanıcı Windows saha kabulü HOLD.
- **Önceki kayıtlar:** islem_001–014 tarihçesi olduğu gibi korunur.
- **Kapsam:** F15 kural-kaynak bağlayıcısı; F13 LegalAST ve F14 RAG ile işlem 012 RuleEngine arasındaki **hukukî doğrulama kapısının hazırlığı**. F08–F12 **HUKUKI_HOLD** kalır.

## 1. Geliştirme hedefleri

1. `src/mimarllm/legal/verification.py`: özgün PDF'ye yerel SHA256 eşleştirme, sayfa/kaynak koordinat kontrolü, `LegalAST` kaynak kimliği ve kullanıcı tarafından belirtilen resmî kaynak/inceleme kaydının **doğrulanmış yetkili yayım yerine geçmediğini** açıkça bildirme. Yalnız format ve dosya geometrisi doğrulaması güvenilir teknik sonuçtur.
2. `src/mimarllm/legal/versions.py`: değişiklik, ilga, yürürlük ve istisna ilişkilerini kaynak PDF/node ID, etkilenen hedef hüküm, değişiklik türü, başlama/bitme tarihiyle bağlayan **açık inceleme beyanı sözleşmesi**. İlişkiyi yalnız metin regex'i veya arama sonucundan kurma yok. Çatışan ve boş zincirlerde `REVIEW_REQUIRED/INSUFFICIENT_EVIDENCE`; `APPROVED_FOR_CHECK` yok.
3. `src/mimarllm/legal/applicability.py`: proje konumu, başvuru/ruhsat tarihi, kullanım sınıfı ve gerekli istisnalar hakkında alanları bilinen/eksik olarak ifade eden `ProjectLegalContext`, `ApplicabilityReview`. Eksik tarih veya kapsamdan otomatik `NOT_APPLICABLE` kararı çıkmaz.
4. `src/mimarllm/rules/evidence.py`: `RuleDefinition.legal_source` ile `LegalDocument` gerçek AST düğümü ve isteğe bağlı `RagHit` referansını **ayrı kaynak** olarak çapraz kontrol eden, kaynak düğümü sayfası/poligonu, PDF hash'i, doğrulanmamış resmiyet, değişiklik ilişki listesi ve proje bağlamı için açık gerekçe döndüren bağlayıcı.
5. `RuleEngine` entegrasyonu: Kuralı değerlendirmek için kaynakların varlığına dair `RegulatoryEvidencePacket` gönderilebilecek; **hiçbir kullanıcı bayrağı, metadata, yerel PDF veya yüksek RRF puanı REGULATORY COMPLIANT/NON_COMPLIANT/NOT_APPLICABLE sonucunu açmayacak**. Kural şemasının ve `RuleResult` yasağının değişmemesi tercih edilir.
6. `tests/test_legal_binding.py`: çok belgeli gerçek sentetik PDF→LegalAST→FTS5→source binder, yanlış SHA, bozuk PDF, sahte hit, sayfa/başka fıkra, değişiklik hedefi, yürürlük çatışması, eksik ruhsat tarihi, istisna, sınır ve hukukî HOLD. Ubuntu+Windows GitHub CI.
7. `docs/specs/legal-binding-v0.1.md`, README, özellik envanteri, karar defteri ve yol haritası güncellenecek.

## 2. Güvenlik / bilimsel kabul

- Belge hash'i aynı olsa bile dosyanın gerçekten Resmî Gazete sunucusundan alınmış olduğunu kanıtlamak mümkün değildir; ağ doğrulaması, imza veya yetkili arşiv onayı yok. `source_url` ve `reviewer_id` kullanıcının beyanıdır; tek başına hukukî doğrulama değil.
- Tarihsel `effective_from` ve yürürlük değişiklik grafının tarihleri **giriş/inceleme adayıdır**. Bu sürümde hukuken yürürlükte metin üretilemez; değişiklik belgesinin kendi MADDE numarası hedef yönetmelikteki MADDE numarası değildir.
- Arama eşleşmesi, OCR confidence, FTS score, dense cosine veya RRF score, hüküm bağlayıcısına geçiş yetkisi vermez.
- `LegalDocument.review_status` her zaman `UNREVIEWED`; `RuleEngine` mevzuat kilidi değişmez.
- Gerçek Resmî Gazete yıllık dosyalarının otomatik çekilmesi, bütün kanunların konsolidasyonu, hukukî uzman incelemesi ve gerçek müşteri Windows kabulü **bu işlemde yapılamadı sayılacak; fiilî sonuçlar sonunda güncellenecek**.

## 3. GitHub kod değişiklikleri ve commit zinciri

**İlk GitHub yazımı:** `docs/islem_015.md`, commit **`3c90cde2dfd2391930336bd9a5ebf6f545247f7b`**. İşlem 015 kodları ve diğer belgeler **bundan sonra** oluşturuldu; önceki `islem_001–014` dosyaları değiştirilmedi.

| Dosya | Gerçek uygulama | Commit |
| --- | --- | --- |
| `src/mimarllm/legal/verification.py` | `SourceAudit`, yerel orijinal PDF SHA256 + PDFium sayfa sayısı, LegalAST tüm native/OCR/tablo/değişiklik span polygonu bounds, ikinci hash kontrolü; resmî orijin garanti edilmez | `4028cd58` |
| `src/mimarllm/legal/versions.py` | `AmendmentClaim`, hedef/amending PDF ayrı kimliği, node/span eşleştirme, tarih aralığı ve çoklu değişiklik uyarıları; resmî konsolidasyon **yok** | `0f509baa` |
| `src/mimarllm/legal/applicability.py` | `ProjectLegalContext`, konum/ruhsat/kullanım/yapı/istisna alanları, bilinmeyen ve incelenmesi gereken veriler | `12837563` |
| `src/mimarllm/rules/evidence.py` | `RuleDefinition.legal_source` → exact LegalAST node/ancestry/span; RAG node-text-polygon eşitliği; local source/version/applicability `HOLD` değerlendirmesi; `RuleEngine` birlikte sonuç wrapper | `9faf85a9` |
| `src/mimarllm/rules/evidence.py` | İlgili tüm amending özgün PDF'lerinin hash/page koordinat kontrolü; eksik veya değiştirilmiş amendment `HOLD_AMENDMENT_CHAIN`; `ProjectLegalContext.drawing_sha256` ile gerçek RuleRequest DrawingIR SHA eşleştirme | `09c43f88`, `02951fbd` |
| `tests/test_legal_binding.py` | ReportLab sentetik farklı ORIGINAL/AMENDMENT PDF'ler, LegalAST, SQLite/RAG, ters düşen madde/sayfa, sahte hit, istisna, tarih, PDF hash/quad, amending PDF eksik/değiştirilmiş, RuleEngine HOLD, proje SHA | `5a524f3a`, `78fb2e32`, `5355c437` |
| `.github/workflows/core-contracts.yml` | `tests/test_legal_binding.py` Ubuntu/Windows Python 3.11 matrise eklendi | `17556413` |
| `docs/specs/legal-binding-v0.1.md` | Gerçek API, kaynak/versiyon/proje inceleme kapıları ve hukukî kilitler | `796606c8` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F15 kısmi gerçek kod, F08–F12 HUKUKI_HOLD, K-111–K-119 kararları, tarihsel yol haritası | `75b7e1b5`, `5f141a32`, `b162ca3e`, `8a206224` |

## 4. Linux/Windows CI ve regresyon kaydı

- İlk kaynak/hüküm/RAG/RuleEngine kanıtı [CI **38425455517**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38425455517): **Ubuntu 213 PASS, Windows 213 PASS**. Testler sentetik PDF'leri gerçekten üretip yeniden okudu; gerçek Resmî Gazete belgeleri kullanılmadı.
- Amendment PDF source hash şartı eklendiğinde henüz testin eski `HOLD_OFFICIALITY` beklentisini kullandığı ara kaynak commit [CI **38425738263**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38425738263) başarısızdı. Eksik değişiklik PDF'sinin `HOLD_AMENDMENT_CHAIN` sayılması davranışı açık testlerle belirtildi.
- DrawingIR kaynak SHA eşleştirmesi eklendiğinde [CI **38425843760**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38425843760): **214 PASS/1 FAIL** her OS; eski sentetik fixture başka drawing SHA'lı proje bağlamı kullanıyordu, yeni güven kapısı bunu reddetti. Test biri uyumsuz, diğeri uyumlu proje SHA için ayrı doğrulama olarak düzeltildi.
- **Son kod commit `5355c437e117f2fcf452ea7ededac5a446264393`: [GitHub Actions 38425898142](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38425898142). Ubuntu Python 3.11: **215/215 PASS (4,44 saniye)**; GitHub-hosted Windows Python 3.11: **215/215 PASS (14,26 saniye)**. Her iki işin job logları ayrı ayrı kontrol edildi.

## 5. Kabul durumu ve bağımsız doğrulama gereksinimleri

**Uygulandı:** Orijinal yerel PDF hash + sayfa/sınır koordinatı, exact LegalAST article/paragraph/ITEM kanıtı, arama sonucunun kaynak düğüme geri bağlanması, kullanıcıca açıkça beyan edilmiş amendment source/target ilişkisinin fiziksel amending PDF'si ve proje kimliğine göre tutarlılık denetimi; gerekçeli `HOLD` çıktısı. Bütün hâlâ `UNREVIEWED`; hiçbir `APPROVED_FOR_CHECK` durumu yok.

**HOLD:** Resmî Gazete orijin/yayın imzası, yetkili arşivdeki asıl belge ile bağımsız kontrol; her tarihte gerçekte yürürlükte olan maddelerin konsolidasyonu (değişiklik, ilga, geçici hükümler, istisnalar); yerel idarenin plan notu ve proje sınıfı uygulama kararı; gerçek yetkili hukukî/mimarî inceleme ve audit imzası; gerçek kullanıcı Windows/RTX 4070 gerçek proje testi yapılmadı. `reviewer_id` bir beyan, imza/yetki doğrulaması değil.

**Sınır:** RuleEngine `RuleDomain.REGULATORY` sonuçları **daima `INSUFFICIENT_EVIDENCE`**. `F15 KISMI/MEVCUT_KOD + SENTETIK_LINUX_WINDOWS_CI_PASS`; F08–F12 `HUKUKI_HOLD`. İlgili hüküm bir RAG hit'inin sıralamada ilk olması, orijinal kaynağın onaylandığı veya hukuken uygulanabilir olduğu anlamına gelmez.

## 6. Sonraki paket

**İşlem 016 ön kaydı henüz oluşturulmadı.** Sırada, resmî kaynak doğrulama ve tarihsel norm konsolidasyonu için görsel PDF incelemesi, açık değişiklik/istisna ilişkilerinin inceleme iş akışı ve doğrulanabilir hukukî kaynak sürüm envanteri ayrı geliştirme olarak ele alınmalı. Kaynak-onaylı normlar sağlanmadan PAİY/BYKHY/otopark/sığınak/BEP için gerçek eşik veya uygunluk kararı etkinleştirilmemeli.
