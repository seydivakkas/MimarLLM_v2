> **GÜNCEL KAYNAK ETL KARARI — İşlem 004:** Mevzuat için özgün PDF'yi yerelde sakla; önce PyMuPDF native spans+quad ile kaynak koordinatını çıkar; eksik/taranmış ROI'de RapidOCR ONNX CPU; tablo için `pdfplumber` veya CPU-uyumlu `Docling` ancak benchmark ve hücre bbox doğrulamasından sonra. İndeksleme, çizim denetimi sırasında değil **ayrı offline hazırlık/ETL fazında** yapılır. Kişisel/özel mevzuat kopyaları public GitHub'a eklenmez. Ayrıntı: [ocr-mimari-pafta.md](ocr-mimari-pafta.md) ve [islem_004.md](islem_004.md).

# MimarLLM V2 — Hiyerarşik Mevzuat RAG ve Özgün Kaynak Kanıtı v0.1

- **İşlem:** [islem_003.md](islem_003.md)
- **Durum:** TASARIM; resmî mevzuat arşivi henüz indirilmedi, indekslenmedi veya hukukî doğrulanmadı.
- **Kullanıcı hedefi:** Mimari çizim denetiminin gerekçesini yönetmeliğin gerçekten yazdığı **özgün belge/sayfa/satır-alanından** görebilmek. Yanıtlar internete çıkmadan üretilir.

## 1. Mevzuat belge kütüphanesi — ilk 5 hedef aile

| Sıra | Hedef yönetmelik | Örnek değerlendirme alanı | Gerçek uygunluk için ilave veri |
| --- | --- | --- | --- |
| R1 | Planlı Alanlar İmar Yönetmeliği | Mekân, yükseklik, çıkma, merdiven, ışıklık, ortak alan | Proje konumu, plan notu, yapı türü, tarih, pafta/detay |
| R2 | Binaların Yangından Korunması Hakkında Yönetmelik | Kaçış, kapı yönü, merdiven, yangın bölgesi | Kullanım sınıfı, kişi yükü, kat, dayanım, yangın senaryosu |
| R3 | Otopark Yönetmeliği | Otopark adedi, geometri, rampalar, manevra | Bağımsız bölüm sayısı, kullanım, ruhsat ve yerel durum |
| R4 | Sığınak Yönetmeliği | Sığınak gerekliliği, alan, havalandırma, çıkış | Yapı kapasitesi, kullanım, plan/kesit, kapsam |
| R5 | Binalarda Enerji Performansı Yönetmeliği | Enerji tasarım gereksinimlerine kaynak rehberi | İklim, malzeme/katman, mekanik sistem, enerji hesabı; 2B plandan tek başına PASS yok |

Bu liste yalnız **indeksleme hedefidir**; güncel sürüm, yürürlük, değişiklik listesi, proje kapsamı ve dağıtım hakları bağımsız doğrulama gerektirir. Özel imar planı/plan notları, belediye veya yetkili kurum kararları, geçici/istisna hükümler ve TSE/TS gibi lisanslı standartlar uygunluğu değiştirebilir. Hukukî yorum kesin otomatikleştirilmez.

## 2. Kaynak envanteri ve belgenin değişmez kimliği

Her ham kaynakta:

```text
document_id, sha256, original_filename, source_url, host, format
official_title, publication_date, gazette_number, publication_identifier
retrieved_at, effective_from, effective_to, status
jurisdiction (nation/province/municipality/plan_id)
source_rank, document_kind (original/amendment/consolidation/circular/plan-note)
copyright_rights, redistribution_policy, review_state, reviewer_note
```

**Üç ayrı tarihin karışması yasak:** yayım tarihi, yürürlük tarihi, projeye uygulanabilirlik/ruhsat tarihi. `retrieved_at` sadece indirildiği gündür; mevzuatın yürürlük tarihi değildir.

Özgün kaynağın SHA-256'sı, daha sonra oluşturulmuş “konsolide yönetmelik” metninin hash'inden ayrı tutulur. Konsolide metin, hangi özgün yayın/değişikliklerden derlendiği doğrulanmadıkça **resmî kaynak yerine** gösterilmez.

**Kaynak edinme:** kullanıcı izni ve dağıtım hakkı uygunsa T.C. Resmî Gazete'nin özgün sayılarından veya doğrulanmış resmî mevzuat kaynaklarından yerel arşiv oluşturulur. Kaynağa çalışma sırasında online bağlanmak zorunlu değildir. [Resmî Gazete](https://www.resmigazete.gov.tr/).

