"""Local-only HTML/JSON/Markdown/PDF analysis reports with bidirectional anchors."""
from __future__ import annotations

from base64 import b64encode
from hashlib import sha256
from html import escape
from io import BytesIO
from pathlib import Path
import json

from mimarllm.legal.models import LegalDocument
from mimarllm.legal.verification import SourceAuditStatus, verify_local_pdf
from mimarllm.reports.models import AnalysisReport
from mimarllm.reports.visualizer import (
    html_id, source_location_label, svg_frame,
)


class ReportExportError(ValueError):
    pass


def _original_page(
    pdf_path: str | Path,
    digest: str,
    page_index: int,
    *,
    max_pixels: int = 5_000_000,
) -> tuple[tuple[float, float], str]:
    """Render a SHA-verified local original PDF page, never a guessed URL."""
    import pypdfium2 as pdfium
    from mimarllm.importers.pdf import render_region, _hash_file, _validate_path

    path = _validate_path(pdf_path, 100 * 1024 * 1024)
    if _hash_file(path) != digest:
        raise ReportExportError("Original PDF SHA256 does not match source evidence")
    try:
        with pdfium.PdfDocument(str(path)) as pdf:
            if not 0 <= page_index < len(pdf):
                raise ReportExportError("Original PDF page index not found")
            size = tuple(float(x) for x in pdf[page_index].get_size())
        region = render_region(
            path, page_index, (0.0, 0.0, *size),
            dpi=100, max_pixels=max_pixels, max_file_bytes=100 * 1024 * 1024,
        )
        if region.document_sha256 != digest or _hash_file(path) != digest:
            raise ReportExportError("Original source PDF changed during rendering")
        buf=BytesIO()
        region.image.save(buf, format="PNG")
        return size, b64encode(buf.getvalue()).decode("ascii")
    except ReportExportError:
        raise
    except Exception as exc:
        raise ReportExportError(
            f"Original PDF could not be safely rendered: {type(exc).__name__}"
        ) from exc


def _legal_sections(
    report: AnalysisReport,
    legal_documents: list[LegalDocument],
    legal_pdf_paths: dict[str, str | Path],
    *,
    max_pages: int,
) -> str:
    if not legal_pdf_paths and not legal_documents and not any(
        finding.legal_evidence is not None for finding in report.findings
    ):
        return ""
    docs = [LegalDocument.model_validate(d.model_dump()) for d in legal_documents]
    lookup = {d.document_sha256: d for d in docs}
    if len(lookup) != len(docs):
        raise ReportExportError("Duplicate legal original PDF document identity")
    images = {}
    fragments = []
    for finding in report.findings:
        link = finding.legal_evidence
        if link is None:
            continue
        key = html_id("legal", finding.finding_id)
        if link.document_sha256 not in lookup:
            # An evidence linker candidate is NOT an original inspected PDF.
            fragments.append(
                f'<section class="legal-source" id="{key}"><h3>Mevzuat kaynak adayı</h3>'
                '<p>LegalAST/orijinal PDF sağlanmadı; kaynak görseli oluşturulmadı. '
                'HUKUKI_HOLD.</p>'
                f'<p><a href="#{html_id("finding", finding.finding_id)}">Bulguyu aç</a></p></section>'
            )
            continue
        doc = lookup[link.document_sha256]
        node = next((n for n in doc.nodes if n.node_id == link.node_id), None)
        if node is None or node.spans != link.spans:
            raise ReportExportError("Legal source text/quad differs from original LegalAST")
        path = legal_pdf_paths.get(link.document_sha256)
        if path is None:
            fragments.append(
                f'<section class="legal-source" id="{key}"><h3>Mevzuat kaynak adayı</h3>'
                '<p>Orijinal mevzuat PDF yerel dosyası mevcut değil. HUKUKI_HOLD.</p>'
                f'<p><a href="#{html_id("finding", finding.finding_id)}">Bulguyu aç</a></p></section>'
            )
            continue
        audit = verify_local_pdf(doc, path)
        if audit.status != SourceAuditStatus.LOCAL_SOURCE_MATCHED:
            raise ReportExportError(
                "Legal original PDF failed SHA/page/geometry verification"
            )
        pages = {}
        for span in link.spans:
            k = (link.document_sha256, span.page_index)
            if k not in images:
                if len(images) >= max_pages:
                    raise ReportExportError("Legal original PDF render page budget exceeded")
                images[k] = _original_page(path, *k)
            width_height, img = images[k]
            width, height = width_height
            if any(not (0 <= x <= width and 0 <= y <= height)
                   for x, y in span.polygon):
                raise ReportExportError("Legal source polygon off original PDF page")
            if span.page_index not in pages:
                pages[span.page_index] = [img, width, height, []]
            pages[span.page_index][3].append(span.polygon)
        rows = []
        for page_index, (img, width, height, polygons) in sorted(pages.items()):
            overlays = "".join(
                f'<polygon points="{" ".join(f"{x:.6f},{y:.6f}" for x,y in polygon)}"/>'
                for polygon in polygons
            )
            rows.append(
                f'<p>PDF sayfası {page_index+1} (indeks {page_index}) · '
                f'SHA-256: <code>{escape(link.document_sha256)}</code></p>'
                f'<div class="pdf-stage"><img alt="Özgün mevzuat PDF sayfası" '
                f'src="data:image/png;base64,{img}"/>'
                f'<svg viewBox="0 0 {width:.6f} {height:.6f}" '
                f'preserveAspectRatio="none">{overlays}</svg></div>'
            )
        reason = ", ".join(link.reason_codes)
        fragments.append(
            f'<section class="legal-source" id="{key}">'
            '<h3>Özgün mevzuat PDF kanıt adayı — HUKUKI_HOLD</h3>'
            f'<p>Node: <code>{escape(link.node_id)}</code></p>'
            f'<p>Kaynak: {escape(link.binding_status)}. '
            f'Hukukî resmiyet/yürürlük doğrulanmadı. '
            f'Nedenler: {escape(reason)}</p>'
            f'<p>Çıkarılan metin (LegalAST): {escape(node.text)}</p>'
            + "".join(rows) +
            f'<p><a href="#{html_id("finding", finding.finding_id)}">'
            'Bu kaynağı kullanan bulguya dön</a></p></section>'
        )
    return "".join(fragments)


