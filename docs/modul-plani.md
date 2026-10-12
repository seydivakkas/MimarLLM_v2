# MimarLLM V2 — Aşamalı Modül ve İş Paketleri Planı v0.1

- **Bağlı işlem:** [islem_002.md](islem_002.md)
- **Bağlı gereksinimler:** [teknik-gereksinimler.md](teknik-gereksinimler.md)
- **Tarih:** 2026-10-12
- **Durum:** **PLANLANDI** (uygulama kodu yok)
- **Kesin ürün:** Mimari teknik çizim analizi ve hata tespiti
- **Kesin dışlama:** Pedagojik portal, LMS, çok ajan, otomatik jüri/puan, bulut AI API

## 1. Tek bilgisayarlık yazılım mimarisi

```text
Yerel kullanıcı arayüzü (tek kullanıcı, teknoloji henüz seçilmedi)
               |
        AnalysisService
               |
       [Dosya içe alma]
               v
          DrawingIR
               |
        +------+-------+
        |              |
     Geometri        Vision
     Topoloji         OCR + VLM
        |              | yalnız öneri/aday
        +------+-------+
               |
     Deterministik kurallar
               |
        Evidence / Findings
               |
     Çizim işaretleme + Rapor
               |
        Yerel depolama
```

**Mimari karar:** Kullanıcının bilgisayarında çalışan **modüler monolit**. Diyagramdaki modüller bağımsız ağ servisleri veya AI ajanları değildir. Yerel OCR/VLM kurulmamışken DXF temelli teknik kontroller çalışabilmelidir.

## 2. Asgari önerilen kod yapısı (henüz oluşturulmadı)

```text
MimarLLM_v2/
├── README.md
├── .gitignore
├── docs/
│   ├── islem_001.md
│   ├── islem_002.md
│   ├── kararlar.md
│   ├── kapsam.md
│   ├── teknik-gereksinimler.md
│   └── modul-plani.md
├── src/mimarllm/
│   ├── core/          # DrawingIR, durumlar, analiz koordinasyonu
│   ├── importers/     # DXF/PDF/raster, koordinat ve birim
│   ├── geometry/      # Geometri, alan, topoloji ve uzamsal indeks
│   ├── rules/         # Deterministik denetim kuralları
│   ├── evidence/      # Bulgu/kanıt kaynak ilişkileri
│   ├── vision/        # Yerel OCR ve VLM; opsiyonel
│   ├── reports/       # İşaretleme ve çıktı
│   └── storage/       # Yerel geçmiş ve dosya referansları
├── app/               # Seçilecek tek kullanıcı arayüzü
├── config/            # Versiyonlanmış güvenli kural/format ayarları
├── scripts/           # Yerel kurulum ve çalışma betikleri
└── tests/             # Sentetik fixture / sözleşme / tekrar üretilebilirlik
```

`src`, `app`, `config`, `scripts`, `tests` klasörlerini henüz sırf görünmeleri için eklemeyeceğiz. İlk kod işi `islem_003.md` ile kayıt altına alınmadan başlamayacak.

## 3. Modül sorumluluk ve çıktı sözleşmeleri

| Modül | Girdi -> Çıktı | Kesin görevi | Yapmaması gereken |
| --- | --- | --- | --- |
| `core` | İş isteği -> `DrawingIR` / analiz kaydı | Sürüm, görev, durum, dönüşümler ve çağrı sırası | Sınırsız arka plan ajanı |
| `importers` | Dosya -> ham vektör/metin/kare | Tür, sayfa, layer, kaynak koordinatı, birim | Ölçek tahminini kesin ölçüm sayma |
| `geometry` | `DrawingIR` -> geometrik ölçüm ve ilişkiler | Poligon/oda/komşuluk, kesişim, açıklık adayları | Mevzuat hükmü üretme |
| `vision` | Yerel image crop -> OCR/VLM adayı | Etiket/metin/nesne semantiği | Otomatik teknik `PASS` |
| `rules` | Doğrulanmış özellik + kural -> sonuç | Sabit algoritma, eşik, tolerans, uygulanabilirlik | Eksik veriyi başarı sayma |
| `evidence` | Sonuçlar -> izlenebilir `Finding` | Kaynak, gerekçe, belirsizlik, karar kaydı | Kanıtsız sonuca kesinlik ekleme |
| `reports` | Bulgular -> çizim üstü işaret + dosya | JSON ve okunabilir rapor | Üretilmemiş ölçü ekleme |
| `storage` | Yerel iş kaydı -> SQLite/yerel dosya | Güvenli tek kullanıcı proje geçmişi | Gizli veriyi Git'e sokma |
| `app` | Kullanıcı etkileşimi -> analiz iş akışı | Dosya seç, incele, onayla, indir | Kimlik/öğrenci yönetimi kurma |