## 3. Belge işleme ve hiyerarşik AST

```text
Source PDF / official HTML snapshot
  -> hash + source metadata
  -> native digital text + glyph bbox, yoksa yerel OCR + bbox
  -> layout blocks / reading order / multi-column guard
  -> header / bölüm / madde / fıkra / bent / alt-bent / ek / geçici madde
  -> tablo + hücre + dipnot + geçiş maddeleri
  -> version relations (amends / repeals / exception / references)
  -> reviewer validation
  -> immutable AST + section pointers + search indexes
```

**LegalNode v0.1 alanları**

```json
{
  "node_id": "local-example-article-1-paragraph-2",
  "regulation_id": "EXAMPLE-ONLY",
  "version_id": "unverified-synthetic",
  "parent_node_id": "local-example-article-1",
  "kind": "paragraph",
  "article_no": "1",
  "paragraph_no": "2",
  "item_no": null,
  "text": "[Sentetik örnek; gerçek mevzuat alıntısı değildir]",
  "document_sha256": "sha256-placeholder",
  "source_page_index": 12,
  "printed_page_label": "10",
  "source_polygons": [[[80, 124], [510, 124], [510, 168], [80, 168]]],
  "coordinate_system": "pdf_point",
  "ocr_line_ids": ["p12-col1-line19", "p12-col1-line20"],
  "table_cells": [],
  "publication_date": null,
  "effective_from": null,
  "effective_to": null,
  "verification": "UNVERIFIED"
}
```

Bu örnekte hiçbir madde veya sayı gerçek yönetmelik hükmü değildir.

**Zorunlu eşleştirme:** Madde/fıkra/bent metninin ilişkilendirildiği sayfada görünür olması; çok sütun / sayfa sonuna taşma / sütunlar arası birleşme / birleşik tablo hücresinin yanlış eşleşmemesi; OCR metni ile kaynak görselin gerektiğinde bağımsız kontrolü.

## 4. Hiyerarşik ve hibrit arama

### A. Lexical indeks

SQLite FTS5, `regulation_id`, `node_id`, `version_id`, `article_no`, `keyword`, `text` ve kategori üst verileriyle hazırlanır.

Terimler için Türkçe normalleştirme kontrollüdür: `ışıklık`, `ıslak hacim`, `kapalı çıkma`, `emsal`, `sığınak`, `kaçış`. Türkçe ek varyantları, yazım farkı ve birleşik terimler için küçük **sürüm kontrollü sözlük**; orijinal hukukî metin asla normalize edilerek değiştirilmez. FTS5'nin Türkçe dilbilgisel kök bulmayı tam yaptığını varsaymayız.

### B. Dense indeks

Yerel ve offline multilingual embedding modelleri karşılaştırılır (ör. `multilingual-e5-small` veya `bge-m3`); lisans/Windows/RAM/semantik başarı benchmark'ından sonra seçim yapılır. Başlangıçta CPU üzerinde az sayıda normlanmış vektörü NumPy ile aramak yeterliyse FAISS/Chroma zorunlu değildir. İndeks boyutu büyürse uygun yerel vektör kütüphanesi eklenir.

**Hibrit retrieval:** lexical top-k + dense top-k -> `RRF` ile aday birleştir -> `regulation,version,scope,date` metadata filtresi -> madde/fıkra ebeveyn bağlamı + tanımlar + uygulanabilir istisnalar -> gerekiyorsa CPU reranker.

Önerilen ilk RRF:
`score(d)= sum(1/(k+rank_i(d)))` (`k=60` başlangıç aday sabiti, benchmark ile ayarlanır).
Bu sadece **sıralama skoru**, hukukî güven veya doğrulama olasılığı değildir.

### C. Yürürlük ve kural bağı

`RegulationVersionGraph` **değiştirir, yürürlükten kaldırır, ekler, yürürlük tarihi, özel/geçici hüküm, atıf** bağları tutar.

**RuleBinding**:
- `rule_id`, `rule_version`, `algorithm_id`
- `legal_node_id`, `source_document_sha256`, `page_polygon`
- `required_project_facts` (izin/ruhsat tarihi, kullanım, belediye, kat vs.)
- `applicability_predicate`, `exception_predicate`
- `measurement_method`, `threshold_value`, `threshold_unit`, `tolerance_profile`
- `verification_state` (`DRAFT`, `REVIEWED`, `APPROVED_FOR_CHECK`, `RETIRED`), reviewer ve audit trail.

