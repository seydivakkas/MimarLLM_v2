# İşlem 019 — Yerel çevrimdışı mimari analiz dashboard (F19)

- **Tarih:** 2026-10-14
- **Durum:** ÖN KAYIT — **İşlem 019'un ilk GitHub yazımı**, kod ve diğer dokümantasyon değişikliklerinden önce.
- **Ön koşul:** İşlem 018 kapatıldı, Ubuntu/Windows 279/279 sentetik test başarılı, F16 pipeline/CLI kısmi.
- **Kapsam:** F19: yerel tek kullanıcıya ait FastAPI/127.0.0.1 tarayıcı uygulaması; Windows-first, hazır çekirdeği yeniden kullanır.
- **İşlem sırası:** Önce bu dosya; sonra kaynak/test/UI/doküman; **en son yine bu dosyaya gerçek commit/test kanıtları yazılarak kapanış**. İşlem 001–018 kayıtları değiştirilmeyecek.

## Hedeflenen çalışan özellikler

1. `src/mimarllm/app/server.py`: `create_app(workspace)`; sabit yerel çalışma alanı; 127.0.0.1/localhost Host ve client doğrulaması; CSRF token, Origin doğrulaması, no-store, CSP, X-Content-Type-Options, dış kaynaklara gerek olmadan FastAPI; upload/analiz isteği tek kullanıcı için sınırlı.
2. `src/mimarllm/app/static/index.html`, `dashboard.css`, `dashboard.js`: Türkçe, erişilebilir yerel arayüz; DXF/PDF yükleme; dosyaları ve önceki analizleri listeleme; ilk analiz; DrawingIR native çizgi ID'si seçip bilinen metre ile kullanıcı referansı ekleyerek ikinci analiz; gelişmiş `PipelineConfig` JSON; frame/katman/kanıt ve teknik/HOLD durumları; gerçek raporu yeni sekmede açma; JSON/MD/PDF/manifest indirme. Her görüntü veri kaynağı çalıştırılmış pipeline/raporla bağlı olmalı.
3. `src/mimarllm/app/launch.py`: `python -m mimarllm.app.launch` / `mimarllm-dashboard` komutu, Uvicorn'un **sadece 127.0.0.1** adresine bağlanması. `--workspace` sadece başlatan yerel kullanıcı argümanı; HTTP talebi çalışma alanı yolunu belirleyemez.
4. Yanlış uzantı/path traversal, aşırı yükleme (DXF 25MB; PDF en çok 50MB), kötü biçimli JSON/config, ikinci eşzamanlı işlem, geçersiz proje/rapor ID, kaynak SHA değişimi, dış Host/Origin/istemci, CSRF ve dashboard kaynaklı HTML injection engellenmeli. Upload dosya adı HTTP dizinine dönüşmemeli. Tarayıcı sadece same-origin statik CSS/JS kullanmalı (CDN yok).
5. Her çalıştırma yeni UUID çalışma dizininde izole kalmalı; raporlar `run_local_pipeline` ve `export_report` aracılığıyla oluşturulmalı; `PARTIAL_WITH_ERRORS` olduğu gibi kullanıcıya gösterilmeli, hukukî `REGULATORY_LOCKED` değişmemeli.
6. `tests/test_dashboard.py` ve `.github/workflows/core-contracts.yml`: GitHub-hosted Linux/Windows üzerinde gerçek ASGI API/HTML yükleme/yeniden analiz/saldırı ve çıktı testleri. Testler gerçek müşteri Windows kullanıcı tarayıcısı kabulünün yerine geçmez.
7. `pyproject.toml` `dashboard` isteğe bağlı ekstra, sürümlemeli kullanım kılavuzu `docs/specs/dashboard-v0.1.md`, README/envanter/yol haritası/kararlar güncellenecek.

## Güven/ürün sınırı

- FastAPI dashboard F19'un ilk gerçek çalışan yerel arayüzüdür; **tam modern Windows native desktop installer veya otomatik CAD plot motoru değildir**. Kullanıcı Windows/Edge gerçek makine testi, uzun süreli dosya güvenliği ve sızma testi sonra yapılır.
- Bu aşamada ağdan mevzuat/PDF/model indirilmez. PDF OCR ancak ayrı CPU OCR ve kullanıcı ROI config ile; GPU/cloud ve ücretli API yok. Kaynak PDF SHA/geometri ve teknik ölçek denetimleri İşlem 018'den korunur.
- Teknik RuleEngine senaryosu "COMPLIANT" bina/yasal uygunluk sertifikası değildir. F08–F12 HUKUKI_HOLD ve RuleEngine.REGULATORY INSUFFICIENT_EVIDENCE.
- API'deki tek seferlik CSRF/görsel/Host savunmaları, makinenin ele geçirilmesine veya başka bir yerel process'e karşı yetkilendirme garantisi değildir; ağ erişimini bilinçli olarak loopback'le sınırla. Bu prototip müşteri LAN'ına açılmamalıdır.

## Gerçek değişiklik ve test sonuçları

Bu bölüm **son GitHub yazımında** kodlanan dosyalar, gerçek commit SHA'lar, Linux/Windows CI linkleri ve kalan açık risklerle tamamlanacaktır.
