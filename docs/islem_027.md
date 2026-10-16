# İşlem 027 — Yerel GGUF/MMProj VLM, VRAM bütçesi ve kanıt-korumalı yorum adayı

**Tarih:** 2026-10-16  
**Durum:** GELİŞTİRME / SENTETİK CI ADAYI  
**Dal:** `feature/islem-027-local-vlm-guard`, kaynak `feature/islem-026-source-25d` (bağımlı İşlem 026 Draft PR #4).  
**İlk GitHub yazımı:** Bu işlem dosyası kod değişikliklerinden önce açılmıştır.

## Kesin mühendislik hedefi

1. Ayrı, isteğe bağlı, **yalnız yerel** llama.cpp `llama-server` çalıştırma adaptörü; **önceden hazırlanmış ve açık SHA256 ile doğrulanan** GGUF ve MMProj ağırlıkları. Dış model indirme, Hugging Face/Ollama remote daemon, ücretli API veya browser'dan rastgele URL yok.
2. Kullanıcı bilgisayarının VRAM/RAM ve model ağırlığı + MMProj + KV/compute rezervine göre fail-closed **bütçe kontrolü**. GPU kanıtı yoksa otomatik VRAM varsayma; güvenli CPU fallback yalnız izin verilmişse ve RAM bütçesi karşılanıyorsa. Modelin pratik doğruluğu, desteklediği vision template ve gerçek Windows GPU çalışma hızı İşlem 031'de kalır.
3. Kullanıcı tarafından açıkça seçilmiş **DrawingIR kaynak kimlikleri**, dosya SHA ve run ID ile bağlanan semantik `UNVERIFIED_VLM_SUGGESTION` JSON. VLM yanıtında yalnız önceden verilmiş entity ID referansları kabul edilir; yeni koordinat, alan, metre, oda, kapı, skor, gerçek hukukî PASS veya CAD mutasyonu yoktur.
4. Harici modelin ham metni, bir **güvenilmez aday** gibi Pydantic strict schema, uzunluk ve kimlik kontrolünden geçirilir. `DrawingIR`, `RuleEngine`, topoloji, rapor, hukukî RAG zinciri ve kullanıcının yüklediği kaynaklar **asla VLM yazmasına açık değildir**. Prompt injection metni komut kabul edilmez.
5. Kullanıcıya açık opt-in, localhost + CSRF, tek in-flight VLM işi, sonlu token/timeout/gövde ve model dosyası sınırları. Model/VRAM/yetki yoksa açık `UNAVAILABLE` / `INSUFFICIENT_EVIDENCE` ve deterministik işleyişe dokunmayan fallback.
6. İlk testler gerçek model ağırlığı gerektirmeyen sentetik adapter/fake llama-server protokolüyle yapılacak; gerçek fiziksel Windows 10/11, 8GB GPU/VRAM, MMProj vision kalitesi, bağımsız CAD/PDF ve offline EXE kullanıcı kabulü **İşlem 031 HOLD**.

## Sınırlar

- Tek kullanıcı, local-first, GGUF+MMProj dosyaları GitHub'a commit edilmeyecek; yerel kayıt SHA doğrulaması ve model-yayımlama/lisans incelemesi ayrı.
- GPU/RAM kapasitesi bilinmiyorsa cihaz niteliği uydurulmayacak. NVIDIA araçları yoksa GPU modu yetersiz kanıt sayılacak. CPU fallback, performans garantisi değildir.
- `RuleEngine.REGULATORY=INSUFFICIENT_EVIDENCE`, `REGULATORY_LOCKED`, F08–F12 `HUKUKI_HOLD` değişmez.
- İşlem 027'nin özellik kodu ve otomatik CI'sı tamamlanınca 028 rubrik ontolojisine geçilecek; fiziksel kabul toplu son 031.

## Teknik implementasyon sırası

1. `vlm/models.py` katı sözleşme/kimlik/fail-closed sonuç şeması.
2. `vlm/budget.py` açık RAM/VRAM bütçesi ve CPU/GPU kararı, gerçek cihaz ölçümüyle doğrulanana dek advisory.
3. `vlm/local_engine.py` explicit SHA ile yerel llama.cpp ikilisi/GGUF/MMProj başlatma ve yalnız `127.0.0.1` isteği, bounded response.
4. `app/server.py` kaynak-run/proje eşleştirmesi ve salt-okunur opt-in VLM endpoint; `static/` arayüzü.
5. Sentetik Linux/Windows testleri, docs/specs ve yeni bağımlı Draft PR.


## Gerçek geliştirilen modüller

- src/mimarllm/vlm/models.py: kullanıcı açık consent=true, kaynak kimliği ve şema validasyonu; yalnız UNVERIFIED_VLM_SUGGESTION, asla DrawingIR/RuleEngine/rapor veya hukukî PASS değil.
- src/mimarllm/vlm/budget.py: yerel OS mevcut RAM ve single NVIDIA nvidia-smi VRAM gözlemi; model+MMProj dosya ağırlığı + rezerv; GPU veya izinli CPU fallback, yetersiz/unknown kaynakta ret.
- src/mimarllm/vlm/source.py: aynı frame'deki 1–48 CAD_NATIVE/PDF_NATIVE LINE ve SHA doğrulamasından sonra tek 512×512 çizgi önizlemesi, orijinal belge/raster olduğuna dair yanlış iddia yok.
- src/mimarllm/vlm/local_engine.py: açık SHA'lı yerel llama-server + GGUF/MMProj, localhost-only geçici çalıştırma, kısa token/timeout, JSON-schema ve kaynak allowlist, redacted exception ve subprocess cleanup. Gerçek model henüz indirilmiyor/test edilmiyor; bilinen uyumlu model seti ispatlanmadı.
- scripts/windows/configure_vlm_027.py: trusted operator komutuyla workspace/vlm-runtime.json profilini atomik ve overwrite olmadan yazma; tarayıcıdan yerel dosya path ayarı yok.
- src/mimarllm/app/server.py: GET /api/vlm/status ve kaynak-run eşleştirmeli, tek in-flight/CSRF, 8KB JSON bütçeli POST .../vlm/suggest; model başarısızlığı deterministik raporları etkilemez.
- static/index.html/dashboard.js/dashboard.css: opt-in, kaynak seçme, soru/incelemeci ve sadece onaysız yorum görüntüsü. Model yoksa normal DXF/PDF/2.5D çalışır.
- tests/test_vlm_027.py: artifakt SHA, düşük VRAM/CPU fallback, sahte/bozuk JSON, ek hukukî/sayısal alanlar, onay yokluğu, kaynak dışı entity, 503/409/422/413/403, immutable orijinal DrawingIR ve localhost API.
- docs/specs/local-vlm-027-v0.1.md: modele erişim ve güvenlik/kabul protokolü. GitHub'a gerçek model ağırlığı veya model lisansı onaylanmadan binary commit edilmedi.

## Sentetik otomasyonun doğrulama durumu

Bağımlı aday Draft [PR #5](https://github.com/seydivakkas/MimarLLM_v2/pull/5) `feature/islem-027-local-vlm-guard` → İşlem 026 dalı. 
[Core CI #38863836375](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38863836375), kaynak / PR commit `d7005b31` için **Ubuntu 381 passed / 1 skipped; Windows 382 passed** (ve JS syntax, local Three vendor SHA hazırlığı), çıktı loglarında success. [Hosted Windows Edge #38863836474](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38863836474) success: gerçek localhost DOM, 027 VLM onay/soru/sonuç kontrolleri ve VLM model henüz yapılandırılmadıysa `configured=false` doğrulaması. Ardından server-side per-request consent=true zorunluluğu eklendi; bu son değişiklikler için yeni CI kesin PASS sonuçları ayrıca kontrol edilecektir.

**İşlem 027 mühendislik adayı:** YEREL_VLM_ADAPTÖRÜ_KODU / SENTETİK_CI_PASS; **gerçek GGUF/MMProj model inference yapılmadı**, fiziksel 8 GiB GPU/CUDA/VRAM testleri ve gerçek mimari kaynak kalitesi ölçülmedi. Bunlar `DEFERRED_TO_031` olarak tutulur. Dolayısıyla 027, yerel AI modelinin ürün ortamında çalıştığının veya düzenlemelerin hukukî geçerli olduğunun kanıtı değildir.

**Bir sonraki işlem 028:** Önce `docs/islem_028.md` yeni dalın ilk GitHub kaydı, sonra uzman hedefleriyle 8 boyutlu rubrik ontolojisi, sürümlü deterministik puanlama ve kaynaklı gerekçe. VLM önerisi hiçbir zaman tek başına not/puan oluşturamaz.
