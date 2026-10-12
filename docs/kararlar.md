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
