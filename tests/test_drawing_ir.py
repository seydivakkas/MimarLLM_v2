"""Pure synthetic IR validation and source traceability tests."""
import math

import pytest
from pydantic import ValidationError

from mimarllm.core.ir import (
    CoordinateFrame, CoordinateKind, DrawingEntity, DrawingIR,
    EvidenceOrigin, Finding, FindingStatus, GeometryPrimitive,
    MeasurementEvidence, PrimitiveKind, SourceKind, SourceReference,
    Transform2D, YDirection,
)
from mimarllm.core.units import UnitCalibration

HASH = "a" * 64
OTHER = "b" * 64


def frame():
    return CoordinateFrame(
        frame_id="cad:model", kind=CoordinateKind.CAD_UNIT,
        y_direction=YDirection.UP, view_id="modelspace",
    )


def entity(entity_id="e1", source_hash=HASH, frame_id="cad:model"):
    return DrawingEntity(
        entity_id=entity_id, frame_id=frame_id,
        geometry=GeometryPrimitive(kind=PrimitiveKind.SEGMENT, points=((0, 0), (1000, 0))),
        source=SourceReference(
            document_sha256=source_hash, source_kind=SourceKind.DXF,
            view_id="modelspace", frame_id=frame_id, cad_handle="F012",
            block_path=("door-block",),
        ),
        origin=EvidenceOrigin.CAD_NATIVE,
        layer="A-WALL",
    )


def drawing(**kwargs):
    data = dict(
        drawing_id="drawing-1", source_sha256=HASH, source_kind=SourceKind.DXF,
        parser_version="synthetic-v0.1", frames=[frame()], entities=[entity()],
    )
    data.update(kwargs)
    return DrawingIR(**data)


def test_ir_json_roundtrip_preserves_source_and_unconfirmed_scale():
    obj = drawing()
    assert obj.calibration.state.value == "UNKNOWN"
    loaded = DrawingIR.model_validate_json(obj.model_dump_json())
    assert loaded == obj
    assert loaded.entities[0].source.block_path == ("door-block",)
    assert loaded.entities[0].type_candidate == "UNCLASSIFIED"


def test_same_input_has_stable_serialisation():
    assert drawing().model_dump_json() == drawing().model_dump_json()


def test_duplicate_frame_or_entity_rejected():
    with pytest.raises(ValidationError, match="Duplicate coordinate frame"):
        drawing(frames=[frame(), frame()])
    with pytest.raises(ValidationError, match="Duplicate entity"):
        drawing(entities=[entity(), entity()])


def test_wrong_sha_or_document_kind_rejected():
    with pytest.raises(ValidationError, match="provenance"):
        drawing(entities=[entity(source_hash=OTHER)])
    pdf_ref = SourceReference(
        document_sha256=HASH, source_kind=SourceKind.PDF,
        frame_id="cad:model", page_index=0,
    )
    pdf_entity = entity().model_copy(update={"source": pdf_ref})
    with pytest.raises(ValidationError, match="provenance"):
        drawing(entities=[pdf_entity])


def test_wrong_source_frame_id_rejected():
    with pytest.raises(ValidationError, match="frames differ"):
        entity(frame_id="invalid")


def test_missing_frame_rejected():
    other_frame = CoordinateFrame(
        frame_id="cad:other", kind=CoordinateKind.CAD_UNIT,
        y_direction=YDirection.UP, view_id="modelspace",
    )
    with pytest.raises(ValidationError, match="missing coordinate"):
        drawing(frames=[other_frame])


def test_pdf_requires_page_and_native_frame():
    with pytest.raises(ValidationError):
        SourceReference(document_sha256=HASH, source_kind=SourceKind.PDF, frame_id="pdf:0")
    source = SourceReference(document_sha256=HASH, source_kind=SourceKind.PDF,
                             frame_id="pdf:0", page_index=0)
    pdf_frame = CoordinateFrame(frame_id="pdf:0", kind=CoordinateKind.PDF_POINT,
                                y_direction=YDirection.DOWN, page_index=0)
    pdf_entity = DrawingEntity(
        entity_id="p0", frame_id="pdf:0", source=source, origin=EvidenceOrigin.PDF_NATIVE,
        geometry=GeometryPrimitive(kind=PrimitiveKind.POINT, points=((10, 10),)),
    )
    obj = DrawingIR(
        drawing_id="p", source_sha256=HASH, source_kind=SourceKind.PDF,
        parser_version="synthetic", frames=[pdf_frame], entities=[pdf_entity],
    )
    assert obj.entities[0].source.page_index == 0


def test_no_pdf_pixels_claimed_as_metres():
    pixel_frame = CoordinateFrame(frame_id="pixel:0", kind=CoordinateKind.PIXEL,
                                  y_direction=YDirection.DOWN, page_index=0)
    pixel_ref = SourceReference(document_sha256=HASH, source_kind=SourceKind.IMAGE,
                                page_index=0, frame_id="pixel:0")
    item = DrawingEntity(entity_id="px1", frame_id="pixel:0",
        source=pixel_ref, origin=EvidenceOrigin.OCR_CANDIDATE,
        geometry=GeometryPrimitive(kind=PrimitiveKind.POINT, points=((100, 20),)))
    obj = DrawingIR(drawing_id="im", source_sha256=HASH,
                    source_kind=SourceKind.IMAGE, parser_version="test",
                    frames=[pixel_frame], entities=[item])
    assert obj.calibration.metres_per_unit is None


