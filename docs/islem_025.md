# İşlem 025 — Kaynak-bağlı 2B inceleme ve sınırlı iş kuyruğu

- Tarih: 2026-10-16
- Durum: GELİŞTİRME / KABUL BEKLİYOR
- Dal: `feature/islem-025-source-2d-jobs`; hedef `main`.
- Ön koşul: İşlem 019 dashboard, İşlem 022 kaynak bozmayan CAD onarım adayları, İşlem 023 kaynaklı PDF OCR, İşlem 024 yerel RAG cache.
- İlk işlem kaydı: Bu dosya yeni dalda ilk kod/doküman yazımıdır. Tarihsel `islem_001.md`–`islem_024.md` değiştirilmez.

## Hedefler
1. Mevcut DXF/PDF analiz çıktısını bozmadan 2B kaynak-native LINE/PDF_LINE üzerinden **salt okunur** çizim görselleştirme, frame/katman filtresi, özgün CAD handle/entity ID ve belge SHA kanıt odaklaması. SVG çizim üzerinde yapılan seçimler orijinal DrawingIR, PDF veya CAD dosyasını değiştirmez. Kanıtla doğrulanmayan semantik çizgiye oda/kapı/kolon adı verilmez.
2. Bir kullanıcı için **tek çalışan iş ve küçük sınırlandırılmış bekleme kuyruğu**; POST ile anonim ancak aynı uygulama oturumundan erişilen iş kimliği, GET ile durum sorgusu. İlerleme, yalnız gerçekten bilinen `QUEUED/RUNNING/COMPLETED/FAILED` ayrımını verir; sahte yüzde veya aşama süreleri yok. İş kimlikleri ve yerel SHA izolasyonu korunur.
3. Mevcut `POST .../runs` senkron istemci sözleşmesi, HTTP CSRF/Origin/Host/loopback sınırları ve sonuç dosyaları geriye dönük kırılmayacak. Önceki kaynak rapor ve kalibrasyon davranışı korunacak. İstemci yeni iş API'sini kullanır.
4. Yeni sentetik regresyon: kapasite, aynı anda çalışan iş, iki proje arasında bağlam/sınıf karışmaması, değişmiş kaynak SHA'sı, durum erişimi, yasal HOLD ve 2B statik UI/CSP/XSS sözleşmeleri. Ubuntu/Windows CI başarılı olmadan kapalı sayılamaz.

## Kapsam dışında
- DXF üzerinde kalıcı edit, onaylanmamış oda/geçiş semantiği veya model yaratma.
- 2.5D/Three.js, GPU/VLM, gerçek pedagojik puan, jüri, resmî mevzuat PASS.
- Kullanıcının fiziksel Windows 10/11/Edge/gerçek A0 pafta/kullanıcı kabulü; İşlem 031'e taşınır.
- Harici ağ, CDN, telemetri, SaaS ve ek ücretli API.

## Son kapı
Dalların kod/test değişiklikleri, CI sonuçları, bilinen eksikler ve gerçek PR özeti bu dosyaya işlemin sonunda işlenecektir. Gerçek kanıt olmadan `KAPATILDI` yazılamaz.

## 1. Bu dalda gerçekten uygulanmış kaynak adayı

- `src/mimarllm/app/jobs.py`: tek yerel worker + en fazla 4 inflight + 64 geçici iş kaydı, kilit paylaşımı, hata metinlerini saklama.
- `src/mimarllm/app/server.py`: 202 `POST .../jobs`, projeye bağlı `GET .../jobs/{job_id}`, geriye uyumlu eşzamanlı `POST .../runs`; native line `origin` ve SHA.
- `src/mimarllm/app/static/{index.html,dashboard.js,dashboard.css}`: kaynaklı salt-okunur SVG, frame/layer filtresi, kaynak-native noktalar, SHA ve CAD handle; durum polling, yüzde uydurmadan.
- `tests/test_dashboard_jobs.py` ve `tests/test_dashboard.py`: job kapasitesi ve proje izolasyonu, boşta kuyruğun tamamlanması, hata redaksiyonu, E2E DXF/manifest/legal gate, CSRF, oversized body, static UI.
- `.github/workflows/core-contracts.yml`: test matrisi ve `node --check` iki OS; PR event tetikleyicisi.
- `docs/specs/dashboard-2d-jobs-v0.1.md`: gerçek kapsam ve güvenlik sınırları.

## 2. İlk sentetik CI kanıtı

Commit `55499a5c87028181f5b5ad4ab13a445f877d70dc` için GitHub Actions [38834544453](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38834544453) **conclusion=success**:
- Ubuntu Python 3.11: **364 PASS, 1 SKIP**, 1 warning (7,98 saniye).
- Windows-hosted Python 3.11: **365 PASS**, 1 warning (14,71 saniye).
- Job loglarında iki ortamın `node --check` komutu da başarılı.
- Atlanan test önceki Windows'a özgü paket manifest testidir; yeni 025 testi değildir.
- CI `python -m pip` bağımlılık çözümleyici uyarısı ve upstream Starlette warning içerir; sonuçlara açıkça HOLD/KISMI ayrımı uygulanır.

Not: Bu koşu `55499a5c` kaynak/test commit'ine aittir; devamında `pull_request` workflow olayı eklendi. **Son PR head CI** ayrıca doğrulanmadan bu değişikliklerin tümü kesin kapalı sayılmayacak.

## 3. Henüz tamamlanmamış İşlem 025 kabulü