**Arayüz seçimi beklemede:** önce bağımsız Python çekirdeği; UI ancak çekirdek sözleşmesi oturduğunda. İlk sürümde çift arayüz geliştirilmez.

## 4. İş paketleri

### P0 — Kapsam ve tasarım sözleşmesi (BU İŞLEM)

**Kapsam:** ürün kararı, FR/NFR, modül bağımlılıkları, kayıt politikası.
**Çıktı:** `docs/islem_002.md`, `docs/teknik-gereksinimler.md`, `docs/modul-plani.md`, güncel `README.md`, `docs/kapsam.md` ve `docs/kararlar.md`.
**Kabul:** dosyalar gerçekten depoda; kararlar ile öneriler karıştırılmıyor; kodun yazıldığı iddia edilmiyor.
**Durum:** Dokümantasyon oluşturma aşaması; son işlem kaydında doğrulanacak.

### P1 — Çekirdek veri sözleşmesi ve koordinat modeli

**Gereksinimler:** FR-002/004/009, NFR-005/006/012.
**Kod alanı (plan):** `core/`, `tests/`.
**İş:** `DrawingIR`, `Entity`, `CoordinateFrame`, `ScaleEvidence`, `Finding` sözleşmeleri; birim/koordinat dönüşümleri; kaynağı koruma; analiz durumları.
**Çıktı:** sürümlenmiş şema ve salt sentetik fixture'larla tekrarlanabilir örnek JSON.
**Kabul:** farklı koordinat birimlerinin sessiz karışması engellenir; kaynağı olmayan `FAIL` kaydedilemez.
**Bağımlılık:** P0.

### P2 — DXF dosya alımı ve temel doğrulama

**Gereksinimler:** FR-001/002/003/004/005.
**Kod alanı:** `importers/dxf.py`, `core/`.
**İş:** DXF okuyucu, katman/handle/entity, ölçü yazıları, blok/INSERT ve dönüşümler; bozuk dosya davranışı; `$INSUNITS` ve kullanıcının kalibrasyonu.
**Çıktı:** `DrawingIR` vektör verisi, layer/nesne özeti, kaynak konumları.
**Kabul:** test DXF'lerinde köken ve dönüşüm doğrulanır; belirsiz birim `UNKNOWN` kalır. `bounding_box` büyüklüğünden kesin birim çıkarılmaz.
**Bağımlılık:** P1.
**Not:** DXF'nin ilk format olması teknik öneridir; format kapsamı sonraki işlemde kesinleştirilecek.

### P3 — Geometri bütünlüğü ve mekânsal topoloji

**Gereksinimler:** FR-006/007, NFR-005/006.
**Kod alanı:** `geometry/`.
**İş:** segment normlama, birleştirme, kesişim, snap toleransı, kopuk/kesişen sınır, poligon/oda adayları, kapı/duvar eşleştirmesi, komşuluk grafı.
**Çıktı:** ölçülebilir feature + topoloji grafı + izlenebilir problem adayları.
**Kabul:** sentetik çokgen, açık sınır ve toleranslı duvar vakalarında beklenen geometrik ilişkiler üretilebiliyor.
**Bağımlılık:** P2.

