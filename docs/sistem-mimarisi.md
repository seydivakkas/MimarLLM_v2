> **PDF LİSANS KAPISI:** Native PDF text extraction motoru `PdfTextBackend` olarak değiştirilebilir tutulur. PyMuPDF AGPL/ticari lisans gerektirebilir; kapalı kaynak Windows dağıtımı için pypdfium2 ve pdfplumber değerlendirmesi bekleniyor. [pdf-lisans.md](pdf-lisans.md).

> **GÜNCEL OCR KARARI — İşlem 004:** Kaynağı koruyan akış artık `DXF TEXT/MTEXT/DIMENSION / PyMuPDF native PDF text -> kalite kapısı -> eksik ROI'de RapidOCR CPU -> quad/transform -> DrawingIR`. OCR ve yerel VLM bağımsızdır. Unlimited-OCR için aşağıdaki tarihsel GPU OCR fazı **varsayılan çalışma yolu değildir**. Mevzuat PDF'leri ayrı offline ETL işleminde ayrıştırılır. Detay: [OCR mimarisi](ocr-mimari-pafta.md) ve [islem_004](islem_004.md).

# MimarLLM V2 — Sistem Mimarisi v0.3

- **İşlem kaydı:** [islem_003.md](islem_003.md)
- **Durum:** TASARIM; uygulama/test/benchmark yapılmadı.
- **Ürün:** Tek bilgisayarda çalışan mimari çizim hata tespiti + özgün kaynak sayfası gösteren mevzuat denetim yardımcısı.
- **Hedef:** Windows, Intel i7 14. nesil, 32 GB RAM, RTX 4070 8 GB VRAM. **Sıfır harici AI API**.
- **Kesin kapsam dışı:** Pedagojik portal, LMS, öğrenci takibi, jüri karakterleri, otomatik mimari proje üretimi, çok ajan.

## 1. Mimarın gerçek iş akışı

Bir mimar çizimini DXF, dijital PDF veya taranmış pafta olarak açar:

1. **Kaynak ve ölçek:** Dosya türü, revizyon, ölçü birimi, modelspace/layout veya PDF sayfası, bilinen kalibrasyon bilgileri gösterilir. Bilinmeyen ölçü kesin varsayılmaz.
2. **Çizim okuma:** Vektörde entity/katman/blok/ölçü bilgisi; rasterda OCR ve VLM ile mahal/kapı/pencere/merdiven adayları çıkarılır.
3. **Nesne ve ilişki doğrulama:** Duvar, açıklık, kapı kanadı, oda sınırları, birbiriyle çelişen metin/ölçü ve mekânsal bağlantılar bir kanıt grafında ilişkilendirilir.
4. **Çizim kalite kontrolleri:** Açık oda sınırı, mükerrer çizgi, hatalı kesişim, belirsiz kapı/açıklık bağı, üst üste binen mahal etiketi, hatalı/eksik kot-ölçü adayları raporlanır.
5. **Mevzuat odaklı kontroller:** Proje kullanım türü, konum, ruhsat/inceleme tarihi ve başka gerekli özellikler varsa sürümlü kurallar değerlendirilir; eksikse inceleme gerekir.
6. **İkili kanıt görünümü:** Kullanıcı bir bulguya tıklar; solda çizim üzerinde hedef geometri, sağda özgün mevzuat PDF sayfası ve işaretli ifade görünür.
7. **Son kullanıcı kararı:** Mimar `ONAYLA`, `YANLIŞ EŞLEŞME`, `YENİDEN ÖLÇ`, `İSTİSNA İNCELEMESİ` gibi inceleme işlemlerini kayda geçirir.
8. **Çıktı:** Girdi hash'i, kontrol algoritması, kural sürümü, ölçü/tolerans, mevzuat kaynak künyesi, sayfa ve geometrik konum rapora girer. Bu çıktı **resmî proje onayı/sertifikasyonu** değildir.

## 2. İki ayrı kanıt kanalı

```text
MİMARİ ÇİZİM KANALI                   MEVZUAT KANALI
DXF / PDF / pafta                    Resmî kaynak PDF / HTML
   |                                    |
Native parser + OCR adayları          Kaynak hash + sürüm envanteri
   |                                    |
DrawingIR + coordinate transforms    PDF/text layout ve AST
   |                                    |
Geometry / topology                  Madde/fıkra/bent/tablo/ek
   |                                    |
Ölçüm + belirsizlik                   FTS5 + CPU embedding + RRF
   |                                    |
   +------> Deterministic Rule Engine <--+
                  |
       Uygulanabilirlik + istisnalar
                  |
       Evidence Graph + Finding
                  |
   Yan yana ÇİZİM / ÖZGÜN KAYNAK ÖNİZLEME
                  |
            Yerel rapor
```

