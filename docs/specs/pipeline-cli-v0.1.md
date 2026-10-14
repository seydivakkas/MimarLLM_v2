# İşlem 018 — Tek dosya çevrimdışı DXF/PDF analiz pipeline ve CLI v0.1

**Kapsam:** Windows-first, yerel DXF/PDF → DrawingIR → her frame'de Shapely aday geometri → yalnız kullanıcı kaynaklı geçit/alan incelemesinde NetworkX → yalnız açıkça verilen teknik RuleEngine senaryoları → İşlem 017 kaynaklı HTML/JSON/Markdown/PDF raporu.

**Kod:** `src/mimarllm/pipeline.py`, `src/mimarllm/cli.py`. **Geçmiş:** [docs/islem_018.md](../islem_018.md). **Sınır:** Gerçek yangın/imar mevzuatı, bina ve yaşam güvenliği uygunluk hükmü **verilmez**; `REGULATORY_LOCKED`. Bu v0.1, yerel klasörde çalışan CLI ve Python API'dir, tam masaüstü grafik arayüzü değildir.

## 1. Kurulum ve kullanım

Windows PowerShell (Python 3.11+; internet gerektirmeyen **çalışma zamanı**, bağımlılıklar önceden lokal kurulmuş olmalıdır):

```powershell
# Bağımlılıklar kurulu yerel Python ortamında:
python -m mimarllm.cli analyze "C:\projeler\plan.dxf" --output-dir "C:\projeler\sonuc"
# Aynı komut script giriş noktasıyla:
mimarllm analyze "C:\projeler\plan.dxf" --output-dir "C:\projeler\sonuc"
# Diğer çıktı biçimleri (ReportLab yalnız PDF dışa aktarımı için opsiyonel):
mimarllm analyze "C:\projeler\plan.pdf" --output-dir "C:\projeler\sonuc_2" --format json --format html --format md --format pdf
# Mevcut inceleme kararlarını yeniden kullanarak:
mimarllm analyze "C:\projeler\plan.dxf" --config "C:\projeler\inceleme.json" --output-dir "C:\projeler\sonuc_3"
```

