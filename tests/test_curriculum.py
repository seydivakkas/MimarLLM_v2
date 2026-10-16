"""Process 025: catalogue and evidence-gated studio read-only contracts."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mimarllm.app.server import create_app
from mimarllm.curriculum.registry import (
    CATALOGUE_VERSION, MODULES, GRADE_COUNTS, grade_snapshot, modules_for_grade,
)


@pytest.mark.parametrize("grade,count", [(1, 18), (2, 31), (3, 45), (4, 55)])
def test_cumulative_grades_and_hold(grade, count):
    snapshot = grade_snapshot(grade)
    assert snapshot["grade"] == grade
    assert snapshot["catalogued_module_count"] == count
    assert snapshot["software_modules_accepted"] == 0
    assert snapshot["legal_gate"] == "REGULATORY_LOCKED"
    assert snapshot["schema_version"] == CATALOGUE_VERSION
    assert len(snapshot["modules"]) == count
    assert all(m["introduced_grade"] <= grade for m in snapshot["modules"])
    assert all(m["implementation_state"] == "CATALOG_ONLY" for m in snapshot["modules"])
    assert not any(m["grading_enabled"] or m["regulatory_approved"]
                   for m in snapshot["modules"])


def test_catalogue_complete_unique_and_early_preview_not_counted():
    assert len(MODULES) == 55
    assert len({m.code for m in MODULES}) == 55
    assert set(GRADE_COUNTS) == {1, 2, 3, 4}
    for i, end in enumerate((118, 213, 314, 410), 1):
        assert modules_for_grade(i)[-1].code == f"MOD-{end}"
    assert "MOD-409" not in {m.code for m in modules_for_grade(3)}
    assert "MOD-410" not in {m.code for m in modules_for_grade(2)}
    assert "sertifik" not in modules_for_grade(4)[-1].title.lower()


@pytest.mark.parametrize("value", [0, 5, -1, 1.0, "1", True, None])
def test_untrusted_grade_rejected(value):
    with pytest.raises(ValueError):
        modules_for_grade(value)


def test_local_api_and_studio_assets(tmp_path):
    app = create_app(tmp_path / "private")
    with TestClient(app, base_url="http://127.0.0.1:8765",
                    client=("127.0.0.1", 54321)) as http:
        for g, count in GRADE_COUNTS.items():
            response = http.get(f"/api/curriculum/grades/{g}")
            assert response.status_code == 200
            payload = response.json()
            assert payload["catalogued_module_count"] == count
            assert len(payload["modules"]) == count
            assert payload["legal_gate"] == "REGULATORY_LOCKED"
        assert http.get("/api/curriculum/grades/5").status_code == 404
        assert http.get("/api/curriculum/grades/a").status_code == 422
        page = http.get("/")
        js = http.get("/static/dashboard.js")
        css = http.get("/static/dashboard.css")
        assert page.status_code == js.status_code == css.status_code == 200
        assert 'id="studio-viewport"' in page.text
        assert 'data-view="legal"' in page.text
        assert 'id="upload-button"' in page.text
        assert "https://" not in page.text
        assert "studio-columns" in css.text
        assert 'api("/api/curriculum/grades/"+grade)' in js.text
        assert "STUDIO_MODULE_EXAMPLES" not in js.text
        assert "Puan: —" in js.text
        assert "REGULATORY_LOCKED" in page.text
        assert "innerHTML" not in js.text
        assert "eval(" not in js.text
        assert "script-src 'self'" in page.headers["content-security-policy"]
