# MimarLLM V2 — Karar Defteri

Bu belge kesin kararları önerilerden ayırır. Her değişiklik işlem kaydıyla izlenir.

| Kod | Karar | Durum | Kaynak |
| --- | --- | --- | --- |
| K-001 | V1'den bağımsız `seydivakkas/MimarLLM_v2` deposunda geliştirme | KESİN | islem_001 |
| K-002 | Tek bilgisayarda Windows odaklı yerel çalışma | KESİN | islem_001 |
| K-003 | Hiçbir bulut yapay zekâ API'si kullanılmaması | KESİN | islem_001 |
| K-004 | Hedef kaynak sınırı 8 GB VRAM / 32 GB RAM | KESİN | islem_001 |
| K-005 | Gereksiz agent altyapısı olmadan sade modüler mimari | KESİN | islem_001 |
| K-006 | Her geliştirme isteğinden önce sıralı `docs/islem_NNN.md` kaydı | KESİN | islem_001 |
| K-007 | Ana ürün: **mimari teknik çizim analizi ve hata tespiti** | **KESİN** | islem_002 |
| K-008 | **Pedagojik eğitim portalı, LMS, sınıf/öğrenci takibi ilk ürün kapsamında yok** | **KESİN** | islem_002 |
| K-009 | İlk girdi formatları: DXF / vektörel PDF / raster PDF / DWG / IFC sırası | TARTIŞILIYOR | islem_002 |
| K-010 | Arayüzün masaüstü / localhost web biçimi | TARTIŞILIYOR | islem_002 |
| K-011 | Yerel OCR ve VLM modelleri/sürümleri | TARTIŞILIYOR | islem_002 |
| K-012 | Mevzuat denetiminin kapsamı ve geçerli kaynaklar | TARTIŞILIYOR | islem_002 |
| K-013 | Jüri karakterleri ve otomatik öğrenci puanlaması ilk ürünün parçası olmayacak | **KESİN** | islem_002 |
| K-014 | Geometrik ölçüm ve kural denetimi deterministik çekirdekte; VLM yalnız yardımcı | **KESİN** | islem_002 |
| K-015 | İlk 5–10 hata kontrolünün ayrıntılı tanımı ve toleransları | TARTIŞILIYOR | islem_002 |
| K-016 | İlk kullanıcı profili: teknik ofis / mimar / öğrenci | TARTIŞILIYOR | islem_002 |

## Kesinleştirilen kapsam gerekçesi

V1'deki eğitim/portal/jüri/çoklu AI servislerini sürdürmek yerine kullanıcıya ölçülebilir teknik çizim hata bulgularını **kaynak konumu ve kanıtıyla** gösteren tek bilgisayarlık uygulama üretmek. Ürün özellikleri olmayan klasör veya menü şablonları eklenmez. Gelecekte kapsam değişirse yeni işlem kaydı ve kullanıcı kararı gerekir.

## Başlangıç önerileri, henüz karar değil

- **Öneri:** İlk vektör formatı DXF; sonraki aşamalar dijital PDF ve raster PDF.
- **Öneri:** Önce `DrawingIR` + geometri + deterministik kontroller; OCR ve VLM daha sonra.
- **Öneri:** Önce Python çekirdeği ve tek bir yerel arayüz; UI teknolojisi ayrı seçilir.
- **Öneri:** Mevzuat kuralları yalnız kaynak ve yürürlük bilgisi doğrulandığında eklenir.

**İş kuralı:** Kesin olmayan seçenekler fiili iş veya doğrulanmış sonuç gibi gösterilmez. Bir sonraki geliştirme isteğinin kaydı `docs/islem_003.md` olacaktır.

**Depo durumu:** 2026-10-12 tarihinde depo **public** olarak doğrulandı; özel kullanıcı çizimleri, veritabanları, anahtarlar ve model ağırlıkları depoya yüklenmez.


## İşlem 003 — Mimari ve mevzuat doğrulama kararları (2026-10-12)

