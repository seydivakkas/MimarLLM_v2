# İşlem 027 — Tamamen yerel GGUF/MMProj VLM güvenlik sözleşmesi v0.1

**İşlem 027 durumu:** Mühendislik kod adayı ve sentetik CI. **Gerçek GGUF + MMProj modeli bu depoda yoktur**; modele gerçek bilgisayarda inference yapıldı denemez. **Fiziksel GPU, kalibre edilmiş VRAM/RSS ve gerçek görüntü kalitesi kabulü İşlem 031'de HOLD.**

## Bileşen sözleşmeleri

- \`vlm/models.py\`: Serileştirme iki ayrı katmandır. Güvenilmeyen model sadece \`ModelOnlyPayload.suggestions\` listesini (\`entity_ids\`, \`kind\`, \`commentary\`) üretebilir. En çok 4 öneri, her öneri 1–8 **yalnız istemcinin seçtiği ve DrawingIR'da doğrulanan** entity, kısa yorum. \`extra="forbid"\`; model kaynak SHA, koordinat, sayısal metre/m², RuleEngine PASS, mevzuat numarası, skor veya DrawingIR nesnesi üretemez. Sonuç kimliği ve \`REGULATORY_LOCKED\`, \`can_modify_drawing=false\`, \`can_approve_regulations=false\` server tarafından eklenir.
- \`vlm/source.py\`: 1–48 native DXF/PDF LINE ve tek kaynak frame; SHA, frame, entity/origin eşleşmesi, NaN/koordinat/boş geometri sınırları; 512×512 PNG \`source-derived linework preview\`. **Bu PNG kaynak belgenin gerçek raster fotoğrafı veya fiziksel plan resmi değildir.** Çoklu sayfa, OCR, VLM kaynaklı veya metin parse edilmiş kimlikler reddedilir.
- \`vlm/budget.py\`: Bilinmeyen RAM bilgisinde model çalışmaz. \`/proc/meminfo\` (Linux) veya \`GlobalMemoryStatusEx\` (Windows) yerel anlık **available RAM**, \`nvidia-smi\` tek GPU boş VRAM sağlayabiliyorsa GPU bütçesi; çift NVIDIA veya NVIDIA dışı GPU'da otomatik GPU cihazı tahmin edilmez. Model+MMProj dosya byte'larının \`1.35×\` yaklaşık büyüklüğüne **1.5 GiB** rezerv eklenir. \`GPU_BUDGETED\` sadece yeterliyse \`n_gpu_layers=99\`; aksi durumda operatörün izin verdiği RAM ölçümü yeterliyse \`CPU_FALLBACK\` (\`n_gpu_layers=0\`, MMProj CPU), yoksa fail-closed. Bunlar **heuristik ön denetim**; gerçek CUDA/Vulkan/Windows VRAM OOM garantisi değildir.
- \`vlm/local_engine.py\`: Operatör konfigürasyonundaki yerel llama-server ikilisi/GGUF/MMProj path+SHA kontrollerinden sonra yalnız \`127.0.0.1\`/rasgele port üzerinde geçici subprocess. \`--model\`, \`--mmproj\`, \`--n-gpu-layers\`, \`--ctx-size\`, \`--parallel 1\`, \`--fit off\`, \`--host 127.0.0.1\`; subprocess kapatılır. \`/v1/chat/completions\` image data URI (yalnız seçilen çizgiler) ve \`response_format.type=json_schema\`; sıcaklık 0, 32–256 output token, startup 5–180 s, response 5–120 s, sıkı JSON output doğrulaması. Proxy kullanılmaz; alt işleme sır/erişim anahtarları aktarılmaz, HF offline işaretleri aktif. OS egress güvenlik duvarının yerini tutmaz; Windows cihazında gerçek network izolasyonu İşlem 031'de doğrulanır.
- \`scripts/windows/configure_vlm_027.py\`: Bilinçli **operatör komutu**; SHA hesaplanır, dosyalar mevcut ve yerel olmalı, \`workspace/vlm-runtime.json\` adlı **tek** operator-owned profil atomik/0600 oluşturulur; varolan ayar otomatik üzerine yazılmaz. Web tarayıcısı yol, binary veya model seçip server'a iletemez.
- \`app/server.py\`: \`GET /api/vlm/status\` (yol ifşa etmeden config var mı), \`POST /api/projects/{project_id}/runs/{run_id}/vlm/suggest\` (CSRF, tek iş kilidi/429, 8192 byte, source SHA/drawing run, ayrı thread, redacted hata). Varolan sync/async analiz, geometri/topoloji kural motorları ve immutable raporlar çağrının yazma hedefi değildir.
- \`app/static/index.html\` + \`dashboard.js\`: açık opt-in, frame ve çizgi ID seçimi, kullanıcı kısa sorusu, incelemeci etiketi, kaynak SHA ve ancak onaysız yorum adayları; DOM \`textContent\` kullanır. Model eksikse rapor/2B/2.5D ve hukuki HOLD aynen çalışır.

## Tek seferlik yerel hazırlama

Çalışma anında **npm, pip, git, curl, Hugging Face, OpenAI/Azure vb. indirme veya abonelik yoktur**. \`llama-server\` executable, lisans/doğrulanmış GGUF temel model ve **onunla uyumlu MMProj** kullanıcı tarafından önceden, hak ve lisansları kontrol edilerek yerel bilgisayara hazırlanır; dosyalar kamu GitHub'a yüklenmez.

Windows örneği (önceden yüklenmiş Python 3.11 + uygulama ortamında):
\`\`\`powershell
python scripts/windows/configure_vlm_027.py --workspace "C:\Users\you\AppData\Local\MimarLLM\workspace" --llama-server "D:\models\llama-server.exe" --model "D:\models\architecture-Q4.gguf" --mmproj "D:\models\mmproj.gguf" --gpu
\`\`\`
Model/binary adları burada sadece operatör tarafından seçilecek örneklerdir; önceden var oldukları iddia edilmez. \`--gpu\` olsa bile yetersiz kanıtta izin verilen CPU fallback işletilebilir, RAM de yetersizse tamamen reddedilir. CPU fallback yasaksa \`--no-cpu-fallback\` verilir.

\`vlm-runtime.json\` içeriği **GitHub'a/rapora/istemciye** aktarılmaz; depoda config dosyasının kendisi veya model ağırlıkları bulunmaz. Şifreleme/çok kullanıcı erişim kontrolü bu sürümün kapsamı değildir; OS kullanıcı dosya hakları önemlidir.

## Güvenlik / kabul matrisinin ölçülen ve eksik kısımları

- Sentetik: Pydantic forbid-extra, model sahte kaynak ID/status/PASS/m² reddi, SHA artifakt tamper, kaynak seçim/immutable DrawingIR, yerel PNG, CPU/GPU memory fail-closed, localhost endpoint CSRF, eksik config = 503, over-limit = 413, hatalı komut = 422 ve single-job kilidi.
- Gerçek model inference: **HOLD**. Hangi llama.cpp binary commit/tag, GPU backend/CUDA, GGUF quant, MMProj chat template/resim token sayısı ve kullanıcının 8 GiB GPU kapasitesinin yeterliliği gerçek donanımda ölçülmedi. JSON schema desteği server sürümüne bağlı olabilir; uyumsuzsa fail-closed. 8GB VRAM ile belirli modelin çalışacağı iddia edilmez.
- Saha: gerçek plan/pafta görüntüleri, mimari uzman false positive/precision, skor/jüri, GPU bellek tepe RSS/VRAM ve offline exe: **İşlem 031**.
- Hukuk: F08–F12 HUKUKI_HOLD, \`REGULATORY_LOCKED\`. VLM model metni asla yönetmelik kaynağı veya teknik uygunluk PASS değildir.

## Sonraki işlem

027 sentetik katman tamamlandığında **028 rubrik ontolojisi ve skorun modelden ayrı deterministik hesaplanması**; 029 jüri ve 030 analitik, 031 son fiziksel kabul. PR'lar bağımlı Draft'tır; hiçbir dal \`main\`e otomatik birleştirilmez.


## Model işleme izni — API düzeyinde ayrıca zorunlu

VlmRequest ayrıca tam olarak **consent=true** alanını gerektirir. İstemcideki onay kutusu bu değeri yalnız işaretliyken gönderir; sunucu gelen JSON'da false/eksik consent'ı şema hatası (422) ile reddeder. VLM otomatik açılmaz, rapor inceleme veya 2B/2.5D iş akışı modele gizli veri göndermez. Yerel operatör config dosyasının mevcut olması kullanıcı onayının yerine geçmez.