def test_transform_roundtrip_translation_scale_y_flip():
    to_pdf = Transform2D(
        source_frame_id="cad:model", target_frame_id="pdf:0",
        coefficients=(0.5, 0, 10, 0, -0.5, 200),
    )
    point = (123.75, 82.5)
    result = to_pdf.inverse().apply(to_pdf.apply(point))
    assert result == pytest.approx(point)
    assert to_pdf.apply((0, 0)) == pytest.approx((10, 200))


def test_rotated_45_degree_transform_roundtrip():
    angle = math.radians(45)
    c, s = math.cos(angle), math.sin(angle)
    t = Transform2D(source_frame_id="a", target_frame_id="b",
                    coefficients=(c, -s, 2.4, s, c, -1.8))
    for xy in ((0, 0), (250, 150), (-120, 8)):
        assert t.inverse().apply(t.apply(xy)) == pytest.approx(xy, abs=1e-10)


def test_singular_and_nonfinite_transforms_rejected():
    with pytest.raises(ValidationError):
        Transform2D(source_frame_id="a", target_frame_id="b",
                    coefficients=(1, 2, 0, 2, 4, 0))
    with pytest.raises(ValidationError):
        Transform2D(source_frame_id="a", target_frame_id="b",
                    coefficients=(float("nan"), 0, 0, 0, 1, 0))


def test_unknown_transform_frames_rejected():
    t = Transform2D(source_frame_id="cad:model", target_frame_id="pdf:0",
                    coefficients=(1, 0, 0, 0, 1, 0))
    with pytest.raises(ValidationError, match="Transform references unknown frame"):
        drawing(transforms=[t])


def test_degenerate_segment_kept_as_an_observation():
    primitive = GeometryPrimitive(kind=PrimitiveKind.SEGMENT, points=((1, 1), (1, 1)))
    assert primitive.points[0] == primitive.points[1]


def test_invalid_primitive_or_nan_rejected():
    with pytest.raises(ValidationError):
        GeometryPrimitive(kind=PrimitiveKind.POLYGON, points=((0, 0), (1, 1), (0, 1)))
    with pytest.raises(ValidationError):
        GeometryPrimitive(kind=PrimitiveKind.SEGMENT, points=((0, 0), (math.inf, 1)))


def test_vlm_candidate_cannot_be_verified_by_claim_only():
    with pytest.raises(ValidationError):
        entity().model_copy(update={"origin": EvidenceOrigin.VLM_CANDIDATE,
                                   "is_verified_semantics": True}).model_validate(
                                       entity().model_dump() | {
                                           "origin": "VLM_CANDIDATE",
                                           "is_verified_semantics": True
                                       })


def test_physical_measurement_needs_confirmed_scale():
    measurement = MeasurementEvidence(
        evidence_id="m1", entity_ids=("e1",), source_value=1000, quantity="length",
        source_frame_id="cad:model", method_id="segment_length",
        tolerance_source_units=0.01, physical_value=1.0, physical_unit="m",
    )
    with pytest.raises(ValidationError, match="confirmed calibration"):
        drawing(measurements=[measurement])
    verified = UnitCalibration.from_dxf_insunits(4, user_confirmed=True)
    obj = drawing(measurements=[measurement], calibration=verified)
    assert obj.measurements[0].physical_value == 1.0


def test_measurement_cross_frame_or_unknown_entity_rejected():
    m = MeasurementEvidence(evidence_id="m1", entity_ids=("missing",),
        source_value=1, quantity="length", source_frame_id="cad:model",
        method_id="length", tolerance_source_units=0)
    with pytest.raises(ValidationError, match="unknown entity"):
        drawing(measurements=[m])
    with pytest.raises(ValidationError, match="Measurement frame missing"):
        drawing(measurements=[m.model_copy(update={"source_frame_id": "bad"})])


def test_definitive_finding_must_reference_evidence():
    with pytest.raises(ValidationError, match="needs entity and evidence"):
        Finding(finding_id="f1", check_id="c", check_version="1", status="PASS", reason_code="ok")
    with pytest.raises(ValidationError, match="Legal compliance certification"):
        Finding(finding_id="f1", check_id="c", check_version="1",
                status="REVIEW_REQUIRED", reason_code="pending",
                legal_compliance_certified=True)
    flagged = Finding(finding_id="f1", check_id="geometry.gap",
        check_version="0.1", status=FindingStatus.REVIEW_REQUIRED,
        entity_ids=("e1",), reason_code="GAP")
    assert drawing(findings=[flagged]).findings[0].reason_code == "GAP"


def test_finding_unknown_evidence_rejected():
    flagged = Finding(finding_id="f1", check_id="c", check_version="0.1",
                      status=FindingStatus.FAIL, entity_ids=("e1",),
                      evidence_ids=("missing",), reason_code="MISSING")
    with pytest.raises(ValidationError, match="unknown measurement evidence"):
        drawing(findings=[flagged])
