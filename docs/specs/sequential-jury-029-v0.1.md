# İşlem 029 — Kaynaklı sıralı pedagojik jüri simülasyonu v0.1

**Sürüm:** `029.0.1` · **Rubrik:** `028.0.1` · **Durum:** Sentetik mühendislik adayı (gerçek uzman/fiziksel cihaz onayı son `031`).

## A. Amaç ve yanlış yorumların önlenmesi

Bu özellik gerçek öğretim üyesi kimliğine sahip 4 uzmanı veya 4 ayrı eğitilmiş AI ajanını temsil **etmez**. Tek `pedagogy/jury.py` motoru, sürümlü pedagojik rubriğe ve önceden incelenmiş insan notlarına bağlı dört farklı **eğitim amaçlı kontrol sorusu dizisi** sunar. Jüri üyesi adına konuşma, oyun çoğunluğu, oy birliği, resmî kabul, gerçek öğretim üyesi atfı veya öğrencinin tasarım niteliği hakkında bağımsız AI kanaati oluşturmaz.

`model_inference_used=false`, `independent_ai_votes=false`, `real_faculty_approval=false`, `official_jury=false`, `official_grade=false`, `numeric_score=null`, `passed=null` ve `legal_gate=REGULATORY_LOCKED` **çıktı sözleşmesinin değişmez alanlarıdır**. VLM #027 yorumları rapora veya skora otomatik aktarılmaz. İşlem 028 yerel puanının sonucu bile 029 raporuna sokulmaz.

## B. Jüri perspektifleri ve kaynak sırası

| Sıra | Perspektif | Rubrik eksenleri | Kaynak garantisi |
| --- | --- | --- | --- |
| 1 | Bağlam ve kavramsal tutarlılık | CONTEXT + CONCEPT | Yalnız ilgili etkin kriterler |
| 2 | İşlev ve mekânsal kurgu | FUNCTION + SPATIAL | Yalnız ilgili etkin kriterler |
| 3 | Yapım ve çevresel yaklaşım | STRUCTURE + ENVIRONMENT | 1. sınıfta `NOT_APPLICABLE_BY_LEVEL` |
| 4 | Temsil ve tasarım süreci | REPRESENTATION + PROCESS | Aynı orijinal kaynak SHA/frame |

1–4. sınıflarda 028'in geçerli kriter maskesi kullanılır: **6/10/14/16** aktif ölçüt. Bu sıra istemci tarafından değiştirilemez; her ölçüt tam bir perspektifte görünür. Aktif kriterin insan incelemesi yoksa `REVIEW_REQUIRED` ve boş kaynak kimlikleri döner. Uygulanmayan boyut hiçbir başarısızlık veya puan kesintisi doğurmaz.

## C. Girdi ve güven sınırı

`POST /api/projects/{project_id}/runs/{run_id}/jury/critique` gövdesi **aynen İşlem 028'in `RubricSubmission` şemasıdır**, örnek:

```json
{
  "source_sha256": "64_haneli_orijinal_sha256",
  "frame_id": "cad:Model",
  "rubric_version": "028.0.1",
  "academic_year": 1,
  "reviewer_label": "İnsan incelemeci etiketi",
  "human_review_attested": true,
  "reviews": []
}
```

- `human_review_attested=true` öz-beyandır; yetkili eğitmen kimlik doğrulaması değildir.
- Her doldurulmuş kriterde insan düzeyi 0–4, 15–500 karakter açıklama ve `DrawingIR` içinde aynı `source_sha256`, `frame_id`, orijinal `source_kind`, `CAD_NATIVE/PDF_NATIVE` entity kimliği zorunludur. `RubricSubmission` ayrıca sınıfa uygunluk, tekrar eden/ek alanlar ve tipleri doğrular.
- Modelden, rastgele metinden veya tarayıcının uydurduğu kaynaktan yeni `entity_id` oluşturmak; `ai_vote`, `jury_pass`, `approval`, `official_grade` gibi sahte parametreler geçirmek yasak; `422/409` ile ret.
- Sunucu değiştirilemez `DrawingIR` ve orijinal run dosyalarını yeniden okur; `build_jury_report` önce `evaluate_rubric` kaynak/insan rubrik sözleşmesini denetler. **Değerlendirme puanı hesaplanabilir fakat 029 raporuna alınmaz.**
- İstek tavanı **32768 byte**, Markdown rapor limiti **26000 karakter**. Büyük giriş fail-closed. Proje/run başka kaynağa aitse ve kaynak SHA eşleşmezse hiçbir rapor üretilmez.
- Tek kullanıcı ve yalnız loopback, aynı yerel CSRF/Host/Origin güvenlik katmanı. Sistemde genel öğrenci profili/öğrenci verisi dosyası oluşturulmaz.

## D. JSON ve Markdown eleştiri raporu

JSON içinde `sequence` dört sıralı `JuryTurn`; her tur `order`, `perspective_id`, iki eksen, kontrollü sabit soru, `REVIEW_REQUIRED`/`NOT_APPLICABLE_BY_LEVEL`/`SOURCE_BOUND_REVIEW_PROMPTS`, her kriter için kaynak ID ve varsa **yalnız insana atfedilmiş doğrulanmamış not** döner. `review_coverage` yalnız tamlık bilgisidir, akademik başarı değerlendirmesi değildir.

`report_markdown` aynı girdiden **deterministik** olarak oluşturulur: rubrik/jüri sürümleri, kaynak SHA/frame, incelemeci öz-beyanı, dört perspektif, kaynak entity kimlikleri, eksik incelemeler ve kaynak sınırları. Notlar Markdown/HTML escape ile inert hale getirilir; tarayıcı raporu ancak kullanıcı tıkladığında yerel Blob olarak indirir. Sunucu, `analysis.json`, `drawingir.json`, CAD/PDF, RuleEngine veya VLM dosyalarını güncellemez.

Arayüzde aynı rubrik girişleri yeniden kullanılır; kullanıcı ilk perspektifi görüntüledikten sonra **Sonraki perspektif** ile 2→3→4 sıralı olarak açar. Kaynağa dön düğmesi, yalnız kullanıcının zaten seçtiği frame üzerindeki orijinal 2B SVG çizgi kimliğine odaklanır. Mevcut SVG bütçesi dışında kalan kaynakta uyarı çıkar; gizlice benzer çizgi seçilmez.

## E. CI ve ertelenen kabul

`tests/test_jury_029.py` dört sıra/16 ve 6 kriter, ilk yıl kapsam dışı perspektif, eksik kanıt, Model/AI sahte oy alanlarının reddi, tam insan kaynaklarına rağmen **numeric_score=null**, Markdown enjeksiyonunun escape edilmesi, API CSRF/run/SHA/32KB, kaynağın ve raporun değişmezliği, UI kontrol noktaları. `scripts/windows/edge_smoke_025.py` hosted Edge üzerinde 029 DOM varlığına genişletilir. Bu **sentetik mühendislik doğrulamasıdır**, gerçek öğrenci/öğretim üyesi/fiziksel Windows uygulayıcısı doğrulaması değil.

**031/HOLD:** gerçek kullanıcı değerlendirme yöntemi, uzman güvenirliği ve etik/onam, resmi rubrik onayı, gerçek mimari paftalar, fiziksel Windows/Edge/offline EXE, gerçek model kalitesi. Üretim ve resmî mevzuat PASS yoktur.
