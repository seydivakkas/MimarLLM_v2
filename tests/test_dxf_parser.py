"""Sentetik DXF -> DrawingIR integration tests; no licensed/customer drawings."""
from __future__ import annotations

import math

import ezdxf
import pytest

from mimarllm.core.ir import PrimitiveKind
from mimarllm.core.units import CalibrationError, CalibrationState
from mimarllm.importers.dxf import DxfInputError, parse_dxf
from mimarllm.importers.layers import layer_hint


def _save(tmp_path, doc, name="test.dxf"):
    filename = tmp_path / name
    doc.saveas(filename)
    return filename


def test_native_geometry_units_handles_and_annotations(tmp_path):
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 4  # mm, not verified
    doc.layers.new("A-DUVAR")
    msp = doc.modelspace()
    line = msp.add_line((0, 0), (2500, 0), dxfattribs={"layer": "A-DUVAR"})
    msp.add_lwpolyline([(0, 0), (10, 0), (10, 6)], close=True)
    msp.add_arc(center=(20, 20), radius=4, start_angle=0, end_angle=90)
    msp.add_circle(center=(40, 40), radius=3)
    text = msp.add_text("KAPI", dxfattribs={"insert": (5, 5), "height": 2})
    msp.add_mtext("ODA 1", dxfattribs={"insert": (6, 7)})
    dim = msp.add_linear_dim(base=(0, -5), p1=(0, 0), p2=(2500, 0))
    dim.render()
    result = parse_dxf(_save(tmp_path, doc))
    ir = result.drawing
    assert len(ir.source_sha256) == 64
    assert ir.calibration.state is CalibrationState.INFERRED
    assert ir.calibration.metres_per_unit == pytest.approx(0.001)
    assert ir.calibration_frame_id == "cad:Model"
    with pytest.raises(CalibrationError):
        ir.calibration.length_metres(2500)
    assert len(ir.frames) == 1
    assert len(ir.entities) == 7
    assert {"LINE", "LWPOLYLINE", "ARC", "CIRCLE", "TEXT", "MTEXT", "DIMENSION"} == {
        e.type_candidate for e in ir.entities
    }
    assert any(e.source.cad_handle == line.dxf.handle for e in ir.entities)
    assert any(e.source.cad_handle == text.dxf.handle for e in ir.entities)
    assert any(e.type_candidate == "CIRCLE" and e.geometry.kind is PrimitiveKind.POLYGON
               for e in ir.entities)
    assert any(e.type_candidate == "ARC" and e.geometry.kind is PrimitiveKind.POLYLINE
               for e in ir.entities)
    assert {a.kind for a in result.annotations} == {"TEXT", "MTEXT", "DIMENSION"}
    assert any(a.kind == "DIMENSION" and a.raw_dimension_value == pytest.approx(2500)
               for a in result.annotations)
    assert not ir.findings
    assert any(layer.name == "A-DUVAR" and layer.hint == "WALL_CANDIDATE"
               for layer in result.layers)
    assert all(not e.is_verified_semantics for e in ir.entities)


def test_block_nested_insert_rotation_and_source_provenance(tmp_path):
    doc = ezdxf.new("R2013")
    base = doc.blocks.new("INNER")
    source_line = base.add_line((0, 0), (4, 0))
    outer = doc.blocks.new("OUTER")
    inner_insert = outer.add_blockref("INNER", (10, 0), dxfattribs={"rotation": 90})
    top_insert = doc.modelspace().add_blockref("OUTER", (100, 100), dxfattribs={"rotation": 90})
    result = parse_dxf(_save(tmp_path, doc))
    lines = [e for e in result.drawing.entities if e.type_candidate == "LINE"]
    assert len(lines) == 1
    leaf = lines[0]
    assert leaf.source.cad_handle == source_line.dxf.handle
    assert len(leaf.source.block_path) == 2
    assert top_insert.dxf.handle in leaf.source.block_path[0]
    assert inner_insert.dxf.handle in leaf.source.block_path[1]
    assert leaf.geometry.points[0] == pytest.approx((100, 110))
    assert leaf.geometry.points[1] == pytest.approx((96, 110))
    assert sum(e.type_candidate == "INSERT" for e in result.drawing.entities) == 2


def test_multiple_insert_instances_unique_ids(tmp_path):
    doc = ezdxf.new("R2013")
    block = doc.blocks.new("DOORS")
    leaf = block.add_line((0, 0), (3, 0))
    instance = doc.modelspace().add_blockref("DOORS", (5, 6))
    instance.grid(size=(1, 3), spacing=(0, 10))
    r = parse_dxf(_save(tmp_path, doc))
    sub = [e for e in r.drawing.entities if e.type_candidate == "LINE"]
    assert len(sub) == 3
    assert len({e.entity_id for e in sub}) == 3
    assert sorted(e.geometry.points[0][0] for e in sub) == pytest.approx([5, 15, 25])
    assert all(e.source.cad_handle == leaf.dxf.handle for e in sub)


def test_same_block_two_insert_instances_keep_independent_paths(tmp_path):
    doc = ezdxf.new("R2013")
    b = doc.blocks.new("B")
    source = b.add_line((0, 0), (1, 0))
    doc.modelspace().add_blockref("B", (1, 1))
    doc.modelspace().add_blockref("B", (9, 9))
    r = parse_dxf(_save(tmp_path, doc))
    leaves = [e for e in r.drawing.entities if e.type_candidate == "LINE"]
    assert len(leaves) == 2
    assert len({e.entity_id for e in leaves}) == 2
    assert all(e.source.cad_handle == source.dxf.handle for e in leaves)


