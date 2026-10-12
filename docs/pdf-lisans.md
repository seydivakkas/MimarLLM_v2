# PDF/OCR Bileşenleri — Lisans ve Yeniden Dağıtım Envanteri

- **İşlem:** [islem_005.md](islem_005.md)
- **ADR:** [ADR-002](adr/ADR-002-PDF-Engine-License.md)
- **Durum:** Seçilen ana bileşenlerin lisans tipi biliniyor; **transitif Windows wheel/SBOM/yeniden dağıtım son kabulü HOLD**.

## Kesin teknoloji yığını

| Rol | Bileşen | Proje üst lisansı | Önemli koşul |
| --- | --- | --- | --- |
| PDF karakter/vektör/geometri | [pdfplumber](https://github.com/jsvine/pdfplumber) | MIT | Atıf ve lisans bildirimi |
| PDF raster/ROI görüntüleme | [pypdfium2](https://github.com/pypdfium2-team/pypdfium2) | Apache-2.0 veya BSD-3-Clause | PDFium'un ve build'in `BUILD_LICENSES` bildirimleri |
| OCR | [RapidOCR](https://github.com/RapidAI/RapidOCR) | Apache-2.0 | Seçilen ONNX ağırlıklarının ek lisans koşulları |
| CPU inference | [ONNX Runtime](https://github.com/microsoft/onnxruntime) | MIT | Wheel ve sistem çalışma zamanı/NOTICE |
| PDF karakter arka ucu | pdfminer.six | MIT | Dağıtımda lisans bildirimi |
| Resim işleme | Pillow | HPND | Bağımlılıklarla birlikte lisans/NOTICE |
| Tipli sözleşme | Pydantic | MIT | Lisans bildirimi |

Üst düzey izinli lisanslar **sıfır yükümlülük** anlamına gelmez. Kullanılan tam sürümlerin transitif bağımlılıkları, PDFium binary lisansı, model ağırlıkları, codec/runtime bileşenleri ve paketleme şekli doğrulanacak.

## Dağıtım kabul kapıları

1. `pip freeze` + `pipdeptree` / CycloneDX SBOM ve gerçek Windows wheel envanteri.
2. Her binary ve model için `LICENSE`, `NOTICE`, redistribution permission.
3. Tarafımıza ait örnek çizimlerin/mimari projelerin kullanım ve telif hakları.
4. Public GitHub'a lisanslı standart/metin/müşteri paftası koymama.
5. Offline Windows paketinde modelin veya kütüphanenin çalışma anında haricî bir web kaynağına bağlanmaması.
6. Nihai dağıtım biçimine göre bağımsız hukukî inceleme.

**Güncel hüküm:** Seçilen üç motor kesin. Bu dosya hukukî engellerin tamamen kalktığına ilişkin bir garanti değildir.
