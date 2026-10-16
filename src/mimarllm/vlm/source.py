"""Only independently selected native DrawingIR segments are rendered as VLM input.

This PNG is an explicitly source-derived linework *preview*, not a photograph,
not a calibrated floor plan, and never evidence of walls/doors or compliance.
"""
from __future__ import annotations

from io import BytesIO
from math import isfinite

from PIL import Image, ImageDraw

from mimarllm.core.ir import DrawingIR, EvidenceOrigin, PrimitiveKind
from mimarllm.vlm.models import VlmFailure, VlmRequest


def selected_line_preview(drawing: DrawingIR, request: VlmRequest) -> bytes:
    if drawing.source_sha256 != request.source_sha256:
        raise VlmFailure("VLM_SOURCE_SHA_MISMATCH")
    frames = {frame.frame_id for frame in drawing.frames}
    if request.frame_id not in frames:
        raise VlmFailure("VLM_UNKNOWN_SOURCE_FRAME")
    by_id = {entity.entity_id: entity for entity in drawing.entities}
    strokes: list[tuple[tuple[float, float], tuple[float, float]]] = []
    for eid in request.entity_ids:
        e = by_id.get(eid)
        if (e is None or e.frame_id != request.frame_id or
                e.source.frame_id != request.frame_id or
                e.source.document_sha256 != drawing.source_sha256 or
                e.origin not in {EvidenceOrigin.CAD_NATIVE, EvidenceOrigin.PDF_NATIVE} or
                e.type_candidate not in {"LINE", "PDF_LINE"} or
                e.geometry.kind != PrimitiveKind.SEGMENT or
                len(e.geometry.points) != 2 or
                not all(isfinite(v) and abs(v) <= 1e8
                        for p in e.geometry.points for v in p)):
            raise VlmFailure("VLM_SELECTION_NOT_NATIVE")
        strokes.append((e.geometry.points[0], e.geometry.points[1]))
    xs = [p[0] for a, b in strokes for p in (a, b)]
    ys = [p[1] for a, b in strokes for p in (a, b)]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    span = max(hi_x-lo_x, hi_y-lo_y)
    if not isfinite(span) or span <= 1e-8:
        raise VlmFailure("VLM_DEGENERATE_PREVIEW")
    scale = min(448/(hi_x-lo_x) if hi_x>lo_x else 1e20,
                448/(hi_y-lo_y) if hi_y>lo_y else 1e20)
    if not isfinite(scale) or scale <= 0:
        raise VlmFailure("VLM_PREVIEW_SCALE_INVALID")
    # Source CAD Y is up; PDF page coordinates are normally down. In both
    # cases the raster is labeled as uncalibrated visual linework only.
    flip_y = drawing.source_kind.value == "DXF"
    def pos(p):
        y = hi_y-p[1] if flip_y else p[1]-lo_y
        return (round(32+(p[0]-lo_x)*scale, 2), round(32+y*scale, 2))
    canvas=Image.new("RGB",(512,512),(255,255,255))
    draw=ImageDraw.Draw(canvas)
    for a,b in strokes:
        draw.line((pos(a),pos(b)),fill=(37,72,101),width=3)
    out=BytesIO()
    canvas.save(out,format="PNG",optimize=True)
    png=out.getvalue()
    if len(png)>350_000:
        raise VlmFailure("VLM_PREVIEW_BYTES_EXCEEDED")
    return png
