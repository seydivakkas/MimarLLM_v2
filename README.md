# MimarLLM V2

**Durum:** Ürün kapsamı kesinleşti; teknik tasarım hazır; henüz çalışan uygulama yok.

**MimarLLM V2, mimari teknik çizim analizi ve hata tespiti için tamamen yerel bir yazılım olarak geliştirilecektir.** Çizimden alınan geometri ve ölçülebilir teknik veriler, deterministik kontrollerle incelenecek; sorunlar dosya konumu, gerekçe ve kanıtlarıyla raporlanacaktır.

Mevcut [MimarLLM V1](https://github.com/seydivakkas/MimarLLM) fikirlerinden yararlanan ama ondan **bağımsız, yeni** bir projedir. V1 kodu/veritabanı/commit geçmişi yeni depoya doğrudan kopyalanmaz.

## Değişmez ilkeler

- **Tamamen yerel inference.** OpenAI, Gemini, Anthropic vb. bulut yapay zekâ API'si veya ücretli servis zorunluluğu yok.
- **Hedef makine:** Windows, NVIDIA RTX 4070 **8 GB VRAM**, Intel Core i7 14. nesil ve 32 GB RAM.
- **Deterministik kararlar:** Ölçü, koordinat, geometri ve kurallar kodla doğrulanır; yerel OCR/VLM aday üretir, kendi başına teknik `PASS` vermez.
- **Kanıt ve belirsizlik:** Kaynak konumuna bağlanabilen bulgu, doğrulanmış ölçek/birim ve sürümlü karar izi.
- **Sadelik:** Tek kullanıcılı modüler monolit. Multi-agent altyapısı ve gereksiz ayrı servisler yok.
- **Gizlilik:** Public depoya özel çizimler, veritabanları, model ağırlıkları veya gerçek kimlik bilgileri eklenmez.
- **Güvenilirlik:** Çalıştırılmamış özellikler/testler veya ölçülmemiş performans tamamlanmış gösterilmez.

## İlk ürünün dışında

**Pedagojik eğitim portalı**, LMS, öğrenci/öğretmen/sınıf yönetimi, jüri karakterleri, otomatik not verme, üretken mimari tasarım, çoklu AI agent orkestrasyonu ve bulut tabanlı çıkarım.

## Belgeler ve geliştirme izleri

Her yeni AI destekli geliştirme isteği uygulanmadan **önce** `docs/islem_NNN.md` dosyasına kaydedilir. İş sonunda gerçekten yapılan değişiklikler, commit'ler ve doğrulama sonucu aynı kayda eklenir.

- [İşlem 001 — Başlangıç ve kayıt protokolü](docs/islem_001.md)
- [İşlem 002 — Ürün kapsamı ve teknik plan](docs/islem_002.md)
- [Ürün kapsamı](docs/kapsam.md)
- [Teknik gereksinimler](docs/teknik-gereksinimler.md)
- [P0–P10 modül planı](docs/modul-plani.md)
- [Karar defteri](docs/kararlar.md)

## Öngörülen ilk çalışan sürüm

Önerilen sıra: `DrawingIR -> DXF -> geometri ve topoloji -> deterministik teknik kontroller -> çizim üzerinde bulgu -> yerel rapor`. Yerel OCR, VLM ve ek dosya formatları daha sonra bu çekirdeği genişletecek. **DXF'nin ilk desteklenecek format olması öneridir, henüz kesin ürün kararı değildir.**

**Henüz yok:** Kaynak kodlu analiz motoru, kurulu model, çalışan kullanıcı arayüzü, gerçek donanım benchmark'ı veya Windows kabul testi.

## İşlem 003 — Mevzuat kanıtı ve yerel OCR tasarımı

MimarLLM V2, çizimdeki ölçülebilir hata/eksikliklere ek olarak **özgün mevzuat kaynağını sayfa ve sayfa içi metin alanıyla gösterebilen** bir kanıt sistemi hedefliyor. Mevzuat araması kaynak belgelerin madde/fıkra/bent/tablo hiyerarşisinde yerel ve hibrit olarak yapılacak; kuralların uygunluk kararı ise deterministik motor ve doğrulanmış yürürlük/bağlam verisine bağlı olacak.

- **Mevzuat hedef aileleri:** Planlı Alanlar İmar, Yangın, Otopark, Sığınak ve Binalarda Enerji Performansı. Belgelerin güncelliği/yürürlük/dağıtım hakları ayrıca incelenecek.
- **OCR:** Önce dijital PDF native text; düşük bellekli yerel OCR; karmaşık taranmış belge için [Baidu Unlimited-OCR](https://github.com/baidu/Unlimited-OCR) ana **benchmark adayı**. Windows 8 GB VRAM uyumu henüz ispatlanmadı.
- **Bellek:** Ağır OCR ve VLM GPU'da aynı anda çalışmaz; ayrı süreçli phase-lock ve CPU fallback.
- **Kanıt ekranı:** Solda çizim nesnesi/ölçü, sağda özgün mevzuat sayfasındaki vurgulu metin ve sürüm/istisna bağlantıları. OCR'dan türetilen satır numarası resmî satır numarası olarak gösterilmez.
- **Lisans/gizlilik:** Gerçek mevzuat PDF'leri, model ağırlıkları ve kullanıcı çizimleri yerelde; public repo yalnız kod, şemalar ve sentetik testler.

**Yeni belgeler:** [İşlem 003](docs/islem_003.md) · [Sistem mimarisi](docs/sistem-mimarisi.md) · [OCR ve VRAM](docs/ocr-ve-bellek.md) · [Mevzuat RAG](docs/mevzuat-rag.md).

**Durum:** Tasarım ve dokümantasyon işlendi; kod, indeks, Windows model testi veya hukukî `PASS` uygulanmadı.

## Güncel OCR kararı — İşlem 004

**Varsayılan:** DXF için doğrudan CAD metni, PDF için PyMuPDF native text, okunamayan/taranmış ROI'lerde **RapidOCR + ONNX Runtime CPU**. 8 GB VRAM VLM için bırakılır. 0/180 sınıflandırıcı, eğik/90/270 çizim metninin hatasız tanınması demek değildir; gerekli ROI rotasyonu ve source quad dönüşümü tasarlanmıştır.

**Unlimited-OCR:** varsayılan OCR motoru olmaktan çıkarıldı; yalnız opsiyonel araştırma. **Mevzuat:** ayrı yerel offline ETL fazında kaynak PDF -> text/OCR -> tablo -> LegalAST -> FTS5 + CPU embedding; özgün sayfa/bbox kanıtı korunur.

- [İşlem 004 — OCR değişikliği ve işlem günlüğü](docs/islem_004.md)
- [Mimari pafta OCR ve kaynak koordinatı tasarımı](docs/ocr-mimari-pafta.md)

Kod, model kurulumu veya Windows benchmark'ı **henüz gerçekleştirilmedi**.
