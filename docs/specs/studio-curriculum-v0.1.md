# İşlem 025 — Müfredat/2B Stüdyo API v0.1 (kısmi)

**Durum:** İlk kaynaklı UI dilimi / taslak PR; kapsamlı İşlem 025 kabulü **henüz bitmedi**.

## Müfredat kayıt defteri

`src/mimarllm/curriculum/registry.py`: `MOD-101..118`, `MOD-201..213`, `MOD-301..314`, `MOD-401..410`; toplam 55 **katalog adayı**, dört kümülatif görünürlük kapsamı: 18, 31, 45, 55. `introduced_grade` kullanılır. Üst sınıf modülünün erken sınıf önizlemesi kümülatif sayıya dahil edilmez.

API: `GET /api/curriculum/grades/{grade}` (1–4, JSON); kayıtlar `CATALOG_ONLY`, `grading_enabled=false`, `regulatory_approved=false`; `software_modules_accepted=0`, `legal_gate=REGULATORY_LOCKED`. Bu endpoint herhangi bir hukuki kuralı çalıştırmaz.

## Arayüz

- F19 localhost-only dashboard eski DXF/PDF yükle ve analiz butonlarını **korur**.
- Stüdyo bölümü: dört sınıf, üç panel ve kanıtlı 2B rapor. Seçilen katalog API'den okunur; salt tarayıcı sabit listesi değil.
- Kanıt sekmesi mevcut `analysis.html` raporuna yalnız aktif proje / run ID aracılığıyla gider. Kaynak dosya yolu, mevzuat, ölçüm veya jüri puanı uydurulmaz.
- 2.5D butonu disabled; sekiz boyutlu pedagojik boyutların puanı `—` gösterilir.
- Dış CDN/Three.js henüz yok; CSP ve no-`innerHTML` korunur. Resmî MÜDEK/ruhsat ön-onay iddiası yok.

## Açık geliştirme/benimseme

- F31 arka plan iş kuyruğu, bounded SSE veya polling, iptal, aynı anda bir CPU işi ve UI yönetimi.
- 2B üzerinde kaynaklı düzenleme/overlay, katman seçimi, kullanıcı inceleme kayıtlarının gerçek rapora dönüşü.
- Mevcut `geometry/repair_viewer.py` SVG işaretlerinin GUI'de salt okunur incelemesi.
- Delphi ağırlıkları, 55 modül uygulama ve değerlendirme kuralı, resmî legal kaynak onayı, gerçek Windows Edge ve 3B/GPU.
- Sentetik GitHub Actions Windows+Ubuntu CI'nin bitip kanıtlanması.

## Kabul kuralları

Bu stüdyo JSON'u bir değerlendirme sonucu/ruhsat uygunluğu üretmez. Kaynak `DrawingIR` SHA/frame ve eski `RunPayload` işlemi değiştirilmez. 2B kanıt raporunun bulunmaması fail-closed olur. İşlem 025, yukarıdaki açık iş paketleri bitene kadar **IN_PROGRESS** kalır.