`RAG` doğru aday hükmü **bulur**, mevzuatın belli bir proje için gerçekten geçerli olduğunu tek başına **ispat etmez**. `Rule Engine`, kaynağın doğrulanmış yürürlük/anlam/uygulanabilirlik bilgisine bağlı deterministik hesap yapar. VLM ölçü veya hukukî `PASS` üretmez.

## 3. Mimara zaman kazandıracak ilk kontrol alanları

| Kontrol kümesi | CAD/raster gereksinimi | Hata türü / sınır |
| --- | --- | --- |
| G0 — Çizim bütünlüğü | Geometri | Kopuk sınır, çift çizgi, sıfır uzunluk, katman tutarsızlığı, çakışma |
| G1 — Mekân/mahal | Kapanan oda poligonları, güvenilir ölçek, etiket | Alan, geçersiz oda sınırı, mahal ismi ve geometri tutarsızlığı |
| G2 — Kapı/pencere/açıklık | Duvar-açıklık semantiği, ölçü, swing kanıtı | Açıklık ilişkisi, kapı yönü adayı, geçiş genişliği ve eksik etiket |
| G3 — Koridor/merdiven/erişim | Bağlılık grafı, net açıklık ve gerekli kesit bilgisi | Geçişe engel olabilecek bağlantı, eksik erişim, ölçüm belirsizliği |
| G4 — Mevzuat gerekçesi | Proje bağlamı + doğrulanmış metin/sürüm | Seçilmiş kuralların kanıtlı kontrolü; görünmeyen bilgi otomatik kabul edilmez |

**2B çizim sınırı:** Yangın kaçışı, gerçek kapı net açıklığı, erişilebilir eğim, pencere açılabilir alanı, enerji performansı, yangın dayanımı ve katlar arası ilişkiler tek plan görüntüsünden güvenilir biçimde doğrulanamayabilir. Gereken kesit, detay, malzeme, kat/konum veya proje metaverisi yoksa `INSUFFICIENT_EVIDENCE` kullanılır.

## 4. Model fazları ve iş sıralaması

```text
Phase 0: Kaynak kontrolü / native DXF/PDF text extraction (CPU)
Phase 1: DXF geometri/topoloji ve ilk kontroller (CPU)
Phase 2: OCR (önce yerel hafif motor; zor sayfada Unlimited-OCR adayı)
         OCR çıktı kaydı -> ayrı süreç durur -> GPU bellek gözlenir
Phase 3: Yerel VLM (yalnız belirsiz nesne ROI'leri; gerektiğinde)
         VLM adayları -> süreç durur
Phase 4: Mevzuat FTS5 + CPU embedding (+ opsiyonel rerank) -> seçili hükümler
Phase 5: Sürümlü kural motoru -> iki yönlü kanıt -> rapor
```

Bunlar tek kullanıcı sıralı işlerdir. Model çalışırken CPU'da bağımsız dosya/arama işlemleri sürebilir fakat ikinci ağır GPU modeli **eşzamanlı başlatılmaz**. Asıl VRAM temizliği için model subprocess'i kapatılır; `gc.collect()` veya `torch.cuda.empty_cache()` kendi başına boş VRAM garantisi değildir.

## 5. Kaynak gösterme kullanıcı deneyimi

**Seçilen bir hata bulgusunun ayrıntı görünümü:**

| Sol — Pafta kanıtı | Sağ — Mevzuat kanıtı |
| --- | --- |
| Kullanıcının DXF/PDF paftası | **Özgün kaynaktan** kaydedilen PDF sayfası / resmî kaynak HTML |
| İlgili duvar/kapı/koridor çokgeni ve ölçüm çizgisi | İlgili madde, fıkra, bent, tablo satırı/hücresi, sayfa kutusu işaretli |
| Ölçülen değer, birim, tolerans ve kalibrasyon | Metin, yayımlanma/yürürlük bilgisi, değişiklik, istisna ve geçerlilik |
| “Geometri doğrulandı mı?” durumu | “Kaynak doğrulandı mı?” ve “Bu projeye uygulanabilir mi?” durumları |

**Atıf birimi:**
`regulation_id + version_id + document_sha256 + original_page_index + bbox/polygon + article/paragraph/item + source_type + extraction_method + review_status`.

Sayfa numarası **PDF indeksinden ayrı** olarak görüntüde yazan basılı sayfa numarasından ayrıştırılır. OCR tarafından türetilmiş satır numarası sadece arayüz içi referanstır; resmî madde-fıkra numaralarının yerine geçmez. Kullanıcı isterse PDF açıldığında renkli vurgulama doğrudan source bounding polygon koordinatlarına dayanır.

