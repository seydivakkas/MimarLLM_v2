# F31 — Dashboard 2B kaynak inceleme ve sınırlı analiz işleri v0.1

**İşlem:** `docs/islem_025.md`. **Durum:** Kaynak kodu adayı; gerçek Windows kullanıcı kabulü / mimari semantik / kalıcı CAD edit mevcut değil.

## Tek yerel kullanıcı modeli

- Mevcut FastAPI `create_app(workspace)`, CSP, loopback, Origin ve `X-Mimar-CSRF` kapıları korunur.
- Yeni `POST /api/projects/{project_id}/jobs`, mevcut `RunPayload` JSON formatını alır. `202` ile `job_id`, `source_sha256`, `QUEUED` döner.
- `GET /api/projects/{project_id}/jobs/{job_id}`: yalnız doğru projeyle eşleşen `job_id` ve durumunu döndürür. Geçersiz veya uygulama yeniden başlatıldığı için artık bilinmeyen iş = `404`.
- Durumlar: `QUEUED` → `RUNNING` → `COMPLETED` veya `FAILED`. `completion` analiz manifestindeki bağımsız teknik tamamlanma etiketidir; hukukî uygunluk değildir.
- `COMPLETED` sonrası `run_id`, eski `GET .../runs/{run_id}` raporuna götürür. Orijinal kaynak, DrawingIR, kaynak SHA ve report JSON aynı kalır.
- Tek daemon analiz çalışanı, uygulama başına en fazla 4 aktif+bekleyen iş, 64 durum geçmişi. Genel servis/dağıtık garantisi, kalıcı iş kuyruğu, uygulama kapanışı sonrası görevi sürdürme, kullanıcı/OS process izolasyonu veya yüzde ilerlemesi sunulmaz.
- `429`: iş kapasitesi dolu; `413`: 256 KB'den büyük JSON; `422`: doğrulanmamış payload; `403`: CSRF/host/origin güvenliği.
- Hatalarda ham içerik, PDF metni ve mutlak yerel dosya yolu API'ye döndürülmez. Kaynak SHA doğrulaması analiz öncesi ve sonrası yapılır.
- Önceki senkron `POST .../runs` yolu korundu; aynı `running` kilidini kullanır ve eşzamanlı çalışma ihtimalini reddeder.

## 2B kanıt katmanı

- Çizim HTML/JS DOM üzerinden yalnız `native_lines` ile yaratılan **salt-okunur SVG**'dir. Sadece kaynaklı `CAD_NATIVE` ve `PDF_NATIVE`, `LINE/PDF_LINE`, `SEGMENT` ve iki nokta; önceki backend'in en fazla 400 native-line önizleme sınırı geçerlidir.
- `frame_id` ve `layer` filtreleri aynı raporda gösterilir. Tek çizgi seçildiğinde `source_sha256`, `frame_id`, `origin`, `entity_id`, CAD handle ve native koordinatlar gösterilir. Hiçbiri ayrı yasal/onaylı oda semantiği değildir.
- Kaynak verisinden `innerHTML` veya `eval` üretilmez; kullanıcı girdisi `textContent`/DOM attribute ile işlenir. Harici JS/CDN/Three.js yüklenmez.
- CAD Y ekseninde görsel dönüşüm yalnız SVG'de uygulanır; PDF native üst-yön referansı ayrı tutulur. Orijinal koordinatlar kaynak panelinde olduğu gibi gösterilir; metrik veya ölçek onayı çıkarılmaz.
- Salt-okunur SVG üzerinde seçimden sonra **manuel inceleme notu** ekleme ve geri alma denetim kaydı mevcuttur. Bu özellik fiziksel CAD geometrisini düzenlemez. Kalıcı CAD edit, geometrik undo, 3B önizleme, otonom Layer 0 sınıflaması ve gerçek PDF sayfa üstüne bindirmesi **henüz yoktur**.

## Kabul

- Ubuntu + Windows mevcut sentetik API/DXF/PDF/RAG/rule testlerinin ve yeni job/2D/CSP kontrolünün geçmesi.
- JavaScript sözdizimi her iki CI ortamında `node --check` ile doğrulanır.
- Gerçek Windows/Edge tıklama, Android/mobil, gerçek mimari A0/bozuk CAD, fiziksel performans, model GPU ve hukukî uzman kabulü nihai İşlem 031'e kalır.

## 3. Yerel manuel inceleme sidecar

- `GET /api/projects/{project_id}/runs/{run_id}/reviews`: mevcut run ve kaynak SHA doğrulandıktan sonra `UNVERIFIED_OBSERVATION` notlarını, geri alınmış kayıtlar dahil döndürür.
- `POST .../reviews` (201): `source_sha256`, `entity_id`, `frame_id`, `reviewer_label`, `note` JSON; 409 kaynak/frame/eşsiz native-line uyuşmazlığı, 413 üst sınır 4KB, 422 şema hatası.
- `DELETE .../reviews/{review_id}` (200): notu silmez, `retracted_utc` ile denetim izini korur; aynı notun tekrar geri alınması 409.
- Yalnız DrawingIR içinde aynı SHA+frame/entity ile bulunan native `LINE/PDF_LINE` için yazım yapılır. Yazım, `run/review-notes.json` sidecar dosyasına atomik yapılır; 100 not / 120KB üst sınır ve symlink ret kapısı vardır.
- Kullanıcı notları gerçek kimlik doğrulamalı uzman görüşü değildir. `reviewer_label` kullanıcı girdisidir; oluşturulan not `RuleEngine` ve hukukî mevzuat kanıtına otomatik eklenmez.
- `analysis.html`, `analysis.json`, orijinal DXF/PDF, `drawingir.json` veya pipeline manifesti not ekleme/geri alma sırasında değiştirilmez. Sidecar PDF HTML rapor çıktısı içine sahte hukukî işaret eklemez.
- CI sentetik testleri persistence, POST/GET/DELETE, CSRF, SHA/ID taklidi, 4KB sınırı, kaynak bütünlüğü ve `REGULATORY_LOCKED` durumunu korumayı inceler.
