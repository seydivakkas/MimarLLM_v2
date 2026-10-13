# İşlem 015 — Kanıt Bağlayıcı v0.1: PDF Kaynak, Değişiklik, Proje, RuleEngine

- **Kod:** `src/mimarllm/legal/verification.py`, `legal/versions.py`, `legal/applicability.py`, `src/mimarllm/rules/evidence.py`
- **Kayıt:** [islem_015.md](../islem_015.md)
- **Durum:** Sentetik orijinal PDF ve LegalAST karşılaştırması; gerçek Resmî Gazete ve hukukî geçerlilik **HUKUKI_HOLD**. Henüz hiç `APPROVED_FOR_CHECK` üretilmez.

## 1. Tasarım kuralı

Bir mevzuat sorusu üç ayrı kaynak arasında bağlanır: (a) RuleDefinition'ın belirtilmiş `LegalSourceLocator`'ı; (b) orijinal PDF'nin hash'iyle oluşturulmuş LegalAST içindeki *tam* `node_id` ve orijinal PDF sayfası/poligonu; (c) varsa RAG hit'i. RAG seçilen metnin/node ID'nin bulunduğunu gösterebilir, ama **doğruluk veya resmî geçerlik puanı değildir**.

Arama adayından `COMPLIANT` üretmek yasaktır. `RuleEngine` içindeki `RuleDomain.REGULATORY` kilidi **korundu**, `RuleResult.legal_compliance_certified=True` hâlâ geçersizdir. `evaluate_regulatory_with_evidence` iki ayrı sonucu birlikte verir: `RuleEvidenceBinding` ile **neden inceleme/HOLD gerektiği**, `RuleResult` ile motorun değişmeyen `INSUFFICIENT_EVIDENCE` sonucu.

## 2. Yerel PDF doğrulaması

`verify_local_pdf(legal_document, local_pdf_path)` şu gerçek teknik kontrolleri yapar: yeniden Pydantic LegalAST validasyonu; yerel PDF başlığı ve byte budget; dosyanın SHA256'sını `LegalDocument.document_sha256` ile karşılaştırma; PDFium sayfa sayısı, her native/OCR/bbox kaynak polygonunun özgün PDF sayfa boyutları içinde olması; işlem sonunda SHA tekrar kontrolü.

`SourceAudit.status`: `LOCAL_SOURCE_MATCHED`, `ORIGINAL_PDF_MISSING`, `ORIGINAL_PDF_MISMATCH`, `PAGE_GEOMETRY_MISMATCH`, `INVALID_SOURCE`. Her durumda `officiality=OFFICIAL_PUBLICATION_NOT_VERIFIED` ve `legal_compliance_certified=False`. `LOCAL_SOURCE_MATCHED` **yalnız aynı yerel byte dizisi ve sayfa koordinatları** demektir; belgenin T.C. Resmî Gazete'nin o tarihteki resmî yayımı olduğunun kanıtı değildir. Kullanıcının bildirdiği URL'ye HTTP isteği yapılmaz, dijital imza/uzman onayı kontrol edilmez.

## 3. Sürüm ve değişiklik bağı (konsolidasyon değil)

`AmendmentClaim` bir beyan olarak: `target_document_sha256`, `target_node_id`, `amending_document_sha256`, `amending_node_id`, `source_span`, `relation=REPLACES/REPEALS/ADDS_EXCEPTION/TRANSITION`, `claimed_effective_from/until`, `reviewer_id`, `reason`. Bu değerlerin **hiçbiri tek başına resmî yürürlük belgesi değildir**.

`assess_version_chain` tam kaynak hedef node'u ve değişiklik node'unu, amending PDF ile node source span'ının eşleşmesini, tarih sırasını, tek tarihte birden çok konsolide edilmemiş ilişkiyi, eksik kaynakları kontrol eder. Çıktı `VersionReview.status` yalnız `INSUFFICIENT_EVIDENCE` veya `REVIEW_REQUIRED`; `consolidated_text=None`, `legal_effect_certified=False`.

`bind_regulatory_evidence`, ilgili amending PDF dosyalarının da SHA/page koordinatını `amendment_pdf_paths` üzerinden ayrıca doğrular. Eksik amending özgün PDF `HOLD_AMENDMENT_CHAIN` üretir. Bir değişiklik PDF'sindeki `MADDE 1`, ana yönetmeliğin `MADDE 1`i sayılmaz; açık `target_node_id` zorunludur. Bu sürüm yürürlükteki konsolide normu hesaplamaz.

## 4. Proje uygulanabilirliği

