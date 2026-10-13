"""Synthetic RuleEngine tests: no law can be 'approved' from user-supplied flags."""
from __future__ import annotations

import math
from datetime import date

import ezdxf
import pytest
from pydantic import ValidationError

from mimarllm.core.ir import DrawingIR, MeasurementEvidence
from mimarllm.core.units import UnitCalibration
from mimarllm.geometry.spatial import analyze_geometry, assess_area
from mimarllm.geometry.topology import (
    EXTERIOR_ID, PassageKind, PassageReview, SpaceKind, SpaceReview,
)
from mimarllm.importers.dxf import parse_dxf
from mimarllm.rules.base import (
    ApplicabilityReview, ApplicabilityStatus, Comparison, LegalSourceLocator,
    MetricKind, RuleDefinition, RuleDomain, RuleRequest, RuleResult, RuleStatus,
)
from mimarllm.rules.engine import RuleEngine, RuleInputError


def scenario_rule(
    metric=MetricKind.SEGMENT_LENGTH_M,
    *, threshold=1.2, operator=Comparison.GE, rule_id="synthetic.min",
):
    if metric == MetricKind.REVIEWED_TOPOLOGY_PATH:
        threshold, operator = None, None
    return RuleDefinition(
        rule_id=rule_id, version="1.0", domain=RuleDomain.TECHNICAL,
        metric=metric, description="Synthetic, NOT Turkish architectural law",
        threshold=threshold, operator=operator,
    )


def _draw(tmp_path, *, two=False):
    doc = ezdxf.new("R2013")
    doc.header["$INSUNITS"] = 6
    m = doc.modelspace()
    # This 2-metre segment is independent of the two-room wall geometry.
    first = m.add_line((30, 20), (32, 20))
    boundary = [
        ((0, 0), (5, 0)), ((5, 0), (5, 6)),
        ((5, 6), (0, 6)), ((0, 6), (0, 0)),
    ]
    if two:
        boundary += [
            ((5, 0), (10, 0)), ((10, 0), (10, 6)),
            ((10, 6), (5, 6)),
        ]
        block = doc.blocks.new("REVIEWED_OPENING_MARKER")
        m.add_blockref("REVIEWED_OPENING_MARKER", (5, 3))
    refs = [m.add_line(a, b) for a, b in boundary]
    file = tmp_path / ("two_rooms.dxf" if two else "one_room.dxf")
    doc.saveas(file)
    drawing = parse_dxf(file).drawing
    assert drawing.calibration.state.value == "INFERRED"
    ids = {entity.source.cad_handle: entity.entity_id for entity in drawing.entities}
    confirmed = drawing.model_copy(update={
        "calibration": UnitCalibration.from_dxf_insunits(6, user_confirmed=True)
    })
    confirmed = DrawingIR.model_validate(confirmed.model_dump())
    measurement = MeasurementEvidence(
        evidence_id="test-length",
        entity_ids=(ids[first.dxf.handle],),
        source_frame_id="cad:Model",
        source_value=2.0, quantity="length", method_id="segment_length",
        tolerance_source_units=0.0, physical_value=2.0, physical_unit="m",
    )
    confirmed.measurements.append(measurement)
    confirmed = DrawingIR.model_validate(confirmed.model_dump())
    ids_for_boundary = [ids[x.dxf.handle] for x in refs]
    return drawing, confirmed, ids_for_boundary


def _regulatory():
    return RuleDefinition(
        rule_id="tr.imar.synthetic.placeholder", version="draft",
        domain=RuleDomain.REGULATORY, metric=MetricKind.SEGMENT_LENGTH_M,
        description="DO NOT ACTIVATE: unverified source placeholder",
        operator=Comparison.GE, threshold=1.2,
        legal_source=LegalSourceLocator(
            document_sha256="f" * 64, page_index=2,
            regulation_id="example-law-not-real",
            article_id="unverified-article", clause_id="placeholder",
            effective_from=date(2026, 1, 1),
        ),
    )


