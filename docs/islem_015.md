# İşlem 015 — Mevzuat kaynak doğrulama, sürüm ilişkisi ve RuleEngine kanıt bağlayıcısı

- **Tarih:** 2026-10-13
- **Durum:** ÖN KAYIT. İşlem 015'in **ilk GitHub yazımıdır**; uygulama kodundan ve diğer belge değişikliklerinden önce açıldı.
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

## 3. Gerçekleştirilen commit ve CI sonuçları

Bu bölüm kaynak modülleri ve sentetik testler kodlandıktan sonra gerçek commit SHA / CI run ID / Linux-Windows PASS-FAIL / açık risklerle doldurulacaktır.
