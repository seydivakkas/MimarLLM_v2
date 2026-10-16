# İşlem 026 — Kaynaklı 2.5D / Three.js v0.1

**Durum:** MÜHENDİSLİK ADAYI, sentetik kabul sürecinde. Fiziksel testler İşlem 031'de. Hukukî kapı REGULATORY_LOCKED.

## Veri modeli ve güvenlik

- Kaynak: DrawingIR içinde SHA256 ile eşleştirilen DXF, cad:Model çerçevesindeki yalnız özgün CAD_NATIVE LINE öğeleri, 3–64 benzersiz entity kimliği; blok içi INSERT, PDF/OCR/VLM ve Z içeren segmentler kabul edilmez.
- Şekil: Her kaynak yüzeyi analyze_geometry ile snap_tolerance=0, tek ve deliksiz/geçerli polygon olacak. Dangles, overlap, kesişen veya eksik kenar, birden çok yüz, delik veya çözülemeyen kanıt sorunu varsa massing üretimi reddedilir.
- Metre: Kalibrasyon CONFIRMED olmalı, cad:Model'a bağlı bağımsız kanıt/evidence_ids bulunmalı, HEADER_UNITS tek başına reddedilmeli. Bilinmeyen ölçü 2.5D kütleye sessizce dönüştürülmez.
- Yükseklik: 0–150 m aralığında açık kullanıcı senaryosu. Gerçek bina/kat yükseklik onayı, ruhsat veya kaçış metrikleri çıkarılmaz.
- Çıktı: UNVERIFIED_MASSING_SCENARIO; kaynak dosya SHA, frame, face, entity IDs/CAD handle, kalibrasyon kanıtı, lokal metre koordinatları, matematiksel taban alanı, beyan yüksekliği, certified_building=false ve REGULATORY_LOCKED. DXF/DrawingIR/analiz/mevzuat dosyaları değişmez.

## API

POST /api/projects/{project_id}/runs/{run_id}/massing25d

JSON alanları: source_sha256 (64 küçük hex), frame_id ("cad:Model"), source_entity_ids (benzersiz kaynak kimlikleri listesi), declared_height_m (0–150 metre aralığında pozitif), reviewer_label (kullanıcı etiketi).

Yanıt 200: yalnız 2.5D önizleme adayı. Hatalar: 403 local CSRF/Origin/Host, 404 proje/run, 409 SHA/kalibrasyon/geometri, 413 >12 KB body, 422 şema ve sınır ihlali.

## Çevrimdışı Three.js

- src/mimarllm/app/static/scene25d.js yerel ./three.module.js kullanır. Gerçek THREE.Shape + THREE.ExtrudeGeometry, Y-up geometri, kaynaklı prizma, tel kenarlar, izometrik kamera, fare döndürme/zoom, klavyeden döndürme, viewport güncellemesi ve güvenli dispose.
- Runtime hiçbir CDN ya da üçüncü taraf API istemez. Three.js hazırlama sürümü **0.160.1**, gözlenmiş kaynak dosya SHA256 değeri **76dea8151bc9352aef3528b4262e249b2604f62543828328db978d060d61a495**.
- Hazırlama betiği scripts/build_three_vendor_026.mjs modülü, boyutu/SHA'sı, three-vendor-026.json envanteri ve MIT LICENSE metnini src/mimarllm/app/static içine yerel olarak kopyalar. Otomatik indirme yalnız açık npm hazırlama adımında olur; runtime indirme yok.
- Windows'ta scripts/windows/prepare_three_026.ps1 -AllowNetwork yalnız kullanıcı onaylı hazırlama; sonrasında -AllowNetwork olmadan SHA kontrolü. build_exe.bat yerel modül doğrulaması başarısızsa durur.
- Three.js kaynağı veya WebGL eksikse önizleme mümkün değil bilgisi gösterilir; 2B ve kaynak analiz akışı korunur.

## Sentetik doğrulama ve kapsam dışı

tests/test_massing25d.py: native kare, kalibrasyon, tek yüz bütçesi, farklı SHA, duplicated/open geometry, nested block, yükseklik, POST/CSRF ve özgün dosya değişmezliği. GitHub CI hem Windows hem Linux'ta Python ve Node JS/sürüm/SHA testleri yürütür. Hosted Edge yalnız local asset ve DOM smoke; gerçek GPU/VRAM/Edge kullanıcısı değildir.

Kapsam dışı: Kat/oda/kapı/çatı/cephe, gerçek bina hacmi sertifikası, tüm 3D CAD, PDF metrik türetme, VLM, yerel GGUF, pedagogik jüri ve hukukî PASS. Bunlar otomatik 2.5D sonucu olarak gösterilemez.

Gerçek Windows, A0/A1/bozuk CAD, fiziksel işlem/performans/RSS/VRAM ve bağımsız kabul: SON İŞLEM 031 / HOLD.
