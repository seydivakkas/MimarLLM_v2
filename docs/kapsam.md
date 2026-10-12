# MimarLLM V2 — Ürün Kapsamı (Taslak)

## Sorun

MimarLLM V1; çizim analizi, jüri simülasyonu, pedagojik öğrenme portalı, RAG, kullanıcı yönetimi ve bulut LLM servislerini aynı üründe toplamaya çalışıyordu. V2'nin tek bilgisayarda ve bütünüyle yerel çalışması hedefleniyor. Hangi işlevlerin yeni ürünün esas görevi olduğu **yeniden kararlaştırılacak**.

## Önerilen birincil iş

Kullanıcı bir mimari çizim yükler. Sistem okunabilir nesneleri ve ölçüleri çıkarır, bilinmeyen ölçeği onaya sunar, kanıta dayalı fiziksel/topolojik bulgular üretir ve izlenebilir rapor hazırlar.

## Olası kullanıcı profilleri

- **Mimarlık öğrencisi:** Çizimdeki ölçü, işaret ve mekânsal eksiklerin tespiti; yorumlayıcı geri bildirim isteğe bağlı.
- **Mimar / teknik ofis:** Teslim öncesi plan QA ve hata/eksiklik listesi.
- **Akademisyen / jüri:** Rubriğe dayalı değerlendirme yardımı; otomatik nihai not verme değil.
- **Mevzuat uzmanı:** Kaynağı/sürümü doğrulanmış teknik kuralları değerlendirme; hukukî kesinlik iddiası yok.

## Kapsam için önerilen öncelik

| Katman | V2 ilk sürüm | Not |
| --- | --- | --- |
| Dosya içe alma, birim, ölçü, geometri, topoloji | Çekirdek adayı | Deterministik |
| Yerel OCR ve görsel etiket önerisi | Çekirdek adayı | Kesin geometri iddiası yok |
| Kanıt zinciri, açık belirsizlik, rapor | Çekirdek adayı | Zorunlu |
| Mevzuat uygunluk kararları | Şartlı / sonraki | Kaynak ve kapsam doğrulaması şart |
| Jüri simülasyonu, eğitim geri bildirimi | Opsiyonel | Temel motora bağlı modül olabilir |
| LMS, öğrenci hesapları, sınıf takibi | İlk sürüm dışında önerildi | Kullanıcı kararına açık |
| Tamamen üretken mimari tasarım | İlk sürüm dışında önerildi | Ayrı Ar-Ge |
| Bulut AI API'si ve çoklu agent orkestrasyonu | Hariç | Tasarım ilkesi |

## Kalite yaklaşımı

- `PASS` ve `FAIL` yalnız geçerli girdiler ve ilgili kurallar üzerinden üretilir.
- Ölçek veya kaynak eksikliği `INSUFFICIENT_EVIDENCE` olarak işaretlenir.
- Öznel mimari değerlendirmeler teknik uyumluluk sonucundan ayrı gösterilir.
- Her kanıt parçası dosya konumu, geometri/hesap ve kural kimliği ile ilişkilendirilir.
- Performans vaadi, hedef Windows donanımında ölçülmeden kabul edilmiş sayılmaz.

## Açık ürün kararı

İlk sürümün **birincil kullanıcısı** ve **ilk tamamlanacak somut kullanıcı senaryosu** netleştirilmeli. Bu iki bilgi olmadan kapsamı gereksiz yere genişletmeyeceğiz.
