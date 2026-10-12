# MimarLLM V2

**Durum:** Kapsam belirleme ve başlangıç mimarisi. Ürün özellikleri henüz uygulanmadı.

MimarLLM V2; mevcut MimarLLM'den ilham alarak, tek bir Windows bilgisayarında **tamamen yerel** çalışacak, mimari çizimlerin ölçülebilir teknik analizine ve kanıt temelli değerlendirilmesine odaklanması planlanan yeni bir projedir.

> Ürün kapsamı henüz dondurulmadı. Bu belgeyi tamamlanmış bir uygulama tanıtımı olarak yorumlamayın.

## Değişmez teknik ilkeler

- Bulut tabanlı AI/LLM/VLM API çağrısı ve ücretli servis zorunluluğu **yok**.
- Hedef sistem: NVIDIA RTX 4070 **8 GB VRAM**, Intel Core i7 14. nesil, **32 GB RAM**, Windows.
- Ölçüm ve kural kararı deterministik; yerel OCR/VLM yalnızca görsel/semantik aday kaynağıdır.
- Açıklanabilir sonuç ve belirsizlik raporlaması zorunludur.
- Tek bilgisayarda kullanılacak **modüler monolit**, gereksiz agent/servis dağıtımı yok.
- Üçüncü taraf kodların lisans koşulları korunur.
- Gizli kullanıcı ve proje verileri GitHub'da tutulmaz.

## Geliştirme kayıtları

Her geliştirme isteği kaynak kod değiştirilmeden önce `docs/islem_NNN.md` altında artan numarayla belgelenir. İlgili işlem kaydı kapsamı, değişiklikleri, açık riskleri ve gerçekten yapılan doğrulamaları izler.

- [İşlem 001 — V2 kapsamının yeniden tanımlanması](docs/islem_001.md)
- [Karar defteri](docs/kararlar.md)
- [Kapsam alternatifleri](docs/kapsam.md)

## İlk ürün seçenekleri

1. **Mimari çizim analizi ve teknik kontrol** — çekirdek için önerilen yön.
2. Mimarlık öğrencisine geri bildirim / jüri provası — isteğe bağlı ek modül.
3. Kaynağı doğrulanmış mevzuat ve standart kontrolü — aşamalı.
4. Genel pedagojik eğitim portalı — ilk sürüme otomatik olarak aktarılmaz.

## Mimari taslak

`src/mimarllm` altında dosya içe alma, geometri, yerel görsel çözümleme, kurallar, kanıt ve rapor modülleri öngörülmektedir. Gerçek klasörler ihtiyaç ortaya çıktıkça oluşturulur; henüz yapılmamış işlevler varmış gibi gösterilmez.

**Not:** Bu depo mevcut V1 projesinin fork'u veya birebir kopyası değildir.
