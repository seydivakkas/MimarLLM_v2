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
