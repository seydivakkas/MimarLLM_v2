# Stüdyo arayüzü — HTML aktarımı için aday dal

Durum: **İLK UI AKTARIMI / DRAFT / ANA DALA BİRLEŞTİRİLMEDİ**. İşlem 021 Windows offline dağıtım önceliğini ve geçmiş 001–020 işlem kayıtlarını değiştirmez. Bu dal ancak uygun işlem kaydında (planlanan 025) değerlendirilerek birleştirilir.

Kaynak: Kullanıcı tarafından sağlanan `gemini-code-1792057462448.html` demo dosyası (2026-10-16).

## Aktarılanlar
- Mevcut localhost dashboard altında opsiyonel "Stüdyo" bölümünde dört sınıflı müfredat seçici; hedef katalog 18/31/45/55.
- Masaüstünde üç sütun / dar ekranda tek sütun arayüz; 2B rapor ve mevzuat kanıt sekmeleri, kısıtlı 3B önizleme bilgilendirmesi.
- Kaynaklı proje/çalışma bilgisi, mevcut raporun güvenli bağlantısı, şimdilik kanıtsız ders modülleri için PLAN statüsü.
- Sekiz pedagojik değerlendirme boyutunu **puansız** gösteren rehber. Delphi ağırlıkları ve jüri notları doğrulanmış değil.

## Kesinlikle aktarılmayanlar
- `cdnjs` ile Three.js yüklenmesi; harici CDN'nin offline/CSP şartını bozması.
- Sabit yönetmelik eşikleri üzerinden otomatik uygun/aykırı kararı; mevzuat REGULATORY_LOCKED / HUKUKI_HOLD devam.
- Sahte % benzerlik, varsayılan 89.7/100 not, sahte 5 jüri, gerçek ölçümden gelmeyen geometri, sahte VRAM/FPS benchmarkı.
- `innerHTML` yoluyla kullanıcı metni ekleme, orijinal CAD/PDF verisini değiştirme.
- MÜDEK/ruhsat "sertifikası" ve resmi kabul iddiası.

## Bağımlılık / kabul
Var olan `src/mimarllm/app/static` dosyaları, localhost API ve `analysis.html` kanıt raporundan yararlanır. Yeni CDN / API / model gerekmez. 55 katalog başlığı mevcut 55 modül planı içinden seçilen gösterim örnekleridir; "çalışan 55 Python modülü" değildir. Yeni yazılım gerçek model/kuralları açmış sayılmaz.

Sentetik regresyon GitHub'da ayrıca koşulmalıdır; gerçek Windows/Edge kullanıcı kabulü, modeller ve 3D işlevi ilgili son aşamada yapılmalıdır.