`ProjectLegalContext`: çizim `SHA256`, il/ilçe/belediye, kullanım/yapı sınıfı, ruhsat/başvuru tarihi, değerlendirme tarihi, istisna kayıtları ve reviewer. `assess_project_context` bunların eksikliğini ve iddia edilmiş istisnanın inceleme gerektirdiğini gösterir.

- Eksik kritik alan: `INSUFFICIENT_EVIDENCE`, liste halinde `unknown_fields`.
- İddia edilmiş istisna: `REVIEW_REQUIRED`, kaynak ID ve reviewer beyanı gereklidir.
- Dolu kullanıcı formu: **hukukî uygulanabilirlik onayı değildir**; bağımsız inceleme HOLD.
- Wrapper girişinde `ProjectLegalContext.drawing_sha256` ile gerçek `RuleRequest.drawing.source_sha256` eşleşmek zorundadır; bir mimari projenin hukuki bağlamı diğer çizimde kullanılamaz.
- `effective_from` ve `effective_until` gibi tarihleri aşan proje beyanı `PROJECT_DATE_BEFORE_ASSERTED_RULE_START` / `PROJECT_DATE_AFTER_ASSERTED_RULE_END` uyarısı verir ama bu tarihler henüz resmî olarak teyit edilmemiştir.

## 5. Kural–LegalAST–RAG eşleşme API

```python
from mimarllm.rules.evidence import (
    bind_regulatory_evidence, evaluate_regulatory_with_evidence,
)

binding = bind_regulatory_evidence(
    regulatory_rule, legal_documents,
    source_node_id="exact-LegalAST-node-id",
    local_pdf_path="local_data/regulations_raw/verified-local-copy.pdf",
    project=project_context,
    amendment_claims=human_asserted_claims,
    amendment_pdf_paths={amendment_pdf_sha: "local_data/amendment.pdf"},
    rag_hit=matching_retrieval_hit,  # İSTEĞE BAĞLI; HİÇBİR GÜVEN KAPISINI AÇMAZ
)
print(binding.status, binding.original_spans, binding.reason_codes)

wrapped = evaluate_regulatory_with_evidence(
    rule_engine, regulatory_rule, rule_request, legal_documents,
    source_node_id="exact-LegalAST-node-id",
    local_pdf_path="local_data/regulations_raw/verified-local-copy.pdf",
    project=project_context,
)
# wrapped.rule_result.status == INSUFFICIENT_EVIDENCE
# wrapped.binding.approval_status == HUKUKI_HOLD
```

Exact bağlayıcı `rule.legal_source.document_sha256`, `regulation_id`, `article_id`, `clause_id`, `page_index` ile gerçek LegalAST node ancestry'sini karşılaştırır. Başka sayfa/madde/fıkra, var olmayan PDF SHA veya yanlış değişiklik konsolidasyonu kabul etmez.

`rag_hit` verilirse `passage.node_id`, `document_sha256`, `regulation_id`, `text`, `node_kind` ve **orijinal `spans` eşitliği** zorunludur. Sayı olarak RRF skoru yalnız tanı amaçlı saklanır; eşiğin üstünde diye bir bağlayıcı başarılı sayılmaz. Sadece tablo hücresini metin düğümüymüş gibi kullanma reddedilir.

`BindingStatus`: `HOLD_LEGAL_NODE`, `HOLD_RAG_CANDIDATE`, `HOLD_ORIGINAL_SOURCE`, `HOLD_AMENDMENT_CHAIN`, `HOLD_PROJECT_CONTEXT`, `HOLD_OFFICIALITY_AND_INDEPENDENT_REVIEW`. **`APPROVED_FOR_CHECK` yoktur.**

## 6. Tamamlanmamış hukukî kabul

1. Resmî Gazete yetkili kaynak URL/dijital imza/orijin/ham PDF doğrulaması, bütün değişikliklerin resmî metinle eşleştirilmesi.
2. Ruhsat tarihi/uygulama türü için geçici maddeler, yerel plan notları, belde/ilçe/yapı sınıfı, istisna ve birbiriyle çatışan hükümler.
3. Gerçek çok yıllı mevzuat külliyatı ve hem orijinal hem amendment PDF hücrelerinin bağımsız görsel onayı.
4. Hukukçu/alan uzmanı audit trail, izin/yetki sistemi, source-level imzalı `APPROVED_FOR_CHECK` kapısı.
5. Gerçek Windows i7/RTX4070 ve gerçek mevzuat/MimarLLM proje kabulü.

Bu modül yalnız **kanıt ilişkilerini denetleyip hangi kapının açık olduğunu göstermek** içindir. Hukukî uzman değerlendirmesi veya yasal görüş üretmez. F15 `KISMI/MEVCUT_KOD`; F08–F12 `HUKUKI_HOLD`.