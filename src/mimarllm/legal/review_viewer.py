"""Offline visual review of REAL PDF pages with source-coordinate SVG overlays.

This is a fully self-contained local HTML inspection form, NOT an online
application or a source/legal authority attestation. User export is unsigned.
"""
from __future__ import annotations

from base64 import b64encode
from html import escape
from io import BytesIO
import json
from pathlib import Path

import pypdfium2 as pdfium

from mimarllm.importers.pdf import PdfInputError, render_region
from mimarllm.legal.models import LegalDocument
from mimarllm.legal.review import (
    ReviewInputError, ReviewQueue, ReviewSelection, build_review_queue,
    task_digest,
)
from mimarllm.legal.verification import SourceAuditStatus, verify_local_pdf
from mimarllm.legal.versions import AmendmentClaim


class VisualReviewError(ReviewInputError):
    pass


def create_visual_review_html(
    queue: ReviewQueue,
    documents: list[LegalDocument],
    original_pdf_paths: dict[str, str | Path],
    output_html: str | Path,
    *,
    amendment_claims: list[AmendmentClaim] | None = None,
    dpi: int = 100,
    max_pixels_per_page: int = 6_000_000,
    max_html_bytes: int = 24_000_000,
) -> Path:
    """Write an offline, source-audited PDF screenshot + overlay review form.

    Reconstruct tasks from original LegalAST and change claims so spoofed
    task text/quad cannot be rendered as an authentic source reference.
    Does not store decisions automatically; user exports a JSON draft.
    """
    checked = ReviewQueue.model_validate(queue.model_dump())
    if not 1 <= len(checked.tasks) <= 24 or not 72 <= dpi <= 200:
        raise VisualReviewError("Review HTML safety budget or DPI invalid")
    docs = [LegalDocument.model_validate(doc.model_dump()) for doc in documents]
    reconstructed = build_review_queue(
        docs,
        [ReviewSelection(
            document_sha256=t.document_sha256,
            kind=t.kind, reference_id=t.reference_id, span_index=t.span_index,
            row_index=t.row_index, column_index=t.column_index,
            amendment_side=t.amendment_side,
        ) for t in checked.tasks],
        amendment_claims=amendment_claims,
    )
    if reconstructed != checked:
        raise VisualReviewError("Review task text or source polygon differs from LegalAST")

    doc_map = {d.document_sha256: d for d in docs}
    if set(original_pdf_paths) != set(checked.source_documents):
        raise VisualReviewError("Supply exactly the original PDFs selected for review")
    audited_paths = {}
    for source_sha in checked.source_documents:
        audit = verify_local_pdf(doc_map[source_sha], original_pdf_paths[source_sha])
        if audit.status != SourceAuditStatus.LOCAL_SOURCE_MATCHED:
            raise VisualReviewError(
                f"Original PDF failed local SHA/page check: {audit.status.value}"
            )
        assert audit.original_pdf_path is not None
        audited_paths[source_sha] = Path(audit.original_pdf_path)

    # Render each source PDF page at most once in this export.
    images: dict[tuple[str, int], tuple[float, float, str]] = {}
    accumulated = 0
    for task in checked.tasks:
        key = (task.document_sha256, task.source.page_index)
        if key in images:
            continue
        path = audited_paths[key[0]]
        try:
            with pdfium.PdfDocument(str(path)) as pdf:
                page = pdf[key[1]]
                width, height = (float(x) for x in page.get_size())
            region = render_region(
                path, key[1], (0.0, 0.0, width, height),
                dpi=dpi, max_pixels=max_pixels_per_page,
                max_file_bytes=100 * 1024 * 1024,
            )
        except (PdfInputError, Exception) as exc:
            raise VisualReviewError(
                f"Cannot display source coordinates safely: {type(exc).__name__}"
            ) from exc
        if region.document_sha256 != key[0]:
            raise VisualReviewError("Source PDF changed during visual rendering")
        file = BytesIO()
        region.image.save(file, format="PNG")
        img = b64encode(file.getvalue()).decode("ascii")
        accumulated += len(img)
        if accumulated > max_html_bytes - 500_000:
            raise VisualReviewError("Visual page data exceeds self-contained HTML budget")
        images[key] = (width, height, img)

    items = []
    drafts = []
    for index, task in enumerate(checked.tasks, 1):
        width, height, image = images[(task.document_sha256, task.source.page_index)]
        polygon = task.source.polygon
        if any(not 0 <= x <= width or not 0 <= y <= height for x, y in polygon):
            raise VisualReviewError("Source polygon is outside displayed original page")
        # Signed area of four-point quadrilateral (PDF source coordinates).
        signed_twice = sum(
            polygon[i][0] * polygon[(i + 1) % 4][1]
            - polygon[(i + 1) % 4][0] * polygon[i][1]
            for i in range(4)
        )
        if abs(signed_twice) < 0.05:
            raise VisualReviewError("Source polygon is degenerate")
        points = " ".join(f"{x:.6f},{y:.6f}" for x, y in polygon)
        description = f"{task.kind.value} · {task.reference_id}"
        if task.amendment_side is not None:
            description += f" · {task.amendment_side.value} ({task.claimed_relation})"
        items.append(f"""<section class="card" data-task="{escape(task.task_id, quote=True)}">
<h2>{index}. {escape(description)}</h2>
<p class="provenance">PDF SHA-256: <code>{escape(task.document_sha256)}</code> ·
PDF sayfası: {task.source.page_index + 1} (dizin: {task.source.page_index}) ·
{escape(task.source.reference_type)} · {escape(task.source.extraction.value)}</p>
<p class="warning">Özgün yerel PDF eşleşti. Resmî yayımlanma, yürürlük ve hukukî onay doğrulanmadı.</p>
<div class="page-frame">
<img alt="Özgün PDF sayfa görüntüsü" src="data:image/png;base64,{image}">
<svg viewBox="0 0 {width:.6f} {height:.6f}" preserveAspectRatio="none"
     aria-label="İncelenen kanıt konumu"><polygon points="{points}"/></svg>
</div>
<p class="excerpt"><strong>Çıkarılan metin (insan doğrulaması gerekir):</strong>
{escape(task.text)}</p>
<label>Görsel inceleme sonucu
<select data-field="choice">
<option value="UNREVIEWED">İncelenmedi</option>
<option value="VISUALLY_MATCHED">Metin/konum görsel olarak eşleşiyor (beyan)</option>
<option value="CORRECTION_REQUIRED">Metin veya konum düzeltme gerektiriyor</option>
</select></label>
<label>İnceleme notu<textarea data-field="observation" rows="3"
placeholder="Metnin veya hücrenin kaynakla karşılaştırmasını yazın"></textarea></label>
</section>""")
        drafts.append({
            "task_id":task.task_id,
            "task_digest":task_digest(task),
        })
    # JSON is embedded only as text, never concatenated into executable JS.
    # Escaping '<' prevents untrusted text from ending the script element.
    raw_data = json.dumps(drafts, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    html = """<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MimarLLM - Kaynak PDF kanıt inceleme (hukukî HOLD)</title>
<style>
body{font:15px/1.5 system-ui,sans-serif;background:#f5f6fa;color:#172236;
 max-width:1320px;margin:auto;padding:20px}
h1{margin-bottom:.2rem} .warning{color:#844300;font-weight:600}
header{padding:14px 20px;background:#fff;border:1px solid #d0d8e0;
 border-radius:12px;margin-bottom:20px}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(430px,1fr));gap:20px}
.card{background:#fff;border:1px solid #cbd5e1;border-radius:12px;
 padding:18px;min-width:0}.card h2{font-size:1.1rem;overflow-wrap:anywhere}
.provenance{font-size:.84rem;overflow-wrap:anywhere}
.page-frame{position:relative;width:100%;border:1px solid #d6dbe1}
.page-frame img{width:100%;display:block}
.page-frame svg{position:absolute;inset:0;width:100%;height:100%;
 pointer-events:none}
.page-frame polygon{fill:rgba(255,216,0,.27);stroke:#edab00;stroke-width:1.3;
 vector-effect:non-scaling-stroke}
.excerpt{white-space:pre-wrap;overflow-wrap:anywhere}
label{display:block;margin:12px 0 4px}
select,textarea,input{width:100%;box-sizing:border-box;padding:10px;
 border:1px solid #9aabc0;border-radius:6px;font:inherit}
button{padding:10px 18px;background:#243959;border:0;color:#fff;
 border-radius:7px;cursor:pointer}
small{display:block;margin-top:8px}
</style></head><body>
<header><h1>Özgün PDF üzerinde kanıt inceleme</h1>
<p>Bu sayfa bilgisayarınızda çalışır; internete başvurmaz. Sarı dörtgen
 kaynak PDF'deki aday metin veya tablo hücresi konumudur. Görsel eşleşme
 sadece <strong>kullanıcının beyanıdır</strong>; resmî kaynak onayı, imza,
 hukukî yürürlük değerlendirmesi veya RuleEngine uygunluk sonucu değildir.</p>
<label>İncelemeyi yapan kişinin kullanıcı etiketi
<input id="reviewer" maxlength="120" placeholder="Örnek: yerel incelemeci"></label>
<button id="export" type="button">İnceleme kararlarını JSON olarak dışa aktar</button>
<small>Dışa aktarım taslaktır. Dosyayı tekrar kaynak manifestine karşı kontrol
 eden yerel Python review_ledger akışına iletin; imzalanmış belge değildir.</small>
</header><main>"""
    html += "\n".join(items)
    html += """</main><script type="application/json" id="manifest">""" + raw_data + """</script>
<script>
"use strict";
const manifest=JSON.parse(document.getElementById("manifest").textContent);
document.getElementById("export").addEventListener("click",()=>{
 const reviewer=document.getElementById("reviewer").value.trim();
 if(!reviewer){alert("İncelemeci etiketi zorunlu");return;}
 const cards=Array.from(document.querySelectorAll("section[data-task]"));
 const decisions=[];
 for(let i=0;i<cards.length;i++){
  const card=cards[i],choice=card.querySelector('select[data-field="choice"]').value;
  const observation=card.querySelector('textarea[data-field="observation"]').value.trim();
  if(choice==="UNREVIEWED")continue;
  if(!observation){alert("Karar verilen her kanıt için açıklama gerekiyor");return;}
  decisions.push({task_id:manifest[i].task_id,task_digest:manifest[i].task_digest,
   choice,reviewer_label:reviewer,observation,reviewed_at:new Date().toISOString(),
   legal_approval:false,authentic_identity_verified:false});
 }
 if(decisions.length===0){alert("Önce en az bir kanıt için karar girin");return;}
 const blob=new Blob([JSON.stringify(decisions,null,2)],{type:"application/json"});
 const url=URL.createObjectURL(blob),link=document.createElement("a");
 link.href=url;link.download="mimarllm_gorsel_inceleme_taslak.json";
 document.body.appendChild(link);link.click();link.remove();URL.revokeObjectURL(url);
});
</script></body></html>"""
    encoded = html.encode("utf-8")
    if len(encoded) > max_html_bytes:
        raise VisualReviewError("Self-contained review HTML exceeds byte budget")
    output = Path(output_html).expanduser().resolve(strict=False)
    if output.suffix.lower() != ".html" or not output.parent.is_dir():
        raise VisualReviewError("Export needs a new .html path in an existing directory")
    try:
        with output.open("xb") as file:
            file.write(encoded)
    except FileExistsError as exc:
        raise VisualReviewError("Refusing to overwrite a previous review report") from exc
    return output
