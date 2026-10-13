# İşlem 014 — Çevrimdışı Hibrit Mevzuat RAG: SQLite FTS5 + yerel embedding + RRF

- **Tarih:** 2026-10-13
- **Durum:** UYGULANDI — SQLite FTS5/BM25 ve yerel dense/RRF çekirdeği GitHub'da; Ubuntu/Windows 197/197 sentetik CI PASS. Gerçek embedding modeli/Resmî Gazete/hukukî kabul HOLD.
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

## 3. Gerçek GitHub commitleri ve geliştirilen dosyalar

**Ön-kayıt ilk commit:** `835ae64de52465dff68470d98ca7f31650f9f437`. **Diğer bütün İşlem 014 yazımlarından önce** `docs/islem_014.md` dosyası oluşturuldu; 001–013 geçmişi değiştirilmedi.

| Dosya | Gerçek uygulama | Örnek commit |
| --- | --- | --- |
| `src/mimarllm/rag/models.py` | `IndexedPassage`, `RagHit`, `RagResponse`, PDF source spans, table row/column, sabit hukukî sertifikasyon yasağı | `249e2e63`, `04baf79c` |
| `src/mimarllm/rag/embeddings.py` | `LocalEmbedder`, CPU-only preinstalled SentenceTransformer, `local_files_only`, `trust_remote_code=False`, finite-normalized embedding kontrolü | `8f2807ab` |
| `src/mimarllm/rag/store.py` | SQLite FTS5/BM25, Türkçe Unicode normalize arama, node+table cell ID, SQLite source span JSON, transactional/idempotent re-index, bounded cosine dense ve çoklu PDF hash ayrımı | `71972adf`, `fd502129`, `891a384e` |
| `src/mimarllm/rag/store.py` | Özgün PDF yolu verilirse SHA ve PDFium sayfa boyutlarıyla vurgulama polygon bounds doğrulaması | `dad8804a` |
| `src/mimarllm/rag/retriever.py` | FTS/dense rank, `RRF(k=60)`, deterministic tie-break, `top_k`, docsha/regulation filtreleri, kaynak PDF erişimi, `legal_compliance_certified=False` | `aff9c93d` |
| `src/mimarllm/rag/indexer.py`, `__init__.py` | Gerçek yerel PDF→LegalAST→SQLite indeks `index_local_legal_pdf`, `search_legal`, `LegalRagStore` API | `d92f9131`, `3e496338` |
| `tests/test_rag.py` | Sentetik yerel PDF ve tablo kaynak konumları, FTS Türkçe, kalıcılık, çoklu doc/yeniden indeks, SQL özel sorgu, hash/bounds, 4D sahte dense stub/RRF, hatalı vektör, DoS bütçesi, gerçek PDF availability | `645c880f`, `39d9214a`, `3fcb24e1` |
| `.github/workflows/core-contracts.yml` | `rag/**` ve `test_rag.py` Linux+Windows matrix | `3ddd2aaa` |
| `docs/specs/rag-v0.1.md` | API, örnek, teknik limit, offline model, hukukî onay sınırları | `b8a44301` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F14 `MEVCUT_KOD/KISMI`, K-101–110 kararlar ve sonraki 015 | `f0ddc1e6`, `1daca78d`, `193c204b`, `388c82e3` |

## 4. GitHub Actions sentetik CI — doğrulanmış sonuçlar

- İlk FTS5/RRF kod ve test seti, [GitHub Actions **38421311127**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38421311127): **Ubuntu 195 PASS**, **GitHub-hosted Windows 195 PASS**.
- Kaynak PDF sayfa sınırı ve yanlış konumda PDF highlight reddi eklenerek [GitHub Actions **38421716450**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38421716450): **Ubuntu 197 PASS**, **Windows 197 PASS**.
- En son `3fcb24e1c5930b6ff36b1829f5a725c32c19b75c` kaynak commit'inde RRF'nin bağımsız aritmetik sonucu da test edildi. **[GitHub Actions 38422429371](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38422429371) — Ubuntu Python 3.11 197/197 PASS (3,74 saniye); Windows GitHub-hosted Python 3.11 197/197 PASS (7,07 saniye)**. İki işin logları ayrı ayrı okundu; sonuç **success/success**.
- Gerçek `ReportLab` sentetik PDF → `pdfplumber` LegalAST → SQLite FTS5 tablosu → BM25 → kaynak PDF bbox; ayrı bir deterministic **fake 4D local embedder** ile cosine/RRF arama akışı doğrulandı. **Gerçek çokdilli embedding ağırlığı yüklenmedi, Türkçe model kalitesi/latency benchmarkı ölçülmedi.**
- GitHub-hosted Windows CI, kullanıcının i7/RTX 4070/32GB Windows sisteminde gerçek müşteri paftası/Resmî Gazete testi değildir.

## 5. Tamamlanan çekirdek ve eksik kabul kapıları

**Kodlandı:** `LegalAST` `UNREVIEWED` doğrulaması ve PDF kimliğini koruyan node/table-cell ingest, gerçek source page/quad saklama, Türkçe diacritic/FTS5 BM25, safe MATCH, idempotent transaction, SHA filtresi, gerçek PDF mevcutsa hash ve sayfa koordinatı sınırı kontrolü, opsiyonel `LocalSentenceTransformer` offline/CPU sözleşmesi, sınırlı cosine ve RRF rank fusion, model yokken `LEXICAL_ONLY`. RAG sonuçlarında hiçbir hukukî onay yok.

**HOLD:** Gerçek yerel çokdilli öğrenilmiş embedding modelinin kurulum/çalışma kabulü; sentetik stub sonuçları semantik doğruluk metriği değildir. Gerçek Resmî Gazete tüm yıllar ve çok sütunlu kanıt doğruluğu, tarihsel yürürlük/değişiklik/istisna konsolidasyonu, yerel hukukî uzman onayı, büyük corpus ANN/performance, reranker ve gerçek kullanıcı makinesi kabulü yapılmadı. PDF'de polygon'un sayfa sınırında olması, söz konusu hukukî ifadenin **görsel olarak eşleştiğinin** bağımsız garantisi değildir.

**Değişmeyen güven sınırı:** İşlem 012 `RuleEngine` `REGULATORY` kilidi açılamaz; F08–F12 `HUKUKI_HOLD`; `LegalDocument.review_status=UNREVIEWED`; indeks sonuçları **kaynak adayıdır**, mevzuat uygunluğu hükmü değildir. Orijinal PDF içerikleri, yerel SQLite ve modeller GitHub'a eklenmedi.

## 6. Sonraki işlem

**F14 `KISMI / MEVCUT_KOD + LINUX_WINDOWS_SENTETİK_CI_PASS`.** Sıradaki yeni kaydın adı **`docs/islem_015.md`** olacak ve diğer herhangi bir kod/doküman değişikliğinden önce oluşturulacak. Konu: ayrı kaynak doğrulama, LegalAST/RuleEngine kaynak düğüm bağı, yürürlük ve proje uygulanabilirliği kanıtları; yetersiz kaynakta hukukî PASS kesinlikle yok.
