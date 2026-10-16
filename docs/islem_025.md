# İşlem 025 — Kaynaklı 2B Stüdyo, Kademeli Müfredat Arayüzü ve Kontrollü İş Akışı

- Tarih: 2026-10-16
- Durum: **IN_PROGRESS / DRAFT — uygulama ve CI doğrulaması bekleniyor.**
- Temel: main `74d311867f68789396cb72fc130650118e336cd5` (islem_024 kapanışı).
- Geliştirme dalı: `feature/islem-025-studio-workflow`.
- Güven kuralı: İşlem 001–024 geriye dönük değişmez; bu dosya dalın **ilk yazımıdır**.
- Önceki aday: `feature/studio-ui-safe-import-20261016` üzerindeki Draft PR #1; arayüz düzeni güvenlik kapıları kontrol edilerek bu işlemde tekleştirilecek, eski PR doğrudan main'e alınmayacak.

## 1. Amaç

Mevcut gerçek F19 FastAPI localhost dashboard'unu üç panelli kaynaklı 2B inceleme stüdyosuna genişletmek. Kaynak HTML'deki dört sınıf seçimi, 18/31/45/55 **müfredat katalog kapsamı** ve kanıt sekmelerini koruyarak; çalışan motorun mevcut `drawingir.json`, `analysis.html` ve `pipeline-manifest.json` kayıtlarıyla bağlamak.

## 2. İleri kapsam / tamamlandı sayılamaz

F31 bounded queue + SSE/polling, 55 modülün bağımsız gerçek özelliklerinin sınıf bazında uygulanması, gerçek 2B geometri üzerinde CAD kalıcı düzenleme, confirm edilmiş metraj, online AI, 2.5D/Three.js/VLM, gerçek rubrik/jüri/Delphi ve teknik hukukî değerlendirme kapsamı bu aşamada **kademeli** olarak geliştirilecektir. Sırf arayüz bölmesi veya MOD etiketi olması tamamlanmış modül demek değildir.

## 3. Önce uygulanacak kontrollü dilim

1. HTML demo uyarlaması: sınıf seçim düğmeleri ve üç panel; dış CDN ve sahte 3D kaldır.
2. `curriculum/registry.py`: 55 benzersiz MOD kimliğini ve 18/31/45/55 kümülatif katalog üyeliğini **salt-okunur, versiyonlu kayıt** olarak ele al; müfredat aktifliğini ürün uygulama durumundan ayır.
3. Kaynaklı 2B kanıt: mevcut analiz çalışmasına ait `analysis.html` bağlantısı; source SHA/frame/rapor kimliğini tek API'den al, yanlış kullanıcı yolunu destekleme.
4. Tek kullanıcı bounded analiz ve iş durumu: mevcut global Lock korunur; yeni SSE/polling iş akışında eşzamanlı iş budget/iptal/zaman ve önceki rapor bozulmaması ayrıca test edilecek.
5. Python + JS + erişilebilirlik + Ubuntu/Windows sentetik regresyon; ancak gerçek Edge görsel/UAT İşlem 031'e kalır.

## 4. Güven kapıları

- `REGULATORY_LOCKED` ve F08–F12 `HUKUKI_HOLD` değişmez. `RuleEngine.REGULATORY` sahte PASS üretmez.
- Kullanıcı referanslı metre ve topo onayı olmadan net alan, kaçış mesafesi, yönetmelik uygunluk ve sahte 3D pinleri yoktur.
- 55 katalog varlığını 55 çalışan modül diye göstermeyin; kısmi modüller için `PLANNED` veya `PARTIAL` durumunu belirtin.
- `main` içine otomatik birleştirme yok; 021–024 kapanmış kayıtlar/PR'lar korunur.
- Dış CDN, yeni API sağlayıcısı, bulut, telemetry ve `innerHTML` ile kullanıcı metni yürütme yok.

## 5. Teknik kapanış için gerekenler

- Kod/test değişiklikleri ve başarılı iki platform sentetik CI bağlantısı.
- Katalog sayımı ve grade gate API/frontend uçtan uca testleri; sahte SHA, yabancı run, boş rapor fail-closed.
- SSE/queue yapılmadıysa F31 `KISMI` belirtilir ve işlem **kapanmış** sayılmaz.
- Resmî hukukî, gerçek pafta, 3D/jüri, Windows/Edge gerçek kabul ayrı HOLD.

## 6. Çalışma kaydı

- **İlk commit:** Bu belge (ilk GitHub yazımı).
- **Sonraki işler:** gerçek kod dosyaları, testler, dokümantasyon ve CI sonuçları commit bazında yazılacak.
- **Şimdiki statü:** IN_PROGRESS; doğrulanmamış başarı iddiası yok.

## 7. Ara teslim — 2026-10-16 / kaynak kod ve sentetik CI

**İşlem 025 henüz kapanmadı.** Aşağıdaki kapsam mevcut dalda aday olarak kodlandı ve ana dala birleştirilmedi.

| Paket | Kod dosyaları | Sonuç |
| --- | --- | --- |
| Kanonik müfredat | `src/mimarllm/curriculum/{__init__,registry}.py` | 55 benzersiz MOD hedefi, 18/31/45/55 kümülatif katalog; `CATALOG_ONLY`, `grading_enabled=false` |
| API | `src/mimarllm/app/server.py` | `GET /api/curriculum/grades/{grade}`, yalnız 1–4; normal localhost Host/Origin/CSRF güvenlik katmanı korunur |
| Stüdyo UI | `app/static/{index.html,dashboard.css,dashboard.js}` | Kaynak HTML'den 3 sütun, dört sınıf, rapor ve hukukî kanıt sekmeleri, puansız 8 boyut çerçevesi; CDN/3D/jüri yok |
| Test | `tests/test_curriculum.py`, `.github/workflows/core-contracts.yml` | Linux/Windows'da mevcut tüm sentetik testlere eklendi |
| Teknik sözleşme | `docs/specs/studio-curriculum-v0.1.md` | Müfredat niyeti, ürün modu ve mevzuat kilidi ayrımı |

**Gerçek CI:** [GitHub Actions 38859351540](https://github.com/seydivakkas/MimarLLM_v2/actions/runs/38859351540), kaynak commit `055c9e1582adcbc61904ab0fa110803f7884d237`:
- Ubuntu Python 3.11: **371 passed, 1 skipped, 1 warning**, 0 failed.
- Windows GitHub-hosted Python 3.11: **372 passed, 1 warning**, 0 failed.
- 1 uyarı upstream Starlette/FastAPI testclient; gerçek kullanıcı Windows/Edge 2B arayüz kabulü değildir.

**Bilinçli olarak henüz yapılmayanlar:** gerçek queued job/SSE/polling, iptal/yeniden çalıştırma, iş geçmişi ve katman bazlı edit overlay; 55 kayıt için gerçek ayrı kurallar; resmî yasal kanıt/Delphi not/jüri; gerçek Windows ve büyük çizim kabulü. F31 tamamlandı veya İşlem 025 kapandı demek **yasak**.

**Önceki PR:** [Demo aktarımı PR #1](https://github.com/seydivakkas/MimarLLM_v2/pull/1) ayrı Draft idi; bu işte uygun arayüz öğeleri güncel `main` üzerinden yeniden alındı. Bu dalın [Draft PR #3](https://github.com/seydivakkas/MimarLLM_v2/pull/3) henüz birleştirilmedi.
