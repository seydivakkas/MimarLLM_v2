"""Native pdfplumber lines/tables and opt-in bounded RapidOCR CPU page extraction.

Every span is expressed in the displayed original PDF page's top-left points.
Never mark inferred article text, publication metadata or source as approved.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from hashlib import sha256
from math import isfinite
from pathlib import Path
from typing import Protocol

from mimarllm.core.models import TextCandidate
from mimarllm.importers.pdf import (
    PdfInputError, RenderedRegion, _hash_file, _validate_path, render_region,
)
from mimarllm.legal.models import (
    LegalLine, LegalReviewIssue, LegalSourceSpan, LegalTable, LegalTableCell,
    TextOrigin,
)


class LegalInputError(ValueError):
    """Corrupt, excessive or nonlocal legal source input."""


class LegalOcrReader(Protocol):
    def read(self, region: RenderedRegion) -> list[TextCandidate]: ...


def _rect(x0: float, y0: float, x1: float, y1: float):
    coords = (x0, y0, x1, y1)
    if not all(isfinite(n) for n in coords) or x0 > x1 or y0 > y1:
        raise LegalInputError("Invalid source PDF rectangle")
    return ((x0, y0), (x1, y0), (x1, y1), (x0, y1))


def _table_spans(page, *, page_index: int, digest: str,
                 max_tables: int, max_cells: int):
    tables = page.find_tables()
    if len(tables) > max_tables:
        raise LegalInputError("Legal PDF table-count budget exceeded")
    extracted: list[LegalTable] = []
    bboxes = []
    count = 0
    issues: list[LegalReviewIssue] = []
    for ti, table in enumerate(tables):
        bbox = tuple(float(v) for v in table.bbox)
        table_source = LegalSourceSpan(
            document_sha256=digest, page_index=page_index,
            polygon=_rect(*bbox), extraction=TextOrigin.NATIVE_PDF,
        )
        values = table.extract()
        cells = []
        for row_index, row in enumerate(table.rows):
            for col_index, cell_bbox in enumerate(row.cells):
                if cell_bbox is None:
                    issues.append(LegalReviewIssue(
                        code="SPANNING_OR_MISSING_TABLE_CELL",
                        page_index=page_index, detail="Table cell has no independent bbox",
                    ))
                    continue
                count += 1
                if count > max_cells:
                    raise LegalInputError("Legal PDF table-cell budget exceeded")
                text = ""
                if row_index < len(values) and col_index < len(values[row_index]):
                    text = values[row_index][col_index] or ""
                cells.append(LegalTableCell(
                    row_index=row_index, column_index=col_index,
                    text=text,
                    source=LegalSourceSpan(
                        document_sha256=digest, page_index=page_index,
                        polygon=_rect(*(float(v) for v in cell_bbox)),
                        extraction=TextOrigin.NATIVE_PDF,
                        reference_type="TABLE_CELL_BBOX",
                    ),
                ))
        extracted.append(LegalTable(
            table_id=f"p{page_index}:table{ti}",
            page_index=page_index, source=table_source, cells=cells,
        ))
        bboxes.append(bbox)
    return extracted, bboxes, issues


def extract_legal_observations(
    path: str | Path,
    *,
    ocr_pages: Sequence[int] = (),
    ocr_engine: LegalOcrReader | None = None,
    dpi: int = 144,
    max_file_bytes: int = 50 * 1024 * 1024,
    max_pages: int = 100,
    max_words_per_page: int = 40_000,
    max_total_lines: int = 60_000,
    max_tables_per_page: int = 60,
    max_cells_per_page: int = 8000,
    max_ocr_pages: int = 15,
    max_render_pixels: int = 8_000_000,
):
    """Return immutable source observations: digest, count, lines, tables, issues.

    Native page reading order is heuristic and ALWAYS requires human review.
    Multi-column native layouts can interleave text, therefore never certify.
    """
    import pdfplumber

    if not all(isinstance(n, int) and n > 0 for n in (
        max_file_bytes, max_pages, max_words_per_page, max_total_lines,
        max_tables_per_page, max_cells_per_page, max_ocr_pages, max_render_pixels,
    )):
        raise LegalInputError("Invalid source extraction safety budgets")
    pdf = _validate_path(path, max_file_bytes)
    digest = _hash_file(pdf)
    chosen = tuple(ocr_pages)
    if (len(chosen) != len(set(chosen))
            or len(chosen) > max_ocr_pages or
            any(not isinstance(p, int) or p < 0 for p in chosen)):
        raise LegalInputError("Invalid or excessive explicit OCR page selection")
    if chosen and ocr_engine is None:
        raise LegalInputError("OCR requires an explicit installed local CPU reader")

    lines: list[LegalLine] = []
    tables: list[LegalTable] = []
    issues: list[LegalReviewIssue] = []
    page_count = 0
    dimensions: list[tuple[float, float]] = []
    try:
        with pdfplumber.open(pdf) as doc:
            page_count = len(doc.pages)
            if not 1 <= page_count <= max_pages:
                raise LegalInputError("Legal PDF page budget exceeded")
            if any(p >= page_count for p in chosen):
                raise LegalInputError("Explicit OCR page index outside PDF")
            for idx, page in enumerate(doc.pages):
                width, height = float(page.width), float(page.height)
                dimensions.append((width, height))
                extracted_tables, excluded_boxes, table_issues = _table_spans(
                    page, page_index=idx, digest=digest,
                    max_tables=max_tables_per_page, max_cells=max_cells_per_page,
                )
                tables.extend(extracted_tables)
                issues.extend(table_issues)
                words = page.extract_words(
                    x_tolerance=2, y_tolerance=3, keep_blank_chars=False,
                    use_text_flow=False,
                )
                if len(words) > max_words_per_page:
                    raise LegalInputError("Native legal PDF word budget exceeded")

                # Exclude glyphs *inside* detected tables: cells carry their own
                # exact source bbox, not fake article/paragraph continuations.
                clean = []
                for word in words:
                    x0, x1 = float(word["x0"]), float(word["x1"])
                    y0, y1 = float(word["top"]), float(word["bottom"])
                    xmid, ymid = (x0 + x1) / 2, (y0 + y1) / 2
                    if any(a <= xmid <= c and b <= ymid <= d
                           for a, b, c, d in excluded_boxes):
                        continue
                    clean.append((x0, y0, x1, y1, str(word["text"])))

                # Top-left page coordinate ordering is deterministic, but
                # *not* verified reading order for two-column gazettes.
                clean.sort(key=lambda w: (w[1], w[0]))
                grouped: list[list[tuple[float, float, float, float, str]]] = []
                for word in clean:
                    if not grouped or abs(word[1] - grouped[-1][0][1]) > 3:
                        grouped.append([word])
                    else:
                        grouped[-1].append(word)
                if (len(grouped) >= 4 and
                    sum(1 for group in grouped
                        if len(group) >= 3 and
                        max(w[0] for w in group) - min(w[2] for w in group) >
                        0.45 * width) >= 2):
                    issues.append(LegalReviewIssue(
                        code="POSSIBLE_MULTI_COLUMN_READING_ORDER",
                        page_index=idx,
                        detail="Word positions may represent multiple columns; review order",
                    ))
                if page.rotation not in (0, None):
                    issues.append(LegalReviewIssue(
                        code="ROTATED_NATIVE_TEXT_REVIEW_REQUIRED",
                        page_index=idx,
                        detail="Rotated PDF glyph order requires visual review",
                    ))
                for group in grouped:
                    group.sort(key=lambda w: w[0])
                    text = " ".join(w[4] for w in group).strip()
                    if not text:
                        continue
                    src = LegalSourceSpan(
                        document_sha256=digest, page_index=idx,
                        polygon=_rect(min(w[0] for w in group),
                                      min(w[1] for w in group),
                                      max(w[2] for w in group),
                                      max(w[3] for w in group)),
                        extraction=TextOrigin.NATIVE_PDF,
                    )
                    lines.append(LegalLine(
                        line_id=f"p{idx}:native:{len(grouped)}:{len(lines)}",
                        reading_index=len(lines), text=text, source=src,
                    ))
                    if len(lines) > max_total_lines:
                        raise LegalInputError("Legal PDF source line budget exceeded")
                if not grouped and not extracted_tables and idx not in chosen:
                    issues.append(LegalReviewIssue(
                        code="NO_NATIVE_CONTENT_OCR_NOT_SELECTED",
                        page_index=idx,
                        detail="No native text/table, explicit offline OCR required",
                    ))
                if grouped and idx in chosen:
                    issues.append(LegalReviewIssue(
                        code="OCR_OVER_NATIVE_TEXT_REVIEW_REQUIRED",
                        page_index=idx,
                        detail="Requested OCR may duplicate or conflict with native text",
                    ))
    except LegalInputError:
        raise
    except Exception as exc:
        raise LegalInputError(f"Native legal PDF extraction failed: {type(exc).__name__}") from exc

    for idx in chosen:
        w, h = dimensions[idx]
        try:
            region = render_region(
                pdf, idx, (0.0, 0.0, w, h), dpi=dpi,
                max_pixels=max_render_pixels, max_file_bytes=max_file_bytes,
            )
        except PdfInputError as exc:
            raise LegalInputError(f"OCR page {idx} cannot be mapped safely: {exc}") from exc
        if region.document_sha256 != digest:
            raise LegalInputError("PDF changed during OCR region extraction")
        assert ocr_engine is not None
        candidates = ocr_engine.read(region)
        for item_index, candidate in enumerate(candidates):
            if candidate.method != "rapidocr_cpu" or candidate.page_index != idx:
                raise LegalInputError("OCR candidate has inconsistent method/page")
            quad = tuple((float(x), float(y)) for x, y in candidate.polygon)
            if (len(quad) != 4
                    or any(not isfinite(v) or v < -1 or v > bound + 1
                           for p in quad for v, bound in zip(p, (w, h)))):
                raise LegalInputError("OCR polygon outside original PDF page")
            lines.append(LegalLine(
                line_id=f"p{idx}:ocr:{item_index}", reading_index=len(lines),
                text=candidate.text,
                source=LegalSourceSpan(
                    document_sha256=digest, page_index=idx,
                    polygon=quad, extraction=TextOrigin.RAPIDOCR_CPU,
                    confidence=candidate.confidence,
                    reference_type="OCR_DETECTION_QUAD",
                ),
            ))
            if len(lines) > max_total_lines:
                raise LegalInputError("Legal PDF source line budget exceeded")

    if _hash_file(pdf) != digest:
        raise LegalInputError("Original PDF changed during LegalAST extraction")
    # All OCR fragments sorted among native lines by source page/position.
    # This remains only an unreviewed visual reading-order candidate.
    lines.sort(key=lambda line: (
        line.source.page_index,
        min(p[1] for p in line.source.polygon),
        min(p[0] for p in line.source.polygon),
        line.line_id,
    ))
    lines = [x.model_copy(update={"reading_index": i})
             for i, x in enumerate(lines)]
    return digest, page_count, lines, tables, issues
