# İşlem 025 — Fiziksel Windows/Edge ve performans kabul protokolü

**Durum:** AÇIK / kullanıcı cihazında yürütülmedi. Bu protokol bir PASS beyanı değildir.
**Test kapsamı:** MimarLLM V2 \`feature/islem-025-source-2d-jobs\` Draft PR, Python 3.11, tek kullanıcı localhost, Windows 10/11, Microsoft Edge.

## A. Ön hazırlık ve yeniden üretim

1. Gerçek Windows 10 veya 11, Edge sürümü, tam CPU/RAM/SSD/GPU özelliklerini, UTC tarihi, Git commit SHA'sını, uygulama \`MimarLLM_V2.exe\` veya local Python çalıştırma türünü ve bağımsız incelemeci ismini formda kaydet. Kaynak DXF/PDF özel verisini public GitHub'a yükleme.
2. Önceden doğrulanmış offline bağımlılıklar / wheelhouse ve lisans kontrolleri için İşlem 021 kabul şartlarını uygula. \`onedir\` bizzat üretilmiş ve SHA doğrulanmış değilse "gerçek paket kabulü" yazma.
3. Bağlı internette hazırlık ayrı; uygulama runtime kabulünü ağ kapalı olarak yeniden test et. Harici CDN/AI API, OCR model indirimi veya fonksiyonları dış ağa yönlendirme reddedilmeli.
4. Hedef bilgisayarın repo checkout ortamında yalnız yüklü Python 3.11 ve bağımlılıklarla \`powershell -ExecutionPolicy Bypass -File scripts/windows/acceptance_025.ps1\` çalıştır. Bu betik \`artifacts/manual-windows-025/\` içine sentetik performans raporu ve ilk manuel kabul formu yazar; hiçbir veri GitHub'a otomatik gönderilmez.

## B. Gerçek tarayıcı ve arayüz

- Edge'de uygulamayı \`http://127.0.0.1:<port>\` ile aç. Yanlış Host/Origin ve uzak istemci istekleri 403, local GET session 200. Bağımsız testçi adres/OS logunu imzalar.
- Klavye ile menü, DXF/PDF dosya yükleme, 2B kaynak line seçme, kaynak inceleme, katman/frame değişimi, inceleme notu, revizyon ve Undo butonlarına sırayla erişilebilmeli. Odak görünür, ekran okuyucu etiketleri mantıklı, Zoom %200 ve yüksek kontrastta taşma not edilir.
- Gerçek çizimden bir doğrudan Model LINE tanımlanır; tam CAD handle, frame ID, yüklenen input SHA ve iki uç değerleri kaydedilir. \`POST .../edits\` ile farklı koordinata taşı; \`GET .../edits/{id}/download\` ile türetilmiş DXF'yi indirip bağımsız CAD görüntüleyicide aç. Yeni dosyada çizgi değişmiş olmalı, aynı handle korunmalı; diğer çizimler ve orijinal dosya byte düzeyinde değişmemiş olmalı.
- \`UNDO\` sonrası yeni, ayrı DXF revizyonunu indirip önceki sürümle byte ve geometri açısından kıyasla. Audit günlüğü silinmemeli. Değişen türetilmiş DXF tekrar import edilip **yeni** rapor/SHA üretilebilir; mevcut raporun otomatik güncellendiği iddia edilmez.
- PDF kaynak/rotasyon/ROI doğrulaması; yanlış kaynak, bozuk PDF ve karmaşık DXF bloklarının fail-closed davranışı gözlenir.
- Hatalı içerikte mutlak Windows kullanıcı dosya yolları, mevzuat PASS veya veri sızıntısı gösterilmemeli.

## C. Performans planı

- **Sentetik baseline:** \`scripts/benchmark_025.py\` 500 native LINE, 5 parse tekrar, tek edit/undo ve Python-only \`tracemalloc\` peak. Github-hosted sayılar yerel makine performansını temsil etmez.
- **Gerçek veri:** En az üç izinli anonimleştirilmiş çizim sınıfı: küçük DXF (yüzlerce entity), kirli/katmanlı büyük DXF (binlerce entity), sayfa boyutu bilinen PDF/A0. Kaynak SHA, entity sayısı, dosya bayt ve OS RAM kullanımını kaydet. Gerçek dosyaları paylaşma.
- Her veri sınıfında en az 20 tekrar p50/p95 wall-clock, yükleme/rapor/çizim/UI ilk etkileşim, CPU/tepe RSS/OS Working Set, disk alanı ve hata oranını ölç. Edge DOM veya sentetik testlerin tek bir başarı anı p95 değildir.
- Performans eşikleri ancak ölçüm öncesi sabitlenmiş ayrı bir kriter formuna yazıldıktan sonra PASS/FAIL verilebilir. Bu sürümde kullanıcı donanımı üzerinde performans sonucu yoktur.
- Bellek/DoS sınırını aşan analizde sistem açık hata vermeli; sessiz otomatik alan/geometri onayına geçmemeli.

## D. Kabul formu ve durum

| Kapı | Kanıt | Başlangıç durumu |
| --- | --- | --- |
| GitHub Windows + Ubuntu sentetik CI | Run URL, test toplamı, commit SHA | Ayrı doğrulanır |
| GitHub-hosted Edge headless smoke | Run URL, DOM doğrulama, artifact | Ayrı doğrulanır |
| Fiziksel Windows Edge kullanıcı tıklama ve erişilebilirlik | Tarihli ekran/konsol/prosedür | HOLD |
| Gerçek CAD DXF revizyonu ve undo ölçümü | SHA + CAD handle + ayrı CAD viewer doğrulaması | HOLD |
| Gerçek PDF/A0 ve performans p50/p95/peak RSS | Ham lokal ölçüm kaydı | HOLD |
| Offline tam \`onedir\`, DLL, imza/lisans/SBOM | Teknik rapor/NOTICE bağımsız inceleme | HOLD |
| Hukukî yürürlük / uzman alan-geometri uygunluk | Bağımsız hukukî ve mimarî kayıt | HUKUKI_HOLD |

**Kapanış kuralı:** Gerçek testçi imzaları, sürüm/OS/cihaz ve ölçüm kanıtları tamamlanmadan \`docs/islem_025.md\` \`KAPATILDI\` olmaz, PR #2 merge edilmez, \`islem_026\` geliştirmesi başlatılmaz.