**Kesin kural:** OCR veya RAG sonucundan otomatik değer çıkarıp doğrudan üretim kuralı haline getirme. Uygulanabilir ve yürürlükteki hukukî sürüm ile sayı/ölçü kuralı **ayrı doğrulanıp** `APPROVED_FOR_CHECK` olmadığı sürece mevzuat `PASS` yasaktır.

## 5. İkili kanıt kartı ve sayfa/satır gösterimi

```text
BULGU #F-012  [REVIEW_REQUIRED]
  Pafta: zemin_kat.dxf  Layout: Model  Entity: A1C4, A1C5
  Tespit: geçiş açıklığının net genişliği belirsiz
  Referans: drawing SHA, CAD coords, ölçüm metodu, tolerans

  Mevzuat referansı adayı:
  Kaynak: Yönetmelik + orijinal yayın tarihi + Resmî Gazete no
  Madde / fıkra / bent: kaynak taraması tamamlanınca doldurulur
  Özgün PDF: sha256 / PDF sayfası / kaynak polygon
  Metin satırı: OCR/yerleşim tarafından TÜRETİLMİŞ line ID
  Değişiklik / istisna / yürürlük: henüz doğrulanmadı -> PASS yok
```

### Kullanıcı ekranında

**Sol panel:** CAD/PDF görüntüleyici -> problemli nesneye zoom; çokgen renk işareti; boyut çizgisi, ölçüm/ölçek ve tolerans.

**Sağ panel:** **aynı hash'e ait özgün PDF** (veya özgün resmî HTML); tam sayfa önizlemesi; ilgili metin bloğuna bbox highlight; belge adı, Resmî Gazete tarih/sayı, PDF sayfa indeksi ve basılı sayfa etiketi; madde/fıkra/bent ve varsa tablo hücresi; değişiklik/istisna bağlantılarını ayrı göster.

**Üçüncü bant:** durum, hesap, kural sürümü, geçerli coğrafya/tarih, gerekli eksik bilgi, kullanıcı inceleme sonucu.

**Kullanıcı “satırı göster” dediğinde:** kaynak PDF sayfasında OCR'ın bulduğu alan ve `line_id` highlight edilir; o satır numarasının OCR sonrası türetilmiş olduğu yazılır. İki sütunlu veya satırları tespit edilemeyen PDF'de satır uydurmak yerine blok/hücre bbox gösterilir.

### Belge biçimlerine göre dürüst etiket

- **Gerçek PDF:** “Özgün PDF — sayfa X, koordinat alanı Y”.
- **Resmî HTML:** “Özgün resmî HTML — bölüm/madde”; browser'dan türetilen PDF “dönüştürülmüş kopya” diye etiketlenir.
- **Konsolide metin:** “Birleştirilmiş metin; kaynak değişiklik zinciri”; her değişikliğin özgün yayını ayrıca kaynaklanır.
- **Tarama OCR:** “OCR okuması, doğrulama durumu”; biçim bozulmasında manuel inceleme.

## 6. Kural ve kanıt sonuçları

`PASS`, `FAIL`, `REVIEW_REQUIRED`, `INSUFFICIENT_EVIDENCE`, `NOT_APPLICABLE`, `ERROR` durumları korunur. Hukukî kaynak eksik olduğunda **geometrik bulgu mevcut olabilir**, fakat `COMPLIANCE_PASS` ayrı işaretlenemez.

Mevzuat hükmüne dayalı bulgu bir *ikili kontrol* içerir:
1. **Geometry Check Status:** Ölçüm doğru ve yeterli mi?
2. **Legal Applicability Status:** Bu kural ilgili konum/tarih/yapı için geçerli ve doğrulandı mı?

Sonuç ancak ikisi de güvenilir olduğunda kesin `PASS/FAIL` olabilir. RAG “bu maddeye benziyor” sonucu yalnız `CANDIDATE_SOURCE` oluşturur.

## 7. Metin hakkı ve yerel arşiv

