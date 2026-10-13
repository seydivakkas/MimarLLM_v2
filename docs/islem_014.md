# İşlem 014 — Çevrimdışı Hibrit Mevzuat RAG: SQLite FTS5 + yerel embedding + RRF

- **Tarih:** 2026-10-13
- **Durum:** ÖN KAYIT. İşlem 014 kapsamında **ilk GitHub yazımı**; yeni kod ve diğer dokümanlardan önce oluşturuldu.
- **Önkoşullar:** İşlem 013 `LegalAST` (`UNREVIEWED`), işlem 012 `RuleEngine` (`REGULATORY` kilitli).
- **Donanım ve erişim:** Windows-first; offline, CPU varsayılan; 32 GB RAM/8 GB VRAM hedefi. **Ağ/API üzerinden model veya belge indirmesi yok**. Yazma işlemleri yerel SQLite/veri dizinine.
- **İşlev sınırı:** Arama isabeti, resmî kaynağın doğrulandığı veya hukuken geçerli maddeyi ispatladığı anlamına gelmez.

## 1. Geliştirme kapsamı

1. `src/mimarllm/rag/models.py`: arama sonucunda `document_sha256`, `regulation_id`, `document_kind`, `node_id`, `parent/article/paragraph/item`, `LegalSourceSpan` dörtgenleri, OCR/native kaynak yöntemi, `FTS5/rerank` sıra ve RRF skorları, `UNREVIEWED` durumu. PDF sayfası+polygon geri verilecek, gerçek URL veya resmî onay uydurulmayacak.
2. `rag/store.py`: yalnız yerel `sqlite3` ile FTS5/BM25; `LegalDocument` kapsamını Pydantic ile yeniden doğrulayarak kimlik+orijinal kaynak SHA saklama; section/article/paragraph/item düğümleri ve `LegalTableCell` kayıtlarını **farklı belgeye taşınmadan** ayrı satırlar olarak dizinleme; kimlikli parent bağları ve kaynak poligonlarının JSON'u; transaction/UPSERT/idempotent yeniden indeksleme, gerekiyorsa kaynak dosya değişiminde eski vektörleri temizleme. FTS sorgusu güvenli, SQL parametreli; DoS limitleri.
3. `rag/embeddings.py`: model çağrısı için `LocalEmbedder` sözleşmesi. **Gerçek dense embedding** yalnız açıkça sağlanan, kurulu yerel model+model dosyalarıyla (CPU, `local_files_only`, `trust_remote_code=False`) çalışacak; sahte anlamsal başarı iddiası yok. Varsayılan embedding **kapalı**, ana bağımlılıklara ağır PyTorch/sentence-transformers eklenmez. Vektörler için sonlu, boyutu kontrol edilen sabit-dim JSON+cosine (v0.1 bounded scan). Fake test embedder yalnız numerik hibrit pipeline kabulüdür.
4. `rag/retriever.py`: FTS BM25 sırası, isteğe bağlı dense cosine sırası, sabit `k=60` ile RRF, deterministik bağ kırma, candidate source provenance, top_k/limit. Yalnız FTS varsa lexical-only; dense-only eşleşmeler de geri verilebilecek.
5. `rag/indexer.py` / `rag/__init__.py`: kullanımı kolay API; hiçbir bulut servisine ve otomatik model indirmesine izin vermeyen varsayılan.
6. `tests/test_rag.py`: sentetik LegalAST kaynak PDF'den uçtan uca ingest→aranan hukukî kelime→madde/fıkra→gerçek page polygon; tablonun hücre konumu, çoklu belge SHA izolasyonu, Türkçe karakter, özel/SQL injection sorgu, aynı dosyanın yeniden indekslenmesi, hayali metadata ve kaynak ret, iki mod RRF ve sahte embedding kaynağı, null/NaN/dimension ve sınır bütçeleri.
7. `.github/workflows/core-contracts.yml` Linux+Windows CI entegrasyonu; `docs/specs/rag-v0.1.md`, README, envanter/yol haritası ve karar kayıtları.

## 2. Katı kabul ve hukukî sınırlar

- *Indeks kaydı* yalnız gerçek `LegalDocument` AST'sinden; `UNREVIEWED` inceleme statüsü korunur. Zorunlu parent/hiyerarşi ve kaynak page polygon'u aranabilir.
- `LegalTableCell` orijinal `source.reference_type=TABLE_CELL_BBOX` olarak geri dönecek; kimliği bilinmeyen veya kaynağı yanlış hücre reddedilecek.
- Aynı PDF'den ayrı düğüm kayıtları `docsha:nodeid` ile kimliklendirilir; bir değişiklik yönetmeliği asıl sürüme otomatik konsolide edilmez.
- Embedding modeli dış dosya konumunu *bilinçli* kullanıcı sağlar; yerel model yoksa FTS araması çalışır, `dense_enabled=False`; vektör temsil/testleri gerçek semantik kalite puanı değildir.
- Arama sonuçları **orijinal PDF kaynağı, sayfa ve poligon** verir; PDF dosyasının kendisi arşivde yoksa görüntüleme katmanı `ORIGINAL_PDF_NOT_PRESENT` gösterecek, hayalî URL açmayacak.
- VLM/RAG, `RuleEngine` REGULATORY mevzuat kilidini kaldıramaz: hukukî onay ayrıca gerekecek. SQLite query ve retrieval score kural kararı değildir.
- Kullanıcıya “tam destek”, “model doğrulandı”, “hukuken uyumlu” veya gerçek yönetmelik indeksi oluşturuldu denmeyecek; sentetik test ve gerçek kullanım sınırları açık.

## 3. İş sonunda güncellenecek kabul

Yazılan gerçek dosyalar/commit SHA, Ubuntu/Windows job logları, testte bulunan hatalar, kalan teknik ve hukukî HOLD burada kayıtlanacak.
