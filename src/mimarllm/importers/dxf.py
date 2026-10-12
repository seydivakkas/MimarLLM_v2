"""Conservative, offline, deterministic DXF -> DrawingIR import.

Native geometry is observed, not classified as architectural elements.
Curves are tessellated to an explicit *CAD-source-unit* tolerance, never metres.
No DXF dimension or layer label can confirm physical scale or legal compliance.
"""
from __future__ import annotations

from hashlib import sha256
from itertools import islice
from math import isfinite
from pathlib import Path
from typing import Literal

import ezdxf
from ezdxf.math import Matrix44
from pydantic import BaseModel, ConfigDict, Field

from mimarllm.core.ir import (
    CoordinateFrame, CoordinateKind, DrawingEntity, DrawingIR,
    EvidenceOrigin, GeometryPrimitive, PrimitiveKind, SourceKind,
    SourceReference, YDirection,
)
from mimarllm.core.units import UnitCalibration
from mimarllm.importers.layers import layer_hint


class DxfInputError(ValueError):
    """Unsafe, corrupt or out-of-contract DXF input."""


class DxfIssue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    code: str
    source_handle: str | None = None
    block_path: tuple[str, ...] = ()
    detail: str


class DxfAnnotation(BaseModel):
    """Native CAD text or dimension *candidate*: not a certified measurement."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    entity_id: str
    source: SourceReference
    kind: Literal["TEXT", "MTEXT", "ATTRIB", "DIMENSION"]
    text: str = ""
    location: tuple[float, float]
    raw_dimension_value: float | None = None
    dimension_kind: int | None = None
    note: str | None = None


class DxfLayer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    name: str
    hint: str | None = None


class DxfImportResult(BaseModel):
    drawing: DrawingIR
    annotations: list[DxfAnnotation] = Field(default_factory=list)
    layers: list[DxfLayer] = Field(default_factory=list)
    issues: list[DxfIssue] = Field(default_factory=list)


def _hash_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _point2(vec: object, *, z_tolerance: float = 1e-7) -> tuple[float, float]:
    x, y = float(vec[0]), float(vec[1])  # type: ignore[index]
    z = float(vec[2]) if len(vec) > 2 else 0.0  # type: ignore[arg-type]
    if not (isfinite(x) and isfinite(y) and isfinite(z)):
        raise ValueError("nonfinite CAD point")
    if abs(z) > z_tolerance:
        raise ValueError("nonplanar or elevated geometry outside 2D v0.1")
    return (x, y)


def parse_dxf(
    file_path: str | Path, *,
    max_file_bytes: int = 25_000_000,
    max_entities: int = 100_000,
    max_block_depth: int = 8,
    max_points_per_entity: int = 8_000,
    curve_flatten_distance: float = 0.05,
    include_paperspace: bool = False,
) -> DxfImportResult:
    """Read a local DXF file without changing it; return source-aware 2D observations.

    Nested block matrix order is child.matrix44() @ cumulative_parent_matrix.
    The resulting sub-entities retain the *original definition* DXF handles
    and each insertion instance has an explicit ordered block_path.

    Unsupported/ambiguous content creates issues, never affirmative findings.
    """
    if not (max_file_bytes > 0 and max_entities > 0 and max_block_depth > 0
            and max_points_per_entity >= 4
            and isfinite(curve_flatten_distance) and curve_flatten_distance > 0):
        raise DxfInputError("Invalid safety limits or flattening tolerance")
    path = Path(file_path).expanduser().resolve(strict=True)
    if path.suffix.lower() != ".dxf" or not path.is_file():
        raise DxfInputError("Local .dxf file required")
    if not 0 < path.stat().st_size <= max_file_bytes:
        raise DxfInputError("DXF file exceeds size limit or is empty")
    digest = _hash_file(path)
    try:
        doc = ezdxf.readfile(path)
        audit = doc.audit()
        if audit.has_errors:
            raise DxfInputError("DXF structural audit has unrecoverable errors")
    except DxfInputError:
        raise
    except (OSError, UnicodeError, ezdxf.DXFError, ValueError) as error:
        raise DxfInputError(f"Cannot read DXF: {type(error).__name__}") from error

    selected = [doc.modelspace()]
    if include_paperspace:
        selected.extend(layout for layout in doc.layouts if layout.name.lower() != "model")
    frames = [
        CoordinateFrame(frame_id=f"cad:{layout.name}",
                        kind=CoordinateKind.CAD_UNIT, y_direction=YDirection.UP,
                        view_id=layout.name)
        for layout in selected
    ]
    header_code = int(doc.header.get("$INSUNITS", 0))
    calibration = UnitCalibration.from_dxf_insunits(header_code)
    drawing = DrawingIR(
        drawing_id=f"dxf-{digest[:16]}", source_sha256=digest, source_kind=SourceKind.DXF,
        parser_version=f"ezdxf-{ezdxf.__version__}-import-v0.1",
        frames=frames, calibration=calibration,
        calibration_frame_id=f"cad:{selected[0].name}" if calibration.metres_per_unit is not None else None,
    )
    result = DxfImportResult(
        drawing=drawing,
        layers=[DxfLayer(name=layer.dxf.name, hint=layer_hint(layer.dxf.name))
                for layer in doc.layers],
    )
    emitted = 0

    def report(code: str, handle: str | None, chain: tuple[str, ...], detail: str) -> None:
        result.issues.append(DxfIssue(
            code=code, source_handle=handle, block_path=chain, detail=detail[:220],
        ))

    def visit(
        entity: object, *, frame_id: str, view_id: str, parent: Matrix44,
        chain: tuple[str, ...], active_layer: str | None, blocks: tuple[str, ...],
    ) -> None:
        nonlocal emitted
        emitted += 1
        if emitted > max_entities:
            raise DxfInputError("DXF expansion entity budget exceeded")
        kind = entity.dxftype()  # type: ignore[attr-defined]
        handle = entity.dxf.get("handle")  # type: ignore[attr-defined]
        if not handle:
            report("MISSING_HANDLE", None, chain, "Original entity has no CAD handle")
            return
        layer = entity.dxf.get("layer", "0")  # type: ignore[attr-defined]
        if layer == "0" and active_layer is not None:
            layer = active_layer
        source = SourceReference(
            document_sha256=digest, source_kind=SourceKind.DXF,
            frame_id=frame_id, view_id=view_id, cad_handle=str(handle),
            block_path=chain,
        )
        # Full path distinguishes identical block definition handles in separate
        # INSERT instances. This is a synthetic ID, never a replacement CAD handle.
        entity_id = "|".join((view_id, *chain, str(handle), kind))

        def emit(geometry: GeometryPrimitive) -> None:
            result.drawing.entities.append(DrawingEntity(
                entity_id=entity_id, frame_id=frame_id, source=source,
                geometry=geometry, layer=layer, origin=EvidenceOrigin.CAD_NATIVE,
                type_candidate=kind, is_verified_semantics=False,
            ))

        try:
            if kind == "INSERT":
                name = str(entity.dxf.name)  # type: ignore[attr-defined]
                insert_matrix = entity.matrix44()  # type: ignore[attr-defined]
                transform = insert_matrix @ parent
                emit(GeometryPrimitive(
                    kind=PrimitiveKind.POINT,
                    points=(_point2(transform.transform((0, 0, 0))),),
                ))
                if name in blocks:
                    report("CYCLIC_BLOCK", handle, chain, f"Recursive block reference: {name}")
                    return
                if len(blocks) >= max_block_depth:
                    report("MAX_BLOCK_DEPTH", handle, chain, f"Depth limit at {name}")
                    return
                block = doc.blocks.get(name)
                if block is None:
                    report("MISSING_BLOCK", handle, chain, f"Missing block definition: {name}")
                    return
                instance_list = list(entity.multi_insert()) if entity.mcount > 1 else [entity]  # type: ignore[attr-defined]
                if len(instance_list) > max_entities - emitted + 1:
                    raise DxfInputError("MINSERT exceeds entity budget")
                for instance_index, instance in enumerate(instance_list):
                    instance_matrix = instance.matrix44() @ parent
                    step = f"{str(handle)}:{name}:instance{instance_index}"
                    next_chain = (*chain, step)
                    for child in block:
                        visit(child, frame_id=frame_id, view_id=view_id,
                              parent=instance_matrix, chain=next_chain,
                              active_layer=layer, blocks=(*blocks, name))
                    # Attached ATTRIB positions are already in the parent's
                    # coordinate system; do not apply the INSERT transform twice.
                    if instance_index == 0:
                        for attrib in entity.attribs:  # type: ignore[attr-defined]
                            visit(attrib, frame_id=frame_id, view_id=view_id,
                                  parent=parent, chain=next_chain,
                                  active_layer=layer, blocks=(*blocks, name))
                return

            if kind in {"LINE", "LWPOLYLINE", "ARC", "CIRCLE"}:
                if kind == "LINE":
                    endpoints = [entity.dxf.start, entity.dxf.end]  # type: ignore[attr-defined]
                    coords = [_point2(parent.transform(p)) for p in endpoints]
                    geom = GeometryPrimitive(kind=PrimitiveKind.SEGMENT,
                                             points=tuple(coords))
                else:
                    from ezdxf.path import make_path
                    cad_path = make_path(entity)
                    verts = list(islice(
                        cad_path.flattening(curve_flatten_distance, segments=8),
                        max_points_per_entity + 1,
                    ))
                    if len(verts) > max_points_per_entity:
                        report("TESSELLATION_LIMIT", handle, chain, "Curve point budget exceeded")
                        return
                    coords = [_point2(parent.transform(p)) for p in verts]
                    closed = bool(cad_path.is_closed or kind == "CIRCLE")
                    if len(coords) > 1 and coords[0] == coords[-1]:
                        coords.pop()
                    if len(coords) < (3 if closed else 2):
                        report("DEGENERATE_PATH", handle, chain, "No usable path points")
                        return
                    geom = GeometryPrimitive(
                        kind=PrimitiveKind.POLYGON if closed else PrimitiveKind.POLYLINE,
                        points=tuple(coords), closed=closed,
                    )
                    if kind in {"ARC", "CIRCLE"} or bool(getattr(entity, "has_arc", False)):
                        report("APPROXIMATED_CURVE", handle, chain,
                               f"Flattened in source units; max deviation target {curve_flatten_distance:g}")
                emit(geom)
                return

            if kind in {"TEXT", "MTEXT", "ATTRIB", "DIMENSION"}:
                if kind == "DIMENSION":
                    raw_point = entity.dxf.get("defpoint", (0, 0, 0))  # type: ignore[attr-defined]
                else:
                    raw_point = entity.dxf.get("insert", (0, 0, 0))  # type: ignore[attr-defined]
                    # TEXT/MTEXT use OCS placement; convert to WCS before block matrix.
                    raw_point = entity.ocs().to_wcs(raw_point)  # type: ignore[attr-defined]
                location = _point2(parent.transform(raw_point))
                emit(GeometryPrimitive(kind=PrimitiveKind.POINT, points=(location,)))
                if kind == "MTEXT":
                    text_value = str(entity.plain_text())  # type: ignore[attr-defined]
                elif kind == "DIMENSION":
                    text_value = str(entity.dxf.get("text", ""))  # type: ignore[attr-defined]
                else:
                    text_value = str(entity.dxf.get("text", ""))  # type: ignore[attr-defined]
                measured: float | None = None
                dimension_kind: int | None = None
                if kind == "DIMENSION":
                    dimension_kind = int(entity.dxf.get("dimtype", 0)) & 7  # type: ignore[attr-defined]
                    try:
                        candidate = entity.get_measurement()  # type: ignore[attr-defined]
                        if isinstance(candidate, (int, float)) and isfinite(float(candidate)):
                            measured = float(candidate)
                    except (TypeError, ValueError, ezdxf.DXFError):
                        report("DIMENSION_UNRESOLVED", handle, chain,
                               "No reliable raw dimension geometry measurement")
                result.annotations.append(DxfAnnotation(
                    entity_id=entity_id, source=source, kind=kind,
                    text=text_value, location=location,
                    raw_dimension_value=measured,
                    dimension_kind=dimension_kind,
                    note=("Raw DXF value only; style, override and block scaling unverified"
                          if kind == "DIMENSION" else None),
                ))
                return

            report("UNSUPPORTED_ENTITY", handle, chain, f"DXF type {kind} not parsed in v0.1")
        except DxfInputError:
            raise
        except (ValueError, TypeError, OverflowError, ezdxf.DXFError) as error:
            report("ENTITY_UNRESOLVED", handle, chain, f"{kind}: {type(error).__name__}: {str(error)[:100]}")

    for layout in selected:
        identity = Matrix44()
        for item in layout:
            visit(item, frame_id=f"cad:{layout.name}", view_id=layout.name,
                  parent=identity, chain=(), active_layer=None, blocks=())
    # Full Pydantic validation after expansion; no false architectural findings.
    result.drawing = DrawingIR.model_validate(result.drawing.model_dump())
    return result
