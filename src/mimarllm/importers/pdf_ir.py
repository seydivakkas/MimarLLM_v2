"""PDF native geometries + explicitly requested CPU OCR -> source-aware DrawingIR.

Uses ONLY pdfplumber for native content, pypdfium2 for ROI, and an
injected RapidOCR-CPU-compatible engine. No OCR/model download is implicit.
Native glyph bboxes are NOT claimed to be true rotated glyph quadrilaterals.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256
from math import isfinite
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from mimarllm.core.ir import (
    CoordinateFrame, CoordinateKind, DrawingEntity, DrawingIR, EvidenceOrigin,
    GeometryPrimitive, PrimitiveKind, SourceKind, SourceReference, YDirection,
)
from mimarllm.core.models import TextCandidate
from mimarllm.importers.pdf import PdfInputError, RenderedRegion, inspect_pdf, render_region
from mimarllm.ocr.tiles import TiledOcrRequest, TiledOcrOutput, read_tiled_ocr
from mimarllm.ocr.layout import LayoutCandidate, detect_layout_candidates

Quad = tuple[tuple[float, float], tuple[float, float],
             tuple[float, float], tuple[float, float]]


class OcrReader(Protocol):
    def read(self, region: RenderedRegion) -> list[TextCandidate]: ...


class PdfIrIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str
    page_index: int = Field(ge=0)
    source_id: str | None = None
    detail: str


class PdfIrResult(BaseModel):
    drawing: DrawingIR
    text_candidates: list[TextCandidate] = Field(default_factory=list)
    issues: list[PdfIrIssue] = Field(default_factory=list)
    tiled_ocr_results: list[TiledOcrOutput] = Field(default_factory=list)
    layout_candidates: list[LayoutCandidate] = Field(default_factory=list)


def _bbox_quad(box: tuple[float, float, float, float]) -> Quad:
    x0, y0, x1, y1 = box
    if not (all(isfinite(v) for v in box) and x0 <= x1 and y0 <= y1):
        raise ValueError("Invalid PDF source bounding box")
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def _safe_points(raw: object) -> tuple[tuple[float, float], ...]:
    out = tuple((float(p[0]), float(p[1])) for p in raw)  # type: ignore[union-attr,index]
    if not all(isfinite(v) for p in out for v in p):
        raise ValueError("Nonfinite PDF geometry")
    return out


def _bezier_points(path: object, *, segments: int = 16, max_points: int = 4096):
    """Flatten pdfplumber's m/l/c/h page-space path; approximations are flagged."""
    points: list[tuple[float, float]] = []
    cursor: tuple[float, float] | None = None
    beginning: tuple[float, float] | None = None
    closed = False
    for command in path:  # type: ignore[union-attr]
        operator, *params = command
        if operator == "m" and len(params) == 1:
            if points:
                raise ValueError("Multiple curve subpaths not supported")
            cursor = _safe_points([params[0]])[0]
            beginning = cursor
            points.append(cursor)
        elif operator == "l" and len(params) == 1 and cursor is not None:
            cursor = _safe_points([params[0]])[0]
            points.append(cursor)
        elif operator == "c" and len(params) == 3 and cursor is not None:
            c1, c2, end = _safe_points(params)
            p0 = cursor
            for k in range(1, segments + 1):
                t = k / segments
                u = 1.0 - t
                x = (u**3*p0[0] + 3*u*u*t*c1[0] +
                     3*u*t*t*c2[0] + t**3*end[0])
                y = (u**3*p0[1] + 3*u*u*t*c1[1] +
                     3*u*t*t*c2[1] + t**3*end[1])
                points.append((x, y))
            cursor = end
        elif operator == "h" and not params and beginning is not None:
            closed = True
        else:
            raise ValueError("Unsupported PDF curve operator")
        if len(points) > max_points:
            raise ValueError("PDF curve point budget exceeded")
    if len(points) > 1 and points[0] == points[-1]:
        points.pop()
    if len(points) < (3 if closed else 2):
        raise ValueError("PDF curve is too short")
    return tuple(points), closed


