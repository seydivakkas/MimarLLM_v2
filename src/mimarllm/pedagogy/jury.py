"""029: source-scoped, ordered pedagogical simulation, never faculty votes.

The perspective turns use only deterministic, versioned educational prompts.
A human rubric observation is an *unverified claim*, not design proof.
"""
from __future__ import annotations

import html
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from mimarllm.core.ir import DrawingIR
from mimarllm.pedagogy.rubric import Axis, DEFAULT_CATALOG, RUBRIC_VERSION
from mimarllm.pedagogy.scoring import RubricSubmission, RubricError, evaluate_rubric

JURY_VERSION = "029.0.1"
SEQUENCE: tuple[tuple[str, str, tuple[Axis, Axis], str], ...] = (
    ("CONTEXT_AND_CONCEPT", "Bağlam ve kavramsal tutarlılık",
     (Axis.CONTEXT, Axis.CONCEPT),
     "Hangi yer ve tasarım niyeti gözlemi çizimle ilişkilendirilebilir?"),
    ("PROGRAM_AND_SPACE", "İşlev ve mekânsal kurgu",
     (Axis.FUNCTION, Axis.SPATIAL),
     "İhtiyaç-program-mekân ilişkisi hangi sorularla sorgulanmalı?"),
    ("STRUCTURE_AND_CLIMATE", "Yapım ve çevresel yaklaşım",
     (Axis.STRUCTURE, Axis.ENVIRONMENT),
     "Bu sınıf seviyesinde strüktür ve iklim kararları nasıl gerekçelendirilmiş?"),
    ("REPRESENTATION_AND_PROCESS", "Temsil ve tasarım süreci",
     (Axis.REPRESENTATION, Axis.PROCESS),
     "Okunurluk, öz değerlendirme ve revizyon gerekçesi nasıl tartışılmalı?"),
)


class JuryError(ValueError):
    """Fail closed if sources or rubric were not verified."""


class JuryComment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    criterion_id: str
    criterion_title_tr: str
    status: Literal["REVIEW_REQUIRED", "HUMAN_CLAIM_RECORDED"]
    guiding_question_tr: str
    method_notice_tr: str
    source_entity_ids: tuple[str, ...] = ()
    human_note_unverified: str | None = None
    source_kind: Literal["UNVERIFIED_HUMAN_ATTESTATION", "MISSING_REVIEW"]


