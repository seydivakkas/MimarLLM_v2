# İşlem 028 — Sekiz eksenli pedagojik rubrik / deterministik taslak değerlendirme sözleşmesi

**Sürüm:** `028.0.1` · **Durum:** KOD ADAYI + sentetik CI; kurumsal/kullanıcı kabulü `031/HOLD`.  
**Asla resmî öğrenci notu / yönetmelik kararı değil.** Üniversiteye özgü rubrik, onaylanmış ders ölçütleri veya kimliği doğrulanmış eğitmen süreci henüz sağlanmadı.

## 1. Sekiz tasarım ekseni ve pilot ağırlıklar

| Eksen | Pilot ağırlık | 1. sınıf durumu |
|---|---:|---|
| Yer ve bağlam okuması | %10 | Temel bağlam gözlemi |
| Kavramsal yaklaşım | %20 | Tasarım niyetinin açıklanması |
| İşlevsel program | %15 | Kullanıcı gereksinimleri |
| Mekânsal organizasyon | %15 | Temel mekânsal ilişkiler |
| Taşıyıcı ve yapım yaklaşımı | %10 | **NOT_APPLICABLE_BY_LEVEL** |
| İklim ve çevresel yaklaşım | %10 | **NOT_APPLICABLE_BY_LEVEL** |
| Mimari temsil ve iletişim | %12 | Planın okunurluğu |
| Tasarım süreci / öz değerlendirme | %8 | Kararlar üzerine eleştirel düşünme |

Toplam statik ağırlık %100'dür. **Bu pilot ağırlıklar herhangi bir kurum/eğitmen tarafından onaylanmış sayılmaz.** Etkin olmayan eksen ağırlıkları aktif boyutlarda normalize edilir; 1. sınıf strüktür/yangın/stüdyo IV kriterleri için otomatik sıfır puan üretmez. Fiziksel ve hukukî teknik eşikler pedagojik rubriğe karıştırılmaz.

## 2. Sınıfa göre kademeli profil

`GET /api/rubric/profile/{academic_year}`: 1–4 değerleri. Sürüm, sekiz eksen, `active`, geçerli kriterler, hariç tutulan üst sınıf kriterleri ve insan değerlendirme düzeyleri döner. İlgili kriter sayıları:

- 1. sınıf: 6 (temel tasarım/ilk proje)
- 2. sınıf: 10 (yerleşim, dolaşım, strüktür fikri, iklim yönelimi ve temsilde bütünlük)
- 3. sınıf: 14 (bağlam/tarihsel okuma, gelişmiş kavram, işlev erişilebilirliği, pasif çevresel yaklaşım)
- 4. sınıf: 16 (strüktür koordinasyonu ve tasarım sürecinin gerekçeli revizyonu)

Kriterler, `src/mimarllm/pedagogy/rubric.py` içinde sürümlü sabit koddur. Tarayıcı bir kriteri, ağırlığı, sınırı veya akademik yıl dışı yükümlülüğü gövdesinde değiştirerek sunucuya kabul ettiremez. Kurum düzeyindeki özel bir rubriği **onaylanmış profilmiş gibi** kullanmak desteklenmez; o özellik ayrı sorumluluk/onay sözleşmesi gerektirir.

## 3. İnceleme ve hesap sözleşmesi

`POST /api/projects/{project_id}/runs/{run_id}/rubric/evaluate`:

```json
{
  "source_sha256": "gercek_64_haneli_SHA256",
  "frame_id": "cad:Model",
  "rubric_version": "028.0.1",
  "academic_year": 1,
  "reviewer_label": "Örnek yerel incelemeci",
  "human_review_attested": true,
  "reviews": [
    {
      "criterion_id": "CONCEPT_INTENT",
      "human_level": 3,
      "source_entity_ids": ["Model|ORNEK_CAD_HANDLE|LINE"],
      "reviewer_note": "Bu tasarım kararı, çizimde insan tarafından bağımsız incelendi.",
      "human_review_attested": true
    }
  ]
}
```