def test_bulge_polyline_tessellated_with_original_source_handle(tmp_path):
    doc = ezdxf.new("R2013")
    pl = doc.modelspace().add_lwpolyline(
        [(0, 0, 0, 0, 1), (10, 0, 0, 0, 0)], format="xyseb"
    )
    r = parse_dxf(_save(tmp_path, doc), curve_flatten_distance=0.05)
    shape = next(e for e in r.drawing.entities if e.type_candidate == "LWPOLYLINE")
    assert len(shape.geometry.points) > 2
    assert shape.source.cad_handle == pl.dxf.handle
    assert any(i.code == "APPROXIMATED_CURVE" for i in r.issues)


def test_unknown_dxf_units_no_physical_scale(tmp_path):
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 0
    doc.modelspace().add_line((0, 0), (100, 0))
    r = parse_dxf(_save(tmp_path, doc))
    assert r.drawing.calibration.state is CalibrationState.UNKNOWN
    assert r.drawing.calibration_frame_id is None
    assert not r.drawing.measurements


def test_bad_file_signature_rejected(tmp_path):
    file = tmp_path / "bad.dxf"
    file.write_text("THIS IS NOT DXF", encoding="utf-8")
    with pytest.raises(DxfInputError):
        parse_dxf(file)


def test_extension_guard_and_size_guard(tmp_path):
    doc = ezdxf.new("R2013")
    file = _save(tmp_path, doc)
    with pytest.raises(DxfInputError, match="size"):
        parse_dxf(file, max_file_bytes=10)
    other = tmp_path / "plan.txt"
    other.write_text("hello")
    with pytest.raises(DxfInputError, match=r"\.dxf"):
        parse_dxf(other)


def test_expansion_entity_budget_rejected(tmp_path):
    doc = ezdxf.new("R2013")
    for i in range(10):
        doc.modelspace().add_line((i, 0), (i, 1))
    with pytest.raises(DxfInputError, match="entity budget"):
        parse_dxf(_save(tmp_path, doc), max_entities=5)


def test_elevated_3d_entity_emits_issue_not_fake_2d(tmp_path):
    doc = ezdxf.new("R2013")
    doc.modelspace().add_line((0, 0, 5), (10, 0, 5))
    r = parse_dxf(_save(tmp_path, doc))
    assert not r.drawing.entities
    assert any(i.code == "ENTITY_UNRESOLVED" for i in r.issues)


def test_paperspace_opt_in_and_separate_frame(tmp_path):
    doc = ezdxf.new("R2013")
    doc.modelspace().add_line((0, 0), (1, 0))
    paper = doc.layout()
    paper.add_line((100, 100), (120, 120))
    file = _save(tmp_path, doc)
    base = parse_dxf(file)
    assert len(base.drawing.frames) == 1
    all_pages = parse_dxf(file, include_paperspace=True)
    assert len(all_pages.drawing.frames) >= 2
    assert all(e.source.view_id in {f.view_id for f in all_pages.drawing.frames}
               for e in all_pages.drawing.entities)


@pytest.mark.parametrize("name,expected", [
    ("A-WALL", "WALL_CANDIDATE"),
    ("A-DUVAR", "WALL_CANDIDATE"),
    ("KAPI_01", "DOOR_CANDIDATE"),
    ("pencere", "WINDOW_CANDIDATE"),
    ("MAHAL", "ROOM_LABEL_CANDIDATE"),
    ("Olcu", "DIMENSION_CANDIDATE"),
    ("A-WALL-DOOR", None),
    ("GEOMETRY", None),
])
def test_layer_hints_are_only_candidates(name, expected):
    assert layer_hint(name) == expected


def test_nonuniform_block_scale_curve_is_approximate_and_source_kept(tmp_path):
    doc = ezdxf.new("R2013")
    b = doc.blocks.new("CURVE")
    circle = b.add_circle((0, 0), radius=10)
    doc.modelspace().add_blockref(
        "CURVE", (100, 20), dxfattribs={"xscale": 20, "yscale": 2}
    )
    r = parse_dxf(_save(tmp_path, doc), curve_flatten_distance=0.05)
    shapes = [e for e in r.drawing.entities if e.type_candidate == "CIRCLE"]
    assert len(shapes) == 1
    assert len(shapes[0].geometry.points) > 16
    xs = [p[0] for p in shapes[0].geometry.points]
    ys = [p[1] for p in shapes[0].geometry.points]
    assert max(xs) - min(xs) == pytest.approx(400, abs=1)
    assert max(ys) - min(ys) == pytest.approx(40, abs=1)
    assert shapes[0].source.cad_handle == circle.dxf.handle
    assert any(i.code == "APPROXIMATED_CURVE" for i in r.issues)


def test_massive_minsert_is_rejected_before_materializing_instances(tmp_path):
    doc = ezdxf.new("R2013")
    b = doc.blocks.new("CELL")
    b.add_line((0, 0), (1, 0))
    block_ref = doc.modelspace().add_blockref("CELL", (0, 0))
    block_ref.grid(size=(100, 100), spacing=(2, 2))
    with pytest.raises(DxfInputError, match="MINSERT exceeds"):
        parse_dxf(_save(tmp_path, doc), max_entities=100)


def test_tessellation_budget_is_explicitly_reported(tmp_path):
    doc = ezdxf.new("R2013")
    doc.modelspace().add_circle((0, 0), 100)
    r = parse_dxf(
        _save(tmp_path, doc),
        curve_flatten_distance=0.00001,
        max_points_per_entity=8,
    )
    assert any(i.code == "TESSELLATION_LIMIT" for i in r.issues)
    assert not r.drawing.entities
