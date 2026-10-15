"""Wheelhouse + frozen onedir package integrity and declared-license inventory.

No network requests, pip installs, signature claims, or rights conclusions.
Checks SHA256 + relative paths + target Python/OS metadata. The manifest
itself must be protected independently to resist a malicious full rewrite.
"""
from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import sys


MAX_ENTRIES = 25_000
MAX_SINGLE_FILE = 3_000_000_000
MAX_TOTAL_BYTES = 6_000_000_000
SAFE_WHEEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+-]*\.whl$")
HEX = re.compile(r"^[0-9a-f]{64}$")


class ManifestError(ValueError):
    pass


def _digest(file: Path) -> str:
    h = hashlib.sha256()
    with file.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _inside(root: Path, raw: str) -> Path:
    if (not raw or raw.startswith(("/", "\\")) or "\\" in raw
            or any(part in {"", ".", ".."} for part in raw.split("/"))
            or ":" in raw):
        raise ManifestError("Unsafe manifest-relative path")
    target = root.joinpath(*raw.split("/"))
    if not target.resolve(strict=False).is_relative_to(root.resolve()):
        raise ManifestError("Manifest path escapes artifact directory")
    # Disallow symlink at every parent. Never hash a link to an external file.
    relative = target.relative_to(root)
    current = root
    if root.is_symlink():
        raise ManifestError("Symlink root directory refused")
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ManifestError("Manifest symlink entry refused")
    return target


def _collect_files(root: Path, *, suffix: str | None = None) -> list[dict]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ManifestError("Manifest root must be a local directory")
    gathered: list[dict] = []
    total = 0
    for item in root.rglob("*"):
        if item.is_symlink():
            raise ManifestError("Symbolic links in package payload are not allowed")
        if not item.is_file():
            continue
        relative = item.relative_to(root).as_posix()
        if suffix is not None and item.suffix.lower() != suffix:
            raise ManifestError("Wheelhouse must contain only .whl files")
        if suffix == ".whl" and (
            "/" in relative or not SAFE_WHEEL.fullmatch(relative)
        ):
            raise ManifestError("Invalid or nested wheel filename")
        if len(gathered) >= MAX_ENTRIES:
            raise ManifestError("Package file count limit exceeded")
        size = item.stat().st_size
        if size < 1 or size > MAX_SINGLE_FILE:
            raise ManifestError("Empty/oversized package payload")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ManifestError("Package payload exceeds total byte budget")
        gathered.append({
            "path": relative,
            "size_bytes": size,
            "sha256": _digest(item),
        })
    if not gathered:
        raise ManifestError("No package files found")
    return sorted(gathered, key=lambda x: x["path"])


