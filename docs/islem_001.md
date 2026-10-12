# İşlem 001 — Proje yönü, yerel çalışma ilkeleri ve kayıt düzeni

- **Tarih:** 2026-10-12
- **İstek:** Mevcut MimarLLM'den ilham alan, ancak sıfırdan geliştirilecek MimarLLM V2 için sade dosya düzeni oluşturulması; her geliştirme isteğinin uygulanmadan önce `docs/islem_XXX.md` olarak kayda geçirilmesi; tamamen yerel AI/VLM ve deterministik karar motoruna uygun kapsamın yeniden değerlendirilmesi.
- **Kaynak proje:** `seydivakkas/MimarLLM` (referans; kod ve veritabanları doğrudan kopyalanmayacak).
- **Hedef depo:** `seydivakkas/MimarLLM_v2`
- **Durum:** Kapsam tartışması / başlangıç. Kod uygulaması henüz başlatılmadı.

## 1. Kullanıcının kesin gereksinimleri

1. **Tek bilgisayar, offline-first:** Windows ortamı; NVIDIA RTX 4070 8 GB VRAM, Intel i7 14. nesil ve 32 GB RAM hedefi.
2. **Sıfır yapay zekâ API'si:** Gemini, OpenAI, Anthropic, çevrim içi inference ve gizli bulut fallback'i olmayacak. Model çıkarımı yerel.
3. **Basit mühendislik dili:** Gereksiz çoklu AI agent/orkestrasyon tasarımı ve böyle bir izlenim uyandıran klasör adları kullanılmayacak.
4. **Önce işlem kaydı:** Her yeni AI destekli geliştirme isteği, uygulanmadan önce benzersiz ve artan numaralı `docs/islem_XXX.md` dosyasına yazılacak.
5. **Ürün kapsamı henüz açık:** V1'deki pedagojik eğitim portalı, öğrenci takip sistemi, jüri simülasyonu ve diğer hedefler otomatik devralınmayacak.
6. **Deterministik karar önceliği:** Ölçek, ölçü, geometri ve kural uygunluğu kararları VLM serbest metnine bırakılmayacak.
7. **Güvenli public depo:** Gerçek proje dosyaları, kullanıcı verileri, yerel veritabanları, model ağırlıkları, token/parolalar ve çalışma çıktıları Git'e alınmayacak.

## 2. Önerilen çekirdek ürün (KESİNLEŞMEDİ)

**Yerel Mimari Çizim Analizi ve Kanıt Tabanlı Değerlendirme Sistemi.**

- Girdi: öncelikle DXF ve dijital PDF; raster PNG/JPEG ikinci iş paketi; DWG/IFC yalnızca ayrıca kararlaştırılırsa.
- İşleme: dosya çözümleme -> birim/ölçek onayı -> geometrik/topolojik temsil -> yerel OCR/VLM ile semantik aday -> deterministik kural denetimi -> kanıtlı rapor.
- Sınır: VLM önerir; çizim, ölçüm ve kaynak olmadan nihai uygunluk hükmü oluşturmaz.
- Bilinmeyenler ayrı ifade edilir: `PASS`, `FAIL`, `INSUFFICIENT_EVIDENCE`, `NOT_APPLICABLE`, `REVIEW_REQUIRED`, `ERROR`.
- Kaynak sürümü, kural sürümü, girdi hash'i ve hesaplama izleri saklanır.
- Hukukî uygunluk, doğrulanmış ve yürürlük bilgisi bulunan kural seti olmadan sertifikasyon iddiasına dönüşmez.

## 3. Ürün kapsamı için karar bekleyen seçenekler

| Seçenek | Ürün yönü | İlk sürümdeki durumu |
| --- | --- | --- |
| A | Mimari teknik çizim inceleme ve raporlama aracı | **Önerilen çekirdek** |
| B | Mimarlık öğrencilerine geri bildirim ve jüri provası | Opsiyonel sonraki modül |
| C | Yönetmelik / standart uyum denetimi | Kaynağı doğrulanınca aşamalı |
| D | Tam pedagojik eğitim portalı / LMS | V2 başlangıç kapsamı dışında |
| E | Mimari tasarım üreten genel AI asistanı | Başlangıç kapsamı dışında |

Bu seçenekler, kullanıcıyla konuşulup kesinleştirilmeden kapsam kabulü yapılmaz.

## 4. Sade dosya düzeni — ÖNERİ

```text
MimarLLM_v2/
  README.md
  .gitignore
  pyproject.toml
  docs/
    islem_001.md
    islem_002.md
    kararlar.md
    kapsam.md
  src/mimarllm/
    importers/       # DXF/PDF/raster dosya okuma
    geometry/        # Ölçüler ve topoloji
    vision/          # Yerel OCR/VLM ve aday çıkarımı
    rules/           # Sürümlü deterministik kurallar
    evidence/        # İddia, kaynağı, durum ve gerekçe
    reports/         # Çıktı biçimleri
    storage/         # SQLite, proje ve sonuç deposu
    api/             # Aynı bilgisayarda localhost API
  app/               # Yerel kullanıcı arayüzü (teknoloji kesinleşmedi)
  config/            # Modellerin sürüm kimlikleri, kurallar
  scripts/           # Kurulum ve yerel çalıştırma
  tests/             # Sentetik fikstürler ve sözleşme testleri
```

