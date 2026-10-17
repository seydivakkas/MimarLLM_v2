# İşlem 029 — Sıralı pedagojik jüri, perspektifler ve kaynaklı eleştiri raporu

**Tarih:** 2026-10-17  
**Durum:** GELİŞTİRME / SENTETİK CI ADAYI  
**Dal:** `feature/islem-029-sequential-jury`; temel: `feature/islem-028-pedagogical-rubric` (Draft PR #6). PR #2/#4/#5/#6 Draft zinciri ve `main` değiştirilmez.

Bu dosya **yeni dalın ilk GitHub kod-dışı kaydıdır**. Yeni özellik geliştirmesi bundan sonra yapılır.

## Sözleşme / güven sınırları

1. 028'in sürümlü sekiz eksenli `RubricCatalog`, sınıf maskeleri ve salt insan girişli `RubricSubmission` verisiyle **dört kesin sıradaki** pedagojik perspektif oluşturulacak:
   - I: Bağlam / kavramsal yaklaşım
   - II: İşlev / mekânsal kurgu
   - III: Taşıyıcı yaklaşımı / iklim
   - IV: Mimari temsil / tasarım süreci
2. Perspektifler **rolleri belli eğitim simülasyonlarıdır**, farklı öğretim üyesi, birbirinden bağımsız AI ajanı, uzman imzası, kurumsal komisyon veya resmî jüri oyu değildir. VLM'nin önceki yorumları not veya jüri oyu gibi kabul edilemez.
3. Her kritik madde rubrik kriter kimliği, sınıf uygulanabilirliği, orijinal `DrawingIR` kaynak SHA/frame ve **yalnız daha önce doğrulanmış insan notundaki entity kimlikleri** üzerinden kurulur. Modelin kanıtsız duvar/oda/alan/ruhsat/başarı tanıması yasaktır. Eksik insan incelemesi kaynak uydurma yerine `REVIEW_REQUIRED` olarak görünür.
4. Eleştiriler, ölçülmemiş alan, bina işlevi, kat, performans veya başarı iddiası içermeyen sürümlü **sabit pedagojik inceleme sorularından** üretilecek. İnsan notu yalnız *insan beyanı* etiketiyle, HTML/Markdown güvenliği korunarak aktarılabilir. Hiçbir yorum resmî not değildir.
5. Jüri sonucu **puan, ortalama jüri oyu, geçme/kalma veya mevzuat PASS üretmez**. İşlem 028'deki ayrı deterministik taslak skor dosyaya yazılmaz ve değiştirilemez. Kaynak DXF/PDF, `drawingir.json`, `analysis.json`, `RuleEngine`, 027 VLM sonucu değişmez.
6. Tek kullanıcılı localhost FastAPI, CSRF ve küçük JSON/rapor bütçesi; transient structured JSON + indirilebilir kaynaklı Markdown eleştiri raporu. Sağlanamayan kaynak veya sahte rubrik/version/frame/ID için fail closed.
7. Sentetik Windows/Ubuntu CI: 4 perspektif sırası, 1–4 sınıf maskeleme, eksik kaynaklarda REVIEW_REQUIRED, sıralama tutarlılığı, sahte AI oyları ve enjeksiyon reddi, immutable dosyalar, REST/CSRF, arayüz ve Markdown escaping.
8. Gerçek öğretim üyesi, mimari jüri pedagojik geçerliliği, bağımsız çift değerlendirici, gerçek öğrenci projeleri, fiziksel Windows/Edge ve onedir EXE kabulü **son İşlem 031 HOLD**.

## Kod sırası
1. `src/mimarllm/pedagogy/jury.py` yapılandırılmış sıralı kanıtlı yorumlar ve kaynaklı Markdown.
2. `POST /api/projects/{project_id}/runs/{run_id}/jury/critique` (aynı güvenlik ve rubrik kaynağı).
3. Sekiz boyutu ve sırayla yürütülen dört perspektifi gösteren UI, güvenli rapor indirmesi.
4. Sentetik testler, Github-hosted Edge, karar/yol haritası ve bağımlı Draft PR.


## Gerçek mühendislik kodu ve sentetik CI kanıtı

- `src/mimarllm/pedagogy/jury.py`: 4 değişmez sıralı eğitim perspektifi, `JuryTurn/JuryComment/JuryReport`, mevcut 028 insan/rubrik/kaynak doğrulaması, eksik kriterde `REVIEW_REQUIRED`, 1. sınıfta uygulanmayan yapım/iklim turu `NOT_APPLICABLE_BY_LEVEL`. Jüri motoru **027 VLM'yi çağırmaz**. Başka modellerin birbirinden bağımsız jüri üyesi olduğu iddiası yok.
- Kaynak kimlikleri: orijinal `drawing.source_sha256`, `frame_id` ve yalnız kullanıcı tarafından 028 rubriğinde geçerli biçimde seçilmiş `DrawingIR CAD_NATIVE/PDF_NATIVE` entity kimlikleri, insan öz-beyan notu ile birleştirilir. Kaynak anlamı veya gerçek öğretim niteliği otomatik doğrulanmaz.
- Rapor: `SOURCE_BOUND_JURY_SIMULATION` ve dördü sıralı `sequence`; `official_grade=false`, `official_jury=false`, `independent_ai_votes=false`, `model_inference_used=false`, `real_faculty_approval=false`, `numeric_score=null`, `passed=null`, `REGULATORY_LOCKED`. Kaynaklı Markdown için HTML/Markdown escape uygulanır; insan notu onaysız beyan olarak etiketlenir.
- API: `POST /api/projects/{project_id}/runs/{run_id}/jury/critique`, `RubricSubmission` doğrulaması ve proje/run kaynak kimliği, 32768 byte üstü 413, eksik öz-beyan 422, sahte SHA/entity 409, yerel güvenlik CSRF/Origin/Host 403. Sonuç sadece transient JSON; hiçbir resmî rapor veya öğrencinin not dosyası yazılmaz.
- UI: `static/index.html`, `dashboard.js`, `dashboard.css` için 4 perspektif sıralı görünüm, sonraki perspektif düğmesi, orijinal SVG'ye kaynak odaklama, eksik kaynak uyarısı ve kullanıcı etkileşimli yerel Markdown indirme. Kaynak/rubrik girdileri değişince önceki jüri taslağı otomatik temizlenir.
- `tests/test_jury_029.py`: dört sıra, 6/16 kriter, 1. sınıf kapsam dışı tur, tam insan incelemesine rağmen resmî not/AI oyu üretmeme, sahte kaynak/alanlar ve Markdown saldırgan girdi reddi, REST immutable, UI.
- Teknik sözleşme: `docs/specs/sequential-jury-029-v0.1.md`.

**Kod ve test commit `bf9fb114f1d5f9aa5a1d91e4338e706e20a24ee6` için [Core CI #38984767523](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38984767523) `success`: GitHub-hosted **Windows 395 passed**, **Ubuntu 394 passed / 1 skipped**, JavaScript `node --check` ve mevcut OCR/RAG/geometri/rapor regresyonları başarılı. Bu kanıt gerçek uzman jürisi veya fiziksel Windows cihazı değildir. PR açıldıktan sonra hosted Edge doğrulaması ayrı kaydedilir.

**Bağımlı [Draft PR #7](https://github.com/seydivakkas/MimarLLM_v2/pull/7)**: base `feature/islem-028-pedagogical-rubric`; önceki PR #2/#4/#5/#6 ve `main` değişmedi. İşlem 029 için **MÜHENDİSLİK_ADAYI / SENTETİK_CI_PASS**; resmi jüri/gerçek eğitmen, gerçek öğrenci, pedagojik kappa, fiziksel Windows/Edge/onedir ve saha kabulleri `DEFERRED_TO_031 / HOLD`.

**Sonraki geliştirme:** İşlem 030 öğrencinin açık rızası, güvenli yerel veri saklama, tekrar eden kaynak kimliği ve küçük örneklem belirsizliği olan analitik. 030'dan sonra 031 fiziksel/uzman nihai kabul; üretim dağıtımı ve resmî notlandırma henüz yasak.