def render_report_html(
    report: AnalysisReport,
    *,
    drawing_pdf_path: str | Path | None = None,
    legal_documents: list[LegalDocument] | None = None,
    legal_pdf_paths: dict[str, str | Path] | None = None,
    max_pages: int = 24,
    max_html_bytes: int = 24_000_000,
) -> str:
    """Produce self-contained offline HTML with finding↔source navigation."""
    report = AnalysisReport.model_validate(report.model_dump())
    if not 1 <= max_pages <= 100 or not 100_000 <= max_html_bytes <= 100_000_000:
        raise ReportExportError("Invalid report rendering budgets")
    has_pdf_frames = any(f.coordinate_kind == "PDF_POINT"
                         for f in report.frames)
    if drawing_pdf_path is not None and (
        report.source_kind != "PDF" or not has_pdf_frames
    ):
        raise ReportExportError("Cannot use PDF page backing for non-PDF drawing")
    if legal_pdf_paths and not legal_documents:
        raise ReportExportError("Legal PDFs require independently revalidated LegalAST")

    original_pages = {}
    if drawing_pdf_path is not None:
        import pypdfium2 as pdfium
        from mimarllm.importers.pdf import _hash_file, _validate_path
        p=_validate_path(drawing_pdf_path, 100 * 1024 * 1024)
        if _hash_file(p) != report.drawing_sha256:
            raise ReportExportError("Drawing source PDF SHA256 mismatch")
        with pdfium.PdfDocument(str(p)) as pdf:
            page_count = len(pdf)
        for frame in report.frames:
            if frame.coordinate_kind == "PDF_POINT":
                if frame.page_index is None or frame.page_index >= page_count:
                    raise ReportExportError("PDF source frame points to missing page")
                if len(original_pages) >= max_pages:
                    raise ReportExportError("Drawing PDF page render budget exceeded")
                original_pages[frame.frame_id] = _original_page(
                    p, report.drawing_sha256, frame.page_index,
                )

    head = (
        '<!doctype html><html lang="tr"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>MimarLLM — kaynaklı teknik analiz raporu</title>'
        '<style>'
        'body{font:15px/1.48 system-ui,sans-serif;background:#f7f9fc;'
        'color:#1a2637;margin:auto;padding:24px;max-width:1350px}'
        'header,section{background:white;border:1px solid #dce2e9;'
        'border-radius:10px;margin-bottom:16px;padding:18px}'
        'section:target,g:target{outline:3px solid #eab308}'
        'a{color:#164a83}code{overflow-wrap:anywhere}'
        '.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(410px,1fr));gap:16px}'
        '.pdf-stage{position:relative;width:100%;border:1px solid #d3dce4}'
        '.pdf-stage img{width:100%;display:block}'
        '.pdf-stage svg{position:absolute;inset:0;width:100%;height:100%;pointer-events:none}'
        '.pdf-stage polygon{fill:rgba(250,204,21,.32);stroke:#b77900;stroke-width:1.3;'
        'vector-effect:non-scaling-stroke}'
        '.source-svg{width:100%;height:auto;max-height:640px;border:1px solid #cfd7e0}'
        '.drawing-evidence{fill:rgba(250,204,21,.18);stroke:#c17b00;stroke-width:2;'
        'vector-effect:non-scaling-stroke;cursor:pointer}'
        '.drawing-evidence:hover{stroke:#9b2c2c;stroke-width:4}'
        '.hold{font-weight:700;color:#845300}'
        '.muted{color:#526174}.candidate{font-style:italic}'
        '</style></head><body>'
    )
    intro = (
        '<header><h1>MimarLLM — kaynaklı mimari analiz raporu</h1>'
        f'<p>Çizim SHA-256: <code>{escape(report.drawing_sha256)}</code></p>'
        f'<p>Ölçek/kalibrasyon: {escape(report.calibration_state)}</p>'
        '<p class="hold">Teknik bulgular mevzuat uygunluk sertifikası değildir. '
        'Mevzuat değerlendirme kilidi: REGULATORY_LOCKED.</p>'
        '</header>'
    )
    finding_cards = []
    for f in report.findings:
        links = "".join(
            f'<a href="#{html_id("source", eid)}">{escape(eid)}</a> '
            for eid in f.entity_ids
        )
        legal = (f'<p><a href="#{html_id("legal", f.finding_id)}">'
                 'Özgün mevzuat PDF kaynak incelemesini aç</a></p>'
                 if f.legal_evidence is not None else
                 '<p class="hold">Doğrulanmış mevzuat PDF bağlantısı yok.</p>'
                 if f.kind.value == "REGULATORY_CANDIDATE" else "")
        finding_cards.append(
            f'<section id="{html_id("finding", f.finding_id)}">'
            f'<h3>{escape(f.check_id)}</h3>'
            f'<p>Tür: {escape(f.kind.value)} · durum: '
            f'<strong>{escape(f.status)}</strong> · '
            f'neden: <code>{escape(f.reason_code)}</code></p>'
            f'<p>Kaynak çizim geometrisi: {links if links else "Kaynak entity bulunmuyor"}</p>'
            f'<p>Ölçüm/diğer kanıt ID: {escape(", ".join(f.evidence_ids))}</p>'
            + legal + '</section>'
        )
    frame_cards = []
    for frame in report.frames:
        src = [s for s in report.sources if s.frame_id == frame.frame_id]
        if not src:
            continue
        view = original_pages.get(frame.frame_id)
        svg = svg_frame(
            report, frame.frame_id,
            pdf_page_size=view[0] if view else None,
            pdf_image_b64=view[1] if view else None,
        )
        source_details = "".join(
            f'<p id="{html_id("source", s.entity_id)}">'
            f'<strong>{escape(s.entity_id)}</strong>: '
            f'{escape(source_location_label(s))}. '
            + " ".join(
                f'<a href="#{html_id("finding", f.finding_id)}">'
                f'{escape(f.check_id)}</a>'
                for f in report.findings if s.entity_id in f.entity_ids
            ) + '</p>' for s in src
        )
        caveat = (
            "Gerçek orijinal PDF sayfası SHA-256 ile doğrulandı; "
            "sarı kaynak çizimi teknik kanıt katmanıdır."
            if view else (
                "DXF DrawingIR kaynak geometrisi SVG vektör gösterimidir; "
                "tam CAD baskı paftası değildir."
                if frame.coordinate_kind=="CAD_UNIT" else
                "Orijinal PDF dosyası sağlanmadı; yalnız DrawingIR kaynak "
                "geometrisi gösteriliyor. PDF sayfa görüntüsü doğrulanmadı."
            )
        )
        frame_cards.append(
            '<section><h3>Çizim kaynağı · ' + escape(frame.frame_id) + '</h3>'
            '<p class="muted">' + escape(caveat) + '</p>'
            + svg + source_details + '</section>'
        )
    legal_html = _legal_sections(
        report, legal_documents or [], legal_pdf_paths or {},
        max_pages=max_pages,
    )
    html = (head + intro + '<h2>Bulgular</h2><div class="cols">'
            + "".join(finding_cards)
            + '</div><h2>Geometrik kaynaklar</h2><div class="cols">'
            + "".join(frame_cards)
            + '</div><h2>Mevzuat kanıtı / kaynak incelemesi</h2>'
            + legal_html + '</body></html>')
    if len(html.encode("utf-8")) > max_html_bytes:
        raise ReportExportError("Offline report exceeds HTML safety budget")
    return html