def _load(file: Path) -> dict:
    file = file.resolve(strict=True)
    if not file.is_file() or file.stat().st_size > 2_000_000:
        raise ManifestError("Invalid/oversized manifest")
    try:
        manifest = json.loads(file.read_text(encoding="utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ManifestError("Cannot read JSON manifest") from exc
    if not isinstance(manifest, dict) or manifest.get("schema_version") != "0.1":
        raise ManifestError("Unsupported package manifest schema")
    return manifest


def _installed_distributions() -> list[dict]:
    inventory = []
    for dist in metadata.distributions():
        name = dist.metadata.get("Name")
        if not name:
            continue
        inventory.append({
            "name": name,
            "version": dist.version,
            "declared_license": (dist.metadata.get("License") or "UNSPECIFIED")[:250],
            "metadata_source": "INSTALLED_PACKAGE_SELF_DECLARATION_NOT_LEGAL_APPROVAL",
        })
    return sorted(inventory, key=lambda x: x["name"].lower())


def create_manifest(
    root: Path,
    *,
    kind: str,
    pyproject: Path | None = None,
) -> dict:
    if kind not in {"WHEELHOUSE", "WINDOWS_ONEDIR"}:
        raise ManifestError("Unknown manifest kind")
    if kind == "WINDOWS_ONEDIR" and sys.platform != "win32":
        raise ManifestError("Windows executable manifest must be generated on Windows")
    entries = _collect_files(root, suffix=".whl" if kind == "WHEELHOUSE" else None)
    if kind == "WINDOWS_ONEDIR" and not any(
        item["path"].lower() == "mimarllm_v2.exe" for item in entries
    ):
        raise ManifestError("Windows onedir executable missing")
    source_hash = None
    if pyproject is not None:
        pyproject = pyproject.resolve(strict=True)
        if not pyproject.is_file():
            raise ManifestError("Project declaration is missing")
        source_hash = _digest(pyproject)
    return {
        "schema_version": "0.1",
        "kind": kind,
        "platform": sys.platform,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}",
        "architecture": platform.machine(),
        "project_pyproject_sha256": source_hash,
        "files": entries,
        "package_inventory": _installed_distributions() if kind == "WINDOWS_ONEDIR" else [],
        "source_authenticity": "LOCAL_HASH_INTEGRITY_ONLY_MANIFEST_NEEDS_EXTERNAL_TRUST",
        "license_review": "HOLD_DECLARED_METADATA_IS_NOT_DISTRIBUTION_RIGHTS_APPROVAL",
    }


def save_manifest(output: Path, manifest: dict) -> Path:
    output = output.resolve(strict=False)
    if not output.parent.is_dir() or output.suffix.lower() != ".json":
        raise ManifestError("Manifest destination must be a new JSON in existing directory")
    try:
        with output.open("x", encoding="utf-8", newline="\n") as writer:
            writer.write(json.dumps(manifest, indent=2, ensure_ascii=False))
            writer.write("\n")
    except FileExistsError as exc:
        raise ManifestError("Refusing to overwrite existing package manifest") from exc
    return output


def verify_manifest(
    root: Path, file: Path, *,
    expected_kind: str,
    pyproject: Path | None = None,
    strict_environment: bool = True,
) -> dict:
    root = root.resolve(strict=True)
    declared = _load(file)
    if declared.get("kind") != expected_kind:
        raise ManifestError("Wrong manifest kind")
    if strict_environment and (
        declared.get("platform") != sys.platform or
        declared.get("python_version") !=
        f"{sys.version_info.major}.{sys.version_info.minor}"
    ):
        raise ManifestError("Wheelhouse target Python or OS differs")
    if pyproject is not None:
        value = declared.get("project_pyproject_sha256")
        if not isinstance(value, str) or not HEX.fullmatch(value):
            raise ManifestError("Project hash absent from manifest")
        if _digest(pyproject.resolve(strict=True)) != value:
            raise ManifestError("Project declaration changed after wheel preparation")
    entries = declared.get("files")
    if not isinstance(entries, list) or not 0 < len(entries) <= MAX_ENTRIES:
        raise ManifestError("No valid entries in package manifest")
    known = set()
    for item in entries:
        if (not isinstance(item, dict)
                or set(item) != {"path", "sha256", "size_bytes"}
                or not isinstance(item["path"], str)
                or not isinstance(item["size_bytes"], int)
                or not isinstance(item["sha256"], str)
                or not HEX.fullmatch(item["sha256"])):
            raise ManifestError("Malformed package file metadata")
        target = _inside(root, item["path"])
        if expected_kind == "WHEELHOUSE" and (
            "/" in item["path"] or not SAFE_WHEEL.fullmatch(item["path"])
        ):
            raise ManifestError("Nonwheel/misplaced wheel in wheelhouse manifest")
        if not target.is_file() or target.stat().st_size != item["size_bytes"]:
            raise ManifestError("Package payload absent or wrong byte size")
        if item["path"] in known:
            raise ManifestError("Duplicate package payload record")
        known.add(item["path"])
        if _digest(target) != item["sha256"]:
            raise ManifestError("Package hash differs from prepared manifest")
    actual = {x["path"] for x in _collect_files(
        root, suffix=".whl" if expected_kind == "WHEELHOUSE" else None,
    )}
    if known != actual:
        raise ManifestError("Unlisted file added or package file removed")
    if expected_kind == "WINDOWS_ONEDIR" and "MimarLLM_V2.exe" not in known:
        raise ManifestError("Expected frozen executable missing from package")
    return declared


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Local hash manifest verification, not signatures")
    s = p.add_subparsers(dest="command", required=True)
    make = s.add_parser("create", help="Create local wheel or onedir inventory")
    verify = s.add_parser("verify", help="Verify all files against existing inventory")
    for cmd in (make, verify):
        cmd.add_argument("--directory", type=Path, required=True)
        cmd.add_argument("--manifest", type=Path, required=True)
        cmd.add_argument("--kind", required=True,
                         choices=("WHEELHOUSE", "WINDOWS_ONEDIR"))
        cmd.add_argument("--pyproject", type=Path)
    args = p.parse_args(argv)
    try:
        if args.command == "create":
            created = create_manifest(
                args.directory, kind=args.kind, pyproject=args.pyproject,
            )
            save_manifest(args.manifest, created)
            print("MANIFEST_CREATED: integrity record, not a source signature")
        else:
            verify_manifest(
                args.directory, args.manifest,
                expected_kind=args.kind, pyproject=args.pyproject,
            )
            print("MANIFEST_SHA_MATCH: local bytes only, licenses unapproved")
        return 0
    except (ManifestError, OSError, ValueError) as exc:
        print("PACKAGE_REJECTED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