| Kod | Karar | Durum | Kaynak |
| --- | --- | --- | --- |
| K-017 | Mimari hata kontrolüne **hiyerarşik/hibrid yerel mevzuat RAG** eklenecek | **KESİN** | islem_003 |
| K-018 | Hata bulgusunda **özgün mevzuat sayfası + metin bbox / tablo hücresi** gösterilecek; satır ID'si türetilmiş olarak etiketlenecek | **KESİN** | islem_003 |
| K-019 | Mevzuat erişimi; madde, fıkra, bent, tablo, ek ve değişiklik/yürürlük sürümüyle tutulacak | **KESİN** | islem_003 |
| K-020 | Mevzuat RAG **arama adayı** döndürür; kural motorunun deterministik hükmünün yerini almaz | **KESİN** | islem_003 |
| K-021 | Ağ üzerinden AI servisi olmadan **yerel OCR** kullanılacak, Baidu Unlimited-OCR ana değerlendirme adayı | **KESİN (değerlendirme)** | islem_003 |
| K-022 | Unlimited-OCR'ın 8 GB VRAM/Windows'ta gerçek kullanım uyumu ve seçilecek quantization/runtime | **ÖLÇÜM BEKLENİYOR** | islem_003 |
| K-023 | Ağır GPU OCR ve VLM aynı anda çalışmayacak; süreç izolasyonlu phase-lock | **KESİN** | islem_003 |
| K-024 | İlk 5 mevzuat ailesi: Planlı Alanlar, Yangın, Otopark, Sığınak, BEP | **KESİN (hedef korpus)** | islem_003 |
| K-025 | Mevzuatın özgün yürürlük/değişiklik kronolojisinin ve kuralların sayısal eşiklerinin doğrulanması | **İNCELEME BEKLENİYOR** | islem_003 |
| K-026 | SQLite FTS5 + yerel CPU embedding + RRF; vector DB sunucusu zorunlu değil | **KESİN (başlangıç mimarisi)** | islem_003 |
| K-027 | Kullanıcı arayüz teknolojisi, DWG/IFC ve ilk uygulanacak kesin mevzuat eşikleri | **AÇIK** | islem_003 |

Ayrıntılar: [Sistem mimarisi](sistem-mimarisi.md) · [OCR/bellek](ocr-ve-bellek.md) · [Mevzuat RAG](mevzuat-rag.md).

**K-012 güncellemesi:** Önceden tartışılan mevzuat desteği K-017 ile çekirdek ürüne eklendi. Ancak **hukukî denetimin hangi maddelerle ve hangi projelerde uygulanacağı** hâlâ ayrı mevzuat ve proje bağlamı incelemesine bağlıdır.

## İşlem 004 — OCR strateji revizyonu (2026-10-12)

**K-021/K-022/K-023 üzerindeki güncelleme:** K-021'deki “Unlimited-OCR ana değerlendirme adayı” artık **tarihsel** bir karardır; ilk çalışır ürünün varsayılan OCR motoru değildir. K-022'deki Unlimited-OCR uyumluluk araştırması **opsiyonel araştırma** durumunda kalır. K-023 GPU model sıralaması VLM ile herhangi bir opsiyonel GPU OCR için geçerlidir; RapidOCR'nin CPU kullanımı aynı GPU kilidini gerektirmez.

| Kod | Karar | Durum | Kaynak |
| --- | --- | --- | --- |
| K-028 | OCR'de önce DXF CAD metni veya PyMuPDF native PDF metni, yalnız eksik/güvenilmez bölgede OCR | **KESİN (tasarım)** | islem_004 |
| K-029 | Birincil yerel OCR çalışma adayı `rapidocr` + `onnxruntime` **CPU**; `rapidocr_onnxruntime` eski paket | **KESİN (teknoloji yönü)** | islem_004 |
| K-030 | Unlimited-OCR varsayılan OCR yolu değil, isteğe bağlı deneysel benchmark alternatifi | **KESİN** | islem_004 |
| K-031 | Native metin de kusurlu olabilir; SHX/kontur metin ve kısmi raster için ROI kalite kapısı | **KESİN** | islem_004 |
| K-032 | Döndürülmüş yazılarda quad/homografi + sayfaya geri dönüş; RapidOCR cls yalnız 0°/180° | **KESİN (yöntem)** | islem_004 |
| K-033 | Türkçe/mimari simgelerin RapidOCR ile gerçek doğruluğu ve Windows CPU RAM/latency | **ÖLÇÜM BEKLENİYOR** | islem_004 |
| K-034 | Mevzuat OCR/tabloları çizim analizinden **ayrı offline ETL** hazırlanacak | **KESİN** | islem_004 |
| K-035 | Tablo çıkarımında PyMuPDF+pdfplumber başlangıç adayı; Docling CPU yalnız gerekli olduğunda | **ÖNERİ/benchmark bekleniyor** | islem_004 |
| K-036 | Kaynak paket adı `src/mimarllm/` olarak korunur; ikinci `src/mimar/` paketi açılmaz | **KESİN (repo bütünlüğü)** | islem_004 |

Kaynak: [İşlem 004](islem_004.md) · [OCR mimari sözleşmesi](ocr-mimari-pafta.md).
