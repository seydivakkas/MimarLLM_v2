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
