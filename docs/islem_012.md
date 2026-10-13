# İşlem 012 — Deterministik RuleEngine çekirdeği, teknik kanıt ve hukukî karar kilidi

- **Tarih:** 2026-10-13
- **Durum:** ÖN KAYIT. Bu dosya işlem 012 kapsamındaki bütün kod/yazılım dosyalarından **önce** oluşturulur.
- **Depo:** seydivakkas/MimarLLM_v2. islem_001…011 kayıtları değiştirilmez.
- **Özellik:** F07; F08–F12 mevzuat paketleri **HUKUKI_HOLD** kalır.
- **Platform:** Windows-first; yalnız CPU/Python/Pydantic/Shapely/NetworkX, internetsiz; GPU ve dış AI API yok.

## 1. Geliştirme kapsamı

- `src/mimarllm/rules/base.py`: açık sürümlü, güvenli deklaratif kural şeması ve kanıt bağlantıları. Durumlar `COMPLIANT`, `NON_COMPLIANT`, `INSUFFICIENT_EVIDENCE`, `REVIEW_REQUIRED`, `NOT_APPLICABLE`, `ERROR`. **Teknik durum** ile kanunî sertifikasyon açıkça ayrı alanlar.
- `src/mimarllm/rules/engine.py`: sadece izinli operatörler ve metrikler, **eval/exec/serbest YAML kod yürütme yok**. Aynı kaynak, metrik ve kural için aynı JSON raporu. Kayıt kimliği/sürümü, threshold, karşılaştırma toleransı, fiziksel birim ve veri kaynakları gösterilir.
- `src/mimarllm/rules/adapters.py` (gerekirse): `DrawingIR` içinde doğrulanmış kaynak `MeasurementEvidence`, `AreaAssessment` ve `TopologyResult` üzerinde yeniden doğrulanabilir ölçüm/graf kanıt adaptörleri. Uydurma model kopyası, kaynak SHA veya farklı frame **fail closed**.
- Tek bir `RuleEngine` değerlendirme API'sinde teknik ölçüm / onaylı iç yüzey alanı / incelenmiş topolojik bağlantı; **mevzuata özgü hiçbir sabit eşik kodlanmayacak**.
- `RuleKind=REGULATORY` varsa, ilgili asıl PDF sha/page/madde/fıkra/bent, yürürlük ve değişiklik tarihlerinin sürümlü ve güvenilir haricî ETL/inceleme kaydı olmadan kural **KESİNLİKLE** `COMPLIANT` veya `NON_COMPLIANT` üretemeyecek. Bu sürümde henüz güvenilir hukukî onay arayüzü bulunmadığından **tüm REGULATORY değerlendirmeleri HOLD**. Kullanıcının bir `approved=true` alanı yazması kuralı açmayacak.
- Eksik/çelişen datum -> `INSUFFICIENT_EVIDENCE/REVIEW_REQUIRED`; doğru kanıtla teknik threshold -> `COMPLIANT/NON_COMPLIANT`; eksiksiz beyan edilmiş ve gözden geçirilmiş kapsam dışılık -> `NOT_APPLICABLE` **yalnız teknik** modda.
- `tests/test_rules.py`: altı durum, limit eşikleri, segment ölçek kaynak doğruluğu, onaylı iç sınır alanı, sahte alan/topoloji, eksik kanıt, farklı DXF/PDF frame, yasal statü bekletme, JSON roundtrip, input DoS bütçesi. Linux+Windows CI.
- `pyproject.toml` ve `.github/workflows/core-contracts.yml` entegrasyonu. `docs/specs/rule-engine-v0.1.md`, README, özelliğin gerçek statüsü, uygulama yol haritası ve karar defteri.

## 2. Kesin kabul/güven kapıları

1. `DrawingIR` kaynak SHA, native CAD/PDF entity, source coordinate frame ve fiziksel CONFIRMED kalibrasyonu doğrulanmadan teknik metrik sonucu yok.
2. Geometri alanı, `assess_area` ile tekrar hesaplanmadan gelen yalın `AreaAssessment.physical_area_m2` verisine güvenilmez.
3. Topolojik bağlantı, `build_topology` ile yeniden üretilmeden/inceleme kaynağı olmadan erişilebilirlik kanıtı sayılmaz. Eksik çizilmiş ağda yol bulunmaması **yapının gerçek erişilemezliği** demek değildir.
4. Kural uygulama tarihi/konumu/istisna ve meşru kaynak fıkra bağı çözülmeden **hukukî PASS yok**.
5. Hatalı kaynak, beklenmeyen operatör, bozuk kural kaydı **geçerli sonuç sanılmayacak**; açık `ERROR` veya doğrulama ret.
6. GitHub-hosted Linux/Windows sentetik kabulü, kullanıcının Windows/i7/RTX4070 cihazı ve hukukî bağımsız incelemesi değildir.

## 3. İş sonunda kaydedilecek gerçek sonuç

Dosya commit SHA'ları, kaç testin gerçekten çalıştığı, hangi CI OS'lerinde PASS/FAIL ve açık kalan mühendislik/hukukî doğrulama burada sonradan yazılacaktır.