### P4 — İlk deterministik kural paketi

**Gereksinimler:** FR-008/009, NFR-005/006.
**Kod alanı:** `rules/`.
**İş:** önce geometri bütünlüğü kuralları: sıfır uzunluk, mükerrer eleman, açıklık/kopuk sınır, çelişkili etiket/ölçü ve çözülemeyen oda sınırı. Kullanılacak tam set ve toleranslar geliştirme kaydında dondurulur.
**Çıktı:** `CheckResult` / uygulanabilirlik / kaynak kimliği / tolerans / gerekçe.
**Kabul:** sabit sentetik çizimlerde aynı kurallar aynı bulguları üretir; `INSUFFICIENT_EVIDENCE` ve `NOT_APPLICABLE` ayrıdır.
**Bağımlılık:** P3.

### P5 — Kanıt zinciri, rapor ve minimal inceleme

**Gereksinimler:** FR-009/010/011/012/018, NFR-006/011.
**Kod alanı:** `evidence/`, `reports/`, `app/` (arayüz biçimi o zaman seçilir).
**İş:** bulgu listesi, plan üzerinde işaretleme, kullanıcı düzeltmesi, JSON/HTML çıktı ve temel yerel arayüz.
**Çıktı:** ilk uçtan uca **AI modeli olmadan** çalışan DXF örneği.
**Kabul:** kullanıcı seçtiği DXF'den koordinatlı teknik problem listesine ulaşır ve her bulgunun dayandığı veriyi görür.
**Bağımlılık:** P4.

### P6 — PDF ve raster işleme altyapısı

**Gereksinimler:** FR-001/013.
**Kod alanı:** `importers/pdf.py`, `importers/image.py`, `core/`.
**İş:** vektörel PDF sayfa/path ve raster sayfa ayrımı; PDF noktası/piksel/dünya birimi dönüşümü; eğiklik/dönüş/çözünürlük bilgisi.
**Çıktı:** sayfa/konum referanslı girdi.
**Kabul:** kalibrasyon yoksa raster pikselden fiziksel alan hükmü verilmez.
**Bağımlılık:** P1, P5 ile entegre.

### P7 — Tamamen yerel OCR

**Gereksinimler:** FR-013/015, NFR-001/002/003.
**Kod alanı:** `vision/ocr.py`.
**İş:** yerel OCR motoru seçimi ve lisans taraması; metin ve ölçü yazısının koordinatlı çıkarımı; yazı birimi doğrulama.
**Çıktı:** `TextCandidate` bbox + tanıma belirsizliği + sayfa kaynağı.
**Kabul:** sentetik etiketlerde yeniden üretilebilir koordinat dönüşümü; okunamayan değer kesin ölçü sayılmaz.
**Bağımlılık:** P6.

### P8 — Yerel VLM (isteğe bağlı semantik doğrulama yardımcısı)

**Gereksinimler:** FR-014/015, NFR-001/002/003/004.
**Kod alanı:** `vision/vlm.py`, `config/`.
**İş:** küçük/nicemlenmiş VLM adaylarının lisans ve Windows/CUDA uyumunu kontrol; model sürüm pinleme; ROI/crop ile kontrollü görsel çıkarım; JSON aday şeması.
**Çıktı:** önerilen eleman etiketi ve görsel referans; kesin ölçü/kural hükmü yok.
**Kabul:** model olmadan sistem bozulmaz; model çıktısı doğrulama katmanına bağlı; 8 GB VRAM'de gerçek ölçüm yapılır.
**Bağımlılık:** P5/P6/P7. P4 motorunu değiştirmeden eklenir.
**Not:** Model adı veya performansı henüz seçilmiş/doğrulanmış değildir.

### P9 — Kullanışlı Windows arayüzü ve yerel geçmiş

