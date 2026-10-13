# LegalAST v0.1 — Offline PDF Evidence and Structural Parsing

- İşlem: [islem_013.md](../islem_013.md).
- Durum: Sentetik Linux/Windows CI ile kod doğrulaması. Gerçek Resmî Gazete kaynaklarının bağımsız hukukî kabulü HOLD.
- Motorlar: pdfplumber (metin ve vektörel tablo hücreleri), pypdfium2 (sınırlı raster render), RapidOCR + onnxruntime CPU (yalnız açıkça enjekte edilmiş model). PyMuPDF veya Unlimited-OCR yok.

## 1. Kullanım ve çıktı

`parse_legal_pdf(path, metadata, ocr_pages=(), ocr_engine=None)` fonksiyonu yerel PDF'yi açar ve `LegalDocument` üretir. `export_legal_json(ast, destination)` ayrıca çağrılmadıkça diske yeni dosya yazmaz; JSON dışa aktarmada mevcut dosya üzerine yazmayı reddeder.

`LegalDocument` aşağıdaki kaynakları tutar:

- `document_sha256`: orijinal PDF içeriğinin hash değeri, ETL sonunda tekrar karşılaştırılır.
- `metadata`: kullanıcı beyanı `regulation_id`, belge türü ORIGINAL/AMENDMENT/CONSOLIDATION/UNKNOWN, gazete tarih/sayı, kaynak URL ve olası yürürlük tarihleri. **Tümü USER_ASSERTED_UNVERIFIED; kaynak doğrulaması değil.**
- `lines[]`: PDF sayfa koordinatında düzenlenmiş metin satırları, kaynak yöntemi ve özgün bbox/quad.
- `nodes[]`: SECTION, ARTICLE, TEMPORARY_ARTICLE, PARAGRAPH, ITEM, TEXT ile parent_node_id; her düğümün bir veya daha fazla özgün source span'ı.
- `tables[]`: vektörel tablolar, satır/sütun indisi, gerçek hücre bbox, metin, yalnız aday parent bağ.
- `changes[]`: AMENDMENT_MENTION/REPEAL_MENTION/EFFECTIVITY_MENTION/EXCEPTION_MENTION; özgün satır referansı; resmî değişiklik sonucu DEĞİL.
- `issues[]`: eksik kaynak, muhtemel çok sütun, hatalı/eksik tablo hücresi, sayfa sınırı, OCR/native uyuşmazlığı vb.
- `review_status=UNREVIEWED` ve `legal_compliance_certified=False` zorunludur; nesne kopyası değiştirilip yeniden doğrulanırsa onaylı gibi sunulamaz.

## 2. Kaynak PDF'ye geri gitme

`LegalSourceSpan` => orijinal belge SHA-256, sıfır tabanlı `page_index`, dört köşeli PDF sayfa-üst-sol koordinatı, extraction method (`NATIVE_PDF` / `RAPIDOCR_CPU`), reference type (`NATIVE_BBOX` / `TABLE_CELL_BBOX` / `OCR_DETECTION_QUAD`), OCR confidence (varsa). Basılı sayfa numarası otomatik uydurulmaz; `printed_page_number` başlangıçta null.

Native metin/tabloların bbox'ı, dönük glyph'in gerçek dörtgeni değildir. OCR polygon'u kaynaktaki tespit poligonudur; okunmuş hükmün hukuken doğru olduğunun kanıtı değildir. Tablodaki kelimeler ana metin çizelgesine ayrıca eklenmez; hücre kaynakları korunur.

## 3. Hiyerarşik ayrıştırma sınırları

- SECTION: BÖLÜM/BOLUM başlığı. ARTICLE: MADDE 1. TEMPORARY_ARTICLE: GEÇİCİ MADDE 1. PARAGRAPH: (1). ITEM: a) / a-. Devam satırları aktif düğümün source span'larına eklenir.
- MADDE 1 – (1) ... gibi tek satırlı fıkralar ayrı düğüm olabilir, ama article ve paragraph **aynı satır bbox'ını paylaşır**. Kod `INLINE_PARAGRAPH_FULL_LINE_BBOX` uyarısı verir; ortadan kesilmiş yapay koordinat üretmez.
- `document_kind=AMENDMENT` belgesinin MADDE 1'i, değiştirilen ana yönetmeliğin MADDE 1'i sayılmaz. `AMENDMENT_ARTICLE_NOT_CONSOLIDATED` uyarısı tutulur.
- Birden fazla sütun, üstbilgiler/dipnotlar, çizgisiz/raster tablolar, karışık satır içi bentler, farklı yıllardaki gazete biçimleri ve karmaşık ekler otomatik kesin doğrulama kapsamı değildir.

## 4. Yürürlük ve değişiklik

ETL, değiştirildi/yürürlüğe girdi/ilga/istisna ifadelerini **metinsel aday** olarak kaydeder. Hukukî yürürlük aralığı, konsolide metin, istisna kapsamı, karşı hüküm ve değişiklik zinciri ayrı hukukî inceleme olmadan üretilmez. Kullanıcının `claimed_publication_date` alanını doldurması resmî gazetenin doğrulanması değildir.

## 5. Kaynak ve güvenlik sınırları

- PDF dosyası yerel dosyadan, imza ve boyut limitleriyle açılır. Model indirme veya ağ isteği yoktur. Özgün PDF GitHub'a yüklenmez.
- Varsayılan: 50 MiB PDF, 100 sayfa, 40000 native kelime/sayfa, 60000 toplam satır, 50000 AST node, 60 tablo/sayfa, 8000 hücre/sayfa.
- Raster PDF'de OCR yalnız `ocr_pages=(...)` ve önceden kurulmuş `ocr_engine` ile; 15 sayfa ve her render için 8 milyon piksel varsayılan limitleri.
- İki sütunlu sayfa için okuma sırası sezgiseldir, olası durumlarda ISSUE raporlanır. Her belge zaten UNREVIEWED'dur.
- CropBox ve rotasyon eşleştirmesi `render_region` sınırlarına tabidir; yanlış konum üretmek yerine işlem reddedilebilir.
- PDF parse/rotasyon/OCR doğruluğu ve RAM sınırları gerçek Resmî Gazete örnekleriyle ayrıca test edilmelidir.

## 6. Özellik durumu ve sonraki paketler

**F13: KISMI / MEVCUT_KOD — sentetik PDF ve Linux/Windows CI.** Özgün Resmî Gazete külliyatı indirilmedi, sürümleri birleştirilmedi, gerçek OCR doğruluk ölçümü ve bağımsız madde-fıkra eşleştirmesi yapılmadı.

**İşlem 014:** SQLite FTS5 + yerel dense/RRF ile LegalAST retrieval; arama hit'inden özgün PDF sayfası ve poligonuna geri gitme. Arama skoru hukuken doğruluk puanı değildir.

**İşlem 015:** Birebir kaynak onayı, yayın/yürürlük/değişiklik/istisna ve proje uygulanabilirliği doğrulanmadan F08–F12 gerçek mevzuat kural paketleri etkin değildir. İşlem 012 RuleEngine REGULATORY kapısı kilitli kalır.
