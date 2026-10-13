# İşlem 013 — Çevrimdışı mevzuat PDF → LegalAST ve özgün kaynak kanıtı

- **Tarih:** 2026-10-13
- **Durum:** UYGULANDI — PDF kaynaklı LegalAST + sentetik Ubuntu/Windows CI PASS; resmî mevzuat/hukukî sürüm, gerçek OCR modeli ve bağımsız hukukî kabul HOLD.
- **Temel kaynaklar:** [Mevzuat doğrulama protokolü](mevzuat-dogrulama-protokolu.md) ve [Mevzuat RAG mimarisi](mevzuat-rag.md).
- **Hedef:** F13, kaynak PDF → kaynak koordinatlı yapılandırılmış hukukî kanıt adayları. F08–F12, F14–F15 henüz hukukî olarak etkinleştirilmez.
- **Kesin teknoloji:** `pdfplumber` native text+table; `pypdfium2` render; `RapidOCR + onnxruntime CPU` yalnız açıkça sağlanan yerel OCR motoru. PyMuPDF/Unlimited-OCR kullanılmaz.
- **Çalışma biçimi:** yerel dosya girişi; internet erişimi/API/model indirmesi yok. PDF veya mevzuat telif içeriği GitHub'a konulmayacak; yalnız sentetik PDF fixture oluşturulacak.

## 1. Uygulanacak kod sözleşmesi

1. `src/mimarllm/legal/models.py`: `LegalDocument`, `LegalSourceSpan`, `LegalNode` (BÖLÜM/MADDE/GEÇİCİ_MADDE/FIKRA/BENT/BAŞLIK), `LegalTable/LegalTableCell`, `LegalChangeCandidate`, `LegalReviewIssue`, `LegalDocumentMetadata` Pydantic modelleri. Her kaynak span **orijinal PDF SHA-256 + 0-based page index + page-top-left PDF point bbox/polygon + extraction method** içerir. Basılı sayfa numarası bilinmiyorsa `null`; OCR satır sayısı basılı sayfa/kanunî madde değildir.
2. `src/mimarllm/legal/extractor.py`: gerçek `pdfplumber` kelime/karakter/tabloları birleştirerek sayfa bazlı, kaynak pozisyonlu satır gözlemleri, hücre geometrisi. Belge ve sayfa sayısı, kelime/tablolar/hücreler ve byte bütçeleri; PDF parse/rotation/reading-order belirsizliğinde diagnostik. İki sütunlu/güvenilmez okuma sırası `REVIEW_REQUIRED`; sessiz kesin doğrulama yok.
3. `src/mimarllm/legal/parser.py`: yapılandırılmış satırlar üzerinde kararlı Türkçe madde/fıkra/bent/GEÇİCİ MADDE ve bölüm tanıma, devam satırlarını kaynak span zincirine ekleme; tabloların üst metin/madde ile yalnız inceleme adayı olarak ilişkilenmesi. Bu aşama bütün tarihsel Resmî Gazete biçimlerini kapsadığı iddiasında bulunmaz.
4. `src/mimarllm/legal/changes.py`: değişiklik/ilga/yürürlük ifadelerini **kaynak bağlı aday** olarak işaretleme; tarih, yürürlük, istisna veya hüküm değiştiren ilişkiyi otomatik hukukî gerçek sayma ya da konsolide metin yaratma yok.
5. `src/mimarllm/legal/etl.py`: yerel `parse_legal_pdf(path, metadata, ...) -> LegalDocument` ve deterministik JSON dosyası dışa aktarımı, açıkça talep edilen OCR sayfa listesi ve enjekte edilmiş RapidOCR CPU adaptörü. Özgün PDF değiştirilmez, indirilmez; hash analiz öncesi/sonrası kontrol edilir.
6. `tests/test_legal_etl.py`: ReportLab ile üretilen çok sayfalı sentetik Türkçe PDF (yazı tipi kabiliyeti kadar), madde/fıkra/bent, GEÇİCİ MADDE, başlık, tablo hücre kaynakları, yürürlük/değişiklik adayları, kaynağa geri gidiş, raster/OCR mock poligonu, bozuk belge, LIMIT ve hash, birden çok fıkra, parser hatası. Windows ve Ubuntu GitHub CI.
7. `docs/specs/legalast-v0.1.md`, README ve F13 envanter/karar/yol haritası güncellemeleri.

