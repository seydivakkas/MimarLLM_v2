"""Fail-closed deterministic evaluator, no eval(), LLM, statutes or cloud API.

Numeric tests are *technical scenarios*.  Regulatory candidates are always
INSUFFICIENT_EVIDENCE pending a separate verified legal-source lifecycle.
"""
from __future__ import annotations

from math import dist, isclose, isfinite
from typing import Iterable

from pydantic import ValidationError

from mimarllm.core.ir import (
    DrawingIR, EvidenceOrigin, PrimitiveKind,
)
from mimarllm.core.units import CalibrationState
from mimarllm.geometry.spatial import (
    GeometryInputError, GeometryReviewStatus, assess_area,
)
from mimarllm.geometry.topology import (
    TopologyInputError, build_topology, shortest_passage_path,
)
from mimarllm.rules.base import (
    ApplicabilityStatus, Comparison, MetricKind, RuleDefinition,
    RuleDomain, RuleRequest, RuleResult, RuleStatus,
)


class RuleInputError(ValueError):
    """Invalid registry or unsafe request structure."""


class RuleEngine:
    """Immutable-by-contract rule registry: deterministic, single-purpose rules."""

    def __init__(self, rules: Iterable[RuleDefinition], *, max_rules: int = 256):
        submitted = list(rules)
        if not 0 < len(submitted) <= max_rules:
            raise RuleInputError("Invalid rule registry size")
        verified = [RuleDefinition.model_validate(r.model_dump()) for r in submitted]
        self._registry: dict[str, RuleDefinition] = {}
        for rule in verified:
            if rule.rule_id in self._registry:
                raise RuleInputError("Duplicate rule identifier")
            self._registry[rule.rule_id] = rule

    def evaluate(self, rule_id: str, request: RuleRequest) -> RuleResult:
        """Evaluate evidence from DrawingIR, never certify legislation.

        Source observations are round-tripped through Pydantic even when a
        caller has mutated a model or used model_copy(update=...).
        """
        if rule_id not in self._registry:
            raise RuleInputError("Unknown rule identifier")
        rule = self._registry[rule_id]
        # Base metadata is always available, including on a held rule.
        common = dict(
            rule_id=rule.rule_id, rule_version=rule.version,
            domain=rule.domain, metric=rule.metric,
            drawing_sha256=request.drawing.source_sha256,
            legal_source=rule.legal_source,
        )

        def outcome(
            status: RuleStatus, reason: str, *,
            frame_id: str | None = None,
            entity_ids: tuple[str, ...] = (),
            evidence_ids: tuple[str, ...] = (),
            value: float | None = None,
            unit: str | None = None,
            tolerance: float | None = None,
        ) -> RuleResult:
            return RuleResult(
                **common, status=status, reason_code=reason,
                frame_id=frame_id, entity_ids=entity_ids,
                evidence_ids=evidence_ids, observed_value=value,
                unit=unit, calculated_tolerance=tolerance,
                threshold=rule.threshold, operator=rule.operator,
            )

        try:
            drawing = DrawingIR.model_validate(request.drawing.model_dump())
            applicability = request.applicability
            # RuleRequest and nested objects are validation boundaries, not
            # trust anchors; refuse in-place mutation or model_copy bypass.
            request = RuleRequest.model_validate(request.model_dump())
            if applicability is not None:
                applicability = request.applicability
        except (ValidationError, ValueError, TypeError):
            return outcome(RuleStatus.ERROR, "INPUT_MODEL_VALIDATION_FAILED")

        # There is deliberately NO flag/API here for unlocking a regulation.
        # The verified Official Gazette/version/applicability pipeline is not
        # installed in this phase. A forged legal_source remains blocked.
        if rule.domain == RuleDomain.REGULATORY:
            return outcome(
                RuleStatus.INSUFFICIENT_EVIDENCE,
                "REGULATORY_SOURCE_AND_APPLICABILITY_UNVERIFIED",
            )

        if applicability is not None:
            if applicability.status == ApplicabilityStatus.UNKNOWN:
                return outcome(RuleStatus.INSUFFICIENT_EVIDENCE,
                               "TECHNICAL_APPLICABILITY_UNKNOWN")
            if applicability.status == ApplicabilityStatus.NOT_APPLICABLE:
                entity_index = {e.entity_id for e in drawing.entities}
                if (applicability.drawing_sha256 != drawing.source_sha256
                        or not set(applicability.supporting_entity_ids) <= entity_index):
                    return outcome(
                        RuleStatus.REVIEW_REQUIRED,
                        "SCOPE_EXCLUSION_SOURCE_UNVERIFIED",
                    )
                return outcome(
                    RuleStatus.NOT_APPLICABLE, "TECHNICAL_SCOPE_EXCLUDED_BY_REVIEW",
                    entity_ids=applicability.supporting_entity_ids,
                )

        try:
            if rule.metric == MetricKind.SEGMENT_LENGTH_M:
                state, reason, value, tolerance, frame, entities, evidence = (
                    self._segment_length(drawing, request)
                )
                unit = "m"
            elif rule.metric in {
                MetricKind.REVIEWED_INTERIOR_AREA_M2,
                MetricKind.REVIEWED_FOOTPRINT_M2,
            }:
                state, reason, value, tolerance, frame, entities, evidence = (
                    self._reviewed_area(rule, drawing, request)
                )
                unit = "m2"
            else:
                return self._path(rule, drawing, request, outcome)

            if state is not None:
                return outcome(
                    state, reason, frame_id=frame, entity_ids=entities,
                    evidence_ids=evidence, value=value, tolerance=tolerance, unit=unit,
                )
            assert value is not None and rule.threshold is not None and rule.operator is not None
            if not (isfinite(value) and isfinite(tolerance)):
                return outcome(RuleStatus.ERROR, "NONFINITE_CALCULATION")
            if tolerance > 0 and abs(value - rule.threshold) <= tolerance:
                return outcome(
                    RuleStatus.REVIEW_REQUIRED,
                    "MEASUREMENT_INTERVAL_OVERLAPS_THRESHOLD",
                    frame_id=frame, entity_ids=entities, evidence_ids=evidence,
                    value=value, tolerance=tolerance, unit=unit,
                )
            comparisons = {
                Comparison.GE: value >= rule.threshold,
                Comparison.GT: value > rule.threshold,
                Comparison.LE: value <= rule.threshold,
                Comparison.LT: value < rule.threshold,
                Comparison.EQ: isclose(value, rule.threshold, rel_tol=0, abs_tol=1e-12),
            }
            return outcome(
                RuleStatus.COMPLIANT if comparisons[rule.operator] else RuleStatus.NON_COMPLIANT,
                "TECHNICAL_COMPARISON_TRUE" if comparisons[rule.operator]
                else "TECHNICAL_COMPARISON_FALSE",
                frame_id=frame, entity_ids=entities, evidence_ids=evidence,
                value=value, tolerance=tolerance, unit=unit,
            )
        except (ValidationError, GeometryInputError, TopologyInputError, ValueError, TypeError):
            # Source mismatch is an evidence issue, not a policy conclusion.
            return outcome(RuleStatus.REVIEW_REQUIRED, "SOURCE_RECOMPUTATION_REJECTED")
        except Exception:
            # Fail closed even on unexpected computational faults; never
            # expose exception content or fall back to a pass.
            return outcome(RuleStatus.ERROR, "DETERMINISTIC_EVALUATOR_ERROR")

    @staticmethod
    def _segment_length(drawing: DrawingIR, request: RuleRequest):
        missing = (RuleStatus.INSUFFICIENT_EVIDENCE, "MEASUREMENT_MISSING",
                   None, None, None, (), ())
        if not request.measurement_evidence_id:
            return missing
        matches = [m for m in drawing.measurements
                   if m.evidence_id == request.measurement_evidence_id]
        if len(matches) != 1:
            return missing
        m = matches[0]
        info = (m.source_frame_id, m.entity_ids, (m.evidence_id,))
        if (m.quantity != "length" or m.method_id != "segment_length"
                or len(m.entity_ids) != 1):
            return (RuleStatus.REVIEW_REQUIRED, "MEASUREMENT_METHOD_UNVERIFIED",
                    None, None, *info)
        entity = next(e for e in drawing.entities if e.entity_id == m.entity_ids[0])
        if (entity.origin not in {EvidenceOrigin.CAD_NATIVE, EvidenceOrigin.PDF_NATIVE}
                or entity.geometry.kind != PrimitiveKind.SEGMENT
                or entity.type_candidate not in {"LINE", "PDF_LINE"}):
            return (RuleStatus.REVIEW_REQUIRED, "NON_NATIVE_SEGMENT_MEASUREMENT",
                    None, None, *info)
        if (drawing.calibration.state != CalibrationState.CONFIRMED
                or drawing.calibration_frame_id != m.source_frame_id
                or m.physical_value is None):
            return (RuleStatus.INSUFFICIENT_EVIDENCE, "CONFIRMED_SCALE_OR_SI_MISSING",
                    None, None, *info)
        length = dist(*entity.geometry.points)
        if abs(length - m.source_value) > m.tolerance_source_units:
            return (RuleStatus.REVIEW_REQUIRED, "SOURCE_SEGMENT_LENGTH_MISMATCH",
                    None, None, *info)
        value = drawing.calibration.length_metres(length)
        # Even if m.source_value is within tolerance, the independently
        # recomputed value is authoritative; original evidence stays cited.
        tolerance = drawing.calibration.length_metres(m.tolerance_source_units)
        return (None, "EVALUATED", value, tolerance, *info)

    @staticmethod
    def _reviewed_area(rule: RuleDefinition, drawing: DrawingIR, request: RuleRequest):
        a = request.area_assessment
        missing = (RuleStatus.INSUFFICIENT_EVIDENCE, "AREA_ASSESSMENT_MISSING",
                   None, None, None, (), ())
        if a is None:
            return missing
        info = (a.frame_id, a.source_entity_ids,
                (f"area:{a.frame_id}:{','.join(a.source_entity_ids)}",))
        expected_role = (
            "INTERIOR_ROOM" if rule.metric == MetricKind.REVIEWED_INTERIOR_AREA_M2
            else "EXTERIOR_ENVELOPE"
        )
        if a.source_sha256 != drawing.source_sha256 or a.boundary_role != expected_role:
            return (RuleStatus.REVIEW_REQUIRED, "AREA_SOURCE_OR_ROLE_MISMATCH",
                    None, None, *info)
        recomputed = assess_area(
            drawing, a.frame_id, a.source_entity_ids,
            boundary_role=expected_role, reviewer_id=a.reviewer_id,
        )
        if recomputed.status != GeometryReviewStatus.MEASURED:
            state = (
                RuleStatus.INSUFFICIENT_EVIDENCE
                if recomputed.status == GeometryReviewStatus.INSUFFICIENT_EVIDENCE
                else RuleStatus.REVIEW_REQUIRED
            )
            return (state, recomputed.reason_code, None, None, *info)
        if (a.status != GeometryReviewStatus.MEASURED
                or a.physical_area_m2 is None or a.source_area_squared is None
                or not isclose(a.physical_area_m2, recomputed.physical_area_m2,
                               rel_tol=1e-9, abs_tol=1e-10)
                or not isclose(a.source_area_squared, recomputed.source_area_squared,
                               rel_tol=1e-9, abs_tol=1e-10)):
            return (RuleStatus.REVIEW_REQUIRED, "AREA_VALUE_DISAGREES_WITH_SOURCE",
                    None, None, *info)
        # v0.1 precise area geometry has no propagated measurement uncertainty.
        # No regulator should use 0 tolerance as an engineering guarantee.
        return (None, "EVALUATED", recomputed.physical_area_m2, 0.0, *info)

    @staticmethod
    def _path(rule: RuleDefinition, drawing: DrawingIR,
              request: RuleRequest, outcome):
        if (request.geometry_analysis is None
                or not request.spaces
                or not request.path_from_space_id
                or not request.path_to_space_id):
            return outcome(RuleStatus.INSUFFICIENT_EVIDENCE,
                           "TOPOLOGY_WITNESS_INCOMPLETE")
        topo = build_topology(
            drawing, request.geometry_analysis,
            request.spaces, request.passages,
        )
        if topo.drawing_sha256 != drawing.source_sha256:
            return outcome(RuleStatus.REVIEW_REQUIRED,
                           "TOPOLOGY_SOURCE_CHANGED")
        ids = {node.space_id for node in topo.nodes}
        if (request.path_from_space_id not in ids
                or request.path_to_space_id not in ids):
            return outcome(
                RuleStatus.INSUFFICIENT_EVIDENCE,
                "TOPOLOGY_SPACE_UNREVIEWED", frame_id=topo.frame_id,
            )
        path = shortest_passage_path(
            topo, request.path_from_space_id, request.path_to_space_id,
        )
        if path is None:
            # Absence of edges in partial plans DOES NOT prove a space has
            # no door/exit in a physical building.
            return outcome(
                RuleStatus.INSUFFICIENT_EVIDENCE,
                "NO_REVIEWED_TOPOLOGICAL_PATH_NOT_PROOF_OF_DISCONNECTION",
                frame_id=topo.frame_id,
            )
        edge_lookup = {edge.passage_id: edge for edge in topo.edges}
        evidence = tuple(path.passage_ids)
        support = tuple(sorted({
            eid for pid in evidence
            for eid in edge_lookup[pid].supporting_entity_ids
        }))
        return outcome(
            RuleStatus.COMPLIANT,
            "TECHNICAL_REVIEWED_TOPOLOGICAL_PATH_EXISTS_NOT_WALKING_DISTANCE",
            frame_id=topo.frame_id,
            entity_ids=support,
            evidence_ids=evidence,
        )
