# İşlem 012 — Deterministik RuleEngine çekirdeği, teknik kanıt ve hukukî karar kilidi

- **Tarih:** 2026-10-13
- **Durum:** UYGULANDI — teknik RuleEngine veri modelleri, Linux/Windows sentetik CI PASS. Hukukî mevzuat ve gerçek Windows/saha kabulü HOLD.
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

## 3. Gerçek uygulama ve commit kanıtları

**İlk yazılan dosya:** `docs/islem_012.md` commit `45286038259421eb88db36d3220ccb6052167dc1`. Bu ön-kayıt, bütün diğer İşlem 012 değişikliklerinden **önce** GitHub'da oluşturuldu.

| Dosya | Gerçek uygulama | Commit |
| --- | --- | --- |
| `src/mimarllm/rules/base.py` | `RuleDefinition`, `RuleRequest`, `RuleResult`, 6 sonuç durumu, scope beyanı ve hukukî locator | `3aa23360`; validator sertleştirme `0a3bfb71` |
| `src/mimarllm/rules/engine.py` | Sadece teknik kural ölçümü; DrawingIR segmentini yeniden hesaplama, Shapely assessment ve NetworkX portal path yeniden doğrulama, hukukî HOLD | `87507b19`; sıfır-hop yol reddi `ce432e17` |
| `src/mimarllm/rules/__init__.py` | Python modül paketi | `683b23d7` |
| `tests/test_rules.py` | Altı durum, fiziksel ölçüm, alan/topoloji, sahte kayıt ve kısıtlı operatör testleri | `48554679`; giriş/kanit testleri `5577b760`, `00f51d06`; zero-hop testi `9df042e5` |
| `.github/workflows/core-contracts.yml` | `rules/**` kaynak dosyaları ve `tests/test_rules.py` Linux/Windows matrix'e eklendi | `d921d588` |
| `docs/specs/rule-engine-v0.1.md` | Statüler, şema, güven kapıları, gerçek kod/sınırlar | `4977693c` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F07 kısmi kod, F08–F12 hukukî HOLD, K-083–K-091 kararları, sonraki ETL aşaması | `ff589247`, `7da80997`, `3e768c78`, `53d6384d` |

## 4. Gerçek test ve regresyon sonuçları

- İlk bütünleşik test [CI 38370549426](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38370549426): **158 PASS / 1 FAIL**. Geçersiz DrawingIR nesnesi teste `RuleRequest` kurulurken verilmiş, motorun girişindeki fail-closed kontrolüne hiç ulaşamamıştı. Test gerçekte geçerli istek oluşturulduktan **sonra** nesnenin değiştirilmesini simüle edecek şekilde düzeltildi.
- Düzeltmeden sonra [CI 38370661989](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38370661989): Linux+Windows **159/159 PASS**.
- `RuleResult` oluşturulurken kaynaksız olumlu teknik kararın veya sahte hukukî `claim_scope` alanının reddedilmesi eklendi; [CI 38370941924](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38370941924): Ubuntu/Windows **162/162 PASS**.
- **Son kaynak kod `9df042e519ec7944de4835815d99c7b7b92dfa47`** için [GitHub Actions run 38371261028](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38371261028): **Ubuntu Python 3.11 163 PASS/0 FAIL (2,19 s)**; **GitHub-hosted Windows Python 3.11 163 PASS/0 FAIL (7,11 s)**. Her iki işin tamamlandığı ve sonuçları GitHub Actions loglarında doğrulandı.
- Testler sentetik; diske kaydedilip yeniden okunan `ezdxf` planlarından native line+polygon ve geçiş tanıkları; `RuleEngine` için gerçek senaryolu testler. Gerçek mimarî müşteri çizimi, gerçek i7/4070/32 GB cihaz, OCR/VLM inference veya bağımsız hukukî denetim test edilmedi.

## 5. Çalışan karar/sınırlar

**Kodlanan teknik çekirdek:** Segment gerçek native uç noktalarından yeniden ölçülür ve confirmed frame bound UnitCalibration şarttır. Alanda ham `AreaAssessment` doğrudan kullanılmaz, `assess_area` ile source geometry yeniden hesaplanır. Topoloji `build_topology` ile yeniden kurulur ve portal kanıt ID'siyle raporlanır; eksik geçit gerçek fiziksel erişilemezlik sonucu üretemez. Uydurma source ID/SHA/model mutasyonu ERROR/REVIEW_REQUIRED veya INSUFFICIENT_EVIDENCE üretir. `NOT_APPLICABLE` yalnız teknik senaryoda kaynak kimliği ve reviewer beyanıyla olabilir; bu beyan gerçek yetki/audit değil.

**Hukukî sertifikasyon yasağı:** `REGULATORY` domain için kanunî özgün PDF MADDE/FIKRA, yürürlük/değişiklik, proje yılı, belediye/kullanım sınıfı, istisna ve bağımsız onay henüz mevcut değildir. Bu yüzden **REGULATORY her zaman `INSUFFICIENT_EVIDENCE`**; kullanıcı verdiği SHA/article/effective_from metadata'sıyla kilidi açamaz. `RuleResult.legal_compliance_certified=True` reddedilir. Planlı Alanlar İmar, Yangın, Otopark, Sığınak, BEP gerçek kural eşikleri veya kullanıma hazır uygunluk hesaplayıcıları bu işlemde yazılmadı.

**Mühendislik sınırları:** PDF gerçek OCR doğruluğu, kapı/oda semantiği, kullanıcı reviewer imzası, gerçek yürüme/navmesh, örneklem dışı geometri hata yayılımı, gerçek Windows saha kabulü ve kaynak yasal geçerlilik HOLD. Sentetik PASS yalnız kod sözleşmesi kabulüdür.

**Sonuç:** F07 `MEVCUT_KOD + SENTETİK_LINUX_WINDOWS_PASS / KISMI`; F08–F12 `HUKUKI_HOLD`. Sonraki mühendislik paketi `docs/islem_013.md` (henüz oluşturulmadı): Resmî mevzuat PDF→LegalAST, madde/fıkra/tabloları orijinal konum ve değişiklik zinciriyle bağlayan offline ETL. Aynı işlem-kayıt numarası artırma disiplini korunacak.
