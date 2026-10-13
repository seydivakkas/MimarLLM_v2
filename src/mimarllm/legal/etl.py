"""Offline original-PDF-to-LegalAST orchestration and deterministic JSON export."""
from __future__ import annotations

import os
from pathlib import Path

from mimarllm.legal.changes import find_change_candidates
from mimarllm.legal.extractor import LegalInputError, LegalOcrReader, extract_legal_observations
from mimarllm.legal.models import (
    LegalDocument, LegalDocumentMetadata, LegalReviewIssue,
)
from mimarllm.legal.parser import parse_legal_tree, suggest_table_parents


def parse_legal_pdf(
    path: str | Path,
    metadata: LegalDocumentMetadata,
    *,
    ocr_pages: tuple[int, ...] = (),
    ocr_engine: LegalOcrReader | None = None,
    max_pages: int = 100,
    max_file_bytes: int = 50 * 1024 * 1024,
    max_total_lines: int = 60_000,
    max_nodes: int = 50_000,
    max_ocr_pages: int = 15,
    max_render_pixels: int = 8_000_000,
) -> LegalDocument:
    """Build *unreviewed* AST. Neither officiality nor law validity is asserted."""
    metadata = LegalDocumentMetadata.model_validate(metadata.model_dump())
    digest, page_count, lines, tables, issues = extract_legal_observations(
        path, ocr_pages=ocr_pages, ocr_engine=ocr_engine,
        max_pages=max_pages, max_file_bytes=max_file_bytes,
        max_total_lines=max_total_lines, max_ocr_pages=max_ocr_pages,
        max_render_pixels=max_render_pixels,
    )
    try:
        parsed = parse_legal_tree(lines, metadata, max_nodes=max_nodes)
    except ValueError as exc:
        raise LegalInputError(str(exc)) from exc
    tables, table_issues = suggest_table_parents(tables, lines, parsed)
    issues += parsed.issues + table_issues
    changes = find_change_candidates(lines, parsed.line_to_node_id)
    if metadata.document_kind == "CONSOLIDATION":
        issues.append(LegalReviewIssue(
            code="CONSOLIDATION_NOT_INDEPENDENTLY_VERIFIED",
            detail="Consolidated text must be checked against every original and amendment",
        ))
    if not parsed.nodes:
        issues.append(LegalReviewIssue(
            code="NO_LEGAL_NODES_EXTRACTED",
            detail="No structured native/OCR legal clauses extracted",
        ))
    issues.append(LegalReviewIssue(
        code="SOURCE_OFFICIALITY_EFFECTIVITY_AND_APPLICABILITY_UNVERIFIED",
        detail="User-provided Gazette metadata and AST content need independent review",
    ))
    return LegalDocument(
        document_sha256=digest, page_count=page_count,
        metadata=metadata, lines=lines, nodes=parsed.nodes,
        tables=tables, changes=changes, issues=issues,
    )


def export_legal_json(document: LegalDocument, destination: str | Path) -> Path:
    """Explicit, local-only atomic JSON export. Never overwrite an existing file."""
    checked = LegalDocument.model_validate(document.model_dump())
    target = Path(destination).expanduser().resolve(strict=False)
    if target.suffix.lower() != ".json":
        raise LegalInputError("LegalAST export must be a .json destination")
    if not target.parent.is_dir():
        raise LegalInputError("LegalAST export parent directory must exist")
    # Exclusive create prevents silent replacement of user evidence, even
    # when this function is invoked repeatedly or concurrently.
    try:
        with target.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(checked.model_dump_json(indent=2))
            stream.write("\n")
    except FileExistsError as exc:
        raise LegalInputError("Refusing to overwrite an existing LegalAST JSON") from exc
    except OSError as exc:
        raise LegalInputError(f"Unable to export LegalAST: {type(exc).__name__}") from exc
    return target
