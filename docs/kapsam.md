# MimarLLM V2 — Ürün Kapsamı v0.3 (İşlem 020 Yeniden Baz)

> **Güncel üst karar (2026-10-15):** [MimarLLM V2 × ARCH-CORE Local Master Mimari](master-mimari-arch-core-local.md). İşlem 002–003'teki ilk ürünün teknik analiz çekirdeği **korunur**; aşağıdaki tarihsel “Pedagojik jüri/LMS kesin kapsam dışı” kararı **ilk çekirdek sürüm** için hâlâ geçerlidir. Kullanıcının üç ARCH-CORE taslak belgesi üzerinden **gelecekteki opsiyonel Eğitim/3D ürün eklentisi** yeniden planlandı, henüz kodlanmış/bağlayıcı bir müşteri taahhüdü değildir.

## 2026-10-15 revize edilmiş ürün sınırı

**Birincil ürün — Engineering Core (mevcut kısmi uygulama):** `src/mimarllm/core`, `importers`, `geometry`, `rules`, `legal`, `rag`, `reports`, `pipeline.py`, `cli.py` ve `app` çalışır kaynaklı çekirdek. İşlem 019 son sentetik CI Ubuntu/Windows 295 PASS; gerçek müşteri cihazı, gerçek mimari pafta doğruluğu, tarihsel mevzuat geçerliliği ayrı HOLD.

**İleri ürün — ARCH-CORE Studio/Education (plan adayı):** Yanında 2.5D sahne, istemli yerel GPU VLM semantik aday, 8B rubrik, seri pedagojik yorum personeleri ve isteğe bağlı öğrenci analitiği; ilk çekirdeğin import/RuleEngine doğruluk ve hukukî kapılarını değiştirmez, müşteriye zorunlu bağımlılık yüklemez. LMS/çok kullanıcılı sınıf portalı, ayrı teacher/student auth, sınıf yönetimi **yine ürün çekirdeği kapsamında değildir**; gerekiyorsa sonradan bağımsız onam, güvenlik ve kaynak planı gerektirir.

**Kaldırılmayan yasaklar:** Hiç ücretli/uzak LLM API, ikinci paralel Python platformu, tüm DXF/PDF koordinatlarını sessiz SI'ye çevirme, VLM metre/alan hesaplatma, sanal kapı köprüsünü gerçek geçit sayma, kaynaksız resmî hukukî PASS, model-kişilik çıktısını insan mimarın gerçek görüşü gibi sunma yoktur.

**Ürün ve bilimsel iddia ayrımı:** Deneysel hedefler (model 3 GB, 300 ms, 60 FPS, kappa, Recall) sonuç değildir. Eğitim dışı mimari analiz ana değer önerisi korunur; bilimsel çalışma metodolojisi ayrıca [risk doğrulama](risk-ve-dogrulama-matrisi.md) ile ölçülecek.

---