def _sha256(path: Path) -> str:
    hasher = sha256()
    with path.open("rb") as reader:
        for chunk in iter(lambda: reader.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def parse_pdf_ir(
    path: str | Path, *,
    ocr_regions: Mapping[int, Sequence[tuple[float, float, float, float]]] | None = None,
    ocr_engine: OcrReader | None = None,
    tiled_ocr: Sequence[TiledOcrRequest] = (),
    dpi: int = 144,
    max_pages: int = 50,
    max_elements_per_page: int = 100_000,
    max_ocr_regions: int = 64,
    max_curve_points: int = 4096,
) -> PdfIrResult:
    """Return validated DrawingIR and text candidates with original PDF source.

    OCR is ONLY executed for explicitly provided ROIs and an injected reader.
    A native selectable title block does not mask missing SHX/raster text.
    Native point positions are PDF media-page display coordinates (top-left).
    """
    import pdfplumber

    base = inspect_pdf(path, max_pages=max_pages,
                       max_elements_per_page=max_elements_per_page)
    source_path = Path(path).resolve(strict=True)
    wanted = ocr_regions or {}
    tiled_requests = tuple(TiledOcrRequest.model_validate(t.model_dump()) for t in tiled_ocr)
    if len(tiled_requests) > 8 or len({
        (t.page_index, t.roi_points) for t in tiled_requests
    }) != len(tiled_requests):
        raise PdfInputError("Tiled OCR request count/duplicate safety budget exceeded")
    if any(t.page_index >= base.page_count for t in tiled_requests):
        raise PdfInputError("Tiled OCR selection references an unavailable page")
    if sum(t.max_tiles for t in tiled_requests) > 256:
        raise PdfInputError("Tiled OCR combined tile budget exceeded")
    if any((not isinstance(index, int) or index < 0 or index >= base.page_count)
           for index in wanted):
        raise PdfInputError("OCR regions reference an unavailable page")
    if sum(len(v) for v in wanted.values()) > max_ocr_regions:
        raise PdfInputError("OCR region budget exceeded")
    if (wanted or tiled_requests) and ocr_engine is None:
        from mimarllm.ocr.rapid_engine import OcrUnavailable
        raise OcrUnavailable("OCR ROIs require an explicitly installed local CPU OCR reader")
    if max_curve_points < 4:
        raise PdfInputError("max_curve_points is below the safe minimum")

    drawing = DrawingIR(
        drawing_id=f"pdf-{base.document_sha256[:16]}",
        source_sha256=base.document_sha256, source_kind=SourceKind.PDF,
        parser_version="pdfplumber-pypdfium2-ir-v0.1",
        frames=[
            CoordinateFrame(frame_id=f"pdf:page{p.page_index}",
                            kind=CoordinateKind.PDF_POINT, y_direction=YDirection.DOWN,
                            page_index=p.page_index)
            for p in base.pages
        ],
    )
    result = PdfIrResult(drawing=drawing)

    def emit(page_idx: int, suffix: str, polygon: Quad,
             geometry: GeometryPrimitive, origin: EvidenceOrigin, kind: str) -> None:
        frame_id = f"pdf:page{page_idx}"
        result.drawing.entities.append(DrawingEntity(
            entity_id=f"pdf:p{page_idx}:{suffix}", frame_id=frame_id,
            source=SourceReference(
                document_sha256=base.document_sha256,
                source_kind=SourceKind.PDF,
                frame_id=frame_id, page_index=page_idx,
                source_polygon=polygon,
            ),
            geometry=geometry,
            origin=origin, type_candidate=kind,
            is_verified_semantics=False,
        ))

    # Native textual candidates keep the complete text matrix and original bbox.
    for page in base.pages:
        for native in page.text:
            quad = tuple(tuple(point) for point in native.polygon)
            result.text_candidates.append(native)
            emit(page.page_index, f"char:{native.candidate_id}", quad,
                 GeometryPrimitive(kind=PrimitiveKind.POINT,
                                   points=(((quad[0][0]+quad[2][0])/2,
                                            (quad[0][1]+quad[2][1])/2),)),
                 EvidenceOrigin.PDF_NATIVE, "PDF_NATIVE_GLYPH_BBOX")

    # Native vector LINE has real endpoints; RECT has corners; CURVE requires
    # cubic flattening and is explicitly marked as approximate.
    with pdfplumber.open(source_path) as doc:
        for idx, page in enumerate(doc.pages):
            if idx >= len(base.pages):
                raise PdfInputError("PDF changed during analysis")
            for kind, items in (("line", page.lines), ("rect", page.rects),
                                ("curve", page.curves)):
                for item_index, obj in enumerate(items):
                    suffix = f"{kind}:{item_index}"
                    try:
                        bounds = (float(obj["x0"]), float(obj["top"]),
                                  float(obj["x1"]), float(obj["bottom"]))
                        bbox = _bbox_quad(bounds)
                        if kind == "line":
                            points = _safe_points(obj["pts"])
                            if len(points) != 2:
                                raise ValueError("PDF line lacks two true endpoints")
                            primitive = GeometryPrimitive(kind=PrimitiveKind.SEGMENT,
                                                          points=points)
                        elif kind == "rect":
                            points = _safe_points(obj["pts"])
                            if len(points) != 4:
                                raise ValueError("PDF rect lacks true corners")
                            primitive = GeometryPrimitive(kind=PrimitiveKind.POLYGON,
                                                          points=points, closed=True)
                        else:
                            points, closed = _bezier_points(
                                obj["path"], max_points=max_curve_points)
                            primitive = GeometryPrimitive(
                                kind=PrimitiveKind.POLYGON if closed else PrimitiveKind.POLYLINE,
                                points=points, closed=closed,
                            )
                            result.issues.append(PdfIrIssue(
                                code="APPROXIMATED_PDF_CURVE", page_index=idx,
                                source_id=suffix,
                                detail="Bezier curve flattened to 16 segments per cubic",
                            ))
                        emit(idx, suffix, bbox, primitive,
                             EvidenceOrigin.PDF_NATIVE, f"PDF_{kind.upper()}")
                    except (ValueError, TypeError, KeyError, IndexError) as error:
                        result.issues.append(PdfIrIssue(
                            code="UNRESOLVED_PDF_VECTOR", page_index=idx,
                            source_id=suffix, detail=f"{type(error).__name__}: {error}"[:180],
                        ))

    # User-selected missing/raster regions: CPU OCR, no model startup or
    # downloads without an explicit reader provided by the caller.
    for page_idx, rois in sorted(wanted.items()):
        for roi_idx, roi in enumerate(rois):
            region = render_region(source_path, page_idx, roi, dpi=dpi)
            if region.document_sha256 != base.document_sha256:
                raise PdfInputError("PDF modified between native scan and ROI render")
            assert ocr_engine is not None
            for token_idx, candidate in enumerate(ocr_engine.read(region)):
                if candidate.method != "rapidocr_cpu" or candidate.page_index != page_idx:
                    raise PdfInputError("OCR reader returned inconsistent method or page")
                quad = tuple(tuple(p) for p in candidate.polygon)
                # Validate finite ROI point positions, not misleading off-page
                # or wrong-source highlight geometry.
                if (len(quad) != 4 or not all(
                    isfinite(v) for p in quad for v in p
                ) or any(
                    not (roi[0]-1 <= p[0] <= roi[2]+1 and roi[1]-1 <= p[1] <= roi[3]+1)
                    for p in quad
                )):
                    raise PdfInputError("OCR polygon outside its original PDF ROI")
                unique = candidate.model_copy(update={
                    "candidate_id": f"p{page_idx}-roi{roi_idx}-t{token_idx}",
                    "review_required": True,
                })
                result.text_candidates.append(unique)
                emit(page_idx, f"ocr:roi{roi_idx}:token{token_idx}", quad,
                     GeometryPrimitive(kind=PrimitiveKind.POLYGON, points=quad,
                                       closed=True),
                     EvidenceOrigin.OCR_CANDIDATE, "PDF_OCR_TEXT_QUAD")

    # Tiled OCR retains the *original* source page quad. OCR does not become
    # a native wall, scale, room or verified legal/architectural symbol.
    for request_index, tile_request in enumerate(tiled_requests):
        assert ocr_engine is not None
        batch = read_tiled_ocr(source_path, tile_request, ocr_engine)
        if batch.document_sha256 != base.document_sha256:
            raise PdfInputError("Tiled OCR source SHA differs from native PDF")
        result.tiled_ocr_results.append(batch)
        page_idx = tile_request.page_index
        for token_index, candidate in enumerate(batch.candidates):
            # Ensure globally unique IDs even if the same page is explicitly
            # selected for different ROIs.
            unique = candidate.model_copy(update={
                "candidate_id":f"p{page_idx}-tiled{request_index}-t{token_index}"
            })
            result.text_candidates.append(unique)
            quad = tuple(tuple(pt) for pt in unique.polygon)
            emit(page_idx, f"ocr:tiled{request_index}:token{token_index}",
                 quad, GeometryPrimitive(kind=PrimitiveKind.POLYGON,
                                         points=quad, closed=True),
                 EvidenceOrigin.OCR_CANDIDATE, "PDF_OCR_TEXT_QUAD")
        if batch.removed_duplicate_count:
            result.issues.append(PdfIrIssue(
                code="TILED_OCR_OVERLAP_DEDUP_REVIEW_REQUIRED",
                page_index=page_idx,
                detail=f"{batch.removed_duplicate_count} duplicate overlap candidates hidden",
            ))
    # Layout locations are only candidate zones. A lower-right text cluster
    # cannot certify actual title-block fields or drawing metadata.
    for page in base.pages:
        result.layout_candidates.extend(detect_layout_candidates(
            base.document_sha256, page.page_index, page.width_pt, page.height_pt,
            [t for t in result.text_candidates if t.page_index == page.page_index],
        ))
    if _sha256(source_path) != base.document_sha256:
        raise PdfInputError("PDF source changed during integration")
    result.drawing = DrawingIR.model_validate(result.drawing.model_dump())
    return result
