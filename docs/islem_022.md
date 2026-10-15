# İşlem 022 — Kirli CAD için Kaynak-Koruyan Onarım Adayı Katmanı

- **Tarih:** 2026-10-16
- **Durum:** UYGULANDI / KAPATILDI — F25 kaynak koruyan CAD sanal onarım adayı ve SVG; F26/F27 sınırlı kaynak ipucu; Ubuntu 327 PASS / 1 SKIP, Windows 328 PASS sentetik CI. Gerçek CAD kullanıcı/Windows/kanunî kabul HOLD.
- **Ön koşullar:** İşlem 007 DrawingIR, 008 DXF parser, 010 Shapely geometri, 011 NetworkX incelemeli geçiş, 018 analiz pipeline, 019 arayüz, 021 Windows dağıtım aday betikleri. İşlem 001–021 kayıtları korunur.
- **Hedef:** Orijinal DrawingIR kaynak koordinatı, entity ID, CAD handle, block_path, kaynak belgesi SHA ve analiz sonucunu değiştirmeden **yalnızca onarım önerisi/overlay** üretmek. Bu aşamada mimari uygunluk, sahada gerçek oda/kapı veya kanunî PASS yoktur.

## 1. Kod kapsamı

1. `src/mimarllm/geometry/repair.py`: yalnız açıkça seçilmiş çizim frame'indeki kaynak-native CAD geometrileri için deterministik, sınırlandırılmış `RepairOverlay` ve `RepairCandidate`. Kısa uç boşlukları için `VIRTUAL_GAP_BRIDGE`, üst üste binen/tekrarlanmış çizgiler için `DUPLICATE_SEGMENT_CANDIDATE`, uç noktalar için `ENDPOINT_SNAP_CANDIDATE`; hiçbir öneri asıl `DrawingIR.entities` üzerinde değişiklik yapmayacak. Kaynak konumları, kaynak entity ID, CAD handle ve blok yolu açık tutulacak. Belirsiz çoklu eşleşme, katmanlar/çizim layoutları arası temas, desteklenmeyen geometri ve hesaplama bütçesi aşımı fail-closed/inceleme uyarısı.
2. `UnitHypothesis`: DrawingIR kalibrasyon/header ve ölçüm kanıtlarına dayalı **INFERRED** ölçek beyanı. Tek başına `CONFIRMED` veya otomatik fiziksel metraj, `PASS`, net/brüt alan üretmeyecek.
3. `Layer0SemanticCandidate`: DXF Layer 0 üzerindeki geometriyi kaynakla bağlayarak yalnız insan incelemesi bekleyen sınıflama *adayı* oluşturacak. Layer adı tek başına kesin duvar/kapı/oda olmayacak.
4. Öneriler `geometry/repair.py` model/serileştirme ve salt-okunur kaynak SVG overlay yardımı üzerinden incelenebilecek; istersek sonraki UI aşaması kaynak rengiyle ayrı gösterecek. Bu aşamada bir `RepairCandidate` otomatik olarak `TopologyResult`, `RuleEngine`, `assess_area` veya `AnalysisReport` doğrulanmış ölçüme enjekte edilmeyecek.
5. `tests/test_repair.py` sentetik ezdxf ile: küçücük çizgi boşluğu, kasıtlı kapı açıklığı olarak yorumlanabilecek belirsiz boşluk, üst üste segment, çoklu uç eşleşmesi, farklı frame, nested block ve CAD handle, DXF Layer 0, `$INSUNITS` inferred, sağlam çizimi değiştirmeme, DOS budget, deterministik JSON, resmî hukukî/ölçek güvenlik kilidi.
6. Ubuntu/Windows sentetik CI dosyaları, README, özellik envanteri, yol haritası, karar kayıtları ve `docs/specs/source-preserving-repair-v0.1.md` güncellenecek.

## 2. Katı güvenlik ve kabul sınırı