def test_technical_length_compliant_and_traceable(tmp_path):
    _, drawing, ids = _draw(tmp_path)
    result = RuleEngine([scenario_rule()]).evaluate(
        "synthetic.min", RuleRequest(drawing=drawing,
                                     measurement_evidence_id="test-length"),
    )
    assert result.status is RuleStatus.COMPLIANT
    assert result.domain is RuleDomain.TECHNICAL
    assert result.claim_scope == "TECHNICAL_ONLY_NOT_LEGAL"
    assert not result.legal_compliance_certified
    assert result.frame_id == "cad:Model"
    assert result.entity_ids == drawing.measurements[0].entity_ids
    assert result.evidence_ids == ("test-length",)
    assert result.observed_value == pytest.approx(2)
    assert result.threshold == pytest.approx(1.2)
    assert result.unit == "m"
    assert result.reason_code == "TECHNICAL_COMPARISON_TRUE"


def test_technical_non_compliant_does_not_mean_building_illegal(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    rule = scenario_rule(threshold=2.5)
    out = RuleEngine([rule]).evaluate(rule.rule_id,
                                     RuleRequest(drawing=drawing,
                                                 measurement_evidence_id="test-length"))
    assert out.status is RuleStatus.NON_COMPLIANT
    assert out.reason_code == "TECHNICAL_COMPARISON_FALSE"
    assert not out.legal_compliance_certified


@pytest.mark.parametrize("operator,threshold,expected", [
    (Comparison.GE, 2, RuleStatus.COMPLIANT),
    (Comparison.GT, 2, RuleStatus.NON_COMPLIANT),
    (Comparison.LE, 2, RuleStatus.COMPLIANT),
    (Comparison.LT, 2, RuleStatus.NON_COMPLIANT),
    (Comparison.EQ, 2, RuleStatus.COMPLIANT),
    (Comparison.EQ, 2.5, RuleStatus.NON_COMPLIANT),
])
def test_declarative_operator_boundary_conditions(tmp_path, operator, threshold, expected):
    _, drawing, _ = _draw(tmp_path)
    r = scenario_rule(operator=operator, threshold=threshold)
    out = RuleEngine([r]).evaluate(r.rule_id, RuleRequest(
        drawing=drawing, measurement_evidence_id="test-length",
    ))
    assert out.status == expected


def test_no_measurement_and_unknown_calibration_are_not_a_fail(tmp_path):
    inferred, confirmed, _ = _draw(tmp_path)
    engine = RuleEngine([scenario_rule()])
    missing = engine.evaluate("synthetic.min", RuleRequest(drawing=confirmed))
    assert missing.status is RuleStatus.INSUFFICIENT_EVIDENCE
    assert missing.reason_code == "MEASUREMENT_MISSING"
    # Even if an independent measurement metadata is provided, no approved
    # scale may be assumed from INSUNITS header alone.
    inferred.measurements.append(confirmed.measurements[0].model_copy(
        update={"physical_value": None, "physical_unit": None},
    ))
    out = engine.evaluate("synthetic.min", RuleRequest(
        drawing=inferred, measurement_evidence_id="test-length"
    ))
    assert out.status is RuleStatus.INSUFFICIENT_EVIDENCE
    assert out.reason_code == "CONFIRMED_SCALE_OR_SI_MISSING"


def test_mathematical_segment_mismatch_cannot_pass(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    altered = drawing.measurements[0].model_copy(update={
        "source_value": 10.0, "physical_value": 10.0,
    })
    drawing.measurements[0] = altered
    # IR is self-consistent wrt scale but SOURCE geometric length still 2m.
    drawing = DrawingIR.model_validate(drawing.model_dump())
    out = RuleEngine([scenario_rule()]).evaluate(
        "synthetic.min", RuleRequest(
            drawing=drawing, measurement_evidence_id="test-length")
    )
    assert out.status is RuleStatus.REVIEW_REQUIRED
    assert out.reason_code == "SOURCE_SEGMENT_LENGTH_MISMATCH"


def test_tolerance_guard_band_prevents_false_threshold_pass(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    drawing.measurements[0] = drawing.measurements[0].model_copy(update={
        "tolerance_source_units": 0.05,
    })
    r = scenario_rule(threshold=1.98)
    out = RuleEngine([r]).evaluate(r.rule_id, RuleRequest(
        drawing=drawing, measurement_evidence_id="test-length"))
    assert out.status is RuleStatus.REVIEW_REQUIRED
    assert out.reason_code == "MEASUREMENT_INTERVAL_OVERLAPS_THRESHOLD"
    assert out.calculated_tolerance == pytest.approx(.05)


def test_unknown_rule_duplicate_registry_and_invalid_operators(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    rule = scenario_rule()
    with pytest.raises(RuleInputError, match="Duplicate"):
        RuleEngine([rule, rule])
    with pytest.raises(RuleInputError, match="Unknown"):
        RuleEngine([rule]).evaluate("wrong-id", RuleRequest(drawing=drawing))
    with pytest.raises(ValidationError):
        scenario_rule(operator="__import__('os').system('whoami')")
    with pytest.raises(ValidationError):
        scenario_rule(threshold=math.inf)
    with pytest.raises(ValidationError):
        RuleDefinition(
            rule_id="bad", version="1", domain="TECHNICAL",
            metric="REVIEWED_TOPOLOGY_PATH", description="bad",
            threshold=2, operator=">=",
        )


def test_source_sha_mismatch_fails_model_validation_as_error(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    request = RuleRequest(
        drawing=drawing, measurement_evidence_id="test-length"
    )
    # A caller might mutate a once-valid model after validation.
    drawing.source_sha256 = "0" * 64
    out = RuleEngine([scenario_rule()]).evaluate(
        "synthetic.min", request,
    )
    assert out.status is RuleStatus.ERROR
    assert out.reason_code == "INPUT_MODEL_VALIDATION_FAILED"


def test_scope_not_applicable_requires_review_and_source(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    eid = drawing.entities[0].entity_id
    exclusion = ApplicabilityReview(
        status=ApplicabilityStatus.NOT_APPLICABLE,
        reviewed_by="synthetic-reviewer", reason="Outside a synthetic check",
        drawing_sha256=drawing.source_sha256,
        supporting_entity_ids=(eid,),
    )
    out = RuleEngine([scenario_rule()]).evaluate(
        "synthetic.min", RuleRequest(drawing=drawing, applicability=exclusion))
    assert out.status is RuleStatus.NOT_APPLICABLE
    assert out.entity_ids == (eid,)
    assert out.reason_code == "TECHNICAL_SCOPE_EXCLUDED_BY_REVIEW"
    assert not out.legal_compliance_certified


def test_forged_scope_source_is_not_accepted(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    exclusion = ApplicabilityReview(
        status=ApplicabilityStatus.NOT_APPLICABLE,
        reviewed_by="synthetic", reason="test",
        drawing_sha256="b" * 64, supporting_entity_ids=("fake",),
    )
    out = RuleEngine([scenario_rule()]).evaluate(
        "synthetic.min", RuleRequest(drawing=drawing, applicability=exclusion)
    )
    assert out.status is RuleStatus.REVIEW_REQUIRED
    assert out.reason_code == "SCOPE_EXCLUSION_SOURCE_UNVERIFIED"
    with pytest.raises(ValidationError):
        ApplicabilityReview(status=ApplicabilityStatus.NOT_APPLICABLE)
    unknown = RuleEngine([scenario_rule()]).evaluate(
        "synthetic.min", RuleRequest(
            drawing=drawing, applicability=ApplicabilityReview()
        )
    )
    assert unknown.status is RuleStatus.INSUFFICIENT_EVIDENCE


def test_regulatory_locator_never_unlocks_without_official_etl(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    rule = _regulatory()
    # Even syntactically complete citation + correct measurement is NOT
    # independent official Gazete PDF/change-chain applicability validation.
    out = RuleEngine([rule]).evaluate(
        rule.rule_id, RuleRequest(drawing=drawing,
                                  measurement_evidence_id="test-length"),
    )
    assert out.status is RuleStatus.INSUFFICIENT_EVIDENCE
    assert out.reason_code == "REGULATORY_SOURCE_AND_APPLICABILITY_UNVERIFIED"
    assert out.legal_source.document_sha256 == "f" * 64
    assert not out.legal_compliance_certified


def test_regulatory_cannot_be_made_not_applicable_by_user_flag(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    rule = _regulatory()
    applicability = ApplicabilityReview(
        status=ApplicabilityStatus.NOT_APPLICABLE,
        reviewed_by="user", reason="claim",
        drawing_sha256=drawing.source_sha256,
        supporting_entity_ids=(drawing.entities[0].entity_id,),
    )
    out = RuleEngine([rule]).evaluate(
        rule.rule_id, RuleRequest(drawing=drawing, applicability=applicability),
    )
    assert out.status is RuleStatus.INSUFFICIENT_EVIDENCE
    with pytest.raises(ValidationError):
        RuleResult(
            rule_id=rule.rule_id, rule_version=rule.version,
            status=RuleStatus.COMPLIANT, domain=RuleDomain.REGULATORY,
            metric=rule.metric, drawing_sha256=drawing.source_sha256,
            reason_code="fake", legal_compliance_certified=True,
        )


def test_technical_rule_cannot_pretend_to_cite_statute():
    with pytest.raises(ValidationError):
        scenario_rule().model_copy(update={"legal_source": _regulatory().legal_source
                                         }).model_validate(
            scenario_rule().model_dump() | {
                "legal_source": _regulatory().legal_source.model_dump(mode="json"),
            }
        )
    with pytest.raises(ValidationError):
        RuleDefinition(
            rule_id="fake", version="1", domain=RuleDomain.REGULATORY,
            metric=MetricKind.SEGMENT_LENGTH_M, description="fake",
            operator=Comparison.GE, threshold=1.2,
        )


def test_reviewed_interior_area_technical_rule_and_source_trace(tmp_path):
    _, drawing, selected = _draw(tmp_path)
    a = assess_area(
        drawing, "cad:Model", selected,
        boundary_role="INTERIOR_ROOM", reviewer_id="synthetic-reviewer",
    )
    assert a.physical_area_m2 == pytest.approx(30)
    rule = scenario_rule(metric=MetricKind.REVIEWED_INTERIOR_AREA_M2,
                         threshold=25, rule_id="synthetic.area")
    out = RuleEngine([rule]).evaluate(rule.rule_id, RuleRequest(
        drawing=drawing, area_assessment=a,
    ))
    assert out.status is RuleStatus.COMPLIANT
    assert out.observed_value == pytest.approx(30)
    assert out.unit == "m2"
    assert out.entity_ids == tuple(selected)
    assert out.drawing_sha256 == drawing.source_sha256


def test_unapproved_area_cannot_generate_m2_rule_verdict(tmp_path):
    inferred, _, selected = _draw(tmp_path)
    a = assess_area(
        inferred, "cad:Model", selected,
        boundary_role="INTERIOR_ROOM", reviewer_id="synthetic-reviewer",
    )
    rule = scenario_rule(metric=MetricKind.REVIEWED_INTERIOR_AREA_M2,
                         threshold=20, rule_id="synthetic.area")
    out = RuleEngine([rule]).evaluate(rule.rule_id, RuleRequest(
        drawing=inferred, area_assessment=a,
    ))
    assert out.status is RuleStatus.INSUFFICIENT_EVIDENCE


def test_forged_area_with_correct_hash_is_refused(tmp_path):
    _, drawing, selected = _draw(tmp_path)
    a = assess_area(
        drawing, "cad:Model", selected,
        boundary_role="INTERIOR_ROOM", reviewer_id="synthetic",
    )
    forged = a.model_copy(update={
        "physical_area_m2": 500.0,
    })
    r = scenario_rule(metric=MetricKind.REVIEWED_INTERIOR_AREA_M2,
                      threshold=100, rule_id="synthetic.area")
    out = RuleEngine([r]).evaluate(r.rule_id, RuleRequest(
        drawing=drawing, area_assessment=forged,
    ))
    assert out.status is RuleStatus.REVIEW_REQUIRED
    assert out.reason_code == "AREA_VALUE_DISAGREES_WITH_SOURCE"


def test_area_role_mismatch_not_reported_as_numeric(tmp_path):
    _, drawing, selected = _draw(tmp_path)
    a = assess_area(drawing, "cad:Model", selected,
                    boundary_role="INTERIOR_ROOM", reviewer_id="synthetic")
    rule = scenario_rule(metric=MetricKind.REVIEWED_FOOTPRINT_M2,
                         threshold=20, rule_id="synthetic.footprint")
    out = RuleEngine([rule]).evaluate(rule.rule_id, RuleRequest(
        drawing=drawing, area_assessment=a,
    ))
    assert out.status is RuleStatus.REVIEW_REQUIRED
    assert out.reason_code == "AREA_SOURCE_OR_ROLE_MISMATCH"


def test_reviewed_two_room_topological_path_is_technical_not_egress(tmp_path):
    _, drawing, _ = _draw(tmp_path, two=True)
    geometry = analyze_geometry(drawing, "cad:Model")
    assert len(geometry.faces) == 2
    spaces = [
        SpaceReview(
            space_id="room" if index == 0 else "corridor",
            face_id=face.face_id, kind=SpaceKind.ROOM if index == 0 else SpaceKind.CORRIDOR,
            reviewer_id="synthetic",
        )
        for index, face in enumerate(geometry.faces)
    ]
    marker = next(e.entity_id for e in drawing.entities if e.type_candidate == "INSERT")
    passage = PassageReview(
        passage_id="reviewed-door",
        from_space_id="room", to_space_id="corridor",
        kind=PassageKind.DOOR, reviewer_id="synthetic",
        supporting_entity_ids=(marker,), path_endpoints=((4, 3), (6, 3)),
    )
    rule = scenario_rule(metric=MetricKind.REVIEWED_TOPOLOGY_PATH,
                         rule_id="synthetic.path")
    request = RuleRequest(
        drawing=drawing, geometry_analysis=geometry,
        spaces=spaces, passages=[passage],
        path_from_space_id="room", path_to_space_id="corridor",
    )
    out = RuleEngine([rule]).evaluate(rule.rule_id, request)
    assert out.status is RuleStatus.COMPLIANT
    assert out.reason_code.endswith("NOT_WALKING_DISTANCE")
    assert out.observed_value is None
    assert out.evidence_ids == ("reviewed-door",)
    assert out.entity_ids == (marker,)
    assert out.threshold is None and out.unit is None

    # Partial graph without passage does not prove there is no real door.
    request.passages = []
    absent = RuleEngine([rule]).evaluate(rule.rule_id, request)
    assert absent.status is RuleStatus.INSUFFICIENT_EVIDENCE
    assert absent.reason_code.startswith("NO_REVIEWED_TOPOLOGICAL_PATH")


def test_forged_topology_face_cannot_pass_technical_path(tmp_path):
    _, drawing, _ = _draw(tmp_path, two=True)
    geometry = analyze_geometry(drawing, "cad:Model")
    spaces = [
        SpaceReview(
            space_id=f"s{i}", face_id=f.face_id,
            kind=SpaceKind.ROOM, reviewer_id="review",
        ) for i, f in enumerate(geometry.faces)
    ]
    faces = list(geometry.faces)
    faces[0] = faces[0].model_copy(
        update={"exterior": tuple((x + .2, y) for x, y in faces[0].exterior)}
    )
    fake = geometry.model_copy(update={"faces": faces})
    marker = next(e.entity_id for e in drawing.entities if e.type_candidate == "INSERT")
    passage = PassageReview(
        passage_id="fake", from_space_id="s0", to_space_id="s1",
        kind=PassageKind.DOOR, reviewer_id="review",
        supporting_entity_ids=(marker,), path_endpoints=((4, 3), (6, 3)),
    )
    rule = scenario_rule(metric=MetricKind.REVIEWED_TOPOLOGY_PATH,
                         rule_id="synthetic.path")
    result = RuleEngine([rule]).evaluate(rule.rule_id, RuleRequest(
        drawing=drawing, geometry_analysis=fake,
        spaces=spaces, passages=[passage],
        path_from_space_id="s0", path_to_space_id="s1",
    ))
    assert result.status is RuleStatus.REVIEW_REQUIRED
    assert result.reason_code == "SOURCE_RECOMPUTATION_REJECTED"


def test_json_roundtrip_determinism_and_registry_limit(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    r = scenario_rule()
    engine = RuleEngine([r])
    request = RuleRequest(drawing=drawing, measurement_evidence_id="test-length")
    first = engine.evaluate(r.rule_id, request)
    second = engine.evaluate(r.rule_id, request)
    assert first.model_dump_json() == second.model_dump_json()
    assert RuleResult.model_validate_json(first.model_dump_json()) == first
    with pytest.raises(RuleInputError, match="registry size"):
        RuleEngine([r], max_rules=0)


def test_result_schema_rejects_forged_technical_verdict_and_scope():
    kwargs = dict(
        rule_id="synthetic", rule_version="1", status=RuleStatus.COMPLIANT,
        domain=RuleDomain.TECHNICAL, metric=MetricKind.SEGMENT_LENGTH_M,
        drawing_sha256="a" * 64, reason_code="forged",
    )
    with pytest.raises(ValidationError, match="needs native evidence"):
        RuleResult(**kwargs)
    with pytest.raises(ValidationError):
        RuleResult(**(kwargs | {
            "entity_ids": ("e1",), "evidence_ids": ("m1",),
            "observed_value": 2.0, "threshold": 1.0,
            "operator": Comparison.GE, "unit": "m",
            "claim_scope": "LEGALLY_CERTIFIED",
        }))
    with pytest.raises(ValidationError, match="source evidence"):
        RuleResult(
            **(kwargs | {
                "status": RuleStatus.NOT_APPLICABLE,
            })
        )
    with pytest.raises(ValidationError, match="not proven disconnection"):
        RuleResult(
            **(kwargs | {
                "status": RuleStatus.NON_COMPLIANT,
                "metric": MetricKind.REVIEWED_TOPOLOGY_PATH,
                "entity_ids": ("e1",), "evidence_ids": ("p1",),
            })
        )


def test_segment_with_wrong_method_must_not_pass(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    drawing.measurements[0] = drawing.measurements[0].model_copy(
        update={"method_id": "unverified_text_dimension"}
    )
    out = RuleEngine([scenario_rule()]).evaluate(
        "synthetic.min", RuleRequest(
            drawing=drawing, measurement_evidence_id="test-length"
        ),
    )
    assert out.status is RuleStatus.REVIEW_REQUIRED
    assert out.reason_code == "MEASUREMENT_METHOD_UNVERIFIED"


def test_regulatory_wont_use_its_declared_effectivity_date_as_legal_approval(tmp_path):
    _, drawing, _ = _draw(tmp_path)
    rule = _regulatory()
    assert rule.legal_source.effective_from == date(2026, 1, 1)
    out = RuleEngine([rule]).evaluate(
        rule.rule_id, RuleRequest(
            drawing=drawing, measurement_evidence_id="test-length",
            applicability=ApplicabilityReview(status=ApplicabilityStatus.APPLICABLE),
        ),
    )
    assert out.status is RuleStatus.INSUFFICIENT_EVIDENCE
    assert out.legal_source.article_id == "unverified-article"
    assert out.legal_compliance_certified is False


def test_zero_hop_self_path_cannot_count_as_reviewed_adjacency(tmp_path):
    _, drawing, _ = _draw(tmp_path, two=True)
    geometry = analyze_geometry(drawing, "cad:Model")
    spaces = [
        SpaceReview(
            space_id=f"room-{i}", face_id=face.face_id,
            kind=SpaceKind.ROOM, reviewer_id="synthetic",
        )
        for i, face in enumerate(geometry.faces)
    ]
    rule = scenario_rule(
        metric=MetricKind.REVIEWED_TOPOLOGY_PATH, rule_id="synthetic.path",
    )
    out = RuleEngine([rule]).evaluate(rule.rule_id, RuleRequest(
        drawing=drawing, geometry_analysis=geometry, spaces=spaces,
        path_from_space_id="room-0", path_to_space_id="room-0",
    ))
    assert out.status is RuleStatus.REVIEW_REQUIRED
    assert out.reason_code == "ZERO_HOP_SELF_PATH_IS_NOT_A_PASSAGE"
    assert out.evidence_ids == ()
