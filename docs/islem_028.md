# İşlem 028 — Sekiz boyutlu pedagojik rubrik ve deterministik puanlama

**Başlangıç:** 2026-10-17. **Dal:** `feature/islem-028-pedagogical-rubric` (bağımlı 027 Draft PR #5), `main` ve mevcut Draft PR'lara dokunulmaz.

## Hedefler
- Mimarlık eğitimi için **sekiz boyut:** bağlam/yer okuma, kavramsal yaklaşım, işlevsel program, mekânsal kurgu, taşıyıcı sistem, iklim/sürdürülebilirlik, temsil/iletişim, tasarım süreci/öz değerlendirme.
- 1–4. sınıf (Proje I–IV) için **kademeli pedagojik iskele**: her seviyede ilgili kriterler görünür/etkin, daha üst seviye zorunluluklarından sahte FAIL/puan kesilmesi yok. Yalnız öğretim amacıyla sürümlü, gözden geçirilmeye açık başlangıç profili; KTÜ veya başka bir kurumun resmî notlandırma kriteri olduğu iddia edilmez.
- Deterministik **score-in-code**: sınıf seviyesi, kriter ağırlığı, ölçüt skoru ve kaynak izi girdilerinden hesaplanır; LLM/VLM puan, eşik veya kanıt kimliği sağlayamaz. `REGULATORY_LOCKED`, F08–F12 `HUKUKI_HOLD`, `DrawingIR`, yerel DXF/PDF/rapor immutable kalır.
- Her kriter için rubrik düzeyi (0–4) **yalnız insan tarafından açık girilen değerlendirme** olarak alınır. Seçili gerçek çizim entity ID, frame ve kaynak SHA kontrol edilir; çizgi bir kavramın başarıyla karşılandığını otomatik kanıtlamaz. Eksik değerlendirilen/kanıtsız kriter varsa **genel puan üretilmez**, kapsama ve eksik kanıt durumları gösterilir.
- Sekiz eksen ve toplam, yalnız tüm geçerli kriterler aynı güvenilir DrawingIR SHA/frame ile manuel kaynaklandırıldığında **yerel taslak senaryo** olarak hesaplanabilir. Kullanıcı kimliği doğrulaması, eğitmen onayı, resmî akademik not veya pedagojik geçerlilik **uygulamada sağlanmış sayılmaz**.
- Rapor ana pipeline'a yazılmaz. VLM yorumu yalnız ayrı, onaysız gözlem olarak kalır. CSRF + loopback, JSON bütçesi ve sentetik Windows/Ubuntu testleri zorunlu.
- Fiziksel Windows/Edge, gerçek öğrenci çizimleri, uzmanlar arası güvenilirlik, resmî rubrik ve çevrimdışı `onedir` kabulü son İşlem 031'de.

## İş sırası
1. Sürüm/şema/8 boyut/kademeli sınıf kriter kataloğu.
2. Kaynak kanıtlı insan değerlendirmesiyle deterministik ve koşullu ağırlıklı puanlama (eksikte NOT_SCORED).
3. Salt-okunur run-scoped API + ilk arayüz ekranı, sonlu veri sınırları ve güvenlik.
4. Sentetik adversarial testler (1. sınıf ileri gereklilik dışlama, spoof VLM/puan, sahte SHA/frame/entity, eksik/aykırı kanıt).
5. Ubuntu/Windows CI, belge ve bağımlı Draft PR; nihai fiziksel kabul 031.


## Gerçekleştirilen mühendislik uygulaması

- `src/mimarllm/pedagogy/rubric.py`: 8 eksenli sürümlü `028.0.1` pilot öğretim rubriği, 100 taban ağırlık; sınıf 1/2/3/4 için sırasıyla **6/10/14/16** geçerli kriter. 1. sınıfta taşıyıcı ve çevre boyutları `NOT_APPLICABLE_BY_LEVEL`, sıfır puan/başarısızlık oluşturmaz.
- `src/mimarllm/pedagogy/scoring.py`: yalnız insanın girdiği 0–4 düzeyi ve kaynaklı native DrawingIR entity ID/SHA/frame/source-kind ile `Decimal ROUND_HALF_UP` skor. Eksik herhangi bir aktif kriter varsa `NOT_SCORED`, `draft_points_out_of_100=null`; tamamında `LOCAL_DRAFT_ONLY` (0–100) ve `official_grade=false`. VLM skor/AI yorum alanları şemada reddedilir; hiçbir kaynak veya rapor düzenlenmez.
- `GET /api/rubric/profile/{academic_year}`: uygun/sınıf dışı kriterleri sekiz eksende listeler. `POST /api/projects/{project_id}/runs/{run_id}/rubric/evaluate`: loopback/CSRF, 32KB JSON, kaynak-run güvenliği, insan öz-beyan zorunluluğu. Gerçek eğitmen kimlik doğrulaması veya okul resmî rubrik onayı değildir.
- UI `static/index.html`, `dashboard.js`, `dashboard.css`: sınıf, frame, kaynak çizgi, insan düzeyi/inceleme notu, sekiz eksen, değerlendirilmeyen kriterlerin HOLD görünümü; öğrenci notu/resmî PASS iddiası yok.
- `tests/test_rubric_028.py`: 1. sınıf ilave strüktür zorlamama, 4. sınıf eksen/puanı, 0–75–100 Decimal, sahte SHA/frame/entity, duplicate kriter, dış model/AI puan alanı, CSRF/HTTP, değişmez DrawingIR/rapor, arayüz sözleşmeleri.
- Windows-hosted Edge smoke: rubrik UI kontrolleri, sınıf 1 ve 4 sayıları, `official_grade=false`. Fiziksel öğrenci bilgisayarı/gerçek kullanıcı onayı değildir.
- Teknik katalog: [`docs/specs/pedagogical-rubric-028-v0.1.md`](specs/pedagogical-rubric-028-v0.1.md).

## Doğrulama kanıtı / nihai kabul sınırı

[Core CI #38983549274](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38983549274), kod commit `dc9e4ad550aa06f2777063b52d982d5607d74c55`: GitHub-hosted Windows **389 passed**, Ubuntu **388 passed / 1 skipped**; kaynak ve UI/test regresyonu `success`. Bu sonucu izleyen kaynak-kind ve doküman commit'lerinin CI ayrı koşusu son aşamada kontrol edilecek.

**Son statü:** `028_MÜHENDİSLİK_ADAYI / SENTETİK_CI_PASS`; `RESMÎ_ÖĞRETMEN_KİMLİĞİ_HOLD`, `RUBRİK_KURUM_ONAYI_HOLD`, `GERÇEK_ÖĞRENCİ_PROJESİ_031_HOLD`, `FİZİKSEL_WINDOWS_EDGE_031_HOLD`. İnsan notu alanının doldurulması resmî öğretim üyesi doğrulaması değildir; puan yalnız yerel taslaktır. `REGULATORY_LOCKED`/F08–F12 `HUKUKI_HOLD` korunur.

**İlerleme kuralı:** 028 sentetik kod adayından sonra İşlem 029 için önce `docs/islem_029.md` açılabilir. Gerçek pedagojik uzmanlar arası tutarlılık, kurumsal onay, gerçek pafta ve kullanıcı testi birleştirilmiş İşlem 031'de yapılacaktır. PR #2/#4/#5/#6 açık Draft, main ve üretim değişmedi.