- **Yasak:** `DrawingIR` kaynak noktasını değiştirme, başka frame'lere ait uçları birleştirme, `CAD handle` veya `block_path` düşürme, otomatik kapı aralığı kapatma veya geçilebilir rota/yangın kaçışı üretme.
- **Belirsizlik:** Her öneri `REVIEW_REQUIRED` ve `VIRTUAL_CANDIDATE` durumunda kalır. Birleştirme sonrası ortaya çıkabilecek poligon mimari net alan sayılmaz; gerçek geometri analizi asıl kaynakta ayrı yapılır.
- **Fiziksel:** Header `$INSUNITS`, katman adı veya tipik duvar aralığından fiziksel SI metre sonuçları/kalibrasyon onayı üretme. Sadece açık kullanıcı bağımsız referansı ve önceki kodun ölçüm kapısı fiziksel değer verebilir.
- **Test:** GitHub-hosted Linux/Windows sentetik deney gerçek yıpranmış CAD müşteri paftası, imzalı hukukî norm, kurulu Windows onedir/Edge görsel kabulü yerine geçmez.
- **Son GitHub yazımı:** Testlerden sonra **aynı `docs/islem_022.md`** commit/CI gerçek kanıtıyla kapatılacak; sonraki işlem `docs/islem_023.md` ilk GitHub yazımı olacak.

## 3. GitHub'da gerçekte yapılan iş ve commit zinciri

**İlk GitHub yazımı:** `docs/islem_022.md` bu işlemde **`09d0faf6fa2391f503ab5614c763914273362f50`** commit'iyle, kaynak/test/doküman değişikliklerinden **önce** açıldı. `islem_001–021` kayıtları değiştirilmedi.

| Kaynak/dosya | Gerçek uygulama | Commit |
| --- | --- | --- |
| `src/mimarllm/geometry/repair.py` | `RepairOverlay`, `RepairCandidate`, `RepairKind`, `UnitHypothesis`, `Layer0SemanticCandidate`; DXF orijinal native kaynak segmenti, SHA, frame, gerçek CAD handle/blok yolu ile boşluk/snap/duplicate/overlap adayı | `603947682110310b9a74d106f529044474d0d97a` |
| `src/mimarllm/geometry/repair.py` | Çoklu endpoint adayları için ek bellek/DoS bütçe sınırı; limiti aşan girdide fail-closed `RepairInputError` | `e7d39a9ff11c5d388137f24216fce7ef37663794` |
| `src/mimarllm/geometry/repair_viewer.py` | Özgün CAD'yi lacivert vektör, sanal kısa bağlayıcıyı turuncu kesikli SVG olarak gösteren; SHA, frame, CAD handle referansı doğrulayan salt-okunur görselleştirici | `8c7b6c85d960a6b86a3a9ef33a388fe633d59f4e` |
| `tests/test_repair.py` | Sentetik `ezdxf`: gap, gerçek uç snap, birleşik kaynak, ters yönlü duplicate, kısmi overlap, katman izolasyonu, belirsiz çoklu aday, frame/PDF ret, `$INSUNITS` inferred, layer0, kaynak mutasyon yokluğu, nested INSERT/source block path, deterministik JSON, kaynak SVG/sahte SHA ve render bütçesi | `ed6f1e5214e6af96411f92d1f0647ff61733e212`, `7010c19e8c85c1953ec7f3e6c97ed4bf31ae9e13`, `4a94e123fdc84fe1635eae83f79eb61083f67f72` |
| `.github/workflows/core-contracts.yml` | Yeni `tests/test_repair.py` Ubuntu/Windows Python 3.11 mevcut tüm testlere eklendi | `66ba50ea48e069d6be17bac5997861a2cbc09b98` |
| `docs/specs/source-preserving-repair-v0.1.md` | API, örnek SVG, source/tolerans/kalibrasyon katı güven sınırları | `f96534cfe8daf46b97c83f65a7732c5d373036b0` |
| `README.md`, `docs/ozellik-envanteri.md`, `docs/uygulama-yol-haritasi.md`, `docs/kararlar.md` | F25 KISMI; F26 sadece header birim ipucu; F27 sadece Layer0 kaynak adayı; K-182–K-190, ileri sürüm ve hukukî HOLD | `ec6f8bff`, `19e869a7`, `51d9f75c`, `e79b1d45` |

