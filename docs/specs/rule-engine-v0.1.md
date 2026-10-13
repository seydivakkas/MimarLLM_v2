# RuleEngine v0.1 — Deterministik Teknik Kanıt ve Hukukî Karar Kilidi

- **İşlem kaydı:** [islem_012.md](../islem_012.md)
- **Kod:** `src/mimarllm/rules/base.py`, `engine.py`
- **Kaynak altyapı:** DrawingIR/UnitCalibration (007), native DXF/PDF (008–009), Shapely yüzey alanı (010), incelenmiş NetworkX geçiş topolojisi (011).
- **Kesin sınır:** v0.1 bir **hukukî uyum doğrulayıcısı değil**, sentetik/senaryo tabanlı teknik gözlem ve kanıt doğrulama motorudur. Resmî mevzuat PDF/LegalAST/version/applicability onay hattı islem_013–015 aşamalarında geliştirilmeden bütün `REGULATORY` kuralları kilitlidir.

## 1. Altı ayrı sonuç durumu

| Durum | Tanım | Teknik motorun davranışı |
| --- | --- | --- |
| `COMPLIANT` | Teknik/sentetik karşılaştırmanın veriye göre olumlu sonucu | Kaynak entity + hesaplanmış metrik + kanıt ID olmadan oluşturulamaz; hukukî onay DEĞİL |
| `NON_COMPLIANT` | Teknik/sentetik karşılaştırmada eşik sağlanmıyor | Fiziksel ölçüm yeniden kaynak geometriye bağlanır; yönetmeliğe aykırılık DEĞİL |
| `INSUFFICIENT_EVIDENCE` | Doğrulanmış fiziksel ölçek/ölçüm/topoloji/yasal kaynak eksik | **Bütün `REGULATORY` kuralları** islem_012'de bu durumda kalır |
| `REVIEW_REQUIRED` | Çelişkili metrik, onaysız sınır, hatalı geometrik konum/kanıt | Kesin eşik/yapı kararı çıkmaz |
| `NOT_APPLICABLE` | Yalnız **teknik** senaryo için açık scope exclusion | Kimliği yazılı reviewer, neden, dosya SHA ve gerçek entity ID gerekir; kullanıcı beyanı otorite incelemesi değildir |
| `ERROR` | Geçersiz model/hesaplama, güvenli çalıştırma hatası | Varsayılan PASS yok; exception detaylarından gizli veri rapora konmaz |

**Not:** `FindingStatus.PASS/FAIL` eski `DrawingIR` gözlem sözleşmesidir. Bu işlem `DrawingIR.findings` listesine hukukî `PASS` yazmaz; ayrı `RuleResult` üretilir.

## 2. Kural tanımlama: Pydantic JSON, kısıtlı operatörler

`RuleDefinition` zorunlu `rule_id`, `version`, `description`, `domain`, `metric`. Sayısal metrikler için `operator` ve sonlu sıfırdan küçük olmayan `threshold` zorunlu; izinli operatörler `>=`, `>`, `<=`, `<`, `==`. Serbest Python, `eval`, dinamik script, dış internet/API veya kütüphane yükleme **yok**. Tam hukukî rule package / YAML loader **henüz yok**.

```python
from mimarllm.rules.base import (
    Comparison, MetricKind, RuleDefinition, RuleDomain, RuleRequest,
)
from mimarllm.rules.engine import RuleEngine

# SADECE SENTETİK TEKNİK ÖRNEK; yönetmelik eşiği DEĞİLDİR.
rule = RuleDefinition(
    rule_id="example.synthetic.minimum_length",
    version="0.1",
    domain=RuleDomain.TECHNICAL,
    metric=MetricKind.SEGMENT_LENGTH_M,
    description="Doğrulanmış bir çizgi uzunluğu için örnek ölçüm kontrolü",
    operator=Comparison.GE, threshold=1.20,
)
result = RuleEngine([rule]).evaluate(
    rule.rule_id, RuleRequest(
        drawing=drawing_ir,
        measurement_evidence_id="some-source-backed-segment-measurement",
    )
)
# result.status=COMPLIANT ancak kaynak segment uzunluğu gerçekten >=1.2 m ise.
# result.legal_compliance_certified her zaman False'dur.
```

Mevcut `MetricKind`:
- `SEGMENT_LENGTH_M`: `DrawingIR.MeasurementEvidence` kaydının `method_id="segment_length"`, tek native `LINE/PDF_LINE`, aynı frame onaylı `UnitCalibration`, ham kaynak segment boyuyla geriye dönük hesap. Ham `source_value` geometriden farklıysa `REVIEW_REQUIRED`.
- `REVIEWED_INTERIOR_AREA_M2`: `AreaAssessment` iç sınırı, source SHA ve `assess_area()` ile **aynı DrawingIR üzerinden yeniden** hesaplanır. Başka bir poligon için uydurulan alan kabul edilmez.
- `REVIEWED_FOOTPRINT_M2`: Aynı kontrol, yalnız **dış bina zarfı oturumu (footprint)**. Toplam yasal brüt kat alanı, emsal veya yangın alanı anlamına gelmez.
- `REVIEWED_TOPOLOGY_PATH`: `GeometryAnalysis` + `SpaceReview[]` + `PassageReview[]` ile `build_topology()` yeniden yürütülür; yerel native CAD/PDF marker ve geometrik ortak sınır geçişi onaylıysa **topolojik bağlantı var**. Bağlantının **olmaması**, fiziksel yapıda kapı/çıkış olmadığının ispatı değildir. Bu yüzden yoksa `INSUFFICIENT_EVIDENCE`, `NON_COMPLIANT` değil.

