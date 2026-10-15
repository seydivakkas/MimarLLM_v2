"""Safe read-only SVG comparison: exact source CAD lines vs dashed virtual proposals.

SVG is a source-unit REVIEW overlay, not an adopted CAD repair or a PDF plot.
"""
from __future__ import annotations

from html import escape
from math import isfinite

from mimarllm.core.ir import DrawingIR, EvidenceOrigin, PrimitiveKind
from mimarllm.geometry.repair import RepairOverlay, RepairInputError


def render_repair_overlay_svg(
    drawing: DrawingIR,
    overlay: RepairOverlay,
    *,
    max_vertices: int = 50_000,
) -> str:
    drawing = DrawingIR.model_validate(drawing.model_dump())
    overlay = RepairOverlay.model_validate(overlay.model_dump())
    if overlay.source_sha256 != drawing.source_sha256:
        raise RepairInputError("Repair SVG source SHA differs from original CAD")
    frame = next((f for f in drawing.frames if f.frame_id == overlay.frame_id), None)
    if frame is None or frame.kind.value != "CAD_UNIT":
        raise RepairInputError("Repair overlay references an unavailable CAD frame")
    native = [
        e for e in drawing.entities
        if e.frame_id == frame.frame_id
        and e.origin == EvidenceOrigin.CAD_NATIVE
        and e.geometry.kind in {
            PrimitiveKind.SEGMENT, PrimitiveKind.POLYLINE, PrimitiveKind.POLYGON
        }
    ]
    by_id = {e.entity_id: e for e in native}
    for c in overlay.candidates:
        for eid, ref in zip(c.source_entity_ids, c.source_references):
            if eid not in by_id or by_id[eid].source != ref:
                raise RepairInputError("Repair SVG candidate mismatches original CAD handle")
    for item in overlay.layer0_candidates:
        if item.entity_id not in by_id or by_id[item.entity_id].source != item.source:
            raise RepairInputError("Layer0 evidence no longer matches source CAD")
    all_geom = [e.geometry for e in native]
    all_geom += [
        c.proposed_geometry for c in overlay.candidates
        if c.proposed_geometry is not None
    ]
    total = sum(len(g.points) for g in all_geom)
    if not 1 <= max_vertices <= 500_000 or total > max_vertices:
        raise RepairInputError("Repair SVG vertex render budget exceeded")
    coords = [p for g in all_geom for p in g.points]
    if not coords:
        return (
            '<svg xmlns="http://www.w3.org/2000/svg" width="700" height="200" '
            'viewBox="0 0 700 200" role="img" aria-label="No native CAD geometry">'
            '<text x="20" y="45">No original CAD line geometry</text></svg>'
        )
    xs,ys=zip(*coords)
    xmin,xmax,ymin,ymax = min(xs),max(xs),min(ys),max(ys)
    margin=max(xmax-xmin,ymax-ymin,1)*.06
    ox,oy=xmin-margin,ymin-margin
    w,h=max(xmax-xmin+2*margin,1),max(ymax-ymin+2*margin,1)
    if not all(isfinite(x) and abs(x)<1e12 for x in (ox,oy,w,h)):
        raise RepairInputError("CAD viewBox outside bounded source coordinates")

    def transform(points):
        return " ".join(
            f"{x:.6f},{(oy+h-(y-oy)):.6f}" for x,y in points
        )
    parts=[
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="Source CAD in dark blue; VIRTUAL repair candidates dashed amber" '
        f'viewBox="{ox:.6f} {oy:.6f} {w:.6f} {h:.6f}" '
        'preserveAspectRatio="xMidYMid meet">',
        f'<rect x="{ox:.6f}" y="{oy:.6f}" width="{w:.6f}" height="{h:.6f}" fill="#f8fafc"/>',
    ]
    for entity in native:
        pts=list(entity.geometry.points)
        if entity.geometry.closed and len(pts)>2 and pts[0]!=pts[-1]:
            pts.append(pts[0])
        if len(pts)<2:
            continue
        label=(
            f"ORIGINAL CAD | entity={entity.entity_id} "
            f"handle={entity.source.cad_handle} "
            f"block_path={'/'.join(entity.source.block_path)} "
            f"layer={entity.layer}"
        )
        parts.append(
            f'<polyline points="{transform(pts)}" '
            'fill="none" stroke="#233d6b" stroke-width="1.8" '
            'vector-effect="non-scaling-stroke">'
            f'<title>{escape(label)}</title></polyline>'
        )
    for c in overlay.candidates:
        if c.proposed_geometry is None:
            continue
        label=(
            f"VIRTUAL CANDIDATE - NOT ACCEPTED | {c.kind.value} | "
            f"source IDs={','.join(c.source_entity_ids)} | "
            "may be intentional opening, review required"
        )
        parts.append(
            f'<polyline points="{transform(c.proposed_geometry.points)}" '
            'fill="none" stroke="#d97706" stroke-width="3" '
            'stroke-dasharray="5,4" vector-effect="non-scaling-stroke">'
            f'<title>{escape(label)}</title></polyline>'
        )
    parts.append('</svg>')
    return "".join(parts)