**Durum KISMI / DRAFT PR**: source-native inceleme ve iş sorgusu kullanılabilir kod adayıdır; ancak **kalıcı CAD geometrisi edit/undo, gerçek kimlik doğrulamalı uzman onayı, analiz aşaması-seviyesi gerçek ilerleme, kalıcı/restart-safe queue, tam bağımsız Edge etkileşim/görsel QA** yoktur. Çizim üzerinde seçim/katman filtresi fiziksel edit değildir. Ayrı review-notes.json sidecar'a kaynak bağlı manuel not ekleme ve audit tombstone ile geri alma, gerçek çizimi değiştirmeden kodlandı. OCR, kalibrasyon, GPU, 2.5D, VLM, jüri ve resmî hukukî uygunluk onayı yanlışlıkla tamamlandı sayılmayacak. İşlem 031 fiziksel kabul ayrı kalır.

F08–F12 `HUKUKI_HOLD`, teknik `INSUFFICIENT_EVIDENCE`, orijinal DrawingIR ve kaynak SHA değişmez. PR #1'in stüdyo demosu bu PR'a birleştirilmedi. **İşlem 025 kapatılmadı; yeni işlem 026'ya resmi sıra ile geçilmez.**

## 4. Kaynaklı manuel inceleme sidecar ek geliştirmesi

`src/mimarllm/app/reviews.py`, `app/server.py`, `app/static/` ve `tests/test_dashboard.py`: özgün native entity + frame + PDF/DXF SHA doğrulamalı manuel gözlem, geri alındığında silinmeyen zaman damgalı audit, atomik yerel sidecar, 100 kayıt/120KB, symlink ve istemci JSON sınırları, CSRF ile koruma. Eğitim uzmanı kimliği veya resmî mevzuat PASS üretmez. Bağımsız Edge gerçek kullanıcı tıklama ve büyük pafta kabulü HOLD.

**Bu ek kod için en son GitHub Actions CI sonucu henüz dosyada doğrulanmadığından İşlem 025 kapalı olarak işaretlenmedi.**

## 5. Kullanıcı önceliğiyle kapsam genişletme — kalıcı DXF revizyonu ve gerçek kabul ayrımı

**16 Ekim 2026 kullanıcı kararı:** İşlem 025 kapanmadan 026'ya ve üretime geçilmez. Başlangıçta 025 kapsamı dışında sayılan "kalıcı DXF edit" yalnız **orijinali değiştirmeyen türetilmiş DXF revizyonu** olarak bu işlem dalına eklenmiştir. Yukarıdaki tarihsel ilk kapsam maddesi bu addendum ile daraltılarak güncellenmiştir.

Gerçekte kodlananlar:
- \`src/mimarllm/app/dxf_edits.py\`: sadece \`cad:Model\` direkt native \`LINE\`, CAD handle, eski/yeni iki uç eşleştirmesi; ezdxf read/audit/roundtrip, kaynağın SHA256 değişmezliği, immutable yeni \`drawing.dxf\`, revizyon JSON ve atomik \`head.json\`.
- Edit endpoint'leri \`/api/projects/{id}/edits\`, \`/edits/undo\`, \`/edits/{revision}/download\` ve UI koordinat formu/undo/indirme. PDF çizgileri, nested INSERT, HATCH/ARC, değişen metaforlar, kalibrasyon ve hukukî onay desteklenmez.
- \`tests/test_dashboard.py\` içinde 1. revizyon, 2. revizyon, undo'nun eski byte'ı geri oluşturması, değişmeyen orijinal DrawingIR, restart kalıcılığı, SHA çakışması, sahte handle ve PDF reddi.
- \`scripts/benchmark_025.py\`: 500 sentetik DXF çizgisinin 5 parse tekrarı, tek edit+undo wall süre ve yalnız Python allocation tracemalloc peak. Gerçek A0/PDFium/ONNX process RSS değildir.
- \`scripts/windows/edge_smoke_025.py\` ve \`.github/workflows/windows-edge-025.yml\`: GitHub-hosted gerçek Edge binary'si ile localhost API/UI DOM taraması; fiziksel Windows/Edge kullanıcı kabulünün yerini almaz.
- \`scripts/windows/acceptance_025.ps1\` ve \`docs/specs/windows-acceptance-025.md\`: bağımsız fiziksel Windows kullanıcı kabulü, gerçek DXF/PDF benchmark ve kullanıcı imza kontrol formu.
- \`docs/specs/dxf-revisions-025.md\`: kaynak-korumalı edit API ve geri alma sözleşmesi.

**Doğrulanmış ara kod commit** \`bd63bf84b3f5487b1e03f72bfc88d0b9d79edc13\`, [Actions 38850588365](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38850588365): Ubuntu **369 PASS/1 SKIP**, Windows **370 PASS**. Aynı koşu sentetik benchmark çıktıları:
- Ubuntu: parser 5 örneği 146.853 / 145.562 / 182.155 / 161.931 / 163.425 ms; edit 282.317 ms; undo 1.706 ms; Python tracer peak 8,254,771 byte.
- Windows: parser 251.357 / 237.165 / 284.868 / 270.868 / 288.021 ms; edit 466.291 ms; undo 5.787 ms; Python tracer peak 8,277,152 byte.
Bunlar yalnız GitHub-hosted sentetik, küçük örneklemli sayılardır; fiziksel hedef bilgisayarda performans eşiği veya p95 onayı değildir.

**Geliştirme durumu:** KISMI / Draft PR #2. Gerçek Windows 10/11 kullanıcı, bağımsız Edge tıklama/erişilebilirlik, gerçek çok katmanlı CAD/A0 PDF, process peak RSS ve imzalı bağımsız test kabulü **HOLD**. Gerçek Windows onedir .exe / lisans/SBOM ayrıca HOLD. İşlem 025 kapanışı yapılmadı; 026 geliştirmesi yapılmayacak. F08–F12 HUKUKI_HOLD ve REGULATORY_LOCKED değişmez.
