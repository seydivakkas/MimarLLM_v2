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
