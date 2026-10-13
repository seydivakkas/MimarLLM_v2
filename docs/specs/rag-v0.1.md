# Hibrit Mevzuat RAG v0.1 — FTS5 + Yerel Dense + RRF + Özgün PDF Konumu

- **İşlem:** [islem_014.md](../islem_014.md)
- **Kod:** `src/mimarllm/rag/{models,store,embeddings,retriever,indexer}.py`
- **Çalışma biçimi:** Lokal SQLite `sqlite3` FTS5/BM25, isteğe bağlı lokal SentenceTransformer CPU, vektör JSON/cosine taraması, RRF; internet/bulut/API yok.
- **Kaynak:** İşlem 013 `LegalDocument`. `review_status=UNREVIEWED` değişmez; RuleEngine `REGULATORY` HOLD.
- **Açık kabul:** FTS/DB/test stub embedding ve RRF sentetik olarak sınanır. Gerçek yerel dil embedding ağırlığı, Türkçe relevance benchmark, gerçek Resmî Gazete ve hukukî kaynak doğruluğu ayrıca kabul ister.

## 1. Basit kullanım: Gerçek yerel PDF'yi indeksleyip ara

```python
from mimarllm.legal.models import LegalDocumentMetadata
from mimarllm.rag import LegalRagStore, index_local_legal_pdf, search_legal

metadata = LegalDocumentMetadata(
    regulation_id="local-example-id",
    document_kind="ORIGINAL",  # kullanıcı beyanıdır; teyit değildir
)
with LegalRagStore("local_data/legal_search.sqlite") as store:
    summary = index_local_legal_pdf(
        "local_data/regulations_raw/example.pdf", metadata, store
    )
    response = search_legal(store, "ışıklık genişliği", top_k=5)
    for hit in response.results:
        p = hit.passage
        print(
            p.article_number, p.paragraph_number, p.item_key,
            p.document_sha256, p.spans[0].page_index,
            p.spans[0].polygon, p.text, hit.rrf_score,
        )
```

`local_data` yolunu ve alt dosyaları kullanıcı oluşturmalı; `.gitignore` gereği kaynak PDF, müşteri dosyaları, indeks, yerel model ağırlıkları GitHub'a eklenmez.

`source_pdf_available=True` yalnız kullanıcı daha önce `original_pdf_path` ile aynı SHA-256'daki yerel dosyayı dizine kaydetmişse **ve arama anında hash tekrar eşleşiyorsa** gelir. Bu bir resmîlik veya içerik-hüküm doğrulaması değildir. Kaynak PDF yoksa `False`; SHA/page/polygon metadata yine sunulur ancak arayüz orijinal PDF görüntüsünü uyduramaz.

## 2. LegalAST → FTS5 indeks sözleşmesi

1. `LegalDocument.model_validate(document.model_dump())` ile tam belge ve hiyerarşi yeniden doğrulanır. Bu, `model_copy(update=...)` ile sahte `APPROVED` atlatma girişimini engeller.
2. Her `LegalNode` ayrı `IndexedPassage`: belge SHA-256, node ID, parent ID, SECTION/ARTICLE/TEMPORARY_ARTICLE/PARAGRAPH/ITEM/TEXT türü, kalıtılmış article/paragraph/item, metin, tüm `LegalSourceSpan` kaynakları.
3. Her dolu `LegalTableCell` ayrı kayıt: `table_id`, `row_index`, `column_index`, `TABLE_CELL_BBOX`; tablo–madde parent yalnız LegalAST'den gelen **inceleme adayı**. Birleştirilmiş metin hiçbir zaman güvenilir mevzuat hükmü değildir.
4. Kimlik `document_sha256 + local node/table identity`; aynı madde numarasını taşıyan farklı Gazete PDF'leri aynı düğüm sayılmaz. Değişiklik belgesi ana yönetmeliğe otomatik konsolide edilmez.
5. Metnin **aranacak kopyası** Unicode NFKD + Türkçe `ı → i` normalizasyonu ile FTS5'e yazılır; sonuçta gösterilen asıl metin ve PDF bbox korunur. FTS5 `unicode61 remove_diacritics 2` ve `bm25(passage_fts)` kullanır.
6. Re-index aynı PDF SHA'yla transaction içinde eskileri/senaryo vektörlerini kaldırıp güncel kayıtları koyar. Dense encoding **önce doğrulanır**, hata olursa eski başarılı dizin bozulmaz. Bir kullanıcı dosyasının adı değişse bile SHA kimliği değişmez; içerik değişirse yeni belge kimliği olur.

**Güvenli FTS sorgusu:** Kullanıcı aramasından yalnız sınırlı Unicode kelimeleri çıkarılır, FTS5 MATCH ifadeleri sabit üretilir ve SQL parametreleriyle gönderilir. Serbest SQL ya da MATCH operatörleri kullanıcıdan çalıştırılmaz. Varsayılan OR eşleşmesi, BM25 sıralaması kullanır; Boolean/phrase filtreleri v0.1 ürün API'si değildir.

## 3. Yerel gerçek embedding — isteğe bağlı ve fail-closed

