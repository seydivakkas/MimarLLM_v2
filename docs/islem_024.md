# İşlem 024 — Türkçe Mimari Terim Arama Genişletmesi ve Kaynak-Kimlikli Yerel RAG Cache

- **Tarih:** 2026-10-16
- **Durum:** ÖN KAYIT — İşlem 024 kapsamındaki **ilk GitHub yazımı**; kod, test veya diğer belgelerden önce açıldı.
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