**Gereksinimler:** FR-010/011/017/018, NFR-007/009.
**Kod alanı:** `app/`, `storage/`.
**İş:** projeler, yükleme, çizim görüntüleme, bulgular, kullanıcı onayı, sonuç geçmişi, rapor aktarma; tek kullanıcı.
**Çıktı:** basit ve kanıta erişimi öne çıkaran uygulama.
**Kabul:** hesap/LMS/jüri ekranları yok; kullanıcı tüm yerel kayıtlarını bulabiliyor.
**Bağımlılık:** P5, P8 isteğe bağlı.

### P10 — Paketleme, bağımsız doğrulama, performans ve lisans kabulü

**Gereksinimler:** NFR-001…012.
**Kod alanı:** `scripts/`, `tests/`, teslim belgeleri.
**İş:** Windows offline dağıtım; CPU/GPU bellek/latency baseline; tekrarlanabilir sentetik set; gizli bilgi taraması, third-party lisans; gerçek mimari çizimlerde kullanıcı izinli değerlendirme.
**Çıktı:** paket ve doğrulama raporları.
**Kabul:** açıkça tanımlanmış gerçek donanım testleri ve hatalar kayıt altına alınır; başarılmayan maddeler `HOLD` olarak kalır.
**Bağımlılık:** geliştirme modülleri.

## 5. İş paketi bağımlılık grafiği

```text
P0 -> P1 -> P2 -> P3 -> P4 -> P5 -> P9 -> P10
        \__________________-> P6 -> P7 -> P8 --/
                                   P8: isteğe bağlı semantik katman
```

Gerçek uygulama sırası örneği: **P1 sözleşme -> P2 DXF -> P3 geometri -> P4 kural -> P5 model gerektirmeyen MVP -> P6 PDF -> P7 OCR -> P8 VLM -> P9 arayüz tamamlanması -> P10 son kabul.** P6/P7/P8, erken deneme gerekirse paralel prototip olabilir; kanıt sözleşmesini atlayamaz.

## 6. Yol haritasında yönetilecek riskler

| Risk | Azaltma politikası |
| --- | --- |
| 8 GB VRAM'in yetmemesi | Tek seferde tek model, düşük çözünürlük/ROI, quantization, ölçüme dayalı bellek bütçesi ve CPU fallback |
| DXF katmanlarının standart dışı olması | Katman sadece hipotez; geometri/nesne ipuçları ve kullanıcı onayı |
| Kötü birim/ölçek | `UNKNOWN/CONFLICT` durumları, fiziksel ölçüm blokajı |
| Raster ölçüm belirsizliği | Kalibrasyon gerektiren kontrolleri otomatik kapat |
| Yanlış pozitif hata tespiti | Tolerans profili, kaynak konum, kullanıcı incelemesi |
| Mevzuat sürüm hatası | Kanıtlanmış metin/uygulanabilirlik olmadan resmî uyum PASS yok |
| VLM halüsinasyonu | Hipotez/aday şeması, geometriyle karşılaştırma, kesin hüküm yasağı |
| Her özelliği tek sürüme yığma | P5 sonunda model bağımsız çalışan minimum dikey dilim |
| Özel çizimlerin public repoya sızması | Sentetik örnekler, ignore + commit öncesi içerik taraması |
| Lisans belirsizliği | Bağımlılıkların lisans ve ticari kullanım izlerini P10 öncesinde tut |

## 7. Tek sonraki mühendislik adımı

**İşlem 003 önerisi:** `DrawingIR v0.1` + coordinate/units contract + ilk 5 geometrik kontrolün kesin gereksinimlerini belirleme. Bu işlem kayda alındıktan sonra kaynak kod ve sentetik fixture geliştirilecek.

Kullanıcının henüz kararlaştırmadığı UI/model/ilk format gibi konular **açık karar olarak korunur**; bu plandaki öngörüler tamamlanmış uygulama değildir.


## 8. İşlem 003 — Mevzuat ve OCR genişleme planı (v0.2 ek)

**Not:** `docs/islem_001.md` ve `docs/islem_002.md` işlem numaraları **değiştirilmeyecek**. İşlem 003 bu mimari kararın kaydıdır. `P0…P10` mühendislik paketleri ile `islem_NNN` GitHub işlem günlüğü **farklı numaralandırmalardır**.