- **Kapsam kararı:** **KESİN**, 2026-10-12, [İşlem 002](islem_002.md).
- **Durum:** Yazılım uygulaması başlamadı; kapsam ve teknik tasarım oluşturuldu.
## Ürün tanımı
**MimarLLM V2, tamamen yerelde çalışan Mimari Teknik Çizim Analizi ve Hata Tespiti Sistemidir.**
Kullanıcı çizim dosyasını açar. Sistem veri ve geometriyi çıkarır, koordinat/ölçek birimlerini doğrular, tanımlı geometrik/topolojik ve teknik kontrolleri çalıştırır; hataları, eksik kanıtları ve şüpheli elemanları **çizimdeki konumlarıyla** gösterir. Sonuç gerekçelidir ve dışa aktarılabilir.
## İlk ürünün işlevsel odağı
- Dosya ve çizim içe alma; güvenli tip, kaynak ve koordinat yönetimi.
- CAD vektör verisi üzerinde deterministik geometri/ilişki kontrolü.
- Oda, sınır, duvar, açıklık, katman/etiket **adaylarının** çözümlemesi.
- Ölçü, ölçek ve belirsizliği açıkça ayırma; yetersiz bilgiyle hüküm vermeme.
- Bulgunun kaynağına geri dönen kanıt zinciri, konumsal işaretleme ve rapor.
- Yerel OCR/VLM ile etiket ve semantik nesne çıkarımının aşamalı eklenmesi.
- Doğrulanmış ve kapsamı belirlenmiş teknik kural paketi; mevzuat sertifikası değil.
## İlk ürün kapsamı dışında — KESİN
- Pedagojik eğitim portalı ve LMS.
- Öğrenci takibi, sınıf yönetimi, öğretmen oturumu ve ders müfredatları.
- Jüri persona/karakterleri, otomatik not verme ve jüri simülasyonu.
- Çoklu AI agent orkestrasyonu ve bulut tabanlı LLM/VLM API hizmetleri.
- Mimari tasarım çizimini baştan üretme, otomatik proje onay/sertifikasyonu.
- Başlangıç için gereksiz Redis/Neo4j/PostgreSQL dağıtımları veya sürekli açık çoklu servisler.
Bunlar ileride yeni bir ürün kararıyla eklenebilir; V2'nin çekirdeği olarak geliştirilmez.
## Kullanıcı ve temel senaryo
Hedef, teknik çizim hazırlayan ya da inceleyen kullanıcıdır. **İlk persona** (mimar / teknik ofis / öğrenci) ayrıca belirlenecektir. Önerilen ilk uçtan uca senaryo:
`DXF seç -> kaynağı/birimi doğrula -> DrawingIR -> geometri/topoloji -> deterministik hata kontrolleri -> çizim üzerinde bulgu -> kanıtlı rapor`
Bu akıştaki **DXF ilk formatı** öneridir; henüz kesinleştirilmemiştir. Vektörel PDF/raster, OCR ve VLM aşamalı sonraki bileşenlerdir.
## Koruyucu ürün ilkeleri
- VLM çıktılarını “kanıtlanmış ölçüm” yerine koyma.
- Ölçeği bilinmeyen çizimde m/m² cinsinden kesin sonuç veya teknik geçerlik kararı üretme.
- İşaretlenemeyen bulguyu doğrulanmış konumsal bulgu gibi gösterme.
- Resmî mevzuat sürümü doğrulanmamışsa hukukî uygunluk `PASS` verme.
- Başarı durumu yalnız belirli kural için geçerlidir, çizimin tamamını “hatasız” ilan etmez.
- Çevrim dışı kullanım ve RTX 4070 8 GB/32 GB donanım sınırına göre tasarım yap; ölçülmeden performans vaadi verme.
- Public depoda özel çizim/veritabanı/model ağırlığı/telif hakkı belirsiz dosya bulundurma.
## Belgeler
- [Teknik gereksinimler ve kabul senaryoları](teknik-gereksinimler.md)
- [Modül sınırları ve P0–P10 geliştirme planı](modul-plani.md)
- [Kesin ve açık kararlar](kararlar.md)
## İşlem 003 kapsam genişlemesi — kabul edildi
Yeni ürün tanımı: **Yerel Mimari Teknik Çizim Analizi, Hata Tespiti ve Özgün Mevzuat Kaynaklı Gerekçe Sistemi.** Geometri/tasarım hata tespiti çekirdek olarak korunur. Mimari mevzuat kütüphanesi; istisna, tarih, değişiklik ve madde/fıkra hiyerarşisini kaybeden serbest metin araması yerine yapısal RAG olarak entegre edilir. Kullanıcı, bulgudaki çizim nesnesi ile ilgili mevzuat hükmünün özgün belge **sayfa/bbox** konumunu aynı ekranda görebilir.
**Beş hedef mevzuat ailesi:** Planlı Alanlar İmar Yönetmeliği; Binaların Yangından Korunması Hakkında Yönetmelik; Otopark Yönetmeliği; Sığınak Yönetmeliği; Binalarda Enerji Performansı Yönetmeliği. Bu liste bir **kaynak indeksleme hedefidir**; her maddenin otomatik hukukî uygunluk kuralı olduğu anlamına gelmez.
**OCR:** PDF native metin/vektör çıkarımı `pdfplumber`; eksik/taranmış ROI render `pypdfium2`; yerel CPU OCR `rapidocr + onnxruntime`. Mevzuat kaynakları ayrı offline ETL ile hazırlanır.
**Hukukî kesinlik sınırı:** Sistem resmî proje kontrol makamı değildir. Belirli bir maddenin uygulanabilirliğini belirlemek için proje tarihi, konumu, kullanım sınıfı, yerel plan notu ve hükmün yürürlük bilgisi gerekebilir. Bilgi eksikse otomatik PASS yok. Satır ID, OCR kaynaklı olabileceğinden özgün resmî satır numarası gibi sunulmaz.
Ayrıntılı tasarım: [sistem-mimarisi.md](sistem-mimarisi.md), [ocr-ve-bellek.md](ocr-ve-bellek.md), [mevzuat-rag.md](mevzuat-rag.md).
## İşlem 004 — Ürünün OCR çalışma yolu güncellendi
Varsayılan PDF motorları kesin: `pdfplumber` + `pypdfium2`, OCR `RapidOCR CPU`. CAD DXF doğrudan ezdxf üzerinden okunacaktır.
**Motor kapsamı:** Önceki alternatifler terk edildi; tek PDF/OCR yolumuz ADR-002 kapsamındadır.
Kullanıcıya özgün belgenin `document_sha256 + page_index + four-point polygon + article/paragraph/item/table cell` kaynak bilgisi korunarak gösterilecek. RapidOCR sınıflandırıcısının 0/180° desteği 45/90/270° yazılarda eksiksiz okuma garantisi olarak sunulmayacak. Detay: [ocr-mimari-pafta.md](ocr-mimari-pafta.md).


## İşlem 006 — Tam ürün hedefi kaydı

MimarLLM V2 ürününe hedef olarak **DrawingIR, DXF ve vektörel/raster PDF, mahal/duvar/kapı/pencere/ölçek, net-brüt alan, geçiş/yangın yürüme topolojisi, Planlı Alanlar+Yangın+Otopark+Sığınak+BEP kaynaklı kontrol aileleri, hiyerarşik offline mevzuat RAG, doğal dil kaynak gösterimi, yerel OCR/VLM, çift kaynaklı kanıt raporu, interaktif çizim arayüzü ve offline Windows standalone paketleme** dahildir.

Bu cümle bunların bugün kodlandığı anlamına gelmez. Teknik kabul durumu [24 özellik takip tablosunda](ozellik-envanteri.md) görülür. Pedagojik LMS, agent orkestrasyonu, bulut AI/API ve tasarım üretme aracı yine kapsam dışıdır. Mevzuat eşikleri ve riskli sayısal varsayımlar [doğrulama kapısına](mevzuat-dogrulama-protokolu.md) tabidir.

[ADR-003](adr/ADR-003-Kapsam-Kanit-ve-Kabul-Kapilari.md) karar sınırlarını açıklıyor.
