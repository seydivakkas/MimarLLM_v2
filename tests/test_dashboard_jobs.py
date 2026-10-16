"""Process 025: finite offline dispatcher and error-isolation regression."""
from __future__ import annotations

from threading import Event, Lock
from time import monotonic, sleep

import pytest

from mimarllm.app.jobs import BoundedAnalysisJobs, JobQueueFull


def project(identifier="a" * 32):
    return {"project_id": identifier, "source_sha256": "1" * 64}


def wait_for(jobs, pid, jid, states=("COMPLETED", "FAILED")):
    until = monotonic() + 3
    while monotonic() < until:
        job = jobs.status(pid, jid)
        if job["state"] in states:
            return job
        sleep(.01)
    pytest.fail("Local worker did not reach its terminal state")


def test_queue_capacity_is_finite_and_project_scoped():
    gate = Event()
    started = Event()
    def worker(p, options):
        started.set()
        assert gate.wait(2)
        return {"run_id": "b" * 32, "completion": "COMPLETE"}
    jobs = BoundedAnalysisJobs(worker, Lock(), max_inflight=2, history_limit=3)
    try:
        first = jobs.submit(project(), object())
        assert started.wait(2)
        second = jobs.submit(project(), object())
        assert second["state"] == "QUEUED"
        assert jobs.status("2" * 32, first["job_id"]) is None
        with pytest.raises(JobQueueFull):
            jobs.submit(project(), object())
    finally:
        gate.set()
    assert wait_for(jobs, "a" * 32, first["job_id"])["run_id"] == "b" * 32
    assert wait_for(jobs, "a" * 32, second["job_id"])["completion"] == "COMPLETE"
    assert jobs.submit(project(), object())["job_id"] not in (first["job_id"], second["job_id"])


def test_error_messages_and_paths_not_exposed():
    def fail(_project, _options):
        raise RuntimeError("private:C:/sensitive/source.dxf")
    jobs = BoundedAnalysisJobs(fail, Lock(), max_inflight=1)
    job = jobs.submit(project(), {})
    result = wait_for(jobs, project()["project_id"], job["job_id"])
    assert result["state"] == "FAILED"
    assert result["reason_code"] == "RuntimeError"
    assert "private" not in str(result)
    assert result["run_id"] is None


def test_job_safety_bounds():
    with pytest.raises(ValueError):
        BoundedAnalysisJobs(lambda *_: {}, Lock(), max_inflight=0)
    with pytest.raises(ValueError):
        BoundedAnalysisJobs(lambda *_: {}, Lock(), max_inflight=17)
    with pytest.raises(ValueError):
        BoundedAnalysisJobs(lambda *_: {}, Lock(), max_inflight=4, history_limit=2)