- T.C. Resmî Gazete: [resmigazete.gov.tr](https://www.resmigazete.gov.tr/); değişiklik ve yayın tarihi için resmî kaynak.
- Resmî derlenmiş mevzuat içerikleri uygun olduğu ölçüde ayrıca kaynaklanır. Güncelliği otomatik varsayılmaz.
- Mahallî plan notları, imar plan kararları ve ruhsat/geçiş tarihleri farklı yetkili kaynaklardan gelebilir.
- TSE/TS standartları ve proje belgeleri gibi telif veya özel kullanım sınırlı malzemeleri **public GitHub deposuna ekleme**; gerektiğinde lisanslı kullanıcı dosyası olarak yerel sakla.
- Güncelleme için çevrim içi resmî kaynak temini yalnız ayrı, açık kullanıcı işlemi; normal RAG ve denetim offline kalır.
- Bağımsız kaynaktan doğrulanamayan normlar "taslak/yetersiz kanıt" statüsündedir; tamamlandı denmez.

## 8. Yerel altyapı

- **SQLite:** `documents`, `nodes`, `node_spans`, `tables`, `table_cells`, `versions`, `amendments`, `rule_bindings`, `review_events`, FTS5 sanal tablosu.
- **Yerel CPU embedding:** seçilecek modele göre saklanan vektörler / küçük veri için NumPy top-k; büyüyünce doğrulanmış FAISS CPU opsiyonu.
- **Haricî vector DB sunucusu yok:** Qdrant, Chroma server, Redis, Neo4j ve PostgreSQL ilk sürüm için zorunlu değil.
- **Kimliklendirme:** bir kaynak `document_sha256` değişince span/line bbox referansları otomatik yeniden doğrulanır; eski sayfa konumu kör biçimde yeniden kullanılmaz.
- **Deterministik scoring:** aynı korpus sürümü, model hash'i ve indeks parametreleri korunur; embedding retrieval sonuçları ve hukukî onay birbirinden ayrı kaydedilir.

## 9. Kabul senaryoları — tasarım

- L01: Madde/fıkra PDF sayfasında doğru highlighted bbox; tablonun satırı/hücresi ayrı görünür.
- L02: Geçmiş sürüm metni yeni sürümle karışmaz; yürürlüğe giriş tarihi eksikse kontrol `REVIEW_REQUIRED`.
- L03: Maddeye istisna uygulandığı durum belgeyle doğrulanmadan `PASS` yok.
- L04: Kaynak hash'i değişirse eski bbox kanıtı kullanılamaz.
- L05: Belediye plan notu veya yapı kullanım türü bilinmiyorsa mevzuat kararı otomatik kesinleşmez.
- L06: OCR hatalı madde numarasını üretmişse reviewer doğrulaması olmadan kural registry'ye girmez.
- L07: Offline ortamda yerel hukukî korpus içinde kaynak arama çalışır; ağ çağrısı yapılmaz.
- L08: Vektör arama devre dışı olsa bile FTS5 ile ilgili hüküm adayları görüntülenebilir.
- L09: Taranmış PDF'de OCR line ID'si özgün yasal satır numarası gibi gösterilmez.
- L10: Hukukî `PASS` için kaynak, sürüm, uygulama bağlamı, ölçüm ve kullanıcı incelemesi gerektiren statüler geçmelidir.

**Not:** Bunlar tamamlanmış testler değildir; ileride hedef Windows üzerinde çalıştırılacak.

## 10. En kritik doğruluk notu

Belirli bir yönetmeliğin örnek madde/fıkra numarasını, minimum kapı genişliği veya koridor eşiğini **uydurmamak** için ilk aşamada hiçbir hukukî sayı kuralı üretim setine konulmayacak. Önce özgün resmî kaynakların güncel ve proje tarihindeki hâli toplanacak, hukukî ilişki / güncelleme zinciri çıkarılacak, insan incelemesiyle kuralın ölçüm tanımı ve uygulanabilirlik koşulu onaylanacak.

**Uygulama kaydı:** [islem_003.md](islem_003.md)

**İşlem 004 PDF lisans kapısı:** PyMuPDF'nin AGPLv3/ticari lisans koşulları sebebiyle offline mevzuat ETL katmanı `PdfTextBackend` ile soyutlanır. Kapalı kaynak/ücretsiz müşteri dağıtımı için `pypdfium2` ve `pdfplumber` alternatifleri lisans+bounding-box doğruluğu karşılaştırmasından geçecek. “PyMuPDF önce” teknik prototip önerisidir; ticari dağıtım onayı değildir. [PDF lisans incelemesi](pdf-lisans.md).