def export_report(
    report: AnalysisReport,
    destination: str | Path,
    *,
    drawing_pdf_path: str | Path | None = None,
    legal_documents: list[LegalDocument] | None = None,
    legal_pdf_paths: dict[str, str | Path] | None = None,
) -> Path:
    """Explicit atomic-no-overwrite local JSON/MD/HTML/PDF export."""
    report = AnalysisReport.model_validate(report.model_dump())
    target=Path(destination).expanduser().resolve(strict=False)
    if not target.parent.is_dir():
        raise ReportExportError("Report output directory does not exist")
    suffix=target.suffix.lower()
    if suffix==".json":
        payload=report.model_dump_json(indent=2).encode("utf-8")
    elif suffix==".md":
        lines=[
            "# MimarLLM — kaynaklı mimari analiz raporu",
            "",
            f"Çizim SHA-256: `{report.drawing_sha256}`",
            f"Kalibrasyon: **{report.calibration_state}**",
            "",
            "**UYARI:** Teknik bulgular hukukî uygunluk değildir. REGULATORY_LOCKED.",
            "",
        ]
        for f in report.findings:
            lines.extend([
                f"## {f.check_id}",
                f"- Durum: {f.status} ({f.kind.value})",
                f"- Neden: {f.reason_code}",
                f"- DrawingIR entity ID: {', '.join(f.entity_ids) or 'YOK'}",
                f"- Kaynak/evidence ID: {', '.join(f.evidence_ids) or 'YOK'}",
            ])
            if f.legal_evidence:
                l=f.legal_evidence
                lines.extend([
                    "- Mevzuat kaynağı: UNREVIEWED / HUKUKI_HOLD",
                    f"- PDF SHA: {l.document_sha256}, LegalAST node: {l.node_id}",
                    f"- PDF sayfaları: {', '.join(str(s.page_index) for s in l.spans)}",
                    f"- Gerekçeler: {', '.join(l.reason_codes)}",
                ])
            lines.append("")
        payload=("\n".join(lines)+"\n").encode("utf-8")
    elif suffix==".html":
        payload=render_report_html(
            report,drawing_pdf_path=drawing_pdf_path,
            legal_documents=legal_documents,legal_pdf_paths=legal_pdf_paths,
        ).encode("utf-8")
    elif suffix==".pdf":
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.pdfgen.canvas import Canvas
        except ImportError as exc:
            raise ReportExportError("PDF report requires optional offline reportlab") from exc
        # PDF report is text-only with references. Interactive source geometry
        # navigation and page highlights are provided in the HTML export.
        font="Helvetica"
        for path in (Path("C:/Windows/Fonts/arial.ttf"),
                     Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
            if path.is_file():
                pdfmetrics.registerFont(TTFont("ReportUnicode",str(path)))
                font="ReportUnicode"
                break
        pdf_buffer=BytesIO()
        pdf=Canvas(pdf_buffer,pagesize=A4,pageCompression=1)
        pdf.setFont(font,10)
        y=A4[1]-45
        def row(txt):
            nonlocal y
            if y<55:
                pdf.showPage()
                pdf.setFont(font,10)
                y=A4[1]-45
            # Bounded single-line text; full values retained in JSON/HTML.
            pdf.drawString(40,y,txt[:108])
            y-=17
        row("MimarLLM - Teknik kaynak raporu / Hukuki HOLD")
        row("Drawing SHA: "+report.drawing_sha256)
        row("Calibration: "+report.calibration_state)
        for f in report.findings:
            row("Finding: "+f.check_id+" ["+f.status+"]")
            row("Reason: "+f.reason_code)
            for eid in f.entity_ids:
                row("CAD/PDF entity ID: "+eid)
            if f.legal_evidence:
                row("LEGAL UNREVIEWED PDF: "+f.legal_evidence.document_sha256)
                row("LegalAST node: "+f.legal_evidence.node_id)
        pdf.save()
        payload=pdf_buffer.getvalue()
    else:
        raise ReportExportError("Report export supports only .json, .md, .html, .pdf")
    # Atomic creation prevents truncated files on failed output generation.
    if target.exists():
        raise ReportExportError("Refusing to overwrite existing analysis report")
    try:
        with target.open("xb") as dst:
            dst.write(payload)
    except FileExistsError as exc:
        raise ReportExportError("Refusing to overwrite existing report") from exc
    return target