class JuryTurn(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    order: int = Field(ge=1, le=4)
    perspective_id: str
    title_tr: str
    perspective_kind: Literal["SINGLE_ENGINE_SEQUENTIAL_VIEWPOINT"] = (
        "SINGLE_ENGINE_SEQUENTIAL_VIEWPOINT"
    )
    axes: tuple[Axis, Axis]
    opening_question_tr: str
    comments: tuple[JuryComment, ...]
    applicable_criterion_count: int
    reviewed_criterion_count: int
    status: Literal["NOT_APPLICABLE_BY_LEVEL", "REVIEW_REQUIRED", "SOURCE_BOUND_REVIEW_PROMPTS"]


class JuryReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal["029.0.1"] = JURY_VERSION
    rubric_version: Literal["028.0.1"] = RUBRIC_VERSION
    status: Literal["SOURCE_BOUND_JURY_SIMULATION"] = "SOURCE_BOUND_JURY_SIMULATION"
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    frame_id: str
    academic_year: int
    reviewer_label: str
    sequence: tuple[JuryTurn, JuryTurn, JuryTurn, JuryTurn]
    review_coverage: Literal["COMPLETE", "INCOMPLETE"]
    reviewed_criterion_count: int
    active_criterion_count: int
    missing_criterion_ids: tuple[str, ...]
    model_inference_used: Literal[False] = False
    independent_ai_votes: Literal[False] = False
    real_faculty_approval: Literal[False] = False
    official_jury: Literal[False] = False
    official_grade: Literal[False] = False
    passed: None = None
    numeric_score: None = None
    legal_gate: Literal["REGULATORY_LOCKED"] = "REGULATORY_LOCKED"
    drawing_modified: Literal[False] = False
    report_markdown: str = Field(max_length=26000)


def _safe_markdown(text: str) -> str:
    """Quote free text as inert Markdown/HTML, one line per note."""
    one_line = " ".join(text.split())
    escaped = html.escape(one_line, quote=True)
    # Escape Markdown link syntax and formatting including backtick (\x60).
    return re.sub(r"([\\\x60*_{}\[\]()#+.!>|-])", r"\\\1", escaped)


def _markdown(*, year: int, sha: str, frame: str, reviewer: str,
              turns: tuple[JuryTurn, ...], missing: tuple[str, ...]) -> str:
    rows = [
        "# MimarLLM — Kaynaklı pedagojik jüri simülasyonu (İşlem 029)",
        "",
        "**YALNIZ EĞİTİM AMAÇLI SIRALI BAKIŞ AÇILARI. RESMÎ JÜRİ, "
        "BAĞIMSIZ AKADEMİSYEN GÖRÜŞÜ, AI OYU YA DA DERS NOTU DEĞİLDİR.**",
        "",
        f"- Rubrik: {RUBRIC_VERSION} / Jüri: {JURY_VERSION}",
        f"- Sınıf: {year}",
        f"- Kaynak SHA256: {sha}",
        f"- Kaynak frame: {_safe_markdown(frame)}",
        f"- İnsan öz-beyan etiketi: {_safe_markdown(reviewer)}",
        "- Hukukî kapı: REGULATORY_LOCKED",
        f"- Eksik insan incelemesi: {len(missing)} kriter",
        "",
    ]
    for turn in turns:
        rows.extend([
            f"## {turn.order}. Perspektif — {_safe_markdown(turn.title_tr)}",
            "",
            f"**Kontrol sorusu:** {_safe_markdown(turn.opening_question_tr)}",
            f"**Durum:** {turn.status}",
            "",
        ])
        if not turn.comments:
            rows.extend(["Bu sınıf seviyesinde etkin kriter bulunmuyor.", ""])
        for item in turn.comments:
            sources = (
                ", ".join(_safe_markdown(sid) for sid in item.source_entity_ids)
                if item.source_entity_ids else "YOK — İNCELEME GEREKLİ"
            )
            rows.extend([
                f"### {_safe_markdown(item.criterion_title_tr)} / {item.criterion_id}",
                f"- Durum: {item.status}",
                f"- Kaynak entity ID: {sources}",
                f"- İnceleme sorusu: {_safe_markdown(item.guiding_question_tr)}",
                f"- Kanıt sınırı: {_safe_markdown(item.method_notice_tr)}",
            ])
            if item.human_note_unverified is not None:
                rows.append("- İnsan öz-beyanı (doğrulanmamış): " +
                            _safe_markdown(item.human_note_unverified))
            rows.append("")
    rows.extend([
        "## Kapanış / kaynak sınırı",
        "",
        "Bu perspektifler aynı sürümlü rubrik ve tek kaynak kümesinden "
        "türetilmiş sorulardır; oylama veya bağımsız uzman uzlaşması değildir.",
        "",
        "Puan, geçme/kalma, resmî mevzuat uygunluğu ve mimari doğruluk sonucu "
        "YOKTUR. Kaynak DXF/PDF, DrawingIR, rapor ve VLM değişmemiştir.",
        "",
    ])
    report = "\n".join(rows)
    if len(report) > 26000:
        raise JuryError("JURY_MARKDOWN_BUDGET_EXCEEDED")
    return report


def build_jury_report(drawing: DrawingIR, submitted: RubricSubmission) -> JuryReport:
    """Produce all four turns in a stable order; do not ask VLM for votes."""
    try:
        drawing = DrawingIR.model_validate(drawing.model_dump(mode="json"))
        submitted = RubricSubmission.model_validate(submitted.model_dump(mode="json"))
        rubric = evaluate_rubric(drawing, submitted)
    except (ValidationError, RubricError, ValueError, TypeError) as exc:
        raise JuryError("JURY_SOURCE_OR_RUBRIC_UNTRUSTED") from exc
    applicable = {
        c.criterion_id: c for c in DEFAULT_CATALOG.criteria
        if c.min_year <= submitted.academic_year <= c.max_year
    }
    reviews = {review.criterion_id: review for review in submitted.reviews}
    turns: list[JuryTurn] = []
    seen: set[str] = set()
    for order, (pid, title, axes, opening) in enumerate(SEQUENCE, 1):
        comments: list[JuryComment] = []
        for criterion in DEFAULT_CATALOG.criteria:
            if criterion.axis not in axes or criterion.criterion_id not in applicable:
                continue
            if criterion.criterion_id in seen:
                raise JuryError("JURY_CRITERION_DUPLICATED_ACROSS_TURNS")
            seen.add(criterion.criterion_id)
            review = reviews.get(criterion.criterion_id)
            comments.append(JuryComment(
                criterion_id=criterion.criterion_id,
                criterion_title_tr=criterion.title_tr,
                status="HUMAN_CLAIM_RECORDED" if review else "REVIEW_REQUIRED",
                guiding_question_tr=criterion.evidence_hint_tr,
                method_notice_tr=(
                    "Kaynak kimliği ve insan öz-beyanı var; mimari anlam, "
                    "öğretim niteliği ve kişinin yetkisi doğrulanmadı."
                    if review else
                    "Bu ölçüt için kaynaklı insan incelemesi yok; çizim "
                    "anlamı veya öğrencinin başarısı çıkarılamaz."
                ),
                source_entity_ids=review.source_entity_ids if review else (),
                human_note_unverified=review.reviewer_note if review else None,
                source_kind=(
                    "UNVERIFIED_HUMAN_ATTESTATION" if review else "MISSING_REVIEW"
                ),
            ))
        reviewed_count = sum(
            comment.status == "HUMAN_CLAIM_RECORDED" for comment in comments
        )
        turns.append(JuryTurn(
            order=order, perspective_id=pid, title_tr=title, axes=axes,
            opening_question_tr=opening, comments=tuple(comments),
            applicable_criterion_count=len(comments),
            reviewed_criterion_count=reviewed_count,
            status=("NOT_APPLICABLE_BY_LEVEL" if not comments else
                    "SOURCE_BOUND_REVIEW_PROMPTS" if reviewed_count == len(comments)
                    else "REVIEW_REQUIRED"),
        ))
    if seen != set(applicable):
        raise JuryError("JURY_CATALOG_AXES_INCOMPLETE")
    sequence = tuple(turns)
    return JuryReport(
        source_sha256=drawing.source_sha256, frame_id=submitted.frame_id,
        academic_year=submitted.academic_year,
        reviewer_label=submitted.reviewer_label,
        sequence=sequence,
        reviewed_criterion_count=rubric.reviewed_criterion_count,
        active_criterion_count=rubric.active_criterion_count,
        missing_criterion_ids=rubric.missing_criterion_ids,
        review_coverage="INCOMPLETE" if rubric.missing_criterion_ids else "COMPLETE",
        report_markdown=_markdown(
            year=submitted.academic_year, sha=drawing.source_sha256,
            frame=submitted.frame_id, reviewer=submitted.reviewer_label,
            turns=sequence, missing=rubric.missing_criterion_ids,
        ),
    )
