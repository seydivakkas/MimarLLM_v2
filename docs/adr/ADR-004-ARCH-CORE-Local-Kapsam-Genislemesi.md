# ADR-004 — ARCH-CORE Local ileri sürüm eğitim/2.5D katmanı; tek modüler monolit

- **Karar tarihi:** 2026-10-15
- **İşlem:** [islem_020.md](../islem_020.md)
- **Karar:** GELECEK KAPSAM GENİŞLEMESİ / PLAN. Yeni pedagojik veya GPU modüllerinin tamamlandığı anlamına gelmez.
- **Alternatif:** Kullanıcının sunduğu üç ARCH-CORE/TÜBİTAK 2209-A taslağına karşı İşlem 001–019'daki gerçek kaynaklı teknik çekirdeğin korunması.

## Bağlam

İşlem 002–003 ilk ürününde pedagojik jüri, LMS, otomatik not, çok ajan ve öğrenci takibi **kapsam dışı**ydı. Kullanıcının yeni üç plan metni ise aynı tek bilgisayar ve sıfır harici API koşuluyla ARCH-CORE'nun yerel 2.5D, rubrik, sıralı jüri, uzman-persona ve öğrenci analitiği işlevlerini ileri sürüme eklemeyi önermektedir. Bu istek mevcut API/RuleEngine/doğrulanmış DrawingIR'yi değiştirip ikinci sistem kurmayı gerektirmez.

## Karar

1. **Engineering Core (ilk ürün) dondurulur:** `src/mimarllm/` tek Python paketi, DrawingIR source SHA/coordinate frames, kaynak alanları ve F08–F12 HUKUKI_HOLD korunacak. CUDA/LLM/3D/jüri çekirdeğin çalışması için zorunlu olmaz.
2. **Studio/Education (opsiyonel ileri sürüm) açılır:** Gerçek kod yazıldığında `vision/`, `geometry/massing.py`, `rubric/`, `jury/`, `analytics/` altında geliştirilir. Kullanıcı eğitimcinin pedagojik kriterleri ve veri gizliliği kapıları olmadan akademik not/yetkili jüri iddiası yok.
3. **Aynı kaynağın birden fazla anlatımı:** DrawingIR orijinali, tam PDF SHA, CAD entity/handle/block path hukukî LegalAST span/versiyonu **salt okunur**. Tamamlanmış oda ve kapı geometrisi/3D basamak yalnız review-onaylı; LLM’den gelen aday ile native geometry birbirine karıştırılmaz.
4. **Tek model üzerinde sıralı perspektifler:** GPU/LLM donanım ölçümü yapıldıktan sonra ortak bağlam yararları araştırılabilir, ancak KV cache prefix paylaşımı kesin hız garantisi değildir. “10 persona” bağımsız 10 insan akademisyen anlamına gelmez.
5. **Doküman/ürün statüsü:** Bugün F01–F19 kısmi kod; F20 ve F25–F37 gelecek plan; F21–F22 VLM hâlâ plan; F08–F12 resmî hukukî onay bekler. 2026-10-15 master ve güncel yol haritası önceki tarihsel tasarım belgelerinin proje durumunu açıklamak için üst referanstır; eski İşlem kayıtları silinmez.
6. **Sıra:** İşlem 020 master/doküman kararına ayrılır; daha önce bu numarada öngörülen Windows offline installer **021** olur. CAD/OCR kaynak kalitesi, UI, 2.5D, VLM ve eğitim modülleri aşamalıdır; gerçek benchmark finalde.

## Reddedilen alternatifler

- Eski `ARCH-CORE/backend/` ağacını ikinci uygulama olarak kopyalama; aynı DrawingIR için farklı alan/ölçü gerçeği üretir.
- Bulut sağlayıcılı API havuzu ve Redis/Qdrant/Neo4j/PostGIS/docker-compose'u tek kullanıcı başlangıcı için zorunlu hale getirme.
- Kapı histogramı veya ±2.5 cm snap ile otomatik `UnitCalibration.CONFIRMED`/net alan/yasal uygunluk.
- VLM/LLM çıktısı üzerine teknik veya hukukî `COMPLIANT` yetkisi vermek.
- GGUF/MMProj modelinin “8 GB'da kesin 2.7 GB/25 saniye” performansını gerçek benchmark olmadan ilan etmek.
- Hakları teyit edilmemiş TS tam metni, model ağırlığı, öğrenci çizimleri veya mimar isimli eğitim profilini gerçek kişi onayı gibi dağıtmak.

## Kabul koşulları

Tüm yeni kod modülleri kendi `docs/islem_NNN.md` dosyası önce açıldıktan sonra geliştirilecek. Sürüm kontrollü bilimsel metrikler, gerçek Windows/GPU testleri, bağımsız öğretim üyesi rubrik kabulü, resmî mevzuat geçerliliği ve yeniden dağıtım lisansları ayrı kontrol edilecek. **ADR kararı tek başına bir özelliğin test PASS veya ürün kabulünü sağlamaz.**

[Master mimari](../master-mimari-arch-core-local.md) · [Özellikler](../ozellik-envanteri.md) · [Risk ve deney](../risk-ve-dogrulama-matrisi.md).
