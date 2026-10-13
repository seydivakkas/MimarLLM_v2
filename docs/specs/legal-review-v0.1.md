# Görsel Mevzuat Kanıt İncelemesi v0.1 — Özgün PDF, Sarı Vurgu ve Sürüm Karşılaştırma

**İşlem:** [islem_016.md](../islem_016.md). **Durum:** Kodlandı; sentetik Linux/Windows CI. Hukukî `APPROVED_FOR_CHECK` ve gerçek kaynak onayı **HOLD**.

## 1. Gerçek işlev ve ürün sınırı

Bu bileşen, İşlem 013 `LegalAST` çıktısının içinde seçilen kaynak madde/fıkra, tablo hücresi veya değişiklik metnini **orijinal yerel PDF sayfası üzerinde** göstermeye yarar. `pypdfium2` ile render edilen sayfa PNG görüntüsü ve PDF üst-sol koordinatındaki `LegalSourceSpan.polygon` alanı SVG ile sarı çizilir. PDF sayfası indeksinin **0 tabanlı** olduğu her kartta yazılır. Bu bir PDF okuma/inceleme raporudur, tam Windows masaüstü uygulaması değildir.

`ReviewTask` yalnız `LegalDocument`'ın gerçekten içerdiği `node_id + span_index`, `table_id + row/column`, `LegalChangeCandidate.candidate_id` veya `AmendmentClaim.claim_id + AMENDING/TARGET` seçiminden oluşturulur. Gelen task'ın metni veya polygonu orijinal LegalAST ile tekrar hesaplandığında eşleşmiyorsa HTML oluşturulmaz. Her task: `task_id`, PDF SHA, metin, kaynak quad, OCR/native türü, varsa beyan edilen amendment başlangıç tarihi, gerekçeli `HUKUKI_HOLD` durumu.

## 2. Offline HTML inceleme akışı

```python
from mimarllm.legal.review import (
    ReviewSelection, TargetKind, build_review_queue,
)
from mimarllm.legal.review_viewer import create_visual_review_html

queue = build_review_queue(
    [legal_document],
    [ReviewSelection(
        document_sha256=legal_document.document_sha256,
        kind=TargetKind.NODE,
        reference_id=selected_legal_node.node_id,
        span_index=0,
    )],
)
html_path = create_visual_review_html(
    queue,
    [legal_document],
    {legal_document.document_sha256: "C:/mevzuat/orijinal.pdf"},
    "C:/mevzuat/inceleme.html",
)
# Tarayıcıda yerel inceleme.html dosyasını açın.
```

HTML içinde görsel kaynak, **SVG sarı vurgulu polygon**, kaynak metin ve `VISUALLY_MATCHED` / `CORRECTION_REQUIRED` / `UNREVIEWED` seçimi vardır. Kullanıcı etiketi ve gerekçeli not istenir; tıklamayla tarayıcıda **taslak JSON** dışa aktarılır. Bu JSON hiçbir sunucuya gönderilmez; bağımsız dijital imza veya incelemeci kimlik yetkilendirmesi değildir. Şüpheli HTML/kaynak metni `html.escape` ile metne çevrilir, `<script>` olarak çalıştırılmaz.

**Kaynak kontrolleri:** özgün PDF SHA256, PDF sayfa sayısı ve LegalAST satır/hücre poligonlarının sınırları `verify_local_pdf` ile denetlenir. Ardından sayfa `render_region` ile bounded DPI/piksel bütçesinde görüntülenir; yeniden SHA denetimi yapılır. Kaynak uyuşmuyorsa, sayfa dışı/boş dörtgen varsa veya render yönlendirmesi güvenilir değilse **görsel rapor üretilmez**. `render_region` standart olmayan CropBox eşleşmelerini reddeder; kullanıcı kaynak koordinatları görselde yanlış konuma kaydırılmaz. Sayfa düzeyinde `viewBox` orijinal PDF point boyutlarını kullanır ve ekrana ölçeklenirken SVG polygon görüntüyle aynı oranda büyür.

**Sınırlar:** SVG polygon kaynağın anotasyon alanını gösterir, dönmüş glifin piksel düzeyindeki bütün şeklini veya tablonun semantik doğruluğunu ispatlamaz. `max 24` görsel task, `72..200 DPI`, varsayılan 6 milyon piksel/sayfa, HTML boyutu en çok 24 MiB. Çok sayfalı/çok büyük külliyatta sayfa cache/akıllı parça yükleme ve canlı PDF gezgini daha sonra geliştirilecektir.

## 3. Tarihsel sürüm karşılaştırması

