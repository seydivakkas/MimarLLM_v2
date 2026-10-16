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


## 1. Bu dalda oluşturulmuş gerçek mühendislik kodu

- Kaynak geometri: src/mimarllm/geometry/massing25d.py — explicit native DXF Model LINE sınır seçimi, exact tek yüz, hata-sız polygonize, bağımsız CONFIRMED fiziksel ölçek, kullanıcı declared_height_m, SHA/handle/frame/evidence kimliği. Sonuç UNVERIFIED_MASSING_SCENARIO, asla gerçek semantik bina modeli değil.
- REST API: server.py içindeki POST /api/projects/{project_id}/runs/{run_id}/massing25d; aynı local-only/CSRF/Host/Origin kapıları; kaynak run DrawingIR ve orijinal DXF hash kontrolü, 12KB JSON bütçesi.
- Arayüz: static/index.html, dashboard.js, dashboard.css — özgün LINE kaynak seçimi, yükseklik ve incelemeci etiketi, 2.5D adayı üretimi, kaynak kimliği paneli, başarısız WebGL veya kapalı geometri için hata.
- Render: static/scene25d.js — yalnız local Three.js modülünden Shape/ExtrudeGeometry, gözlem amaçlı prizma, fare + klavye orbit, resize ve dispose. Serbest organik 3B / odalar / katlar / yangın değerlendirmesi yok.
- Offline hazırlama: package.json sürümü three=0.160.1, scripts/build_three_vendor_026.mjs sha doğrulayıcı, scripts/windows/prepare_three_026.ps1, build_exe.bat ve mimar.spec yerel asset kontrolü, pyproject.toml paket verisi, .gitignore.
- Sentetik API/saf geometri: tests/test_massing25d.py kaynak immutable, confirmed kalibrasyon ve HEADER_UNITS yasağı, exact boundary, blok içi çizgi ret, CSRF/oversized/wrong SHA, gerçek run dosyası korunumu.
- Ek sözleşme: docs/specs/massing25d-v0.1.md.

## 2. Gerçekte doğrulanmış ilk CI

Bağımlılık hazırlama betiğiyle Three.js 0.160.1 tek yerel asset SHA256:
76dea8151bc9352aef3528b4262e249b2604f62543828328db978d060d61a495.
GitHub-hosted Ubuntu/Windows CI'da yerel dosya/manifest iki kez doğrulandı, Python sentetik 026 testleri ve Node scene25d.js sözdizimi başarıyla çalıştı.

[Core CI #38859926379](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38859926379), commit 7909e215508ac588953e9071c5c6d1c3b2659747:
- Ubuntu 374 PASS, 1 SKIP.
- Windows 375 PASS.
- Bu koşu 026 API + render kaynak kodu + 026 testleri ve yerel npm-prep SHA içerir.
- Sonraki build/manifest/Edge smoke güvenlik iyileştirmeleri için [Core CI #38860361363](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38860361363) GitHub'da success; son PR-head CI ayrıca kaydedilecek.

## 3. Kapanmayan ve ertelenen kabul

- 026 kod adayı **MÜHENDİSLİK / SENTETİK_CI_PASS** olabilir; gerçek Windows 10/11 fiziksel makine, Edge klavye/erişilebilirlik, 2.5D gerçek GPU/VRAM/RSS ve mimari A0/CAD doğruluğu **İşlem 031 / HOLD**.
- Yerel vendor hazırlama adımı gereklidir. Kaynak dalı tek başına hazır Three binary'sini içermez; zip veya exe dağıtımında Three ESM + SHA manifest + MIT license kopyaları doğrulanmalı. Binary yoksa Three.js preview kullanılamaz ve CDN fallback uygulanmaz.
- 026 2.5D önizlemesi GPU aygıt testi, gerçek IFC/BIM veri modeli, kat, oda veya resmî yönetmelik uygunluğu iddia etmez.
- İşlem 027–030 sentetik CI/regresyon sürdürülerek geliştirilebilir, fiziksel kullanıcı kabulü yalnız 031'de. F08–F12 HUKUKI_HOLD ve REGULATORY_LOCKED değişmedi.
- Bağımlı PR stratejisi: 025 Draft PR #2'yi main'e doğrudan taşımadan 026 dalı onun üzerine kuruldu; 026 PR ayrı Draft ve hedef 025 branch. Kod veya build entegrasyonu doğrulanmadan main merge/ürün yayımlama yok.


## 4. Son PR-head CI kanıtı — 2026-10-16

Yeni İşlem 026 bağımlı Draft [PR #4](https://github.com/seydivakkas/MimarLLM_v2/pull/4), temel: feature/islem-025-source-2d-jobs; PR #2 Draft ve main değişmemiştir.

Kod/karar head commit b12c75b7f8c94d795717fa347294b007d0fc2fdb için:
- [Core CI #38860877700](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38860877700): SUCCESS. Ubuntu Python 3.11 **374 passed, 1 skipped**, Windows **375 passed**. node --check ve Three ESM local manifest SHA kontrolü başarılı.
- [Hosted Windows Edge #38860877687](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38860877687): SUCCESS. Windows-hosted Microsoft Edge, gerçek localhost JS/DOM (massing-canvas, massing-build) ve /static/three.module.js SHA256 doğrulandı. Bağımsız fiziksel ekran/GPU/erişilebilirlik testi değildir.
- Three.js sürüm 0.160.1, 1,272,972 byte ESM kaynak SHA256: 76dea8151bc9352aef3528b4262e249b2604f62543828328db978d060d61a495. Yerel preparasyon npm gerektirir; runtime CDNsizdir. Üretim paket asset'i bağımsız gerçek EXE testine dek kabul edilmiş sayılmaz.

**026 mühendislik kararı:** 2.5D salt görsel teknik önizleme adayı = SENTETIK_CI_PASS / HOSTED_EDGE_STATIC_PASS; gerçek WebGL etkileşim/performans ve fiziksel Windows/GPU/A0 kabulü = DEFERRED_TO_031 / HOLD. REGULATORY_LOCKED ve F08–F12 HUKUKI_HOLD değişmedi. PR #4 Draft kalır, 027'ye geçiş için 026 fiziksel testine gerek yok; bir sonraki kod işinden önce docs/islem_027.md ilk kayıt olacaktır.