## 3. Giriş doğrulama ve kaynak zinciri

`RuleRequest.drawing` ve bütün iç kanıtlar değerlendirmede yeniden Pydantic valide edilir; dış kodun `model_copy(update=...)` veya sonradan nesne değişikliğiyle doğrulamayı aşması engellenir. `DrawingIR` SHA, sayfa/layout/coordinate frame, entity ve measurement `evidence_id` bağı korunur.

| Kaynak | Yeniden hesaplanan şey | Kabul için |
| --- | --- | --- |
| Segment uzunluğu | Gerçek `GeometryPrimitive.SEGMENT` iki noktası ve onaylı CAD/PDF birim dönüşümü | Metod `segment_length`, native source, aynı frame, SI değer |
| İç sınır/dış footprint | `assess_area` ile tek kapalı Shapely polygon, source entity IDs, frame, ölçüm ve reviewer beyanı | `MEASURED`, source SHA eşit, geometriden tekrar hesaplanan m² eşit |
| İncelenmiş topoloji | `build_topology` Shapely yüzeyleri kaynak DrawingIR'den tekrar üretir, geçiş marker geometrisini kontrol eder | Kaynak yüzey değiştirilmemiş, reviewer/passage ID ve geçiş kenarı aynı |
| Kapsam dışılık | `ApplicabilityReview` reviewer kimliği, neden, drawing SHA ve mevcut entity IDs | **Yalnız teknik** senaryolarda `NOT_APPLICABLE` |

Geometrik uzunluk toleransı kaynak birim cinsinden girilir, yeniden fiziksel birime çevrilir. `abs(measurement - threshold) <= propagated_tolerance` ise **eşik belirsizlik aralığında**: `REVIEW_REQUIRED` döner. Alan hesapları henüz bağımsız hata yayılımı içermediği için alan toleransı 0'dır; bu, mühendislik hassasiyetinin sınırsız olduğu anlamına gelmez. Fiziksel alanın epistemik doğruluğu için bağımsız çizim/ölçüm kabulü hâlâ gerekir.

## 4. Yasal kurallar için mutlak HOLD

`RuleDomain.REGULATORY` kuralı tanımı ancak `LegalSourceLocator` (PDF SHA-256, PDF sayfası, regulation/article/clause, amendment kimliği, yürürlük aralığı gibi **aday metadata**) ile kurulabilir.

**Ancak bu metadata kendi kendine onay belgesi değildir.** V0.1'de bağımsız resmî PDF orijin doğrulaması, değişikliklerin yürürlük birleştirmesi, belediye/yapı sınıfı/üretim yılı, istisnalar, hukukî gözden geçirme ve imza sistemi yoktur. Bu yüzden teknik ölçümler tamamen mevcut olsa bile **bütün `REGULATORY` çağrıları** `INSUFFICIENT_EVIDENCE / REGULATORY_SOURCE_AND_APPLICABILITY_UNVERIFIED` döner. Kodda bunu kullanıcı alanıyla etkinleştirecek `approved=true` veya `legal_compliance_certified=true` anahtarı **bulunmaz**; `RuleResult` şeması böyle bir iddiayı reddeder.

İşlem 013 LegalAST + resmi PDF kaynak bağlayıcı; 014 FTS5/RAG kanıt eşleştirme; 015 doğrulanmış tarihli mevzuat kural paketleri geliştirildikten sonra ayrı kabul kapısı tasarlanacaktır. Bu aşamada Planlı Alanlar, Yangın, Otopark, Sığınak, BEP için gerçek maddeler veya sayısal hukukî eşikler **kodlanmadı**.

## 5. Kabul senaryoları

`tests/test_rules.py`: altı sonuç, altı komparatör/eşik senaryosu, gerçek `ezdxf.new/save/read` segmenti, birimi bilinmeyen çizim, kaynak `MeasurementEvidence` uyuşmazlığı, doğrulanmış iç alan, kötüye kullanılan sahte alan, yanlış rol, NetworkX iki odalı ve eksik kapılı bağlantı, forged topology, kaynak SHA mutation, doğru ve sahte teknik kapsam dışılık, invalid legal source, regulatory hold, JSON/registry determinismi.

Linux/Windows GitHub-hosted Python 3.11 sentetik testleri gerçek cihaz veya bağımsız hukukî/mimari doğrulama değildir. OCR inference, VLM, yürünebilir 3B kaçış mesafesi ve uygulama arayüzü bu işlemde geliştirilmez.
