"""029: sequential critique is not faculty voting, LLM scoring, or official approval."""
from __future__ import annotations

from hashlib import sha256

import ezdxf
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from mimarllm.app.server import create_app
from mimarllm.importers.dxf import parse_dxf
from mimarllm.pedagogy.rubric import profile
from mimarllm.pedagogy.scoring import (
    CriterionReview, RubricSubmission, evaluate_rubric,
)
from mimarllm.pedagogy.jury import (
    JuryError, JURY_VERSION, SEQUENCE, build_jury_report,
)


@pytest.fixture
def drawing(tmp_path):
    path = tmp_path / "jury.dxf"
    dxf = ezdxf.new("R2013")
    space = dxf.modelspace()
    for first, last in [
        ((0, 0), (6, 0)), ((6, 0), (6, 4)),
        ((6, 4), (0, 4)), ((0, 4), (0, 0)),
    ]:
        space.add_line(first, last)
    dxf.saveas(path)
    ir = parse_dxf(path).drawing
    return path, ir, tuple(e.entity_id for e in ir.entities)


def human_submission(ir, ids, year=1, complete=False, note=None):
    criteria = [c["criterion_id"] for c in profile(year)["criteria"]]
    used = criteria if complete else criteria[:1]
    reviews = tuple(CriterionReview(
        criterion_id=key, human_level=3,
        source_entity_ids=(ids[0],),
        reviewer_note=note or
        "Bu çizim kaynak noktasında insan tarafından gözlem ve tasarım kararı tartışıldı.",
        human_review_attested=True,
    ) for key in used)
    return RubricSubmission(
        source_sha256=ir.source_sha256, frame_id="cad:Model",
        academic_year=year, reviewer_label="İnsan pilot değerlendirmesi",
        human_review_attested=True, reviews=reviews,
    )


def test_stable_four_perspective_sequence_partial_and_no_votes(drawing):
    path, ir, ids = drawing
    before = (path.read_bytes(), ir.model_dump_json())
    payload = human_submission(ir, ids)
    result = build_jury_report(ir, payload)
    assert result.schema_version == JURY_VERSION
    assert [turn.perspective_id for turn in result.sequence] == [
        "CONTEXT_AND_CONCEPT", "PROGRAM_AND_SPACE",
        "STRUCTURE_AND_CLIMATE", "REPRESENTATION_AND_PROCESS",
    ]
    assert [turn.order for turn in result.sequence] == [1, 2, 3, 4]
    assert len(result.sequence) == 4
    assert result.status == "SOURCE_BOUND_JURY_SIMULATION"
    assert result.review_coverage == "INCOMPLETE"
    assert result.reviewed_criterion_count == 1
    assert result.active_criterion_count == 6
    assert len(result.missing_criterion_ids) == 5
    assert result.sequence[2].status == "NOT_APPLICABLE_BY_LEVEL"
    assert len(result.sequence[2].comments) == 0
    assert not result.model_inference_used
    assert not result.independent_ai_votes
    assert not result.official_jury
    assert not result.real_faculty_approval
    assert not result.official_grade
    assert result.passed is None and result.numeric_score is None
    assert result.legal_gate == "REGULATORY_LOCKED"
    assert result.drawing_modified is False
    assert result.source_sha256 == sha256(path.read_bytes()).hexdigest()
    assert set(
        item.criterion_id for turn in result.sequence for item in turn.comments
    ) == {c["criterion_id"] for c in profile(1)["criteria"]}
    first = next(item for turn in result.sequence for item in turn.comments
                 if item.criterion_id == "CONTEXT_OBSERVATION")
    assert first.source_entity_ids == (ids[0],)
    assert first.source_kind == "UNVERIFIED_HUMAN_ATTESTATION"
    assert all(item.source_entity_ids == ()
               for turn in result.sequence for item in turn.comments
               if item.status == "REVIEW_REQUIRED")
    assert before == (path.read_bytes(), ir.model_dump_json())
    assert build_jury_report(ir,payload).model_dump_json() == result.model_dump_json()
    assert "resmî" in result.report_markdown.lower()
    assert result.report_markdown.index("1. Perspektif") < result.report_markdown.index("4. Perspektif")


def test_full_human_claims_dont_generate_jury_grade_or_votes(drawing):
    _, ir, ids = drawing
    filled = human_submission(ir,ids,year=4,complete=True)
    score = evaluate_rubric(ir,filled)
    assert str(score.draft_points_out_of_100) == "75.00"
    result = build_jury_report(ir,filled)
    assert result.review_coverage == "COMPLETE"
    assert result.reviewed_criterion_count == result.active_criterion_count == 16
    assert all(turn.status == "SOURCE_BOUND_REVIEW_PROMPTS" for turn in result.sequence)
    assert sum(len(turn.comments) for turn in result.sequence) == 16
    assert result.numeric_score is None
    assert result.official_grade is False and result.official_jury is False
    assert "75.00" not in result.report_markdown
    assert result.model_inference_used is False