```python
from mimarllm.rag.embeddings import LocalSentenceTransformer
from mimarllm.rag import LegalRagStore, index_local_legal_pdf, search_legal

# Model klasörü önceden ve kullanıcı iradesiyle yerel olarak hazırlanmalı.
# sentence-transformers opsiyonel Python paketidir; çekirdek kurulumda zorunlu değil.
emb = LocalSentenceTransformer(
    r"C:\local_models\multilingual_sentence_transformer",
    model_id="local-multilingual-v1",
)
with LegalRagStore(r"C:\local_data\mevzuat.sqlite") as store:
    index_local_legal_pdf(
        r"C:\local_data\orijinal.pdf", metadata, store, embedder=emb,
    )
    results = search_legal(store, "havalandırma boşluğu", embedder=emb)
```

`LocalSentenceTransformer` yalnız **var olan mutlak yerel klasörü** kabul eder; `modules.json` varlığını kontrol eder, modeli `device="cpu"`, `local_files_only=True`, `trust_remote_code=False` ile yükler. İndeks ve sorgu için **aynı model ID ve embedding dimension** gerekir. Kullanıcının model_id beyanı modelin ağırlıklarının kriptografik imzası değildir; model manifest/hafıza/performans kabulü daha sonra. Gerçek model bulunamazsa **ağdan indirme denemesi yok**, açık hata veya embeddings verilmeden FTS5 yolu kullanılır.

Dense v0.1 tüm vektörleri SQLite'da JSON saklar; modelden üretilen sayısal vektörler uzunluk ve NaN/Infinity/zero norm kapısından geçer. Varsayılan en fazla 50000 vektör için **exact linear cosine taraması**, ANN (FAISS/HNSW/Chroma) gibi ilave bileşen yok. Büyük Gazete külliyatı için hız benchmark ve ANN optimizasyonu sonraya bırakıldı.

`tests/test_rag.py` vektör kontrolünde **öğrenilmiş semantik model yerine deterministik sentetik embedder** kullanır; bu yalnız \`cosine + rank + RRF\` kod sözleşmesidir. Test, gerçek Türkçe embedding benchmarkı değildir.

## 4. RRF ve sonuçlar

`search_legal(store, query, embedder=None, top_k=10, candidate_limit=100, rrf_k=60, regulation_id=None, document_sha256=None)`

- Lexical sıra: FTS5/BM25; embedding açık ve indeksli ise dense sıra: normalize edilmiş cosine.
- RRF: her doküman için rank yerleşimi, `score = Σ 1/(rrf_k + rank_i)`; skor bir **birleştirilmiş sıralama** puanıdır, hukuken doğruluk veya mevzuat geçerlilik puanı değildir.
- `RagResponse.mode` `LEXICAL_ONLY` / `DENSE_ONLY` / `HYBRID`. `dense_state` `DISABLED` / `NO_MODEL_VECTORS` / `INDEXED`; kaynak model yokken semantik sonuçmuş gibi davranılmaz.
- Sonuç: `RagHit.passage` içinde özgün metin, kimlik, article, paragraph, item, table row/column, \`spans[]\` PDF SHA, PDF page index, four-point polygon, native/OCR türü. `fts_rank`, `dense_rank`, `rrf_score` ayrı; `legal_compliance_certified=False`, `claim_scope=RETRIEVAL_CANDIDATE_NOT_LEGAL_ADVICE` sabit.
- `document_sha256`/`regulation_id` filtreleri veri deposunda parametreli uygulanır. 0 tabanlı PDF page ile basılı Resmî Gazete sayfa numarası farklı olabilir. Arayüz PDF vurgulamayı *source span* koordinatında çizer.

## 5. Sağlamlık, sınırlar ve eksikler

- Lokal SQLite WAL zorunlu değil; tek kullanıcı ve işlem bazında ACID transaction. FTS5 SQLite derlemede yoksa açık ret.
- Kullanıcı query sınırı 512 karakter/24 token; varsayılan search top_k 10, max 50; candidate max 200; indexed passages max 20000/belge; indexed passage text max 50000 karakter, span sayısı max 300; embedding dim 2..4096, batch <=256.
- `original_pdf_path` verildiğinde hash ve **sayfa geometri boyutları** pypdfium2 ile kontrol edilir: görüntü dışı polygon indekslenmez. Bu koordinatın doğru kanunî cümleye denk düştüğünün görsel doğrulaması değildir.
- OCR gerçek model Türkçe CER/tablolar, iki sütun doğru okuma sırası, alt fıkra/istisna referansı, eski-yeni metin yürürlükteki sürüm grafı **yok**.
- Kullanıcının `APPROVED_FOR_CHECK` beyanı veya RAG sonucu RuleEngine `REGULATORY` kilidini açmaz. Yalnız resmî PDF kaynakları yetkili incelemeyle tarih/bölge/yapı kullanımı bağlandıktan sonra kural paketleri için ayrı çalışma yapılabilir.
- Herhangi bir çevrimdışı SQLite/arşiv kullanıcı verisi sistematik yedekleme, büyük veri ann indeks ve LLM reranker performansı bu işlemde doğrulanmadı.

**İşlem 014: F14 KISMI/MEVCUT_KOD, F13 KISMI/MEVCUT_KOD, F08–F12 HUKUKI_HOLD.**