### Yeni bağımlılıklar

```text
P1 DrawingIR -> P2 DXF -> P3 Geometri -> P4 Karar Kuralları
       |                                    |
       +--> P6 PDF -> P7 OCR --> R1 AST ---+--> R3 hukukî kaynak bağlama
                         |       |                  |
                         +--> R2 FTS5/Vector/RRF ---+
       +--> P8 yerel VLM (opsiyonel)                |
       +--------------------------------------------+--> P5/P9 kanıtlı arayüz/rapor -> P10
```

`P5` ilk model gerektirmeyen teknik denetim dikey dilimidir; `R1–R3` bu çekirdeğe **sonradan eklenecek** mevzuat yeteneğidir. Kullanıcının talep ettiği yan yana çizim/mevzuat kanıt ekranı, R3 tamamlandığında P9 arayüzüne entegre edilir.

| Ek paket | Somut teknik çıktı | Doğrulanacak kabul |
| --- | --- | --- |
| R0 Kaynak envanteri | 5 yönetmelik ailesi için özgün yayın/değişiklik/yerel izin envanteri | Güncel ve proje tarihindeki hükümler birbirine karışmıyor |
| R1 LegalAST + provenance | Madde/fıkra/bent/tablo/ek, page bbox, source_sha256, temporal version graph | OCR satırının özgün sayfa konumu ve kimliği kaybolmuyor |
| R2 Hibrid retrieval | FTS5 + CPU embedding + RRF; rerank optional | Arama adayları node/version ID ile dönüyor; retrieval legal PASS vermiyor |
| R3 Rules -> legal source | `RuleBinding`, uygulanabilirlik, exception, doğrulama kapısı | Resmî kaynak/sürüm/onay ve proje bağlamı yoksa `PASS` yok |
| P7-GPU kapısı | Phase-lock: ayrı OCR/VLM subprocess, GPU admission, fallback | RTX 4070 8 GB'da gerçek kaynak ölçümü tamamlanmadan “destekleniyor” iddiası yok |
| P9 kaynak ekranı | Çizimde entity highlight + özgün PDF sayfa/bbox highlight | Bir bulgudan iki belgenin gerçek konumuna geri gidiliyor |

### İlk MVP'nin geciktirilmemesi

Önce DXF'de **G0/G1 geometri hatalarını** güvenilir bulalım. Ardından belge kaynaklarını yapısal biçimde alıp hukukî konum eşlemesini ve sürüm grafını oluşturalım. İlk onaylı teknik mevzuat kuralı ancak bu iki veri kanalı birlikte doğrulandığında uygulanır. Önceden örneklenen kapı/koridor eşikleri **üretim mevzuatı olarak sabitlenmez**.

### Güncel taslak dizin sorumlulukları

- `src/mimarllm/core/`: DrawingIR ve birimler
- `src/mimarllm/importers/`: DXF, PDF ve raster
- `src/mimarllm/geometry/`: geometrik kontrol ve topoloji
- `src/mimarllm/vision/`: OCR/VLM/scheduler; tek ağır GPU modeli
- `src/mimarllm/regulations/`: belge envanteri, AST, sürüm, FTS5/dense retrieval, PDF kaynak koordinatları
- `src/mimarllm/rules/`: deterministik kurallar ve doğrulanmış `RuleBinding`
- `src/mimarllm/evidence/`: çizim+mevzuat birleşik kanıt grafı
- `src/mimarllm/reports/`: çift kaynaklı rapor/önizleme
- `src/mimarllm/storage/`: yerel arşiv/indeks (public repoda değil)

**Şimdiki durum:** Bunlar sadece tasarlanmış modül sınırlarıdır; source code, model, arşiv veya benchmark hazır değildir. [Mimari](sistem-mimarisi.md) · [OCR/VRAM](ocr-ve-bellek.md) · [Mevzuat](mevzuat-rag.md).
