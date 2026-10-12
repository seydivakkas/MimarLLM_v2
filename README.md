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