## 2. Doğruluk ve hukukî kilitler

- `source_url`, `publication_date`, `gazette_number`, `regulation_id`, `document_kind` dışarıdan beyan edilen **inceleme bekleyen metadata**; internetten doğrulanmış otorite kimliği değildir.
- Native metin, OCR metni, dönük glyph veya tablo hücresi farklı kaynaktır; yöntemi ve güven sınırı korunur. OCR ile otomatik madde doğruluğu gerekmez; kullanıcı incelemesi şart.
- Satır veya tablo hücresine verilen bbox PDF sayfasında vurgulanabilir olmalı; desteklenmeyen işaretlemede yanlış konumdan kesin atıf çıkarılamaz.
- Değişiklik PDF'indeki `MADDE 1` asıl yönetmeliğin `Madde 1`i olarak **otomatik birleştirilmeyecek**. Tek belge AST'si ile konsolidasyon ayrı iş.
- `LegalDocument.review_status` her zaman `UNREVIEWED`; `APPROVED_FOR_CHECK` veya yasal `COMPLIANT` bu işlemde yok. Var olan `RuleEngine` REGULATORY HOLD korunur.
- Basılı sayfa numarası için OCR tahmini varsayılan asıl kaynak değil; elle doğrulanmadıkça null.
- Tek sayfa çok sütun/dipnot, devam eden satır/bent, tekrar edilen madde başlığı, ekler ve karmaşık/çizgisiz tablolar için güvenli hata/inceleme çıktısı ve kapsama sınırları dürüstçe belirtilir.
- Parser deterministik, CPU/RAM bütçeli ve VLM'den bağımsız. Gerçek Resmî Gazete/OCR doğruluğu ve hukukî sonuç kabulü için kullanıcı kaynaklarıyla bağımsız inceleme bekler.

## 3. Gerçek commit ve test sonuçları

**Zorunlu ön kayıt ilk yazım:** `docs/islem_013.md`, commit `f9bd34886e89afb5c4f531981f6ab90b293a3732` **uygulama dosyalarından önce** oluşturuldu. 001–012 kaydı üzerine yazılmadı.

| Dosya | Yapılan uygulama | Commit |
| --- | --- | --- |
| `src/mimarllm/legal/models.py` | LegalDocument/Metadata, LegalLine/Node/SourceSpan, TableCell/Table, ChangeCandidate, ReviewIssue; UNREVIEWED ve certification=False şema kilidi | `2d5256a7` |
| `src/mimarllm/legal/extractor.py` | `pdfplumber` native satır/gerçek hücre bbox, PDF SHA, girdi bütçesi, açıkça seçilen sayfada `pypdfium2 + RapidOCR CPU` koordinatı | `6706875e` |
| `src/mimarllm/legal/parser.py` | Türkçe BÖLÜM/MADDE/GEÇİCİ MADDE/FIKRA/BENT, devam span'ı ve tablo parent adayı, ASCII transliterasyonu, aynı satırdaki fıkra | `3928fcd1`, `5dd931b5`, `32138c19` |
| `src/mimarllm/legal/changes.py` | Değişiklik/ilga/yürürlük/istisna **metinsel adayları**, node ve kaynak PDF satırına bağ | `99bf89d3` |
| `src/mimarllm/legal/etl.py` | Offline `parse_legal_pdf`, hash validasyonu, JSON export (sessiz overwrite yok), AST limit hatası | `37ace2ee`, `4e9892cf` |
| `src/mimarllm/legal/__init__.py` | Yeni aynı paket içinde legal modül | `df5c37fe` |
| `tests/test_legal_etl.py` | ReportLab ile gerçek sentetik 2 sayfalı Türkçe PDF/tablo, native/OCR quad, source SHA, hiyerarşi, değişiklik, hukukî onay reddi, JSON, limitler ve inline fıkra | `60ed4eac`, `d4a78460`, `dfbabc92` |
| `.github/workflows/core-contracts.yml` | Legal ETL sentetik testlerini mevcut Ubuntu/Windows CI matrisine bağ | `ed548837` |
| `docs/specs/legalast-v0.1.md` | Kullanım, kaynak koordinatı, AST ve hukukî HOLD şartnamesi | `ef6a9113` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F13 KISMI, K-092…K-100 kararları ve 014–015 bağlantısı | `e154b355`, `b8eed947`, `ccc372eb`, `c50cd021` |

