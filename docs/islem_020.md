# İşlem 020 — MimarLLM V2 × ARCH-CORE Local: Kapsam ve Mühendislik Yol Haritası Yeniden Yapılandırması

- **Tarih:** 2026-10-15
- **Durum:** ÖN KAYIT — İşlem 020 kapsamında yapılan **ilk GitHub yazımı**; kod ve diğer belge değişikliklerinden önce açılmıştır.
- **İstek:** Kullanıcının sunduğu üç yerel proje/teknik risk/klasör mimarisi metnini, GitHub'da İşlem 001–019 altında gerçekten yazılmış MimarLLM V2 kodu ile karşılaştırarak mevcut sistem ve gelecekteki ARCH-CORE pedagojik jüri/2.5D hedeflerini tek modüler monolit planına dönüştürmek.
- **Sınır:** Bu bir **mimari karar, özellik envanteri ve yol haritası güncellemesi** işlemidir; yeni jüri/LLM/3D/Windows installer modülü geliştirilmiş gibi gösterilmez.
- **Değişiklik kuralı:** Önce bu kayıt → yeni güncel master mimari/karar/risk/kabul belgeleri → mevcut README, kapsam, mimari, envanter, planlanan dosya yapısı ve yol haritasının tutarlı biçimde güncellenmesi → **en son bu kaydın commit/doğrulama ile kapatılması**. İşlem 001–019 kayıtları değiştirilmeyecek.

## 1. Temel ürün kararı

**Çekirdek V2** ve **opsiyonel ARCH-CORE Eğitim/3D** özellikleri, yeni repo veya `ARCH-CORE/backend/` paralel Python paketi oluşturulmadan **mevcut `src/mimarllm/`** altında bağımlılığı kontrollü modüller olarak tasarlanır. Çekirdeğin kaynak kimliği ve gerçek ölçüm güvenlik sınırı korunur. Mevcut kapsam defterindeki ilk sürümün pedagojik jüri dışında kalması tarihsel bir karardır; burada proje **ileri sürüm genişleme adayları** olarak eğitim modülleri planlanır, henüz uygulamaya alınmaz.

## 2. İncelenmiş mevcut gerçeklik

- **İşlem 019 kapalı**, tek kullanıcılı FastAPI/yerel CSS+JS dashboard var; İşlem 019 son sentetik CI kaydı GitHub-hosted Ubuntu/Windows **295/295 PASS** (gerçek kullanıcı cihazı değil). Mevcut tek paket `src/mimarllm/` ve DrawingIR v0.1 değişmeden kalır.
- **Var:** DXF/PDF→DrawingIR, Shapely/NetworkX adaylar, RuleEngine teknik değerlendirmeleri, offline LegalAST/FTS5/RRF ve hukukî kaynak HOLD, kaynaklı JSON/MD/HTML/PDF, CLI, localhost dashboard.
- **Yok / doğrulanmadı:** resmî hukukî geçerlilik, tam otomatik net alan/yangın kaçış/geçiş, gerçek ürün Windows installer, Layer0 kurtarma doğrulama, tam sayfa tiled OCR, otomatik gerçek SI ölçek, yerel GPU VLM, 3D WebGL, jüri/rubrik/öğrenci analitiği, gerçek mimari performans ve akademik benchmark.

## 3. Yeni plan çalışması

1. Mevcut kod → sunulan üç metnin önerileri karşılaştırma matrisi; **MEVCUT / KISMI / PLAN / HOLD / AR-GE** durumları.
2. `docs/master-mimari-arch-core-local.md`: katmanlar, kararlar, DrawingIR/Evidence/LegalAST ayrımı, pedagojik modül **non-authoritative** sınırı, tek bilgisayar kaynak bütçesi, veri gizliliği/lisans.
3. `docs/risk-ve-dogrulama-matrisi.md`: kirli CAD, ölçek, Layer0, büyük OCR, model JSON, RAG eşanlam, UI/SSE/3D hız riskleri için fail-closed B planları; metinlerde iddia edilen %94, 300ms, 60FPS, VRAM 2.7 GB, kappa/Recall gibi sayılar **henüz doğrulanmış sonuç değildir**.
4. `docs/uygulama-yol-haritasi.md`, `docs/ozellik-envanteri.md`, `docs/planlanan-dosya-yapisi.md`, `docs/kapsam.md`, `docs/sistem-mimarisi.md`, README ve karar defteri yeniden uyarlanır; tarihsel notlar silinmez.
5. 020 yeniden planlama kaydı olduğundan **Windows offline installer çalışması 021'e taşınır**; büyük çizim/doğruluk, RAG ve eğitim modülleri kademeli yeni sıra alır. Numaralar yalnız plan, o işlem kodlanana kadar GitHub belgesi var sayılmaz.

## 4. Sabit güven ve bilimsel kısıtlar

- Otomatik kapı boyu histogramından metre kalibrasyonu **INFERRED**, açık kapı köprüleme/snap yalnız **VIRTUAL/CANDIDATE** katmanıdır: gerçek ölçüm/oda semantiği/geçiş ve kesin PASS üretmez.
- VLM ölçüm ve hukukî mevzuat kararı vermez; RAG benzerlik hukuken yürürlük onayı değildir; bir jüri personası bağımsız, gerçek mimar/uzman görüşü değildir.
- Vektör PDF'nin OCR gereksinimi bölgesel olabilir; tüm vektör sayfada OCR'ı toptan kapatma varsayılmaz. Karo tabanlı OCR'da kaynak bbox/crop/orientation geri dönüştürme şarttır.
- Tek GPU/CPU budgets ve GGUF+mmproj uyumu donanım üzerinde ölçülmeden *kesin* süre/VRAM ve %0 hata iddiası yoktur. Ayrıntılı paket, geçiş lisans/TS standardı yeniden dağıtım hakları ayrıca kontrol edilir.
- Gerçek hukukî kaynak, yürürlük ve uzman kabulü mevcut F08–F12 **HUKUKI_HOLD** durumunu korur.

## 5. Kapanış kaydı

Gerçek eklenen belgeler, değişen envanter satırları/roadmap ve GitHub commit SHA ile okuma/bağlantı denetimi **son GitHub yazımı olarak bu dosyaya** eklenecek. Bu dokümantasyon-only işlemde kod regresyon testi çalıştırıldıysa gerçek sonuç; çalıştırılmadıysa açıkça belirtilir.
