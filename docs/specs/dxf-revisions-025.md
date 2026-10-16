# İşlem 025 — DXF kalıcı, kaynak-koruyan revizyon sözleşmesi v0.1

**Statü:** DRAFT; sentetik CI doğrulaması gerçek mimari kullanıcı kabulü değildir.

## Kapsam ve garantiler

1. Kullanıcının orijinal dosyası değişmez: \`projects/{project_id}/input.dxf\` immutable. SHA256 hem yükleme hem edit öncesi doğrulanır. Analiz raporu, DrawingIR, existing PDF ve mevzuat HOLD kesinlikle düzenleme ile güncellenmez.
2. Düzenleme sadece DXF **doğrudan Model layout LINE** elemanı içindir. \`cad:Model\`, kaynak CAD handle ve \`Model|{handle}|LINE\` eşsiz eşleşmesi zorunludur. INSERT içi LINE, paperspace, PDF çizgisi, ARC/POLYLINE/HATCH, Z≠0, belirsiz veya kötü DXF ret edilir.
3. İstemci \`source_sha256\`, \`expected_head\`, \`expected_sha256\`, özgün entity ID/frame/handle ve eski/yeni endpoint koordinatlarını gönderir. Kaynağa bağlı olmayan, eski snapshot ya da çakışan edit **409**. Alan hesabı/ölçek teyidi/yapı uygunluğu otomatik çıkarılmaz.
4. Noktalar 2B sonlu, [-1e6,1e6] CAD birimi aralığında; segment uzunluğu [1e-8,1e6] aralığında. \`ezdxf\` read/audit/write/read round-trip ile CAD handle ve editlenen noktalar yeniden doğrulanır. Geometri birimi **CAD native**, metre garantisi değildir.
5. \`edits/{revision_id}/drawing.dxf\` ve \`revision.json\` immutable revizyon; \`edits/head.json\` atomik head pointer ve append-only 24 revizyonlu geçmiş. Eşzamanlı değişiklik önleme uygulama içi kilit + beklenen head SHA kontrolü; aynı dosyanın farklı OS process'leri tarafından aynı anda düzenlenmesi **desteklenmez**.
6. \`UNDO\` son \`MOVE_LINE\` revizyonunun ebeveyn DXF bytes'ını *yeni* revizyona kopyalar. Undo geçmişten dosya silmez; üst üste otomatik undo/redo yok. Her revizyonda bağımsız SHA ve \`REGULATORY_LOCKED\` metadata tutulur.
7. \`GET /api/projects/{id}/edits\` geçmiş; \`POST /api/projects/{id}/edits\` düzenleme; \`POST /api/projects/{id}/edits/undo\` geri alma; \`GET /api/projects/{id}/edits/{revision_id}/download\` immutable DXF indir. Eski \`POST .../runs\`, yeni \`.../jobs\`, \`/reviews\`, \`/reports\` değişmedi.
8. Yeni dosya yükleyip analiz etmek **ayrı kullanıcı kararıdır**. Düzenlenmiş revizyon, önceki raporu otomatik geçerli kılmaz. SVG önizleme özgün kaynak çizgilerini göstermeye devam eder; edited DXF'nin yeni analizi ancak tekrar import sonrası gösterilebilir.

## Hata ve tehdit sınırları

- 403: Host, Origin, CSRF; 404: bilinmeyen revizyon; 409: SHA/HEAD/entity/geometry, symlink ve güvenli XML/DXF audit ret; 413: >4096 byte edit JSON; 415: PDF; 422: geçersiz Pydantic alanlar.
- Disk doluluğu, Windows antivirüs, büyük gerçek CAD, XREF, blok matrisleri, model/paper kesitleri, diğer CAD sistemleri ve çok process aynı workspace gerçek testlerde **HOLD**. Ani process ölümü \`head.json\` öncesi orphan revizyon klasörü bırakabilir; aktif head eski kalır. Bakım/garbage collector bu sürümde otomatik silmez.
- JavaScript UI kaynağı seçer, koordinat formuna kopyalar, doğrulanmış komutu yerel API'ye yollar; sonraki düzenleme için türetilmiş DXF'nin yeniden yüklenmesi önerilir. Orijinal çizim üzerinde görünmez değişiklik yok.
- Hiçbir CAD edit kaydı yeni oda, kapı, yangın çıkışı, brüt/net metrekare, mühür ya da hukukî sertifika değildir.

## Sentetik ve gerçek kabul ayrımı

\`tests/test_dashboard.py\`: ezdxf gerçek byte DXF üretim/audit, Model LINE handle-endpoint roundtrip, ikinci versiyon ve geri almanın önceki revizyon byte'ına dönüşü, restart sonrası kalıcılık, source/DrawingIR SHA koruması, JSON/CSRF/PDF/forged entity/stale SHA sınırları.

\`scripts/benchmark_025.py\` 500 sentetik Model LINE için 5 tekrar parser süresi, edit ve undo süreleri, Python-only tracemalloc peak; **native PDFium/ONNX DLL ve toplam Windows process RSS değildir.** Benchmark raporundaki süreler runner donanımı için geçerlidir, bağımsız müşteriye performans vaadi oluşturmaz.

\`scripts/windows/edge_smoke_025.py\` real Microsoft Edge headless + FastAPI localhost DOM; yalnız GitHub-hosted Windows testidir. Kullanıcının bilgisayarı, fiziksel aygıt, ekran okuyucu veya gerçek mimari çizim kabulü değildir.

\`scripts/windows/acceptance_025.ps1\` yalnız yüklü bağımlılıklar üzerinde test/manuel kanıt toplama, otomatik PASS imzalama değil.
