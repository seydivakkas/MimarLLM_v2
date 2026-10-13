# İşlem 013 — Çevrimdışı mevzuat PDF → LegalAST ve özgün kaynak kanıtı

- **Tarih:** 2026-10-13
- **Durum:** ÖN KAYIT — **işlem 013'ün ilk GitHub yazımı**; koddan önce açıldı.
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

Uygulama sonunda dosya bazında commit SHA, Linux/Windows gerçek CI durumu, başarısız fixture'lar ve açık hukukî/mühendislik riskleri eklenecek.
