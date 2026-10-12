# İşlem 006 — V2 tam özellik envanteri ve uygulama yol haritası

- **Tarih:** 2026-10-13
- **Durum:** PLANLANDI — kayıt, bu isteğin diğer değişikliklerinden önce oluşturuluyor.
- **İstek:** Kullanıcının yüklediği 20 metin/Markdown ekinde ve sohbet metninde hedeflenen geometri, topoloji, OCR, yapısal mevzuat RAG, 5 hukukî kontrol ailesi, raporlama, CLI, yerel web arayüzü, Windows run/build betikleri, yerel VLM ve benchmark çalışmalarını MimarLLM V2'nin özellik kapsamına dahil et; yapılmış gibi gösterme; sonraki geliştirme adımlarını planla.
- **Depo:** `seydivakkas/MimarLLM_v2`
- **Değişmezler:** Windows-first, 14. nesil i7/32 GB RAM/RTX 4070 8 GB, sıfır bulut AI API, tek kullanıcı modüler monolit, deterministik geometri ve kural, PDF/OCR için sadece `pdfplumber` + `pypdfium2` + `rapidocr`/`onnxruntime CPU`, gerçek mimari dosya veya model ağırlığı public repoya konmaz.

## 1. İncelenen kaynakların statüsü

- Kullanıcının sağladığı `Yapıştırılan metin(20261012-210047).txt` ve `Yapıştırılan markdown (2).md` … `(20).md` dahil **20 yükleme**.
- `(14).md` ve `(15).md` içerikleri birebir aynı Sığınak Yönetmeliği işlem taslağıdır; **bir kez** envantere alınacak.
- Eklerdeki “geliştirilmiştir / PASS / %100 / 0ms / 0MB / <2.5GB” ifadeleri **kanıt değildir**; bunlar örnek kod/tasarım ve hedef iddiasıdır. GitHub'da olmayan özellik `PLANLANDI` veya `HOLD`.
- Eklerdeki `src/mimar/` ve yeniden başlatılmış `islem_002`…`islem_020` numaraları **kullanılmayacak**: gerçek repo paketi `src/mimarllm/`; bu işlem `islem_006`. Mevcut 001–005 korunur.

## 2. Bu işlemde üretilmesi beklenen belgeler

1. `docs/ozellik-envanteri.md` — tüm hedeflerin modül, öncelik, mevcut durum, kabul kanıtı ve kaynak taslak numarasıyla tek takip tablosu.
2. `docs/uygulama-yol-haritasi.md` — iş paketleri ve bağımlılıklar; değişmeyen islem kayıt sıra politikası.
3. `docs/mevzuat-dogrulama-protokolu.md` — 5 hedef mevzuat için kaynak, sayfa/quad, temporal applicability, hukukî doğrulama kapısı ve yüksek riskli sayısal varsayımlar.
4. `docs/planlanan-dosya-yapisi.md` — gerçek paket adlarıyla minimal modüler monolit dizini; sadece gerektiğinde modül oluşturma.
5. `docs/windows-dagitim-plani.md` — run.bat, PyInstaller onedir ve tek-user localhost web tasarım/kurulum kapıları; var olmayan web uygulaması çalışıyor izlenimi yok.
6. `docs/adr/ADR-003-Kapsam-Kanit-ve-Kabul-Kapilari.md` — esas mimari karar.
7. `README.md` ve `docs/kararlar.md` — tek kaynak bağlantıları ve kapsam güncellemesi.

## 3. Doğruluk ve güvenlik şartları

- Mimari oda/duvar/kapı tanıma bir belirsizlik modelidir; katman adları ve şekil sezgileri kesin sınıf değildir.
- Ölçek CAD `$INSUNITS`, doğrulanmış ölçü entity veya kalibrasyon çubuğu olmadan tahmin edilmez.
- Net alan iç yüzey geometrisiyle hesaplanır; tek bir poligon `buffer` her durumda gerçek net alan değildir.
- Yangın kaçışı için oda centroidleri arasındaki düz çizgi değil, yürüme yolu/kısıtlı alan grafı ve doğru çıkış hedefi gerekir.
- Mevzuat: her eşik yalnız doğrulanmış özgün madde/fıkra/bent/tablo, değişiklik/yürürlük, proje tarihi ve sınıfı, istisna ve gerekirse mahalle/imar plan notu ile `APPROVED_FOR_CHECK` statüsünde etkinleşir.
- 2025 sonrası düzenleme değişiklikleri bulunduğu için kullanıcının taslaklarındaki Yangın/Sığınak/Otopark/BEP sayıları **ön onaylı üretim kuralı değildir**.
- Mevzuat arama isabeti, hukukî uyum veya doğru atıf yerine geçmez.
- Yerel VLM semantik aday üretir; ölçü, yasa veya nihai PASS oluşturmaz.
- Web arayüzü localhost loopback, CSRF/dosyaya erişim sınırları ve statik paket offline kontrolüne bağlı.
- Ticari dağıtım için lisans/NOTICE/alt kütüphane/binary SBOM olmadan “tam lisans temizliği” PASS değil.

## 4. İlk GitHub kod durumu (işlem başı)

Gerçek mevcut kod: `src/mimarllm/core/models.py`, `src/mimarllm/importers/pdf.py`, `src/mimarllm/ocr/rapid_engine.py`, minimal `__init__.py` dosyaları ve `tests/test_pdf_contract.py`. `pyproject.toml` var; `src/mimarllm/geometry`, `rules`, `rag`, `app`, `pipeline`, `cli`, `run.bat`, `build_exe.bat`, `.spec` **henüz yok**. Gerçek RapidOCR/OCR Windows testi yok.

## 5. Uygulama sonuçları

Belgeler commit edilip kontrol edildikten sonra bu bölüm güncellenecektir. Yeni kod geliştirme isteği kayıt sırasına göre `docs/islem_007.md` ile başlayacaktır; bu `islem_007`, yüklenen eski taslaktaki OCR numarasıyla karıştırılmamalıdır.
