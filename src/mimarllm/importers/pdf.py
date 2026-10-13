"""Hybrid PDF reader: pdfplumber vectors/text + pypdfium2 bounded ROI render.

PDF coordinates: top-left origin, x rightwards, y downwards, units PDF points.
DrawingIR/world units must NEVER be derived from these coordinates without
an explicit drawing scale/calibration. This module performs no OCR itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from mimarllm.core.models import PageObservation, PdfObservation, TextCandidate, VectorObservation


class PdfInputError(ValueError):
    """Invalid or unsupported PDF input."""


@dataclass(frozen=True)
class RenderedRegion:
    image: object  # PIL.Image.Image; not stored inside JSON output.
    page_index: int
    roi_points: tuple[float, float, float, float]
    pixels_per_point: float
    document_sha256: str
    page_rotation_degrees: int = 0
    pixel_origin_pdf_points: tuple[float, float] | None = None

    def source_to_pixel(self, x: float, y: float) -> tuple[float, float]:
        """Convert displayed-page PDF coordinates to ROI bitmap coordinates."""
        from math import isfinite
        x0, y0 = self.pixel_origin_pdf_points or self.roi_points[:2]
        if not all(isfinite(v) for v in (x, y, self.pixels_per_point)):
            raise PdfInputError("Nonfinite source or render scale")
        return ((x - x0) * self.pixels_per_point, (y - y0) * self.pixels_per_point)

    def pixel_to_source(self, x: float, y: float) -> tuple[float, float]:
        """Map the OCR bitmap pixel center to PDF top-left points."""
        from math import isfinite
        if not all(isfinite(v) for v in (x, y)):
            raise PdfInputError("Nonfinite OCR pixel coordinate")
        x0, y0 = self.pixel_origin_pdf_points or self.roi_points[:2]
        return (x0 + x / self.pixels_per_point, y0 + y / self.pixels_per_point)


def _validate_path(path: str | Path, max_bytes: int) -> Path:
    pdf = Path(path).expanduser().resolve(strict=True)
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        raise PdfInputError("A local .pdf file is required")
    if not 0 < pdf.stat().st_size <= max_bytes:
        raise PdfInputError("PDF file size is outside safety limits")
    with pdf.open("rb") as fh:
        if fh.read(5) != b"%PDF-":
            raise PdfInputError("PDF signature not found")
    return pdf


def _hash_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_pdf(
    path: str | Path,
    *,
    max_file_bytes: int = 50 * 1024 * 1024,
    max_pages: int = 50,
    max_elements_per_page: int = 100_000,
) -> PdfObservation:
    """Extract native PDF glyph and vector *observations*, without assumptions."""
    import pdfplumber

    pdf = _validate_path(path, max_file_bytes)
    digest = _hash_file(pdf)
    result: list[PageObservation] = []
    try:
        with pdfplumber.open(pdf) as document:
            if not 1 <= len(document.pages) <= max_pages:
                raise PdfInputError("PDF page count exceeds configured limit")
            for page_index, page in enumerate(document.pages):
                chars = page.chars
                lines = page.lines
                curves = page.curves
                rects = page.rects
                if len(chars) + len(lines) + len(curves) + len(rects) > max_elements_per_page:
                    raise PdfInputError("PDF entity count exceeds configured limit")
                page_data = PageObservation(
                    page_index=page_index,
                    width_pt=float(page.width),
                    height_pt=float(page.height),
                    rotation_degrees=int(page.rotation or 0),
                )
                for idx, char in enumerate(chars):
                    x0, y0 = float(char["x0"]), float(char["top"])
                    x1, y1 = float(char["x1"]), float(char["bottom"])
                    matrix = char.get("matrix")
                    page_data.text.append(TextCandidate(
                        candidate_id=f"p{page_index}-ch{idx}",
                        page_index=page_index,
                        text=str(char.get("text", "")),
                        method="native_pdf",
                        polygon=((x0, y0), (x1, y0), (x1, y1), (x0, y1)),
                        font_name=str(char.get("fontname", "")) or None,
                        font_size_pt=float(char.get("size", 0.0)),
                        text_matrix=tuple(float(n) for n in matrix) if matrix is not None and len(matrix) == 6 else None,
                    ))
                for kind, items in (("line", lines), ("curve", curves), ("rect", rects)):
                    for idx, item in enumerate(items):
                        page_data.vectors.append(VectorObservation(
                            source_id=f"p{page_index}-{kind}{idx}",
                            page_index=page_index,
                            kind=kind,
                            bounds=(float(item["x0"]), float(item["top"]), float(item["x1"]), float(item["bottom"])),
                            line_width_pt=float(item.get("linewidth") or 0.0),
                        ))
                result.append(page_data)
    except PdfInputError:
        raise
    except Exception as exc:
        raise PdfInputError(f"PDF could not be inspected: {type(exc).__name__}") from exc
    return PdfObservation(document_sha256=digest, page_count=len(result), pages=result)


def render_region(
    path: str | Path,
    page_index: int,
    roi_points: tuple[float, float, float, float],
    *,
    dpi: int = 150,
    max_pixels: int = 8_000_000,
    max_file_bytes: int = 50 * 1024 * 1024,
) -> RenderedRegion:
    """Render a displayed-page ROI including standard /Rotate metadata.

    The PDF crop tuple uses displayed-page margins (left,bottom,right,top).
    Non-default CropBox is rejected to prevent misleading source placement.
    """
    import pypdfium2 as pdfium

    pdf = _validate_path(path, max_file_bytes)
    if not (72 <= dpi <= 300):
        raise PdfInputError("ROI DPI must be within 72..300")
    scale = dpi / 72.0
    document = None
    try:
        document = pdfium.PdfDocument(pdf)
        if not 0 <= page_index < len(document):
            raise PdfInputError("PDF page index outside document")
        page = document[page_index]
        # PDFium get_size()/render() use the displayed page coordinates even
        # when /Rotate is 90/180/270. pypdfium2 render crop is post-rotation.
        # A non-default CropBox changes the visible origin, and PDF plumber
        # keeps media-based coordinates. Until that offset is proven by
        # cross-engine tests, fail closed instead of forging OCR polygons.
        rotation = int(page.get_rotation())
        if rotation not in (0, 90, 180, 270):
            raise PdfInputError("Unsupported PDF page rotation")
        mediabox = tuple(float(v) for v in page.get_mediabox())
        cropbox = tuple(float(v) for v in page.get_cropbox())
        if any(abs(a - b) > 1e-6 for a, b in zip(mediabox, cropbox)):
            raise PdfInputError(
                "Non-default CropBox needs verified cross-engine page offset"
            )
        width, height = [float(n) for n in page.get_size()]
        x0, y0, x1, y1 = roi_points
        if not (0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height):
            raise PdfInputError("ROI must fall inside the PDF page in points")
        if (x1 - x0) * (y1 - y0) * scale * scale > max_pixels:
            raise PdfInputError("Rendered region pixel budget exceeded")
        from math import ceil
        if rotation in (90, 180, 270):
            # PDFium's partial-page crop under /Rotate=90 can disagree with
            # full-page crop (verified by synthetic regression). Render fully
            # and crop with PIL ONLY when the full bitmap is safely bounded.
            full_width, full_height = ceil(width * scale), ceil(height * scale)
            if full_width * full_height > max_pixels:
                raise PdfInputError(
                    "Rotated page requires bounded full-page render; page too large"
                )
            full_bitmap = page.render(scale=scale)
            full_image = full_bitmap.to_pil()
            left_px, top_px = round(x0 * scale), round(y0 * scale)
            image = full_image.crop((
                left_px, top_px,
                round(x1 * scale), round(y1 * scale),
            )).copy()
        else:
            bitmap = page.render(
                scale=scale, crop=(x0, height - y1, width - x1, y0)
            )
            image = bitmap.to_pil().copy()
            left_px, top_px = ceil(x0 * scale), ceil(y0 * scale)
        if image.width * image.height > max_pixels:
            raise PdfInputError("Actual render exceeded pixel budget")
        return RenderedRegion(
            image=image, page_index=page_index,
            roi_points=roi_points, pixels_per_point=scale,
            document_sha256=_hash_file(pdf),
            page_rotation_degrees=rotation,
            pixel_origin_pdf_points=(left_px / scale, top_px / scale),
        )
    except PdfInputError:
        raise
    except Exception as exc:
        raise PdfInputError(f"PDF rendering failed: {type(exc).__name__}") from exc
    finally:
        if document is not None:
            document.close()
