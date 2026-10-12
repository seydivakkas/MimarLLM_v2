# MimarLLM V2 — Mevzuat Doğrulama ve Hukukî Kanıt Kapıları

**İşlem:** [islem_006](islem_006.md) · **Durum:** Mevzuat paketlerinin üretim hukukî kabulü **HOLD**.

## 1. Beş mevzuat ailesi — mevcut kural kapsamı

| Alan | Modül hedefi | Taslakta geçen ölçü ve koşullar | Üretim kararı |
| --- | --- | --- | --- |
| Planlı Alanlar İmar Yönetmeliği | `rules/registry/tr_imar.py` | Piyes alanı/kenarı, kapılar, koridor, net yükseklik, ışıklık | Madde/fıkra, muafiyet ve proje tipi doğrulanacak |
| Binaların Yangından Korunması Hakkında Yönetmelik | `rules/registry/tr_yangin.py` | Kaçış uzaklığı, çıkmaz koridor, kapı net açıklığı/açılış, sprinkler | Ek-5/A ve Ek-5/B, kullanıcı yükü, kullanım sınıfı ve hükümler doğrulanacak |
| Otopark Yönetmeliği | `rules/registry/tr_otopark.py` | Bağımsız bölüm başına sayı, rampalar, engelli park ve manevra | Ruhsat tarihi, kullanım, yerel not/istisna, rampa kesiti |
| Sığınak Yönetmeliği | `rules/registry/tr_siginak.py` | Bağımsız bölüm, kişi/alan, kapı, net tavan, kaçış | 7 Kasım 2025 değişikliği dahil geçerli hükümler ayrı incelenecek |
| Binalarda Enerji Performansı / TS 825 | `rules/registry/tr_bep.py` | WWR, havalandırma, U/yalıtım, A/V | TS lisansı + iklim/yapı zarfı/malzeme ve ilgili hesap gerekir |

**Taslaklardan alınan sayısal değerler**, tarih/kullanım/proje koşulları ve kaynakça doğrulanmadan üretim sabiti değildir. Özellikle pencere/duvar %40 ve duvar kalınlığı 0.20m tek başına enerji mevzuatı ihlali sonucuna dönüşemez; U değeri, malzeme, yapı zarfı, hesap yöntemi ve yürürlükteki standart gerekir.

## 2. Mutlak kanıt zinciri

```text
Original official source PDF or official HTML
  -> sha256 + URL + publication Gazette date/number
  -> original PDF page index / document printed page
  -> layout char polygon / OCR line/cell bbox
  -> LegalAST article/paragraph/item/table/annex
  -> amendment effective_from/effective_to + repeal/exception edges
  -> human-reviewed rule binding and project applicability
  -> verified geometry or explicit INSUFFICIENT_EVIDENCE
  -> compliant/noncompliant or review-needed result
```

`legal_node_id`, `rule_id`, `rule_version`, `official_document_sha256`, `source_page_index`, `source_polygon`, `effective_dates`, `project_location`, `permit_or_application_date`, `building_use`, `exception_evaluation`, `geometry_entity_ids`, `measurement_method` ve `reviewer_status` zorunlu.

**Sayfa/satır uyarısı:** PDF'de sayfa içi OCR satır indeksi resmî bir hukukî atıf değildir; gerçek belgeye vurgulama için `polygon/bbox` gerekir. Resmî PDF yoksa dönüştürülmüş dosyaya “özgün PDF” etiketi koyma.

## 3. Kural motoru durumları

- `COMPLIANT` / `NON_COMPLIANT`: yalnız **tanımlı kural + doğrulanmış proje kapsamı + yürürlükte kaynak + güvenilir geometrik ölçüm** varsa.
- `INSUFFICIENT_EVIDENCE`: kritik proje tarihi, sınıfı, ölçü, kesit veya kaynak eksik.
- `REVIEW_REQUIRED`: çelişen OCR/kaynak / ihtilaflı istisna / hukukî belirsizlik.
- `NOT_APPLICABLE`: uygulanmaz olduğu doğrulanmış kural.
- `ERROR`: parse/kural/inference istisnası; PASS değildir.

Arama skoru ve VLM güven skoru hiçbir zaman hukukî geçerlik puanı değildir. Tam kaynak bulunamadığında tahmini madde numarası alıntılanmaz. Bir resmî metin revize edildiğinde geçmiş analiz kaydının o gün geçerli kural sürümü değiştirilmez.

## 4. Türkiye resmî mevzuat kaynakları ve bilinen güncelleme riski

- [T.C. Resmî Gazete — 7 Kasım 2025 tarihli Sığınak değişikliği, 33070](https://resmigazete.gov.tr/eskiler/2025/11/20251107-2.htm)
- [T.C. Resmî Gazete — 1 Temmuz 2025 BYKHY değişiklik yayını, 32943](https://www.resmigazete.gov.tr/eskiler/2025/07/20250701-9.pdf)
- [Adalet Bakanlığı resmî mevzuat portalı — BYKHY](https://mevzuat.adalet.gov.tr/mevzuat/116939)
- [Bakanlık BYKHY uygulama kılavuzu](https://webdosya.csb.gov.tr/db/meslekihizmetler/haberler/b-nalarin-yangin-korunmasi-hakkinda-yonetmel-k-28.03.2025-etk-les-m-20250328093036.pdf)
- [T.C. Resmî Gazete ana sayfa](https://www.resmigazete.gov.tr/)

Bu kaynakların bazıları güncel değişiklik örnekleri olarak doğrulandı; **beş mevzuat ailesinin tüm maddeleri, tüm değişiklikleri veya doğru konsolide tarihsel sürümleri incelenmiş değildir**. BYKHY'de kaçış mesafesini yalnız oda ağırlık merkezleri arasından almak, resmî yürüme yolu tanımının yerini tutmaz. Plan notları/geçici maddeler/yapı sınıfı, yerel idari bağlam ayrı inceleme ister.

## 5. Rule registry giriş kapısı

**`APPROVED_FOR_CHECK` için hepsi şart:**

1. Özgün resmî metin ve madde/fıkra/tablo hücresi `source_sha256 + page polygon` ile eşleşmiş.
2. Yayım/yürürlük/değişiklik/istisna zinciri, ruhsat/proje tarihi ve belediye/yapı sınıfı bakımından onaylanmış.
3. Eşik birimi, ölçüm yöntemi, kuralın uygulanabilirlik koşulları ve toleransı belirtilmiş.
4. Kaynak sürümüne bağlı sentetik PASS, FAIL, insufficent ve not-applicable fixture'ları bulunuyor.
5. Bağımsız hukukî veya alan uzmanı gözden geçirme kaydı var.

Henüz bu kontrolü geçmeyen `tr_imar`, `tr_yangin`, `tr_otopark`, `tr_siginak` veya `tr_bep` kuralı otomatik gerçek mevzuat PASS/FAIL vermemeli. Son kullanıcıya hangi şartın eksik olduğu gösterilmeli.
