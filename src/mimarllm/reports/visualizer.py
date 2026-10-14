"""Offline drawing coordinate SVG: no inferred geometry or CAD scale.

DXF is a source-entity vector witness, NOT a complete DWG/DXF print view.
PDF sources may have a real locally verified PDF page image in exporter.
"""
from __future__ import annotations

from hashlib import sha256
from html import escape
from math import isfinite

from mimarllm.core.ir import PrimitiveKind
from mimarllm.reports.models import AnalysisReport, ReportSource


def html_id(kind: str, raw: str) -> str:
    return kind + "_" + sha256(raw.encode("utf-8")).hexdigest()[:20]


def source_location_label(source: ReportSource) -> str:
    ref = source.origin_reference
    if ref.cad_handle is not None:
        return (
            f"DXF layout={ref.view_id}; CAD handle={ref.cad_handle}; "
            f"block path={'/'.join(ref.block_path) if ref.block_path else '(root)'}"
        )
    return f"PDF page_index={ref.page_index}; coordinate frame={ref.frame_id}"


def svg_frame(
    report: AnalysisReport,
    frame_id: str,
    *,
    pdf_page_size: tuple[float, float] | None = None,
    pdf_image_b64: str | None = None,
    max_points: int = 100_000,
) -> str:
    """Render EXACT source geometry, with local links back to report findings.

    PDF mode uses original PDF points (top-left origin). CAD mode only scales
    to viewBox and flips Y for display, preserving source CAD coordinates.
    """
    report = AnalysisReport.model_validate(report.model_dump())
    frame = next((f for f in report.frames if f.frame_id == frame_id), None)
    if frame is None:
        raise ValueError("Unknown report coordinate frame")
    selected = [s for s in report.sources if s.frame_id == frame_id]
    total = sum(len(s.geometry.points) for s in selected)
    if total > max_points or not 1 <= max_points <= 500_000:
        raise ValueError("SVG source vertex count exceeds limit")
    pdf_mode = frame.coordinate_kind == "PDF_POINT"
    if pdf_image_b64 is not None and (pdf_page_size is None or not pdf_mode):
        raise ValueError("Verified original page image only supported in PDF frame")
    if pdf_page_size is not None:
        w, h = pdf_page_size
        if not (isfinite(w) and isfinite(h) and 0 < w <= 30_000 and 0 < h <= 30_000):
            raise ValueError("Invalid original PDF page dimensions")
        if not pdf_mode:
            raise ValueError("PDF sizes cannot be assigned to CAD view")
        bounds = (0.0, 0.0, w, h)
    else:
        xs = [x for e in selected for x, _ in e.geometry.points]
        ys = [y for e in selected for _, y in e.geometry.points]
        if xs:
            minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
            margin = max(maxx-minx, maxy-miny, 1) * 0.06
            bounds = (
                minx-margin, miny-margin,
                max(maxx-minx + 2*margin, 1),
                max(maxy-miny + 2*margin, 1),
            )
        else:
            bounds = (0.0, 0.0, 800.0, 600.0)
    ox, oy, width, height = bounds

    def pt(x: float, y: float) -> str:
        # PDF point coordinate Y increases down; CAD Y increases up.
        display_y = y if pdf_mode else oy + height - (y - oy)
        return f"{x:.6f},{display_y:.6f}"

    # Provenance-only SVG; all clickable anchors point to validated findings.
    bits = [
        f'<svg class="source-svg" xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="{ox:.6f} {oy:.6f} {width:.6f} {height:.6f}" '
        f'role="img" aria-label="DrawingIR kaynak koordinat kanıtları">'
    ]
    if pdf_image_b64 is not None:
        # Base64 created locally from verified original PDF page, not user URL.
        bits.append(
            f'<image x="0" y="0" width="{width:.6f}" height="{height:.6f}" '
            f'href="data:image/png;base64,{pdf_image_b64}"/>'
        )
    else:
        bits.append(f'<rect x="{ox:.6f}" y="{oy:.6f}" width="{width:.6f}" '
                    f'height="{height:.6f}" fill="#f3f6fa"/>')
    match = {
        e.entity_id: f.finding_id
        for f in reversed(report.findings)
        for e in selected
        if e.entity_id in f.entity_ids
    }
    for e in selected:
        points = [pt(x, y) for x, y in e.geometry.points]
        if e.geometry.kind == PrimitiveKind.POINT:
            x,y=points[0].split(",")
            element = f'<circle cx="{x}" cy="{y}" r="3.5" fill="#d39d00"/>'
        elif e.geometry.kind == PrimitiveKind.POLYGON or e.geometry.closed:
            element = f'<polygon points="{" ".join(points)}"/>'
        else:
            element = f'<polyline points="{" ".join(points)}"/>'
        target = html_id("finding", match[e.entity_id]) if e.entity_id in match else None
        source_id = html_id("source", e.entity_id)
        bits.append(f'<g id="{source_id}" class="drawing-evidence">')
        if target is not None:
            bits.append(f'<a href="#{target}">')
        bits.append(f'<title>{escape(source_location_label(e))}</title>')
        bits.append(element)
        if target is not None:
            bits.append('</a>')
        bits.append('</g>')
    bits.append('</svg>')
    return "".join(bits)
