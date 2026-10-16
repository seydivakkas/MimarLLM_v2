"""Bounded, opt-in tiled OCR using source-accurate PDF page-point coordinates.

Native PDF glyphs and drawing geometry are not modified. OCR is always a
review candidate; no auto calibration, room semantics or legal decision.
"""
from __future__ import annotations

from math import ceil, isfinite
from pathlib import Path
from typing import Literal
import unicodedata

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mimarllm.core.models import TextCandidate
from mimarllm.importers.pdf import (
    PdfInputError, _hash_file, _validate_path, render_region,
)


class TiledOcrRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    page_index: int = Field(ge=0)
    roi_points: tuple[float, float, float, float]
    tile_width_pt: float = Field(default=384, ge=32, le=900, allow_inf_nan=False)
    tile_height_pt: float = Field(default=384, ge=32, le=900, allow_inf_nan=False)
    overlap_pt: float = Field(default=32, ge=0, le=200, allow_inf_nan=False)
    dpi: int = Field(default=144, ge=72, le=240)
    max_tiles: int = Field(default=128, ge=1, le=256)
    max_pixels_per_tile: int = Field(default=4_000_000, ge=50_000, le=8_000_000)
    max_total_pixels: int = Field(default=60_000_000, ge=50_000, le=120_000_000)
    max_ocr_candidates: int = Field(default=3000, ge=1, le=10_000)

    @model_validator(mode="after")
    def validate_window(self):
        x0, y0, x1, y1 = self.roi_points
        if not all(isfinite(x) for x in self.roi_points) or not (x0 >= 0 and y0 >= 0 and x1 > x0 and y1 > y0):
            raise ValueError("Tiled ROI must be a nonempty finite PDF-point rectangle")
        if self.overlap_pt >= min(self.tile_width_pt, self.tile_height_pt) / 2:
            raise ValueError("Tiled overlap must be smaller than half the tile side")
        return self


class OcrTile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    tile_id: str
    page_index: int = Field(ge=0)
    roi_points: tuple[float, float, float, float]
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    rotation_degrees: int


class TiledOcrOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    page_index: int
    tiles: tuple[OcrTile, ...]
    candidates: tuple[TextCandidate, ...]
    candidate_tile_ids: tuple[str, ...]
    removed_duplicate_count: int = Field(ge=0)
    approval_status: Literal["REVIEW_REQUIRED"] = "REVIEW_REQUIRED"

    @model_validator(mode="after")
    def check(self):
        if len(self.candidates) != len(self.candidate_tile_ids):
            raise ValueError("Each tiled OCR candidate must have an original tile")
        ids = {tile.tile_id for tile in self.tiles}
        if (len(ids) != len(self.tiles) or
            any(t.document_sha256 != self.document_sha256
                or t.page_index != self.page_index for t in self.tiles)):
            raise ValueError("Tiled OCR source SHA/page identity mismatch")
        if any(tid not in ids for tid in self.candidate_tile_ids):
            raise ValueError("OCR tile reference not in source page plan")
        if any(c.page_index != self.page_index or not c.review_required
               or c.method != "rapidocr_cpu" for c in self.candidates):
            raise ValueError("Tiled text must be unverified page-local CPU OCR")
        return self


def _tile_starts(low: float, high: float, width: float, overlap: float) -> list[float]:
    """Deterministic coverage without tail microtiles or unbounded while loops."""
    length = high - low
    if length <= width:
        return [low]
    count = int(ceil((length - width) / (width - overlap))) + 1
    return [low + i * (length - width) / (count - 1) for i in range(count)]


def plan_ocr_tiles(
    pdf_path: str | Path, request: TiledOcrRequest, *,
    max_file_bytes: int = 50 * 1024 * 1024,
) -> tuple[OcrTile, ...]:
    """Preflight all page/tile/pixel counts BEFORE rendering any bitmap."""
    import pypdfium2 as pdfium

    request = TiledOcrRequest.model_validate(request.model_dump())
    path = _validate_path(pdf_path, max_file_bytes)
    digest = _hash_file(path)
    try:
        with pdfium.PdfDocument(str(path)) as pdf:
            if not 0 <= request.page_index < len(pdf):
                raise PdfInputError("Tiled OCR page index does not exist")
            page = pdf[request.page_index]
            size = tuple(float(x) for x in page.get_size())
            rotation = int(page.get_rotation())
            media = page.get_mediabox()
            crop = page.get_cropbox()
    except PdfInputError:
        raise
    except Exception as exc:
        raise PdfInputError("Tiled PDF page metadata is not inspectable") from exc
    if rotation not in (0, 90, 180, 270):
        raise PdfInputError("Unsupported PDF rotation for tiled OCR")
    if any(abs(float(a)-float(b)) > 1e-6 for a,b in zip(media,crop)):
        raise PdfInputError("Nondefault CropBox cannot be tiled with known coordinates")
    width,height = size
    x0,y0,x1,y1 = request.roi_points
    if (not all(isfinite(z) for z in size) or width<=0 or height<=0
            or x1 > width or y1 > height):
        raise PdfInputError("Tiled OCR region exceeds finite displayed source page")
    scale = request.dpi/72.0
    def count_tiles(length:float, tile_width:float) -> int:
        if length <= tile_width:
            return 1
        return ceil((length-tile_width)/(tile_width-request.overlap_pt))+1
    # Preflight the integer grid count BEFORE allocating a possibly huge list.
    nx = count_tiles(x1-x0, request.tile_width_pt)
    ny = count_tiles(y1-y0, request.tile_height_pt)
    if nx*ny > request.max_tiles:
        raise PdfInputError("Tiled OCR tile count safety budget exceeded")
    xs = _tile_starts(x0,x1,request.tile_width_pt,request.overlap_pt)
    ys = _tile_starts(y0,y1,request.tile_height_pt,request.overlap_pt)
    if rotation:
        # Existing PDFium ROI path uses a bounded full-page render on rotated
        # source pages. Preflight it; never secretly rasterize A0 at full DPI.
        if ceil(width*scale)*ceil(height*scale) > request.max_pixels_per_tile:
            raise PdfInputError("Rotated large page needs verified local tile transform")
    output = []
    total_pixels = 0
    for j,y in enumerate(ys):
        for i,x in enumerate(xs):
            roi = (x,y,min(x+request.tile_width_pt,x1),min(y+request.tile_height_pt,y1))
            pixels = ceil((roi[2]-roi[0])*scale) * ceil((roi[3]-roi[1])*scale)
            if pixels > request.max_pixels_per_tile:
                raise PdfInputError("Tiled OCR single tile pixel budget exceeded")
            total_pixels += pixels
            if total_pixels > request.max_total_pixels:
                raise PdfInputError("Tiled OCR cumulative pixel budget exceeded")
            output.append(OcrTile(
                tile_id=f"p{request.page_index}:tile{j:03d}_{i:03d}",
                page_index=request.page_index, roi_points=roi,
                document_sha256=digest, rotation_degrees=rotation,
            ))
    if _hash_file(path) != digest:
        raise PdfInputError("PDF source changed during OCR tile planning")
    return tuple(output)