def test_markdown_untrusted_human_text_is_inert(drawing):
    _, ir, ids = drawing
    malicious = (
        "<script>alert('XSS')</script> "
        "[jüri](https://evil.example) **ONAYLANDI** "
        + "bir incelemeci beyanıdır."
    )
    result=build_jury_report(ir,human_submission(ir,ids,note=malicious))
    md=result.report_markdown
    assert "<script>" not in md
    assert "&lt;script&gt;" in md
    assert "[jüri](https://evil.example)" not in md
    assert "human_level" not in md
    assert "MODEL_PASS" not in md
    # Honest source note remains attributable to the claimant, never verdict.
    assert "İnsan öz-beyanı" in md


def test_wrong_frame_sha_criterion_duplicate_ai_grade_fail_closed(drawing):
    _,ir,ids=drawing
    valid=human_submission(ir,ids)
    with pytest.raises(JuryError):
        build_jury_report(ir,valid.model_copy(update={"source_sha256":"f"*64}))
    with pytest.raises(JuryError):
        build_jury_report(ir,valid.model_copy(update={"frame_id":"cad:Other"}))
    with pytest.raises(JuryError):
        bad=valid.model_copy(update={"reviews":(
            CriterionReview(criterion_id="CONCEPT_INTENT",human_level=3,
               source_entity_ids=("FAKE_ENTITY",),
               reviewer_note="Bu gerçeğe dayanmayan çizim referansı kabul edilmez.",
               human_review_attested=True),)})
        build_jury_report(ir,bad)
    with pytest.raises(ValidationError):
        RubricSubmission.model_validate({
            **valid.model_dump(),"jury_pass":True,
        })
    with pytest.raises(ValidationError):
        RubricSubmission.model_validate({
            **valid.model_dump(),"ai_vote":5,
        })
    with pytest.raises(ValidationError):
        RubricSubmission.model_validate({
            **valid.model_dump(),"reviews":[valid.reviews[0].model_dump()]*2,
        })
    with pytest.raises(ValidationError):
        RubricSubmission.model_validate({
            **valid.model_dump(),"human_review_attested":False,
        })


def test_api_source_run_scope_csrf_size_immutability_and_markdown(tmp_path,drawing):
    path,ir,ids=drawing
    root=tmp_path/"workspace"
    with TestClient(create_app(root),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as client:
        csrf=client.get("/api/session").json()["csrf"]
        upload=client.post("/api/projects",content=path.read_bytes(),headers={
            "X-Mimar-CSRF":csrf,"X-Mimar-Extension":"dxf",
        })
        assert upload.status_code==201,upload.text
        project=upload.json()["project_id"]
        run=client.post(f"/api/projects/{project}/runs",
            json={"config":{},"formats":["json","html"]},
            headers={"X-Mimar-CSRF":csrf})
        assert run.status_code==201,run.text
        runid=run.json()["run_id"]
        payload=human_submission(ir,ids).model_dump(mode="json")
        url=f"/api/projects/{project}/runs/{runid}/jury/critique"
        runroot=root/"projects"/project/"runs"/runid
        original=(runroot/"drawingir.json").read_bytes(),(runroot/"analysis.json").read_bytes()
        assert client.post(url,json=payload).status_code==403
        ok=client.post(url,json=payload,headers={"X-Mimar-CSRF":csrf})
        assert ok.status_code==200,ok.text
        response=ok.json()
        assert response["official_jury"] is False
        assert response["independent_ai_votes"] is False
        assert response["model_inference_used"] is False
        assert response["numeric_score"] is None
        assert response["review_coverage"]=="INCOMPLETE"
        assert len(response["sequence"])==4
        assert response["source_sha256"]==ir.source_sha256
        assert "Kaynak SHA256" in response["report_markdown"]
        assert client.post(url,json={**payload,"source_sha256":"f"*64},
            headers={"X-Mimar-CSRF":csrf}).status_code==409
        assert client.post(url,json={**payload,"ai_critic":"resmî hoca"},
            headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert client.post(url,json={**payload,"reviews":[{
            **payload["reviews"][0],"source_entity_ids":["FORGED"]
        }]},headers={"X-Mimar-CSRF":csrf}).status_code==409
        assert client.post(url,json={**payload,"human_review_attested":False},
            headers={"X-Mimar-CSRF":csrf}).status_code==422
        assert client.post(url,content=b"x"*32769,
            headers={"X-Mimar-CSRF":csrf}).status_code==413
        assert original==((runroot/"drawingir.json").read_bytes(),
                          (runroot/"analysis.json").read_bytes())
        assert not (runroot/"jury-report.md").exists()
        assert not (runroot/"rubric-grade.json").exists()


def test_jury_ui_has_ordered_manual_perspectives_and_no_remote_requests(tmp_path):
    with TestClient(create_app(tmp_path/"ui"),base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1",12345)) as client:
        page=client.get("/").text
        js=client.get("/static/dashboard.js").text
        for element in ("jury-029","jury-generate","jury-next",
                        "jury-download","jury-clear","jury-turns","jury-status"):
            assert f'id="{element}"' in page
        assert '"/jury/critique"' in js
        assert "SOURCE_BOUND_JURY_SIMULATION" in js
        assert "model_inference_used" in js
        assert "independent_ai_votes" in js
        assert "rubric-criterion-level" in js
        assert "innerHTML" not in js
        assert "eval(" not in js
        assert "https://" not in page
