# İşlem 020 — MimarLLM V2 × ARCH-CORE Local: Kapsam ve Mühendislik Yol Haritası Yeniden Yapılandırması

- **Tarih:** 2026-10-15
- **Durum:** UYGULANDI / KAPATILDI — Kullanıcının üç plan metninden mevcut MimarLLM V2 kodunu koruyan, ARCH-CORE Local eğitim/3D gelecek katmanını opsiyonelleştiren master mimari, özellik statüsü, risk/kabul, 2209-A ve 021–031 sıra revizyonu. **Dokümantasyon-only**: yeni 3D/jüri/VLM/kurtarma kodu yazılmadı; hukukî HOLD devam.
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

## 5. Gerçek GitHub uygulama kaydı ve kabul

**GitHub değişiklik sırası:** İşlem 020'nin **ilk GitHub yazımı** `docs/islem_020.md` oluşturma commit'i **`8b31c1d143e349f5722c6a79d472d4058a58be03`**. Daha sonra aşağıdaki master ve destek belgeleri, envanter ve README değiştirildi. İşlem 001–019 kayıtları **değiştirilmedi**. **Son GitHub yazımı bu dosyanın kapanış güncellemesidir**.

### 5.1. Oluşturulan yeni belgeler

| Dosya | GitHub gerçek commit | Çıktı |
| --- | --- | --- |
| `docs/islem_020.md` | `8b31c1d` | Kapsam/ilk yazım iş günlüğü |
| `docs/master-mimari-arch-core-local.md` | `0fe32fc0`; linkleri `59c0578a` | Çalışan V2 kaynaklı çekirdek + opsiyonel ARCH-CORE eğitsel 2.5D/VLM/jüri ve tek `src/mimarllm` |
| `docs/risk-ve-dogrulama-matrisi.md` | `c0f98f94` | CAD repair, unit, Layer0, A0 OCR, VRAM/grammar, RAG synonym, SSE/3D risk ve B planları |
| `docs/adr/ADR-004-ARCH-CORE-Local-Kapsam-Genislemesi.md` | `4222f8b4` | İlk teknik ürünün eğitim dışlamasının korunup ileri eğitim sürümünün opsiyonel eklenme kararı |
| `docs/tubitak-2209a-is-paketleri.md` | `8c4a8405` | Çekirdek bilimsellik, 12 aylık göreli örnek program, gerçek deney ve onam/HOLD metodolojisi |

### 5.2. Güncellenen mevcut belgeler (kaynak kodu değil)

| Dosya | Gerçek commit | Karar |
| --- | --- | --- |
| `docs/uygulama-yol-haritasi.md` | `56ec944f`; ``1152f8de` | 020–031 işlemleri, eski 007–019 tarihçesini koruma, F20 Windows paket 021 |
| `docs/planlanan-dosya-yapisi.md` | `d4a3075a` | Gerçek paket `src/mimarllm`, dosyalar MEVCUT vs PLAN, ARCH-CORE/backend ikinci paket reddi |
| `docs/ozellik-envanteri.md` | `7c77c87c`; `e2479ae3` | F01/F03/F04/F20/F21/F22/F23 durum düzeltmeleri, yeni F25–F37 stabil hedef kimlikleri |
| `docs/kapsam.md` | `ec43cb65` | Engineering Core ilk ürün korunur, ARCH-CORE Studio/Education ileri sürüm |
| `docs/sistem-mimarisi.md`, `docs/modul-plani.md`, `docs/teknik-gereksinimler.md` | `34f97906`, `994cf419`, `dbac97ad` | Eski “TASARIM, kod yok, pedagojik kesin kapsam dışı” cümlelerinin tarihsel olduğuna dair güncel yönlendirme |
| `docs/windows-dagitim-plani.md` | `6bbf0d8e` | Windows offline onedir/wheelhouse/SBOM uygulaması 021'e ertelenmiş hedef |
| `docs/kararlar.md` | `718cb952` | K-157–K-171 kaynak-güvenli mimari, araştırma ve hukukî HOLD kararları |
| `README.md` | `3c1ab6da`; `96bd6c83` | Eski kod-yok tutarsızlıkları giderildi; gerçek kod, yerel CLI/dashboard, yeni plan/HOLD ve ADR/2209 bağlantıları |

### 5.3. Doğrulama ve geriye uyumluluk

- **Kapanış öncesi read-only GitHub ağaç kontrolü:** 125 gerçek tracked dosya; İşlem 020 öncesi 120 dosyadan **5 yeni belge** eklenmiştir. 15 ana belge/README yolu ve içlerindeki yerel Markdown bağlantıları kontrol edildi: **0 kayıp relative link**.
- **Kod değişikliği yok:** `src/mimarllm`, `tests/`, `pyproject.toml` veya `.github/workflows` bu işlemde değiştirilmedi. Bu yüzden **İşlem 020 için yeni Python/CI test sonucu yoktur**; sentetik regresyon İşlem 019'un [GitHub Actions 38557404737](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38557404737) kaydındaki **Ubuntu 295 PASS, Windows 295 PASS** sonucudur. Bu önceki koşudur; yeni ARCH-CORE işlevlerini test etmez.
- **Kaynaklar:** Kullanıcı tarafından iletilen üç metindeki ARCH-CORE yerel model, darboğaz ve klasör önerileri plan/girdi olarak değerlendirildi; benchmark sayı/performans ve yönetmelik örnekleri resmî onaylanmış gerçek olarak GitHub'a taşınmadı.
- **Korunan:** DrawingIR v0.1 kaynak SHA/page/quad/CAD handle, asıl rapor kanıt zinciri, yalnız reviewed passage, `REGULATORY_LOCKED`, F08–F12 `HUKUKI_HOLD`, sıfır harici AI API ve Windows-first tasarım.
- **Sonraki işlem:** `docs/islem_021.md` **henüz açılmadı**. İlk kod değişikliğinden önce **bu dosya ilk GitHub yazımı olarak** oluşturulmalı. Öncelik Windows offline dağıtım `onedir/wheelhouse/SBOM`. Kirli CAD/A0 OCR/LLM/2.5D/jüri hedefleri `islem_022–031`; gerçek saha/hukukî/TÜBİTAK bilimsel kabul finalde.

**Kapanış statüsü:** ARCH-CORE Local yeniden planlama ve proje dokümantasyon senkronizasyonu **TAMAMLANDI**. Yeni üretim fonksiyonu, hukukî kaynak ve özgün akademik test hedefi **henüz TAMAMLANMADI**.
