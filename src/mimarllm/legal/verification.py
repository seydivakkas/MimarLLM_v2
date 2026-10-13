"""Offline verification of LOCAL PDF bytes/page coordinates, never officiality.

A matching file hash is only an integrity check. It does not establish
authentic publication, editorial correctness, dates or lawful effect.
"""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Literal

import pypdfium2 as pdfium
from pydantic import BaseModel, ConfigDict, Field

from mimarllm.legal.models import LegalDocument, SHA_PATTERN


class SourceAuditStatus(str, Enum):
    LOCAL_SOURCE_MATCHED = "LOCAL_SOURCE_MATCHED"
    ORIGINAL_PDF_MISSING = "ORIGINAL_PDF_MISSING"
    ORIGINAL_PDF_MISMATCH = "ORIGINAL_PDF_MISMATCH"
    PAGE_GEOMETRY_MISMATCH = "PAGE_GEOMETRY_MISMATCH"
    INVALID_SOURCE = "INVALID_SOURCE"


class SourceAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    document_sha256: str = Field(pattern=SHA_PATTERN)
    status: SourceAuditStatus
    page_count: int = Field(ge=1)
    inspected_spans: int = Field(ge=0)
    original_pdf_path: str | None = None
    reasons: tuple[str, ...] = ()
    officiality: Literal["OFFICIAL_PUBLICATION_NOT_VERIFIED"] = (
        "OFFICIAL_PUBLICATION_NOT_VERIFIED"
    )
    legal_compliance_certified: Literal[False] = False


def verify_local_pdf(
    document: LegalDocument,
    local_pdf: str | Path | None,
    *, max_file_bytes: int = 100 * 1024 * 1024,
    coordinate_epsilon: float = 1e-5,
) -> SourceAudit:
    """Revalidate AST then hash and check every source span on original pages.

    Does not access the Internet and cannot prove the PDF came from an
    official Gazette host. The user-supplied metadata URL is not visited.
    """
    document = LegalDocument.model_validate(document.model_dump())
    if max_file_bytes < 1 or coordinate_epsilon < 0 or coordinate_epsilon > 0.01:
        raise ValueError("Invalid local PDF verification limits")

    def done(status: SourceAuditStatus, reason: str, *,
             inspected: int = 0, path: str | None = None) -> SourceAudit:
        return SourceAudit(
            document_sha256=document.document_sha256,
            status=status, page_count=document.page_count,
            inspected_spans=inspected, original_pdf_path=path,
            reasons=(reason,),
        )

    if local_pdf is None:
        return done(SourceAuditStatus.ORIGINAL_PDF_MISSING,
                    "NO_LOCAL_ORIGINAL_PDF")
    try:
        file = Path(local_pdf).expanduser().resolve(strict=True)
        if not file.is_file() or not 0 < file.stat().st_size <= max_file_bytes:
            return done(SourceAuditStatus.INVALID_SOURCE,
                        "SOURCE_NOT_A_BOUNDED_REGULAR_FILE")
        # Existing source hash helper intentionally accepts ONLY local PDF bytes.
        from mimarllm.rag.store import _sha_file
        if _sha_file(file, max_bytes=max_file_bytes) != document.document_sha256:
            return done(SourceAuditStatus.ORIGINAL_PDF_MISMATCH,
                        "LOCAL_PDF_SHA256_DIFFERS_FROM_LEGALAST")
        spans = [line.source for line in document.lines]
        spans += [span for n in document.nodes for span in n.spans]
        spans += [t.source for t in document.tables]
        spans += [cell.source for t in document.tables for cell in t.cells]
        spans += [c.source for c in document.changes]
        if len(spans) > 250_000:
            return done(SourceAuditStatus.INVALID_SOURCE, "SOURCE_SPAN_BUDGET_EXCEEDED")
        with pdfium.PdfDocument(str(file)) as pdf:
            if len(pdf) != document.page_count:
                return done(SourceAuditStatus.PAGE_GEOMETRY_MISMATCH,
                            "ORIGINAL_PDF_PAGE_COUNT_DIFFERS")
            sizes = [tuple(float(v) for v in page.get_size()) for page in pdf]
        for span in spans:
            width, height = sizes[span.page_index]
            for x, y in span.polygon:
                if not (-coordinate_epsilon <= x <= width + coordinate_epsilon
                        and -coordinate_epsilon <= y <= height + coordinate_epsilon):
                    return done(
                        SourceAuditStatus.PAGE_GEOMETRY_MISMATCH,
                        "SOURCE_POLYGON_OUTSIDE_ORIGINAL_PAGE",
                        inspected=len(spans), path=str(file),
                    )
        # Source must remain unchanged while page inspection happened.
        if _sha_file(file, max_bytes=max_file_bytes) != document.document_sha256:
            return done(SourceAuditStatus.ORIGINAL_PDF_MISMATCH,
                        "LOCAL_PDF_CHANGED_DURING_VERIFICATION")
        return done(
            SourceAuditStatus.LOCAL_SOURCE_MATCHED,
            "LOCAL_BYTES_PAGE_COUNT_AND_POLYGON_BOUNDS_MATCH_NOT_OFFICIALITY",
            inspected=len(spans), path=str(file),
        )
    except (FileNotFoundError, PermissionError, OSError):
        return done(SourceAuditStatus.ORIGINAL_PDF_MISSING,
                    "ORIGINAL_PDF_UNAVAILABLE")
    except Exception as exc:
        return done(SourceAuditStatus.INVALID_SOURCE,
                    f"SOURCE_FILE_COULD_NOT_BE_VERIFIED_{type(exc).__name__}")