**Kaynak zinciri kırılırsa:** PDF artık yok, hash farklı, madde-satır uyuşmaz, OCR belirsiz veya değişiklik grafı eksik -> o kontrolün hukukî sonucu `REVIEW_REQUIRED` / `INSUFFICIENT_EVIDENCE`, asla otomatik `PASS`.

## 6. Sade dizin mimarisi — PLANLANAN

```text
MimarLLM_v2/
├── docs/
│   ├── islem_001.md
│   ├── islem_002.md
│   ├── islem_003.md
│   ├── sistem-mimarisi.md
│   ├── ocr-ve-bellek.md
│   ├── mevzuat-rag.md
│   ├── teknik-gereksinimler.md
│   ├── modul-plani.md
│   ├── kararlar.md
│   └── kapsam.md
├── src/mimarllm/                    # ileride kodla oluşturulacak
│   ├── core/                        # DrawingIR, koordinatlar, sözleşme
│   ├── importers/                   # dxf.py, pdf.py, image.py
│   ├── geometry/                    # spatial.py, topology.py
│   ├── vision/                      # ocr.py, vlm.py, scheduler.py
│   ├── regulations/                 # parser.py, catalog.py, versions.py
│   │   ├── retrieval.py             # FTS5 + embedding + RRF
│   │   └── citations.py             # PDF bbox/line/table kökeni
│   ├── rules/                       # deterministic checks + source binding
│   ├── evidence/                    # chain.py, findings.py
│   ├── reports/                     # JSON/HTML/PDF ve üstüne çizim
│   └── storage/                     # local SQLite/dosya yönetimi
├── app/                             # tek arayüz, teknoloji ayrıca seçilecek
├── config/                          # sürümlü kurallar ve güvenli yapılandırma
├── tests/                           # sentetik çizim + hukuki belge fixture
└── scripts/                         # tamamen yerel kurulum/benchmark
```

Bu ağacın `src/`, `app/`, `tests/` vb. kısımları **henüz kod değildir**. Başlangıç için çoklu agent, Neo4j/Postgres/Redis/Qdrant sunucusu zorunlu kılınmaz. Şimdilik depoda sadece tasarım belgeleri güncellenir.

Yerel çalışma dosyaları (Git dışı; `.gitignore` kapsamına alınır):

```text
local_data/
  projects/                    # kullanıcı DXF/PDF ve geçici raporları
  regulations/raw/             # özgün Resmî Gazete PDF/HTML snapshot
  regulations/parsed/          # source-linked AST ve layout çıktısı
  regulations/index/           # SQLite FTS5 ve yerel embedding indeksi
  models/                      # izinli offline model ağırlıkları
  runs/                        # VRAM ölçümleri, iş günlükleri
```

## 7. Dört mimari kalite kapısı

- **KAYNAK:** özgün belgenin SHA-256'sı doğrulandı mı, ilgili sayfa/alan fiziksel belgede mevcut mu?
- **HUKUK:** sürüm, yürürlük, istisna, mekânsal yetki ve proje bağlamı doğrulandı mı?
- **GEOMETRİ:** çizimde fiziksel birim, referans eleman ve hesap doğrulandı mı?
- **SİSTEM:** yerel kaynaklarla, VRAM sınırında, sessiz ağ çağrısı olmadan ve hata/iptal davranışıyla çalışıyor mu?

Bir kapıdan geçemeyen durum raporda açık kalır. Kullanıcı incelemesi otomatik kanıt üretmiş gibi sunulmaz.

## 8. Açık tasarım / hukukî riskler

- Yönetmeliklerin yürürlük/değişiklik listesi henüz ayrı ayrı doğrulanmadı; hiçbir örnek madde/fıkra veya ölçü eşiği üretim kuralı sayılmaz.
- Belediye imar plan notları, yerel planlar, proje tarihindeki geçiş hükümleri ve özel yapı türleri değerlendirme kapsamını değiştirir.
- TS standartları ve diğer telifli dokümanların kullanımı/dağıtımı ayrı lisans konusudur; kamuya açık repoda tam metin arşivlenmeyecek.
- Unlimited-OCR Windows 8 GB BF16 OOM riski; modelin varlığı onun test edilmiş uyumlu olduğu anlamına gelmez.
- OCR bir satırda birden fazla sütunu karıştırabilir; tablolar ayrı satır/hücre kanıtlarıyla doğrulanır.

## 9. Referans kaynaklar

- [Baidu Unlimited-OCR resmî repo](https://github.com/baidu/Unlimited-OCR)
- [Baidu Unlimited-OCR model kartı](https://huggingface.co/baidu/Unlimited-OCR)
- [PaddleOCR PP-StructureV3 açıklaması](https://github.com/PaddlePaddle/PaddleOCR/blob/main/docs/version3.x/algorithm/PP-StructureV3/PP-StructureV3.en.md)
- [T.C. Resmî Gazete](https://www.resmigazete.gov.tr/)