def _bbox(c: TextCandidate) -> tuple[float,float,float,float]:
    xs = [p[0] for p in c.polygon]
    ys = [p[1] for p in c.polygon]
    return min(xs), min(ys), max(xs), max(ys)


def _iou(a: TextCandidate, b: TextCandidate) -> float:
    x0,y0,x1,y1 = _bbox(a)
    u0,v0,u1,v1 = _bbox(b)
    intr = max(0.,min(x1,u1)-max(x0,u0)) * max(0.,min(y1,v1)-max(y0,v0))
    union = (x1-x0)*(y1-y0)+(u1-u0)*(v1-v0)-intr
    return intr/union if union>0 else 0.


def _normalized_text(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC",text).casefold().split())


def read_tiled_ocr(
    pdf_path: str | Path,
    request: TiledOcrRequest,
    ocr_reader: object,
) -> TiledOcrOutput:
    """Read one bounded tile at a time, revalidate OCR PDF-source quadrilaterals.

    Dedup requires *both* identical Unicode-normalized text and overlap of
    source bboxes (IoU >= 0.50); repeated labels at different locations stay.
    """
    request = TiledOcrRequest.model_validate(request.model_dump())
    if not callable(getattr(ocr_reader, "read", None)):
        raise PdfInputError("A local, explicitly provided CPU OCR reader is required")
    tiles = plan_ocr_tiles(pdf_path, request)
    from mimarllm.importers.pdf import _validate_path
    path = _validate_path(pdf_path, 50 * 1024 * 1024)
    chosen: list[tuple[TextCandidate, str]] = []
    removed = 0
    seen_count = 0
    for tile in tiles:
        region = render_region(
            path, tile.page_index, tile.roi_points, dpi=request.dpi,
            max_pixels=request.max_pixels_per_tile,
        )
        if region.document_sha256 != tile.document_sha256:
            raise PdfInputError("PDF source changed during tiled OCR")
        try:
            raw = ocr_reader.read(region)
        except Exception as exc:
            raise PdfInputError("Local CPU OCR tile failed") from exc
        if not isinstance(raw,(tuple,list)):
            raise PdfInputError("OCR reader must provide a bounded list of text candidates")
        seen_count += len(raw)
        if seen_count > request.max_ocr_candidates:
            raise PdfInputError("OCR candidate total safety budget exceeded")
        for token_index, token in enumerate(raw):
            candidate = TextCandidate.model_validate(token.model_dump())
            if candidate.method != "rapidocr_cpu" or candidate.page_index != tile.page_index:
                raise PdfInputError("OCR method or page index mismatch in tile")
            if not candidate.text.strip() or len(candidate.text) > 512:
                raise PdfInputError("Empty or unbounded OCR token")
            if not all(isfinite(v) for p in candidate.polygon for v in p):
                raise PdfInputError("OCR quadrilateral contains nonfinite point")
            left,top,right,bottom = tile.roi_points
            if any(not (left-1 <= x <= right+1 and top-1 <= y <= bottom+1)
                   for x,y in candidate.polygon):
                raise PdfInputError("OCR source quad outside its original tile")
            x0,y0,x1,y1 = _bbox(candidate)
            if (x1-x0)*(y1-y0) < 0.001:
                raise PdfInputError("OCR text quadrilateral is degenerate")
            unique = candidate.model_copy(update={
                "candidate_id":f"{tile.tile_id}:token{token_index:04d}",
                "review_required":True,
            })
            match = next((j for j,(old,_) in enumerate(chosen)
                          if _normalized_text(old.text) == _normalized_text(unique.text)
                          and _iou(old,unique) >= 0.50),None)
            if match is not None:
                removed += 1
                old,old_tile = chosen[match]
                if (unique.confidence if unique.confidence is not None else -1) > (
                    old.confidence if old.confidence is not None else -1
                ):
                    chosen[match] = (unique,tile.tile_id)
            else:
                chosen.append((unique,tile.tile_id))
    if _hash_file(path) != tiles[0].document_sha256:
        raise PdfInputError("Source PDF mutated before tiled OCR completed")
    return TiledOcrOutput(
        document_sha256=tiles[0].document_sha256,
        page_index=request.page_index,
        tiles=tiles,
        candidates=tuple(c for c,_ in chosen),
        candidate_tile_ids=tuple(t for _,t in chosen),
        removed_duplicate_count=removed,
    )
