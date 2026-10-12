# MimarLLM V2 — Ürün Kapsamı v0.2

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
