# PDF Motoru Lisans ve Dağıtım Kapısı — İşlem 004

- **İşlem:** [islem_004.md](islem_004.md)
- **Tarih:** 2026-10-12
- **Durum:** TEKNİK TASARIM; hukukî değerlendirme ve Windows gerçek paket testi yapılmadı.

## 1. Önemli lisans kısıtı

**PyMuPDF/MuPDF**, kaynağı üreten Artifex'e göre `AGPLv3` veya ticari lisans altında sunuluyor. AGPL yükümlülüklerine uymadan onu proprietary/kapalı kaynak müşteri ürününe entegre etmek güvenli bir varsayım değildir. Açık kaynak olarak GitHub'a kod koymak da tek başına AGPL uyumunun tüm dağıtım koşullarını karşıladığını kanıtlamaz; eldeki lisans, birleşik eser ve dağıtım modelini ayrıca değerlendirmek gerekir.

**Resmî lisans kaynakları:**
- [PyMuPDF/Artifex lisans politikası](https://pymupdf.io/licensing)
- [PyMuPDF depo lisans açıklaması](https://github.com/pymupdf/PyMuPDF#licensing)

**Karar:** PDF metin motoru uygulamada **`PdfTextBackend` arayüzü** arkasında olacak. `pymupdf` örnek/AGPL-uyumlu geliştirme ortamı veya satın alınan ticari lisans yolu için teknik adaydır; ücret ve lisans gerektirmeyen, kapalı kaynaklı müşteri dağıtımı kesinleşmeden **PyMuPDF zorunlu üretim bağımlılığı yapılmayacak**.

## 2. Alternatifler

| Motor | Lisans | PDF text+render aday rolü | Açık kalite işleri |
| --- | --- | --- | --- |
| PyMuPDF | AGPLv3 **veya ticari** | Teknik baseline; rotasyon/quad güçlü | AGPL/ticari lisans uyumu ve maliyet |
| pypdfium2 / PDFium | pypdfium2 Apache-2.0/BSD-3-Clause; PDFium BSD-style + üçüncü taraf bildirimleri | Ticari, offline yerel PDF render/text adayı | Char box, span yönü/quad, PDF crop/rotate, performans |
| pdfplumber (pdfminer.six) | MIT (bileşen lisansları ayrıca kontrol) | Metin/karakter koordinatları ve tablolar | Rotasyon/çok sütun, büyük pafta performansı, layout |
| Docling | MIT ana proje; ayrı model/bağımlılık lisansları | Offline düzen/tablolar için opsiyonel ağır hazırlık aracı | CPU/RAM maliyeti, modele bağımlılık, kaynak kutuları |

Kaynaklar:
- [pypdfium2 lisans açıklaması](https://github.com/pypdfium2-team/pypdfium2#licensing)
- [pdfplumber MIT](https://pypi.org/project/pdfplumber/)
- [pdfminer.six MIT](https://github.com/pdfminer/pdfminer.six/blob/master/LICENSE)
- [Docling resmî](https://docling.ai/)

**Not:** pypdfium2'nin izin verici lisansı, PDFium içinde kullanılan bütün üçüncü taraf bileşenlerin bildirimlerinin ayrıca korunması gerekmediği anlamına gelmez.

## 3. PdfTextBackend v0 sözleşmesi

```python
class PdfTextBackend(Protocol):
    def inspect_page(self, file_path: Path, page_index: int) -> PageInfo: ...
    def extract_native_text(self, file_path: Path, page_index: int) -> list[TextCandidate]: ...
    def render_region(self, file_path: Path, page_index: int, roi: Quad, dpi: int) -> RenderedRegion: ...
```

Bu kod **yalnız tasarım örneğidir**, repo modülü değildir.

- `TextCandidate`: dört nokta, kaynak PDF sayfası, glyph/char/font/direction, metadata.
- `RenderedRegion`: image, source page hash, crop/rotation/scale transform, dpi.
- Koordinat ve bbox contract motor bağımsız tutulur; farklı motorların `origin` ve `y axis` sistemleri normalize edilir.
- Engine kullanılabilir değilse farklı backend denenebilir, ama OCR doğrudan sahte source polygon üretmez.
- PyMuPDF üzerine bağımlı `recover_quad` işlemleri yalnız o backend'de kullanılır; ortak `box_utils` motor-bağımsız matematik taşır.

## 4. Teknoloji seçim kabul kapısı

1. Ticari kapalı kaynak ve kullanıcı kendi makinesinde çalışma için lisans yükümlülüklerinin bağımsız incelenmesi.
2. Gerçek Windows 14. nesil i7/32 GB üzerinde PDF text/rotate/crop/text quality karşılaştırması.
3. Mixed SHX/TrueType, 45/90/270° metin ve kaynak highlight geometrisinin test edilmesi.
4. Resmî Gazete iki sütun, birleşik tablo hücrelerinde `document_hash/page/quad` kökeninin korunması.
5. Gerçek yeniden dağıtım bileşenleri ve üçüncü taraf NOTICE/lisans envanterinin kaydı.

**Sonuç:** “RapidOCR CPU + PDF native-first” prensibi kesin; ancak PDF'in somut kütüphanesi **lisans ve mühendislik benchmark kapısına** bağlıdır. Bu ayrım yapılmadan “PyMuPDF ile ticari paket hazır” denmeyecek.