```python
from datetime import date
from mimarllm.legal.version_workflow import create_version_review_packet

packet = create_version_review_packet(
    [original_ast, amendment_ast],
    [manual_amendment_claim],
    target_document_sha256=original_ast.document_sha256,
    target_node_id=original_node.node_id,
    as_of=date(2026, 5, 1),
)
html = create_visual_review_html(
    packet.review_queue,
    [original_ast, amendment_ast],
    {
        original_ast.document_sha256: "C:/mevzuat/asli.pdf",
        amendment_ast.document_sha256: "C:/mevzuat/degisiklik.pdf",
    },
    "C:/mevzuat/tarihsel_inceleme.html",
    amendment_claims=[manual_amendment_claim],
    version_review=packet.chain_assessment,
)
```

`VersionReviewPacket`: orijinal hedef ve her ilgili değişiklik belgesi **ayrı kaynak PDF** olarak görsel görev listesinde yer alır. `assess_version_chain` sonucu `chain_assessment.issues` alanında saklanır; gelecekteki beyan tarihlerinin önceki ruhsata uygulanması otomatik yapılmaz. Aynı `MADDE 1` numarası farklı PDF'leri birleştirme yetkisi değildir. `claimed_effective_from` **yalnız beyan** olarak ekranda görünür. Bu aşamada gerçek konsolide norm metni, değişiklik süresi veya hukukî istisna onayı **üretilmez**.

## 4. JSON içe alma, kaynak doğrulama ve ledger

```python
from mimarllm.legal.review_ledger import (
    import_exported_review_json, append_review_decisions, read_review_ledger,
)

decisions = import_exported_review_json("C:/mevzuat/mimarllm_gorsel_inceleme_taslak.json")
appended = append_review_decisions(
    "C:/mevzuat/inceleme_gecmisi.jsonl",
    queue,
    decisions,
)
history = read_review_ledger("C:/mevzuat/inceleme_gecmisi.jsonl")
```

İçe alma, her kararın `task_id` ve `task_digest` değerini **seçilen LegalAST kaynak metni/poligonu** ile tekrar kontrol eder. Değiştirilen metin/polygon için eski karar kullanılamaz. Her kayıt `sequence + previous_sha256 + decision + record_sha256` zinciriyle append-only JSONL dosyasına yazılır; eski zincir okunurken doğrulanır.

**Önemli:** Yerel hash zinciri dış bir kurumda/sistemde anchoring olmadan dosyanın tümden yeniden yazılmasını yakalayamaz. Tek yazıcı varsayımı vardır; kilitleme/dijital imza/kimlik yetkilendirmesi yoktur. `VISUALLY_MATCHED` yalnız insanın gösterilen metni ve poligonu gördüğüne dair **imzasız beyanıdır**. Hukukî kaynak resmiyeti, yürürlük/geçiş/istisna, ruhsatın tabi olduğu mevzuat ve bağımsız uzman incelemesi ayrıca gereklidir.

## 5. Kesin sınır ve sonraki paket

**Bu işte kodlandı:** PDF bitmap + SVG sayfa polygon, tek sayfa OCR/native metin/madde/fıkra/tablo hücresi ve değişiklik PDF karşılaştırma kuyruğu; kullanıcı gözlemi JSON export/import; hash bağlantılı yerel inceleme tarihi.

**Kodlanmadı / HOLD:** Resmî Gazete'nin tarihsel bütün değişikliklerinin doğrulanması, kaynak kurumun kriptografik resmiyet kontrolü, gerçek hukukî norm konsolidasyonu, elektronik imzalı onay, canlı PDF gezgini, gerçek müşteri Windows kabulü, RuleEngine REGULATORY COMPLIANT/NON_COMPLIANT. F15'in görsel kaynak gözden geçirmesi **kısmi olarak ilerledi**, F18'in rapor/PDF işaretleme hedefinin yalnız **mevzuat özelindeki alt parçası** bu aşamada kodlandı. F08–F12 `HUKUKI_HOLD` korunur.


**VersionReview HTML görünürlüğü:** `create_visual_review_html(..., version_review=packet.chain_assessment)` parametresi verildiğinde hedef kaynak PDF SHA/düğümüyle eşleşen `VersionReview.issues[]` gerekçe kodları ve açıklamaları offline HTML içinde ayrı **Tarihsel sürüm inceleme uyarıları** bölümünde gösterilir. Bu ifadeler yalnız kaynaklı inceleme uyarılarıdır; yürürlükte hangi normun uygulanacağını onaylamaz.