### CI ve başarısız testlerin açıklaması

- İlk tümleşik [run 38375659668](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38375659668): Ubuntu **171 PASS, 2 FAIL**. İki sorun: sentetik belgede fıkra sayısı testte 3 sanılmıştı, gerçekte 4'tü; `max_nodes` aşımında genel `ValueError` yükseliyor, tutarlı `LegalInputError` kullanılmıyordu. Fixture beklentisi ve hata türü düzeltildi.
- Düzeltmeden sonraki [run 38375826267](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38375826267): Ubuntu/Windows **173 PASS**, 0 FAIL.
- Yaygın `MADDE 1 – (1) ...` örüntüsüne aynı satırda fıkra ve dürüst **tam-satır PDF bbox** paylaşma desteği, ilga ifadesinin aday olması testleri eklendi.
- **Son kaynak test commit `dfbabc92bac10e4e9a309c67774873a01953f381` için [GitHub Actions 38376004832](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38376004832): Ubuntu Python 3.11 175/175 PASS (2,85 s); GitHub-hosted Windows Python 3.11 175/175 PASS (7,56 s)**. Her iki işin job logları ayrı incelendi.
- Sentetik PDF dokümanları ReportLab ile test çalışma anında oluşturulup gerçek `pdfplumber` tarafından okunuyor, tablo hücre bbox'ları ve metinler geri test ediliyor. OCR metin/quad **enjekte edilen sahte yerel reader** ile doğrulanıyor; gerçek RapidOCR model inference test edilmedi. Gerçek resmî gazete PDF corpus/yıl dönemi, bağımsız hukukî inceleme veya kullanıcı i7/RTX4070 Windows donanımı test edilmedi.

## 4. Açık riskler, hukukî HOLD ve sonraki işlem

**Kodlanan teknik katman:** Yerel PDF→LegalAST, çok sayfa, native metin, çizgili vektör tablo hücreleri, kaynak SHA+page+bbox/polygon, açıkça seçilen raster sayfada OCR quad, madde/fıkra/bent ve değişiklik/yürürlük/istisna *ifade adayları*. JSON dışa aktarımı user/localdır, PDF deposu GitHub'a eklenmedi.

**Kritik eksikler:** Yıllara göre tüm resmî PDF'lerin indirilmesi ve kaynak resmiyetinin doğrulanması, her resmî Gazete'nin karmaşık sütun/dipnot/tablo OCR/layout testi, özgün PDF üstünde bağımsız hücre-vurgu incelemesi, yürürlük/değişiklik/istisna ilişkilerinin tarihsel konsolidasyonu, yerel idari uygulanabilirlik ve hukukî uzman/denetçi onayı. Kod yalnız ifadeleri işaretler; iddia ettiği resmî tarih ve norm hükmünü otomatik karara dönüştürmez.

**Özellik sonucu:** F13 **KISMI / MEVCUT_KOD + Linux/Windows sentetik CI PASS**. F08–F12 **HUKUKI_HOLD**. İşlem 012'deki `RuleEngine` `REGULATORY` kilidi **değiştirilmedi ve açılmadı**; LegalAST `review_status=UNREVIEWED`. İki sütunlu sayfalar, çizgisiz/raster tablolar, eski ve yeni Resmî Gazete yazı tipleri ve OCR karakter doğruluğu ayrıca kabul ister.

**Sıradaki İşlem 014:** Kaynak `LegalAST` üzerinde offline SQLite FTS5 + yerel dense embedding/RRF/retriever, özgün PDF span/quad erişimi. Arama skoru hukukî uygunluk/otorite skoru değildir. Bu işlem için önce `docs/islem_014.md` açılacaktır.