Bunlar planlanan klasörlerdir; kaynak kodun yazılmış olduğunu göstermez. Henüz doğrulanmayan kapsam için boş modül/ajan dosyaları oluşturulmaz.

## 5. İşlem kayıt protokolü

Her kullanıcı isteği için:
1. Son kayıt numarasını oku; yeni `docs/islem_NNN.md` oluştur.
2. İsteğin özeti, gerekçe, hedef, kapsam dışı maddeler, etkilenebilecek dosyalar, kabul koşulları ve açık kararları yaz.
3. Durumu `PLANLANDI`, `DEVAM_EDİYOR`, `UYGULANDI`, `BEKLEMEDE`, `İPTAL` olarak izle.
4. Ancak bu kayıt oluştuktan sonra ilgili kaynak kod veya yapılandırma üzerinde değişiklik yap.
5. Sonunda gerçekten yapılan değişiklikler, commit ve çalıştırılmış kontrollerle kayıt güncelle; yapılmayan işi yapılmış olarak gösterme.
6. Bir isteğin tamamlanması kullanıcıdan yeni istek gelmesi için zorunlu değildir. Yine de numaralar artan, çakışmasız ilerler.
7. Kamuya açık kayıtlara gizli veri, kullanıcıya ait ham çizimler veya kimlik bilgileri eklenmez.

## 6. Teknik ilkeler

- **Modüler monolit:** Tek kurulum, tek bilgisayar, mümkün olan en az servis.
- **Model yönetimi:** 8 GB VRAM içinde model belleği bütçesi; gerektiğinde sırayla yükle/boşalt. Model performansı benchmark ile doğrulanmadan kesinleştirilmez.
- **Çizim doğruluğu:** Ölçek tahmini kesin ölçüm değildir. DXF birimi, kalibrasyon ve belirsizlik raporlanır.
- **Karar ayrımı:** Geometrik gerçekler / heuristik adaylar / öznel mimari yorum farklı seviyelerde tutulur.
- **Localhost güvenliği:** Varsayılan erişim loopback; dosya yolları ve yerel saklama güvenlik kontrolleri.
- **Lisans:** Modeller, OCR, DWG dönüştürücü ve üçüncü taraf bileşenlerin lisansı ayrı doğrulanacak.

## 7. Bu işlemde yapılanlar ve açık işler

**Tamamlanan:**
- Yeni deponun GitHub üzerinden varlığı ve boş olduğu doğrulandı.
- Deponun **public** olduğu görüldü; bu bilgi kullanıcıya bildirildi.
- İstek, çalışma protokolü ve ilk ürün seçenekleri belgelendi.

**Yapılmadı:**
- Uygulama kodu, model kurulumu, arayüz, benchmark ve güvenlik testleri.
- V1 dosyalarının V2'ye kopyalanması.
- Ürün kapsamının kesinleştirilmesi.

**Sonraki kararlar:**
1. V2 öncelikle kim için? Mimar, mimarlık öğrencisi, akademisyen veya teknik ofis?
2. İlk sürümde ölçülebilir kullanım senaryosu nedir?
3. İlk kabul edilen girdi formatları hangileri?
4. Jüri provası ve mevzuat değerlendirmesi çekirdekte mi, sonradan mı?
5. Windows arayüzü masaüstü mü, localhost web arayüzü mü?

> Bu belge, uygulamadan önce oluşturulan ilk işlem kaydıdır. Kararlaştırılmamış özellikleri tamamlanmış göstermez.

## 8. Uygulama kaydı — güvenli dokümantasyon iskeleti

**Uygulanan değişiklikler (2026-10-12):**
- `docs/islem_001.md`: istek ve karar prosedürü, geliştirme öncesinde oluşturuldu (commit `6621539`).
- `README.md`: bağımsız V2'nin taslak ürün tanımı; kesin ilkeler ve ürün seçenekleri (commit `9114386`).
- `.gitignore`: yerel veritabanları, özel çizimler, model ağırlıkları ve kimlik bilgilerine yönelik varsayılan dışlama listesi (commit `5ce0fbf`).
- `docs/kararlar.md`: kesin ve tartışılan kararların ayrımı (commit `7328a76`).
- `docs/kapsam.md`: kullanım alanları, kapsam ve hariç tutulan konular (commit `fb16d49`).

**Bilinçli olarak yapılmayan:** `src/` altında boş teknik modüller, çoklu ajan şablonları, bağımlılık kurulumu, model ağırlıkları, gerçek veriler ve işlev varmış izlenimi veren örnek kod oluşturulmadı. Bunlar ancak ürün kapsamı netleştikten sonra kendi işlem kayıtlarıyla ele alınacak.

**Kontrol:** GitHub yazma işlemleri commit SHA üretti; yerel Windows çalıştırma veya test yapılmadı. `.gitignore` halihazırda Git'e izlenen bir sırrı gizlemez, bu nedenle git diff/secret taraması ayrıca gereklidir.

**Son durum:** Başlangıç dokümantasyonu oluşturuldu, kapsam kararı bekleniyor.
