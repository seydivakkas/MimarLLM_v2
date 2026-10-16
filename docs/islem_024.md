# İşlem 024 — Türkçe Mimari Terim Arama Genişletmesi ve Kaynak-Kimlikli Yerel RAG Cache

- **Tarih:** 2026-10-16
- **Durum:** UYGULANDI / KAPATILDI — F29 opt-in Türkçe mimari arama ipuçları + F30 yalnız yerel SQLite FTS5 pasaj-ID cache'i kodlandı. Son sentetik CI Ubuntu **358 PASS / 1 Windows-only SKIP**, Windows **359 PASS**. Gerçek Türkçe relevance, hukukî kaynak/yürürlük ve tam workspace kabulü HOLD.
- **Ön koşul:** İşlem 014 SQLite FTS5/BM25 ve opsiyonel yerel dense/RRF; İşlem 015–017 LegalAST source span; İşlem 023 opt-in PDF tile OCR; İşlem 001–023 kayıtları değiştirilmeyecek.
- **Katı sınır:** Türkçe mimarlık terimleri **arama ipucudur**; resmî mevzuatın eşdeğer hükmü, norm istisnası, yürürlük veya legal `COMPLIANT` çıkarsaması değildir. Kaynak belge SHA, node/page/polygon, `UNREVIEWED`, `RuleEngine.REGULATORY` HOLD korunacak.

## Kod geliştirme sırası
1. `src/mimarllm/rag/lexicon.py`: küçük sürümlü, gözden geçirilebilir **kurasyonlu arama-terim haritası**; Türkçe diakritik normalizasyonu, kontrollü anlam yakınlığı, yanlış otorite iddialarına karşı yalnız isteğe bağlı genişletme. Kısa terim/çok sözcüklü eşleşme ve bounded token miktarı; kullanıcı eklediği sözlük veri olarak değerlendirilecek, SQL/MATCH operatörlerine dönüşmeyecek.
2. `src/mimarllm/rag/retriever.py`: `search_legal` için varsayılan davranışı bozmadan `lexical_expansion` opt-in; özgün sorgunun BM25 sıralamasını önceleme, zayıf eşanlam adaylarını ayrı sıralama kanalında RRF ile birleştirme; aynı PDF pasajı kaynak/kimlik bakımından tekil kalacak. Dense arama varsa **özgün sorgu** ile çalışmaya devam edecek; sorgu genişletmesi dense model eğitim onayı değildir.
3. `src/mimarllm/rag/store.py` veya `rag/cache.py`: yerel SQLite çalışma alanında küçük, sürümlü, bounded arama sonucu kimlik cache'i; belge yeniden indekslenmesi ve model/sözlük/filtre değişiminde sonuçların bayat kalmaması, belge SHA izolasyonu; arama sonucu `source_pdf_available` dosya hash'i her sonuçta **yeniden kontrol edilmeli**, kaynak PDF görüntüsü cache içinde saklanmayacak.
4. `tests/test_rag_lexicon.py`: Türkçe sorgu/diakritik, çok sözcük, FTS özel karakterlerinin güvenli quote edilmesi, resmî bir hükümle karıştırılmayan benzer terimler, kaynak/filtre/var olan dosya hash/yeniden indeks cache izolasyonu, RRF sırası deterministikliği, sentetik PDF LegalAST page/quad ve hukukî HOLD; Linux+Windows CI.
5. `docs/specs/rag-lexicon-v0.1.md`, README, envanter, karar ve yol haritası açıklamaları; `.github/workflows/core-contracts.yml` test kapsamı.

## Kabul kapıları
- Gerçek Türkçe embeddings modeli relevance/NDCG/MRR değerlendirmesi yapılmış sayılmayacak; kavramları eşanlam saymak **hukukî tanımları eşitlemez**.
- SQLite arama/önbelleği yalnız lokalde, deterministik kaynak passage ID ve filtre anahtarlarına göre; eski/yeni Resmî Gazete PDF'leri birleştirilmez.
- Gerçek mevzuat uzmanı onayı, tarihsel konsolidasyon, özgün kaynak otantiklik, kapsamlı gerçek doküman ve Windows hedef cihaz testleri HOLD.
- İşlem sonunda gerçek commit zinciri, CI logu/başarısızlık/düzeltme, sınırlamalar **bu aynı dosyanın son GitHub yazımında** kaydedilecek.


## 4. Gerçek GitHub commitleri ve oluşturulan kaynaklar

**İlk GitHub yazımı:** `docs/islem_024.md` ön-kayıt commit'i **`6ec335a6458115f6d5bc64b3302f4d6244ff5635`**. Kod ve diğer dokümanlar **bundan sonra** yazıldı; 001–023 işlem belgelerine dokunulmadı.