**\`--output-dir\` zaten var olan bir yerel dizin olmalıdır**; CLI var olan dosyaları üzerine yazmaz. Farklı koşular için farklı klasör kullanın. Varsayılan çıktı `analysis.json`, `analysis.html` ve `pipeline-manifest.json`. `analysis.md` ve `analysis.pdf` isteğe bağlı. `pip install -e ".[reports]"` ile isteğe bağlı yerel ReportLab kurulabilir; kurulum offline gereksinimini karşılamak için paketler önceden cache/wheel olarak bulundurulmalıdır. Kod paket yöneticisine sessizce indirme talimatı vermez.

## 2. İlk koşu → source entity seçimi → kanıtlı ikinci koşu

İlk komut, DrawingIR kaynak geometrilerini ve `pipeline-manifest.json` dosyasını üretir. Açıklayıcı `analysis.json` içinde `sources[]` gerçek `entity_id`, `frame_id`, `origin_reference.document_sha256`, DXF için `cad_handle` / `block_path`, PDF için `page_index`, native `geometry.points` taşır.

İlk raporu görüp **doğru kaynak çizgisini gerçekten insan olarak seçtikten sonra**, ikinci koşunun inceleme JSON'una o `entity_id` kimliğini yazın. Örnek (placeholder gerçek kaynak ID ile değiştirilmelidir):

```json
{
  "calibration": {
    "entity_id": "BURAYA_ILK_RAPORDAN_NATIVE_LINE_ENTITY_ID",
    "known_length_metres": 4.0,
    "reviewer_id": "Yerel incelemeci",
    "method": "USER_REFERENCE"
  },
  "rules": [
    {
      "definition": {
        "rule_id": "synthetic.length.example",
        "version": "v1",
        "domain": "TECHNICAL",
        "metric": "SEGMENT_LENGTH_M",
        "description": "Yalnız sentetik teknik senaryo; yönetmelik değildir",
        "operator": ">=",
        "threshold": 3.5
      },
      "measurement_entity_id": "BURAYA_ILK_RAPORDAN_NATIVE_LINE_ENTITY_ID",
      "measurement_tolerance_source_units": 0
    }
  ]
}
```

Bu **teknik karşılaştırma** örneğindeki eşik bir Resmî Gazete sayısı değildir, gerçek mevzuat uygulaması olarak sunulamaz. Gerçek `entity_id` bulunmazsa kalibrasyon/ölçüm ret. Kaynak çizgi `CAD_NATIVE/PDF_NATIVE` değilse veya geometrisi native tek `SEGMENT` değilse fiziksel ölçek üretilmez. `$INSUNITS` yalnız `INFERRED`; otomatik `CONFIRMED` yapmaz. Onaylı referans **gerçek çizim kaynağından** hesaplanan uzunluk ve kullanıcı beyanlı gerçek metre eşleştirmesidir; bu ayrıca bağımsız saha metrologisi sertifikası değildir.

## 3. Opsiyonel OCR ve çoklu frame

PDF OCR **varsayılan kapalı**. İsteğe bağlı JSON: `"ocr_regions": {"0": [[20, 20, 300, 180]]}` (0 tabanlı PDF sayfası, üst-sol kaynak point koordinatlarında bbox). Sadece yerel `RapidCpuOcr` ve CPU ONNX Runtime bulunursa çalışır; explicit ROI verilmedikçe scan/OCR başlatılmaz, ücretli API gerekmez. Kod içinden `run_local_pipeline(path, ..., ocr_regions=..., ocr_reader=...)` ile bağımsız yerel OCR okuyucusu sağlanabilir. DXF OCR isteği ret. Koordinat, model ve tarayıcı tarafı OCR görsel review sonunda yapılmalıdır.

Varsayılan **bütün DrawingIR frame'leri** (PDF'de her sayfa, DXF'de mevcut model/layout) Shapely ile ayrı işlenir. `geometry_frame_ids` verilirse yalnız belirtilen frame'ler analiz edilir; yanlış frame ID veya 20 frame bütçesi aşımı ret. Fiziksel birimler frame bazlıdır; çoklu PDF sayfalarını rastgele birleştirip oda/kaçış rotası çizilmez. Özellikle metin glyph kutuları geometrik oda sınırı değildir.

## 4. Topoloji ancak açıkça seçilirse

`"topology"` seçeneklerinde `frame_id`, `spaces[]` (`SpaceReview.space_id, face_id, kind, reviewer_id`) ve `passages[]` (`PassageReview` taraf odaları, kaynak native marker ID, reviewer, sınırı kesen gerçek koordinat çifti) gerekir. `face_id` Shapely `GeometryAnalysis.faces` sonucundan gelmeli. Kullanıcı beyanlı açık kapı/geçit olmadan **otomatik NetworkX kenarı üretilmez**. Kullanıcının yalnız oda isimlerini/merkez noktalarını sağlaması yangın tahliye mesafesi üretmez.

`RuleRun` içerisinde `REVIEWED_TOPOLOGY_PATH` ancak `topology_frame_id`, `path_from_space_id`, `path_to_space_id` ve doğrulanmış ReviewedTopology ile değerlendirilebilir. Rapor `TOPOLOGICAL_HOPS_NOT_WALKING_DISTANCE` sınırını korur. İncelenmiş kapı olmayan dosyada `TOPOLOGY: SKIPPED`.

Alan teknik kontrolü için `ReviewedArea.frame_id`, `source_entity_ids`, `boundary_role` ve `reviewer_id` açıkça gerekir; Shapely tek ve net kapanan native boundary+aynı frame+kalibre edilmiş fiziksel ölçek yoksa `COMPLIANT` üretilmez. Başlık/layer/kapı adından oda/alan semantiği çıkarılmaz.

## 5. Aşama manifesti ve çıkış kodları

`pipeline-manifest.json` içinde `drawing_id`, SHA, kaynak türü, frame ID'leri, native entity sayısı, `face_candidate_count`, `topology_edge_count`, `rule_count`, `report_finding_count`, `calibration_state`, `import_issue_codes`, her aşamanın `status/reason_code/frame_id/details` alanı ve sabit `legal_gate=REGULATORY_LOCKED` bulunur.

| CLI kodu | Anlamı |
| --- | --- |
| `0` | Yerel kaynak ve rapor dosyaları oluşturuldu; inceleme/eksik kanıt açık olabilir. **Hukukî PASS değildir.** |
| `2` | Desteklenmeyen/bozuk yerel girdi, config, output çakışması veya reddedilen kaynak bağı |
| `3` | Beklenmeyen yerel pipeline istisnası; stack trace kullanıcıya yazdırılmaz |
| `4` | Rapor dosyaları kaynaklı üretildi ancak en az bir geometri/topoloji/RuleEngine aşaması `ERROR`; manifest `PARTIAL_WITH_ERRORS`. Kesin teknik sonuç olarak yorumlanamaz |

Sahte kesin başarımı önlemek için pipeline sonuç başlığı hiçbir zaman `BUILDING_COMPLIANT` değildir. `COMPLETED_WITH_REVIEW_GATES` her zaman manuel kaynak/uygulanabilirlik uyarılarını içerir; hata görüldüyse `PARTIAL_WITH_ERRORS` olur.

## 6. Güvenlik, performans ve açık kabul

- Açık dosyalar yalnız yerel `.dxf/.pdf`; configuration yalnız yerel `.json` (256 KB limit), unknown fields Pydantic `extra=forbid`; no remote API / secret token / background model download.
- DXF importer max entity budget, PDF importer max sayfa/eleman ve OCR ROI; geometri source segment budget; PDF/HTML export kaynak SHA ve bitmap boyutu limitleri mevcut v0.1 modüllerinden korunur.
- Sonraki koşunun çıktıları üzerine yazılmaz; CLI kaynakları yerel rapora bağlarken gerçek resmî Gazete PDF'si **kendiliğinden indirmez veya birleştirmez**. Hukukî kaynak görseli İşlem 015–017 API'lerine bağımsız, doğrulanmış LegalAST/PDF sağlanınca mümkün; CLI v0.1 doğrudan resmî norm vermez.
- **HOLD:** Gerçek kullanıcı Windows 10/11 cihazında kurulum ve uçtan uca test, gerçek mimari ve çok sayfalı saha PDF'leri, DXF zengin layout/hatch/render kabulü, hukuki bütün yılı kapsayan mevzuat ve yetkili orijin/yürürlük/görsel inceleme onayı, localhost masaüstü GUI. F16 yalnız **kısmi**; F08–F12 **HUKUKI_HOLD**.

**Mevcut CLI, mimarın kaynakları görerek kontrol edeceği bir mühendislik aracı çekirdeğidir; bağımsız bina güvenliği ve hukukî uygunluk yazılımı olarak sertifikalandırılmamıştır.**