## 4. Sentetik CI sonuçları, düzeltme geçmişi

- İlk koşu [Actions **38826074963**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38826074963): Ubuntu **323 PASS / 1 FAIL / 1 SKIP**; nested INSERT testinin yanlışlıkla kaynak çizginin `drawing.entities[0]` olduğunu varsayması düzeltildi. Gerçek kaynağın `entity_id→SourceReference` eşleşmesiyle karşılaştırılması sağlandı.
- SVG sahte SHA testi sonrasındaki [Actions **38826192982**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38826192982): Ubuntu **326 PASS / 1 FAIL / 1 SKIP**. Geçersiz outer SHA, `RepairOverlay` Pydantic kaynağı kapısında reddedilirken test istisna türü olarak `RepairInputError` bekliyordu; güvenlik ret kararı doğruydu, test artık `ValidationError` bekliyor.
- **Son kaynak-kod commit `e7d39a9ff11c5d388137f24216fce7ef37663794`** için [GitHub Actions **38826340165**](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38826340165):
  - **Ubuntu Python 3.11:** **327 PASS, 0 FAIL, 1 SKIP**, 1 upstream Starlette test uyarısı, **4,75 saniye**.
  - **GitHub-hosted Windows Python 3.11:** **328 PASS, 0 FAIL**, 1 upstream Starlette test uyarısı, **36,16 saniye**.
  - Atlanan Ubuntu testi yalnız Windows `onedir` snapshot/manifest davranışını inceler. Linux ve Windows CI işlerinin her ikisi log bazında ayrıca kontrol edildi.
- Bu testler ReportLab/ezdxf ile oluşturulan sentetik geometri ve özgün DXF CAD handle/blok referansı doğrulamasını, önerilerin kaynak nesneleri değiştirmediğini, SVG kaynak farkını ve bütün öncül regresyonları içerir. **Gerçek kirli mimari CAD dosyaları, fiziksel Windows/Edge kullanıcı oturumu, gerçek bina geometrisi ve hukuka uygunluk kabulü test edilmedi.**

## 5. Nihai mühendislik durumu ve açık işler

**F25 KISMI/MEVCUT_KOD, sentetik Linux/Windows CI başarılı.** Kaynak segmentleri üzerinde kısa boşluk/örtüşme işaretleri ve turuncu kesikli salt-okunur görseli **gerçek kodda** var. `RepairOverlay.changes_drawing_ir=False`, `can_feed_topology=False`, `can_feed_ruleengine=False`; hiçbir aday ölçümü, sanal kapı veya hukukî geçerli çizim olarak kabul edilmez.

**F26 KISMI:** Yalnız mevcut `UnitCalibration` durumunu `UnitHypothesis` olarak açıklama; dimension/door histogramı, kaynak ölçü yazısı ile gerçek geometri eşleştirmesi veya resmî fiziksel metrik doğrulama yapılmadı. **F27 KISMI:** Layer 0 çizgi/görsel kaynak adayı var; HATCH/ARC, kesin duvar/kapı/kolon/oda sınıfı yok.

**HOLD:** Kirli CAD kullanıcı gerçek-data performans/doğruluk testi; insan onayıyla gerçek CAD edit/undo/transaksiyon, Windows paketlenmiş GUI ve etkileşim/görsel kabul; 2.5D, yerel VLM, rubrik/jüri; gerçek çok yıllı hukukî hüküm konsolidasyonu, F08–F12 `HUKUKI_HOLD` ve kullanıcı donanımı real benchmark. Source `DrawingIR` değişmezliği devam eder.

**Sonraki mühendislik işlem kaydı:** `docs/islem_023.md` **henüz oluşturulmadı**. Yol haritasına göre A0/A1 sayfa tile/ROI OCR ve belge yerleşimi, PDF source quad/rotasyon ve bellek güvenlik bütçesi. İlk GitHub değişikliği yine önce yeni işlem kaydı olacak.