| Kaynak | Kodlanan işlev | Gerçek commit |
| --- | --- | --- |
| `src/mimarllm/rag/lexicon.py` | Sürüm `architectural-search-hints-v0.1`, tam sözcük/çok sözcüklü Türkçe normalize arama ipuçları ve fail-closed token bütçesi | `d712732a` |
| `src/mimarllm/rag/models.py` | `RagResponse.expansion_version` ve `search_hint_terms`; legal sertifikasyon yasağı devam | `abc6ddaa` |
| `src/mimarllm/rag/retriever.py` | `lexical_expansion=False` varsayılan; enabled durumda özgün FTS5/BM25 eşleşmelerinin önceliği, ek adayların filtreli ikinci lexical kanal üzerinden tekilleştirilmesi, dense varsa yalnız asıl query embedding | `4aea2762`, `0719cd92`, `4b26626f`, `18ddf419` |
| `src/mimarllm/rag/store.py` | `rag_lexical_cache`: query+limit+regulation/doc SHA keyed 128 ranking list, orijinal PDF içeriği/kimliği yerine sıralı passage ID; reindex ile transaction invalidation | `14071019` |
| `src/mimarllm/rag/store.py` | SQL üzerinden `passages` INSERT/UPDATE/DELETE olması durumunda trigger ile cache invalidation; yeniden indeks veya farklı süreç sonucunda stale pasaj adaylarını engelleme | `8fa16faf` |
| `src/mimarllm/rag/__init__.py` | Arama ipuçları sürümünü ve opt-in yordamını public package API'de sunma | `1ece6ed4` |
| `tests/test_rag_lexicon.py` | Gerçek sentetik PDF→LegalAST→SQLite FTS, diakritik/multiword, özel karakter injection, belge SHA/regulation izolasyonu, kaynak quad/HOLD, cache sınırı/idempotence, byte-altered PDF kaynak durumu, iki SQLite bağlantısı ve SQL trigger regresyonları | `119092e9`, `1e38e299` |
| `.github/workflows/core-contracts.yml` | Yeni arama/cache testleri tüm eski Ubuntu+Windows kontrat matrisi içinde | `5e785292` |
| `docs/specs/rag-lexicon-v0.1.md` | API, kaynak/hüküm güvenlik sözleşmesi, lexical rank cache sınırı, örnekler, gerçek kabul eksikleri | `b6bd51d3` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F29/F30 kısmî gerçek kod, kapsam dışı genel workspace/WAL/retention ve hukukî HOLD; K-199–K-208 | `45cb041f`, `e5983644`, `0b7eba3c`, `89241f47` |

## 5. CI — gerçekten doğrulanan son durum

- Yeni lexicon/cache testlerinin ilk tam paketi: [GitHub Actions 38832450015](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38832450015), **Ubuntu 356 PASS / 1 SKIP**, **Windows 357 PASS**. Mevcut tüm çekirdek/RAG/OCR/dashboard/Windows paketleme sentetik testleriyle birlikte çalıştı.
- SQL mutation trigger ve iki bağımsız SQLite bağlantısı testleri eklendikten sonra kaynak commit **`1e38e2997f31a489b7c8c2d4f0d8f49a63572ad9`** üzerinde [GitHub Actions **38832687907**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38832687907) **conclusion=success**:
  - **Ubuntu Python 3.11: 358 PASS / 1 SKIP, 1 warning; 8,26 saniye.**
  - **Windows GitHub-hosted Python 3.11: 359 PASS, 1 warning; 13,25 saniye.**
- İki işletim sisteminin CI job logları ayrıca incelendi. Uyarı bu işlemden değil, FastAPI testclient içindeki **StarletteDeprecationWarning: httpx/starlette.testclient** bağımlılık uyarısı. Ubuntu'daki 1 SKIP önceden var olan Windows-özel test koşuludur. Sıfır test başarısızlığı.
- Kaynak PDF'ler yalnız **sentetik ReportLab** ile oluşturuldu; gerçek resmî Gazete doğrulaması, gerçek cihaz/Windows offline paketlenmiş programın GUI kabulü ve gerçek öğrenilmiş çokdilli model performans ölçümü yapılmadı.

## 6. Güven sınırı, kısmi durum ve sıradaki kayıt

**Gerçekte mevcut:** Kullanıcı `search_legal(..., lexical_expansion=True)` ile yalnız arama *adayı* olan Türkçe mimari terminoloji yakınlığına ulaşabilir. Sonuçta `IndexedPassage` özgün LegalAST düğüm, madde/fıkra, `document_sha256`, PDF source page/quad korunur. SQLite cache'i yalnız passage ID listesini saklar; original PDF SHA dosyası her aramada güncel olarak yeniden kontrol edilir. Tek indeks değişikliğinde cache transaction + SQL trigger ile iptal olur.

**F29 KISMI:** Küçük kurasyonlu ipucu listesi resmî hukukî eşanlamlı sözlük değildir. Gerçek Türkçe arama `Recall@k/nDCG/MRR`, kullanıcı sözlüğü/uzman yargısı, yerel embedding model doğruluğu yok.

**F30 KISMI (yalnız lexical RAG cache):** Genel proje çalışma alanı, uygulama geçmişi, WAL politika/kurtarma, çok-kullanıcı güvenliği, retention ve disk kullanım/ağır corpus benchmarkı kodlanmış değildir. RAG cache'i F30 tamamlandı anlamına gelmez.

**HUKUKI_HOLD:** Resmî kaynak otantiklik/yıl-yürürlük değişiklik grafı, özel istisna, onaylı mevzuat eşikleri ve uzman hukukî incelemesi yapılmadı. `RuleEngine.REGULATORY=INSUFFICIENT_EVIDENCE`, `RagHit.legal_compliance_certified=False`, `UNREVIEWED` statüleri **değişmedi**.

**Sonraki işlem:** `docs/islem_025.md` henüz yok. Yeni kapsam için önce bu dosya **ilk GitHub yazımı olarak** oluşturulmalıdır; İşlem 024 ve geçmişi sonradan geriye dönük değiştirilmeyecek.
