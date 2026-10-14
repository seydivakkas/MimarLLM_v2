"""Fail-closed report assembly from existing deterministic source contracts."""
from __future__ import annotations

from typing import Sequence

from mimarllm.core.ir import DrawingIR
from mimarllm.geometry.spatial import GeometryAnalysis
from mimarllm.geometry.topology import TopologyResult
from mimarllm.reports.models import (
    AnalysisReport, LegalEvidenceLink, ReportFinding, ReportFrame,
    ReportKind, ReportSource,
)
from mimarllm.rules.base import RuleDomain, RuleResult, RuleStatus
from mimarllm.rules.evidence import RegulatoryEvidenceEvaluation


class ReportInputError(ValueError):
    pass


def build_analysis_report(
    drawing: DrawingIR,
    *,
    rules: Sequence[RuleResult] = (),
    regulatory_evaluations: Sequence[RegulatoryEvidenceEvaluation] = (),
    geometry: GeometryAnalysis | None = None,
    topology: TopologyResult | None = None,
    max_entities: int = 2_000,
    max_findings: int = 2_000,
) -> AnalysisReport:
    """Build source-anchored findings without reclassifying legal candidates.

    RuleEngine is assumed to have calculated supplied RuleResults; this module
    checks provenance and referential integrity, not their hidden computation.
    Do not synthesize PASS/FAIL from geometry candidate or RAG similarity.
    """
    if not 1 <= max_entities <= 20_000 or not 1 <= max_findings <= 20_000:
        raise ReportInputError("Invalid report budgets")
    drawing = DrawingIR.model_validate(drawing.model_dump())
    if len(drawing.entities) > max_entities:
        raise ReportInputError("Report drawing entity budget exceeded")
    indexed = {e.entity_id: e for e in drawing.entities}
    measured = {m.evidence_id: m for m in drawing.measurements}
    checked_rules = [RuleResult.model_validate(r.model_dump()) for r in rules]
    if len({(r.rule_id, r.rule_version) for r in checked_rules}) != len(checked_rules):
        raise ReportInputError('Duplicate RuleResult source and version')
    evaluations = [
        RegulatoryEvidenceEvaluation.model_validate(e.model_dump())
        for e in regulatory_evaluations
    ]
    by_rule = {}
    for item in evaluations:
        key = (item.rule_result.rule_id, item.rule_result.rule_version)
        if key in by_rule:
            raise ReportInputError("Duplicate legal source binding for one rule")
        by_rule[key] = item
    for k in by_rule:
        if k not in {(r.rule_id, r.rule_version) for r in checked_rules}:
            raise ReportInputError("Orphan regulatory source binding")
    if geometry is not None:
        geometry = GeometryAnalysis.model_validate(geometry.model_dump())
        if geometry.source_sha256 != drawing.source_sha256:
            raise ReportInputError("Geometry analysis from a different drawing")
        if geometry.frame_id not in {f.frame_id for f in drawing.frames}:
            raise ReportInputError("Geometry analysis uses an unknown coordinate frame")
    if topology is not None:
        topology = TopologyResult.model_validate(topology.model_dump())
        if topology.drawing_sha256 != drawing.source_sha256:
            raise ReportInputError("Topology from another drawing")
        if topology.frame_id not in {f.frame_id for f in drawing.frames}:
            raise ReportInputError("Topology coordinate frame missing")
        if geometry is not None and geometry.frame_id != topology.frame_id:
            raise ReportInputError("Geometry/topology frame mismatch")

    def source_frame(ids: tuple[str, ...], suggested: str | None) -> str | None:
        if not set(ids).issubset(indexed):
            raise ReportInputError("Finding points to an unknown source drawing entity")
        frames = {indexed[eid].frame_id for eid in ids}
        if len(frames) > 1:
            raise ReportInputError("One finding cannot mix drawing layouts or PDF pages")
        if suggested is not None and frames and suggested not in frames:
            raise ReportInputError("Finding declared frame differs from source entity")
        return suggested if suggested else next(iter(frames), None)

    findings = []
    for f in drawing.findings:
        findings.append(ReportFinding(
            finding_id="drawing:" + f.finding_id,
            kind=ReportKind.DRAWING_FINDING,
            check_id=f.check_id,
            status=f.status.value,
            reason_code=f.reason_code,
            frame_id=source_frame(f.entity_ids, None),
            entity_ids=f.entity_ids,
            measurement_ids=f.evidence_ids,
        ))

    available_passages = {
        edge.passage_id for edge in topology.edges
    } if topology is not None else set()
    for rule in checked_rules:
        if rule.drawing_sha256 != drawing.source_sha256:
            raise ReportInputError("RuleResult source SHA mismatch")
        evidence = set(rule.evidence_ids)
        missing = evidence - set(measured) - available_passages
        derived_area = {e for e in missing if e.startswith("area:")}
        missing -= derived_area
        if missing:
            raise ReportInputError("RuleResult includes unknown measurement/passage evidence")
        frame = source_frame(rule.entity_ids, rule.frame_id)
        legal = None
        if rule.domain == RuleDomain.REGULATORY:
            binding = by_rule.get((rule.rule_id, rule.rule_version))
            if binding is not None:
                if (binding.rule_result != rule
                        or binding.binding.source_document_sha256
                        != rule.legal_source.document_sha256
                        or binding.binding.rule_id != rule.rule_id
                        or binding.binding.rule_version != rule.rule_version):
                    raise ReportInputError("Legal evidence does not bind to exact RuleResult")
                b = binding.binding
                if not any(span.page_index == rule.legal_source.page_index
                           for span in b.original_spans):
                    raise ReportInputError("Legal rule locator page differs from source")
                legal = LegalEvidenceLink(
                    document_sha256=b.source_document_sha256,
                    node_id=b.source_node_id,
                    spans=b.original_spans,
                    binding_status=b.status.value,
                    reason_codes=b.reason_codes,
                    original_local_audit=(
                        b.local_source_audit.status.value
                        if b.local_source_audit else None
                    ),
                )
        findings.append(ReportFinding(
            finding_id=f"rule:{rule.rule_id}:{rule.rule_version}",
            kind=(ReportKind.TECHNICAL_RULE
                  if rule.domain == RuleDomain.TECHNICAL
                  else ReportKind.REGULATORY_CANDIDATE),
            check_id=rule.rule_id,
            status=rule.status.value,
            reason_code=rule.reason_code,
            frame_id=frame,
            entity_ids=rule.entity_ids,
            evidence_ids=rule.evidence_ids,
            measurement_ids=tuple(e for e in rule.evidence_ids if e in measured),
            technical_domain=rule.domain,
            observed_value=rule.observed_value,
            threshold=rule.threshold,
            unit=rule.unit,
            legal_evidence=legal,
        ))

    if geometry is not None:
        for i, issue in enumerate(geometry.issues):
            frame = source_frame(issue.entity_ids, issue.frame_id)
            findings.append(ReportFinding(
                finding_id=f"geometry:issue:{i}",
                kind=ReportKind.GEOMETRY_ISSUE,
                check_id="shapely.geometry",
                status="REVIEW_REQUIRED",
                reason_code=issue.code,
                frame_id=frame,
                entity_ids=issue.entity_ids,
            ))
        for face in geometry.faces:
            frame = source_frame(face.boundary_entity_ids, face.frame_id)
            findings.append(ReportFinding(
                finding_id=f"geometry:face:{face.face_id}",
                kind=ReportKind.FACE_CANDIDATE,
                check_id="shapely.polygon_candidate",
                status="REVIEW_REQUIRED",
                reason_code="UNCLASSIFIED_FACE_NOT_CONFIRMED_ROOM",
                frame_id=frame,
                entity_ids=face.boundary_entity_ids,
                observed_value=face.source_area_squared,
                unit="source_units_squared",
            ))

    if topology is not None:
        for i, issue in enumerate(topology.issues):
            findings.append(ReportFinding(
                finding_id=f"topology:issue:{i}",
                kind=ReportKind.TOPOLOGY_ISSUE,
                check_id="networkx.topology",
                status="REVIEW_REQUIRED",
                reason_code=issue.code,
                frame_id=topology.frame_id,
            ))
        # Neither centroid segments nor a topological hop count is a fire
        # egress walking route. Only explicit source-marked passage evidence
        # can accompany a precomputed technical RuleResult.

    if len(findings) > max_findings:
        raise ReportInputError("Report finding count budget exceeded")

    source_ids = {eid for f in findings for eid in f.entity_ids}
    report = AnalysisReport(
        drawing_id=drawing.drawing_id,
        drawing_sha256=drawing.source_sha256,
        source_kind=drawing.source_kind.value,
        frames=tuple(
            ReportFrame(
                frame_id=f.frame_id, coordinate_kind=f.kind.value,
                page_index=f.page_index, view_id=f.view_id,
            ) for f in drawing.frames
        ),
        sources=tuple(ReportSource(
            entity_id=e.entity_id,
            drawing_sha256=drawing.source_sha256,
            frame_id=e.frame_id,
            geometry=e.geometry,
            origin_reference=e.source,
            layer=e.layer,
        ) for e in drawing.entities if e.entity_id in source_ids),
        findings=tuple(findings),
        calibration_state=drawing.calibration.state.value,
    )
    return report
