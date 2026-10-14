"""Offline Windows-first command line entrypoint, no network or paid APIs.

Exit 0 means report artifacts were written, NOT technical/legislative approval.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from pydantic import ValidationError

from mimarllm.pipeline import PipelineConfig, PipelineInputError, run_local_pipeline
from mimarllm.reports.exporter import ReportExportError, export_report


_ALLOWED = ("json", "md", "html", "pdf")


class CliError(ValueError):
    pass


def _load_config(path: Path | None) -> PipelineConfig:
    if path is None:
        return PipelineConfig()
    try:
        path = path.expanduser().resolve(strict=True)
        if path.suffix.lower() != ".json" or not path.is_file():
            raise CliError("Configuration must be a local .json file")
        if not 0 < path.stat().st_size <= 256_000:
            raise CliError("Configuration exceeds 256 KB or is empty")
        return PipelineConfig.model_validate_json(path.read_bytes())
    except (FileNotFoundError, OSError, UnicodeError, ValidationError, ValueError) as exc:
        if isinstance(exc, CliError):
            raise
        raise CliError("Local configuration JSON is missing or invalid") from exc


def _write_pipeline(
    source: Path,
    output: Path,
    config: PipelineConfig,
    formats: Sequence[str],
) -> tuple[list[Path], str]:
    """Preflight output collisions and rollback only artifacts created this run."""
    if not output.exists() or not output.is_dir():
        raise CliError("Choose an existing local output directory")
    names = tuple(dict.fromkeys(formats))
    if not names or any(fmt not in _ALLOWED for fmt in names):
        raise CliError("Report formats must be selected from json, md, html, pdf")
    manifest_path = output / "pipeline-manifest.json"
    targets = [output / f"analysis.{fmt}" for fmt in names] + [manifest_path]
    if any(p.exists() for p in targets):
        raise CliError("Output already exists; no existing report will be overwritten")

    ocr_reader = None
    if config.ocr_regions:
        from mimarllm.ocr.rapid_engine import RapidCpuOcr, OcrUnavailable
        try:
            ocr_reader = RapidCpuOcr()
        except (OcrUnavailable, ImportError) as exc:
            raise CliError("Requested CPU OCR runtime is unavailable locally") from exc

    result = run_local_pipeline(
        source, config, ocr_reader=ocr_reader,
    )
    generated: list[Path] = []
    try:
        for fmt in names:
            file = output / f"analysis.{fmt}"
            generated.append(export_report(
                result.report, file,
                drawing_pdf_path=source if fmt == "html"
                    and result.drawing.source_kind.value == "PDF" else None,
            ))
        # Manifest is emitted last. This records explicit hold stages in a
        # machine-readable, authoritative source SHA-linked summary.
        with manifest_path.open("x", encoding="utf-8", newline="\n") as writer:
            writer.write(result.manifest.model_dump_json(indent=2))
            writer.write("\n")
        generated.append(manifest_path)
    except (OSError, ValueError, ReportExportError):
        for path in generated:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        raise
    return generated, result.manifest.source_sha256


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="mimarllm",
        description="Offline DXF/PDF technical evidence inspection; not legal compliance.",
    )
    sub = p.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Generate source-backed local reports")
    analyze.add_argument("drawing", help="Existing local .dxf or .pdf file")
    analyze.add_argument("--config", type=Path,
                         help="Optional local JSON review/rule/calibration configuration")
    analyze.add_argument("--output-dir", type=Path, required=True,
                         help="Existing local directory for NEW report outputs")
    analyze.add_argument("--format", dest="formats", choices=_ALLOWED,
                         action="append", help="One or more formats; default json + html")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command != "analyze":
        return 2
    try:
        cfg = _load_config(args.config)
        source = Path(args.drawing).expanduser()
        output = args.output_dir.expanduser()
        files, digest = _write_pipeline(
            source, output, cfg, args.formats or ["json", "html"],
        )
    except (CliError, PipelineInputError, ReportExportError,
            ValidationError, OSError, ValueError) as exc:
        print("MIMARLLM_ERROR: " + str(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        # No traceback or source content/path from arbitrary parser exceptions.
        print(
            "MIMARLLM_ERROR: Unexpected local pipeline failure ("
            + type(exc).__name__ + ")",
            file=sys.stderr,
        )
        return 3
    print("MIMARLLM_COMPLETED_WITH_REVIEW_GATES: " + digest)
    for path in files:
        print("OUTPUT: " + str(path))
    print("REGULATORY_LOCKED: all legal compliance and legal effectivity remain unverified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