- İnceleme düzeyi: insanın **açıkça girdiği** 0–4 *tam sayı*, 4 en yüksek pilot düzeydir. LLM/VLM bu alanı yazamaz. Bir kişisel incelemeci etiketi `reviewer_label` gerçek öğrenci/öğretim üyesi kimlik doğrulaması değildir. `human_review_attested=true` öz-beyandır.
- Her değerlendirmede en az bir **aynı run, aynı kaynak SHA, aynı frame** içindeki gerçek `CAD_NATIVE` veya `PDF_NATIVE` `DrawingIR` entity kimliği ve en az 15 karakter değerlendirme notu gerekir. Kaynak çizgi konumu, o öğrenciye ait tasarım başarısını otomatik kanıtlamaz.
- İlk versiyon her kriterde 1–12 kaynak entity kimliğini kabul eder; UI tek bir ilgili native çizgiyi seçtirir. Şema yalnız açık `criterion_id/human_level/source_entity_ids/reviewer_note/human_review_attested` kabul eder; `ai_grade`, `vlm_score`, yeni rubric weight veya mevzuat PASS `extra=forbid` ile reddedilir.
- Puan `Decimal` + `ROUND_HALF_UP`, kodda saklı sabit kriter ağırlıkları ile hesaplanır:
  `axis_percent = (sum(level * internal_weight) / sum(internal_weight)) × 25`; 
  `total_draft = sum(axis_percent_unrounded × active_axis_weight) / sum(active_axis_weight)`.
- Her aktif kriter için insan değerlendirmesi yoksa `status=NOT_SCORED`, `draft_points_out_of_100=null`; üst yıl ve aktif olmayan boyutlar `NOT_APPLICABLE_BY_LEVEL`. Bütün aktif kriterler kapsandığında `status=LOCAL_DRAFT_ONLY`, 0.00–100.00 arası **resmî olmayan** sayısal senaryo. Model kararı/başarı notu değildir.
- Tam sayı ve sürüm/sınıf aralıkları katı Pydantic şeması ile sınırlanır. Gönderilen her DrawingIR/rubrik nesnesi yeniden doğrulanır, sahtelenmiş SHA/frame/entity/criterion veya uyuşmayan akademik yıl `409`.
- API 403 localhost CSRF/Host/Origin, 404 bilinmeyen run, 413 32 KB üstü, 422 kötü JSON/eksik insan onayı, 409 kaynak veya kriter uyuşmazlığı. Tüm sonuçlar transient JSON; kaynak CAD/PDF, `drawingir.json`, `analysis.json`, hukuki RuleEngine ve raporlar **değişmez**.

## 4. UI ve değerlendirme sorumluluğu

Yerel arayüzde `rubric-year`, `rubric-frame`, `rubric-reviewer`, `rubric-human-confirm`, 8 eksenli kriter listesi, insan düzeyi, kaynak çizgi, not ve `rubric-outcome` vardır. Sınıf seviyesinin değişmesi, üst seviye ölçütlerini aktif sınıf kapsamına eklemez. İnsan onayı verilmeden ve kaynak seçilmeden değerlendirme tetiklenemez.

Gösterilen not yalnız taslak senaryodur. Gerçek pedagojik geçerlilik için rubrik komisyonu, örnek paftalar, öğrenci izni, bağımsız çift incelemeci, ağırlık onayı ve güvenirlik (örn. ağırlıklı kappa) testleri **031/HOLD**. Öz-beyan imzalı eğitmen onayı değildir.

## 5. Otomatik testler ve açık kabuller

`tests/test_rubric_028.py`: sekiz eksen/ağırlık 100; yıl bazında 6/10/14/16 kriter; 1. sınıf strüktür ve çevre dışlama; eksik veride `NOT_SCORED`; tam 0/75/100 taslak için Decimal; puan deterministik sıralama; yanlış kaynak, sahte `vlm_score`, `ai_grade`, yıl dışı kriter, yanlış öğrenci/onay alanlarının reddi; immutable DrawingIR/rapor; CSRF ve HTTP şema sınırları; offline yerel ekran.

GitHub-hosted Windows/Ubuntu otomatik regresyon ve Edge DOM smoke, gerçek kullanıcı/ekran okuyucu testinin yerini tutmaz. Üretim dağıtımı, resmî not ve resmî mevzuat uygunluğu **asla** otomatik açılmaz.

**Geliştirme sırası:** 028 sentetik kapı → 029 sıralı, iddiası sınırlı pedagojik jüri → 030 izinli analitik → 031 tüm gerçek fiziksel, uzman pedagojik ve bağımsız veri kabulleri.
