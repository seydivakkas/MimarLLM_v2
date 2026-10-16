# İşlem 024 — Türkçe Mimari Arama İpuçları ve Yerel SQLite RAG Cache v0.1

- **Kod:** `src/mimarllm/rag/lexicon.py`, `retriever.py`, `models.py`, `store.py`
- **İşlem kaydı:** [islem_024.md](../islem_024.md)
- **Kapsam:** Türkçe mimarlık terminolojisiyle **isteğe bağlı** FTS5 sorgu genişletme ve yerel SQLite pasaj-kimliği önbelleği.
- **Yasak sonuç:** Arama terimi ilişkisinden hukuken eşdeğer hüküm, doğrulanmış yürürlük, teknik proje uygunluğu veya resmî mevzuat sertifikası çıkarılamaz. `UNREVIEWED` ve `HUKUKI_HOLD` kalır.

## 1. Çalışma biçimi

```python
from mimarllm.rag import LegalRagStore, search_legal
from mimarllm.rag.lexicon import expand_architectural_terms

hints = expand_architectural_terms("ışıklık")
print(hints.hints, hints.version)
# örnek: ("isik kuyusu", "aydinlatma boslugu")
with LegalRagStore("C:/mimarllm/workspace/regulations.sqlite") as store:
    response = search_legal(
        store, "ışıklık", lexical_expansion=True, top_k=10,
        regulation_id="ACIK_KAYNAK_BELGE_KIMLIGI",
    )
    for hit in response.results:
        print(hit.passage.text, hit.passage.document_sha256,
              hit.passage.spans[0].page_index,
              hit.passage.spans[0].polygon,
              hit.fts_rank, hit.rrf_score)
```

`lexical_expansion` varsayılan **False**. Parametre verilmediğinde İşlem 014 sonuç arayüzü ve FTS5 BM25 davranışı değişmez. Etkinleştirildiğinde sistem özgün sorguyu önce güvenli parametrik FTS5 ile arar; `lexicon.py` içinde kurasyonlu listeden tam kelime/çok sözcüklü eşleşen en çok 6 alternatif **arama ipucunu** ikinci sorguya gönderir. Özgün sorgu pasajlarının sırası, yalnız FTS5 modunda ek önerilerin önündedir. Aynı pasaj iki kanaldan gelse bile bir kez gösterilir; isteğe bağlı dense embedding yalnız **özgün sorguya** uygulanır ve RRF ile sıralamada etkilidir.

Örnek ilişki: `ışıklık ↔ ışık kuyusu`, `kapı temiz genişliği ↔ kapı net genişliği`, `kaçış merdiveni ↔ yangın merdiveni`. Bunlar bazı kullanıcıların arama alışkanlıklarıyla bağlantılı ifadelerdir; **mevzuatta birbiriyle aynı hukuki anlama geldikleri iddia edilmemektedir**. Terimler, yüklenen mevzuat metnini değiştirmez, indekse yapay hüküm veya PDF koordinatı eklemez.

`RagResponse.expansion_version` ve `search_hint_terms` yalnız uygulanan genişletmenin görünür kaydıdır; doğrulanmış norm sınıflandırması değildir. `RagHit.legal_compliance_certified=False` ve `claim_scope=RETRIEVAL_CANDIDATE_NOT_LEGAL_ADVICE` değişmez.

## 2. Sorgu ve kaynak güvenliği

- `match_expression`: NFKD/Türkçe `ı → i` normalizasyonu; en çok 512 karakter / 24 token / 72 karakterlik sözcük, sabit çift tırnaklı FTS5 MATCH ifade üretimi; arayan kişinin `OR`, `NEAR`, SQL yorum veya `DROP TABLE` metni komut olarak çalıştırılamaz.
- Sözlükteki alternatifler yalnız normal sözcük dizileri ve mevcut `store.lexical_rank` parametrik sorgusu üzerinden gider; harici web/dense model indirimi ve uzaktan API yoktur.
- Hem özgün hem genişletilmiş aramada `document_sha256` ve `regulation_id` veritabanı tarafında **ayrı ayrı** uygulanır. Bir değişiklik PDF'si, başka bir ana mevzuat kaydıyla birleştirilmez.
- Kaynak dönüşü gerçek `IndexedPassage`'dan `document_sha256`, gerçek LegalAST `node_id/paragraph/article` ve `spans[]` PDF page/quad'dır. Sözlük hiçbir sahte kaynak spanı oluşturamaz.

## 3. Kaynak-kimlikli SQLite çalışma alanı cache

`LegalRagStore`, daha önce açılmış mevcut SQLite indeksinde küçük `rag_lexical_cache` tablosunu otomatik oluşturur. Bu tablo **yalnız FTS5 sorgu kimliği ve sıralanmış passage ID dizileri** içerir; tam mevzuat metni, PDF görüntüsü veya kullanıcının açık sorgusu önbelleğe alınmaz.

- Cache anahtarı: SHA-256(`lexical-cache-v1`, güvenli FTS ifadesi, limit, `regulation_id`, `document_sha256`). Böylece filtre/limit farkı başka dosyanın sonuçlarını cache'ten çekmez.
- En çok **128** arama varyantı saklanır; eski anahtarlar sıralama sayacına göre budanır. Sözlük sürümü ve alternatif sorgu metni değişirse zaten yeni FTS ifadesi/anahtar kullanılır; orijinal sonuçları etkilemez.
- `index_document` içinde **tek SQLite transaction** ile önce eski cache silinir, sonra belge FTS/passage/vector indeksi değiştirilir. Başarısız PDF hash/embedding doğrulamasında eski indeks ve cache bozulmaz. Ek `passages` INSERT/UPDATE/DELETE SQLite trigger'ları da dışarıdan yapılan pasaj değişikliğinde cache'i boşaltır.
- Cache'ten dönen pasaj ID'leri ardından `store.get_passage` ile gerçek mevcut pasajlardan okunur. `source_pdf_available` fonksiyonu PDF'nin **şu anki SHA-256 byte durumunu her sonuçta tekrar denetler**. Cache asla dosya erişilebilirliğini, özgünlük onayını ya da sayfa görüntüsünü saklamaz.
- SQLite cache kullanıcıya özel tek lokal çalışma alanıdır; çok kullanıcılı sunucu, FTS5 küme sunucusu, dağıtık invalidasyon ve çok büyük külliyat performans sözleşmesi değildir.

## 4. Doğrulama ve açık kalan işler

`tests/test_rag_lexicon.py` sentetik gerçek PDF→LegalAST→FTS5 ve SQLite cache testleri: özgün sorgu önceliği, related-only belge, farklı SHA filtreleri, Türkçe normalizasyon, SQL/MATCH güvenliği, cache'i yeniden indekslemede silme, kötü PDF'de işlemi reddederken cache'i koruma, PDF değişince `source_pdf_available` tekrar SHA kontrolü, 128 kayıt sınırı, `UNREVIEWED/HUKUKI_HOLD` geri dönüşü.

**Gerçek öğrenilmiş Türkçe embedding modeliyle relevance / recall / nDCG / MRR benchmarkı yapılmadı.** Sentetik test sayılarının arama kalitesi, hukukî kavram eşdeğerliği, Resmî Gazete gerçek özgünlüğü, yürürlükteki metin veya kullanıcı Windows bilgisayarı kabulünü ispatlamadığı kaydedilmelidir.
