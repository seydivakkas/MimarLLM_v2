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
