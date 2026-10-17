"""030: eight-axis comparison uses only same-year, same-version, fully
human-reviewed draft snapshots. No extrapolation across academic years.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from mimarllm.analytics.models import AxisSeries, TrendComparison
from mimarllm.pedagogy.rubric import Axis, DEFAULT_CATALOG


def compare_drafts(before: dict, after: dict) -> TrendComparison:
    same_scope=(
        before["academic_year"]==after["academic_year"]
        and before["rubric_version"]==after["rubric_version"]
    )
    complete=(
        before["rubric_status"]=="LOCAL_DRAFT_ONLY"
        and after["rubric_status"]=="LOCAL_DRAFT_ONLY"
        and before["draft_total"] is not None
        and after["draft_total"] is not None
        and before["reviewed_criterion_count"]==before["active_criterion_count"]
        and after["reviewed_criterion_count"]==after["active_criterion_count"]
    )
    comparable=same_scope and complete
    reason=("LEVEL_OR_RUBRIC_DIFFER" if not same_scope else
            "INSUFFICIENT_REVIEW_COVERAGE" if not complete else
            "SAME_LEVEL_AND_RUBRIC")
    axes=[]
    for definition in DEFAULT_CATALOG.axes:
        name=definition.axis.value
        raw_before=before["axes"].get(name)
        raw_after=after["axes"].get(name)
        values_available=raw_before is not None and raw_after is not None
        # Never use 0 for a missing axis; no inferred geometry or scores.
        delta=(
            float((Decimal(str(raw_after))-Decimal(str(raw_before))).quantize(
                Decimal("0.01"),rounding=ROUND_HALF_UP))
            if comparable and values_available else None
        )
        axes.append(AxisSeries(
            axis=definition.axis,label_tr=definition.title_tr,
            before_percent=raw_before if comparable else None,
            after_percent=raw_after if comparable else None,
            delta_points=delta,comparable=bool(comparable and values_available),
        ))
    total=(
        float((Decimal(str(after["draft_total"]))-
               Decimal(str(before["draft_total"]))).quantize(
            Decimal("0.01"),rounding=ROUND_HALF_UP))
        if comparable else None
    )
    return TrendComparison(
        status="COMPARABLE_DRAFT_ONLY" if comparable else "NOT_COMPARABLE",
        reason=reason,
        before_id=before["snapshot_id"],after_id=after["snapshot_id"],
        before_period=before["period_label"],after_period=after["period_label"],
        academic_year_before=before["academic_year"],
        academic_year_after=after["academic_year"],
        rubric_version_before=before["rubric_version"],
        rubric_version_after=after["rubric_version"],
        axes=tuple(axes),total_draft_delta=total,
    )
