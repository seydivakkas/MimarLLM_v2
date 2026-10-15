# İşlem 022 — Kirli CAD için Kaynak-Koruyan Onarım Adayı Katmanı

- **Tarih:** 2026-10-16
- **Durum:** ÖN KAYIT. **Bu dosya İşlem 022'nin ilk GitHub yazımıdır**; kod/test/diğer belge değişikliklerinden önce oluşturuldu.
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

## 3. Gerçek commit ve CI kanıtları

İşlem tamamlanınca somut kaynak dosyaları, işlenen hash/commit ID'leri, varsa başarısız CI koşuları, final Ubuntu/Windows sentetik test sayıları, açık riskler ve kapanış buraya eklenecektir.
