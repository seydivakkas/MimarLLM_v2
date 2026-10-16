# İşlem 026 — Kanıt-bağlı 2.5D kütle ve yerel Three.js

- Tarih: 2026-10-16
- Durum: GELİŞTİRME / SENTETİK KABUL BEKLİYOR
- Dal: `feature/islem-026-source-25d`; bağımlı temel: `feature/islem-025-source-2d-jobs` (PR #2 hâlâ Draft), nihai hedef `main` ancak merge yok.
- **İlk kayıt:** Bu dosya yeni dalın koddan önceki ilk GitHub değişikliğidir; tarihsel `islem_001–025` dosyaları korunur.
- Nihai fiziksel Windows/Edge, gerçek kirli CAD/A0 PDF, performans/RSS/VRAM, offline EXE ve kullanıcı uzman imzalı testler İşlem 031'e ertelenmiştir. Bu, sentetik CI veya güvenlik şartlarını kaldırmaz.

## İş hedefi
1. Çizim kaynağındaki şekli yalnız açık kimliklerle, fail-closed biçimde 2.5D prizmatik mühendislik **önizlemesine** dönüştürmek. Kapı, pencere, çatı, kat, oda ve gerçek bina yüksekliği otomatik tahmin edilmeyecek.
2. Kaynak `DrawingIR.source_sha256`, `frame_id`, kaynak native destekleyici entity kimlikleri / CAD handle ve fiziksel birim durumu 2.5D şemada taşınacak. Farklı sayfa / frame / kaynak revizyonundan karışım reddedilecek.
3. Bir veya daha fazla kanıtlanmış kapalı poligon, tekrarlanabilir 2B miter/triangulation ve dikey ekstrüzyon; tek seferde sıkı geometri/vertex/bütçe sınırları.
4. Yükseklik kullanıcı tarafından pozitif metre olarak **açık senaryo beyanıyla** girilecek; gerçek binanın yüksekliği, ruhsat ya da kat adedi olduğu iddia edilmeyecek. Ölçek `CONFIRMED` ve frame bağlı değilse gerçek metreyle 3B kütle üretilmeyecek.
5. Üretim runtime'ında ağ gerektirmeyen, yerel statik Three.js ESM görüntüleyici. Modelin kaynağına tıklandığında SVG / kaynak kimliği açıklanacak; WebGL başarısızsa ayrı bilgilendirme, sessiz geometri uydurma yok.
6. Mevcut kaynak dosyası, DrawingIR ve raporlar değiştirilmeyecek; 2.5D yalnız ayrı candidate/preview nesnesi olarak dönecek. `RuleEngine.REGULATORY_LOCKED` ve F08–F12 `HUKUKI_HOLD` korunacak.
7. CI: sentetik geometri, kaynak eşleştirme, yanlış SHA/frame/kalibrasyon, self-intersection/holes, büyüklük bütçesi, API/CSRF ve offline/static JS sözleşmeleri. Gerçek fiziksel kabul yine 031.

## Başlangıç kapsama kararı
İlk kod adımında kaynak-lokasyon denetimli yüzey ve dikey ekstrüzyon **ayrı çekirdekte** kurulacak; ardından API ve yerel Three.js bağlanacak. Şimdilik otomatik semantik sınıflama, VLM, render üzerinden metrik/kaçış hukuku, serbest organik yüzey üretimi veya 3B dosya edit işlemi yok.

## Kapanış kapısı
Uygulanmış dosyalar, GitHub Actions gerçek run/commit kanıtları ve açık kısıtlar bu dosyada belirtilecek. Fiziksel UAT yokluğu 026 sentetik geliştirmesini tek başına durdurmaz, ama ürünü yayıma hazır da yapmaz.
