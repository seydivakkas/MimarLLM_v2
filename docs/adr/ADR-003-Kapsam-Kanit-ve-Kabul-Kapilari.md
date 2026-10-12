# ADR-003 — Kanıta Dayalı Modüler Ürün Kapsamı ve Kabul Kapıları

- **Durum:** KABUL EDİLDİ — tasarım ilkesi
- **Tarih:** 2026-10-13
- **İşlem:** [islem_006](../islem_006.md)
- **Alternatifler:** Yüklenen 20 ekten doğrudan kaynak kopyalama; 20 işi bitmiş varsayma; işlem numaralarını başa sarma; düz metin/embedding skoru ile hukukî PASS üretme.

## Karar

MimarLLM V2 kapsamındaki tüm kullanıcı taslakları [özellik envanterinde](../ozellik-envanteri.md) korunur ama GitHub kodu doğrulanmadan **uygulanmış sayılmaz**. Mevcut `docs/islem_001...005` numaraları korunur; yeni işlem `islem_006`, sonraki kaynak geliştirme `islem_007`. Eski `src/mimar` şeması yeni projeye kopyalanmaz; `src/mimarllm` tek paket.

### Güven ve otorite ayrımı

1. **Native CAD/PDF:** Geometri/koordinat ve kaynak entity referansı; CAD layer dahi kesin semantik olmayabilir.
2. **OCR:** RapidOCR CPU'dan metin+polygon adayı; hata/rotation ve sembol belirsizliği saklanır.
3. **VLM:** Yerel modelden belirsiz semantik aday; net ölçü veya mevzuat nihai kararına ulaşamaz.
4. **Geometri:** Kalibre edilmiş kaynak ve tanımlı toleransla hesap; net alan için iç yüzey sınırı zorunlu.
5. **RAG:** Yapısal, sürümlü kaynak metni arama; arama sonucu `CANDIDATE_SOURCE`.
6. **Kural:** kaynak, değişiklik/yürürlük, istisna ve proje bağlamı alan uzmanı tarafından bağlanmışsa `APPROVED_FOR_CHECK`; ölçü doğruysa COMPLIANT/NON_COMPLIANT.
7. **Rapor:** Kaynak PDF sayfa/quad, çizim entity/bbox ve hesap aynı bulguda; eksik kaynak raporda açık.

### Kural değerleri için karar

Yapıştırılan örneklerdeki oda 2.80m, 12m², kapı 0.90m, koridor 1.20m, kaçış 15/30m, sığınak 12 bağımsız bölüm, otopark birim hesabı, BEP %40 WWR vb. rakamlar **kaynakta doğrulanmadan mühendislik kuralı yapılmayacak**. Kodda varsayılan hukukî sabitler yerine onaylanmış sürümlü `RuleBinding` kullanılacak. Sentetik test eşikleri örnek olarak tutulursa **SYNTHETIC_ONLY**.

### Mimari sınırlamalar

- Donanım: i7 14. nesil, RAM 32 GB, NVIDIA 8 GB. VRAM/CPU performansı ölçülmeden iddia yok.
- PDF/OCR: [ADR-002](ADR-002-PDF-Engine-License.md) kesin: pdfplumber, pypdfium2, RapidOCR CPU; başka engine eklenmeyecek.
- Tek kullanıcı, yerel/localhost, sıfır AI API, makul bağımlılık, önce sentetik test sonra gerçek kullanıcı verisi izinleri.
- Mevzuat kaynak sayfaları ve özel müşteri dosyaları yalnız `local_data/`; public GitHub'a kopyalanamaz.
- Seçilen izinli lisanslar, dağıtımın tam lisans risksiz olduğunu kanıtlamaz; son SBOM kapısı zorunlu.

### Kabul ölçütleri

Aynı kaynak geometri ve sürümlü kural aynı sonucu üretmeli; reviewer olmadan mevzuat kararı kesinleşmemeli; konum gösterimi hash ile kaynak PDF ve CAD varlığına dönmeli; sistem VLM/OCR olmayan cihazda deterministik çekirdekle uygun kapsamda çalışmalı; başarısız modül `ERROR`/eksik kanıt üretebilmeli, otomatik `PASS` olamaz.

**Sonuç:** Özellik listesi “tam ürün hedefi”, mevcut kod “kısmi uygulama” ve doğrulanan çalışma “ayrı kabul” kavramları korunur.
