"""Bounded, in-memory single-user analysis dispatcher.

Job states are ephemeral and NEVER legal/technical evidence. Analysis results
remain in the existing project/runs folder with their original source hash.
No network clients, external workers or unbounded process/thread pools.
"""
from __future__ import annotations

from collections import OrderedDict
from queue import Queue
from threading import Lock, Thread
from typing import Any, Callable
from uuid import uuid4


class JobQueueFull(RuntimeError):
    """A finite in-process capacity was reached."""


class BoundedAnalysisJobs:
    """One daemon worker, at most `max_inflight` jobs including active work."""

    def __init__(
        self,
        worker: Callable[[dict, Any], dict],
        analysis_lock: Lock,
        *,
        max_inflight: int = 4,
        history_limit: int = 64,
    ) -> None:
        if not 1 <= max_inflight <= 16 or history_limit < max_inflight:
            raise ValueError("Unsafe job bounds")
        self._worker = worker
        self._analysis_lock = analysis_lock
        self._queue: Queue[tuple[str, dict, Any]] = Queue(maxsize=max_inflight)
        self._lock = Lock()
        self._inflight = 0
        self._max_inflight = max_inflight
        self._history_limit = history_limit
        self._jobs: OrderedDict[str, dict] = OrderedDict()
        self._started = False

    def submit(self, project: dict, options: Any) -> dict:
        with self._lock:
            if self._inflight >= self._max_inflight:
                raise JobQueueFull("Bounded job capacity reached")
            # Completed records may be evicted, but unfinished jobs never are.
            while len(self._jobs) >= self._history_limit:
                terminal = next(
                    (k for k, v in self._jobs.items()
                     if v["state"] in ("COMPLETED", "FAILED")), None
                )
                if terminal is None:
                    raise JobQueueFull("Job history saturated")
                del self._jobs[terminal]
            job_id = uuid4().hex
            record = {
                "job_id": job_id,
                "project_id": project["project_id"],
                "source_sha256": project["source_sha256"],
                "state": "QUEUED",
                "run_id": None,
                "completion": None,
                "reason_code": None,
            }
            self._jobs[job_id] = record
            self._inflight += 1
            self._queue.put_nowait((job_id, dict(project), options))
            if not self._started:
                self._started = True
                Thread(target=self._loop, name="mimarllm-analysis", daemon=True).start()
            return dict(record)

    def status(self, project_id: str, job_id: str) -> dict | None:
        with self._lock:
            record = self._jobs.get(job_id)
            if record is None or record["project_id"] != project_id:
                return None
            return dict(record)

    def _loop(self) -> None:
        while True:
            job_id, project, options = self._queue.get()
            try:
                with self._lock:
                    self._jobs[job_id]["state"] = "RUNNING"
                # The pre-existing synchronous route shares this lock.
                with self._analysis_lock:
                    result = self._worker(project, options)
                with self._lock:
                    self._jobs[job_id].update(
                        state="COMPLETED",
                        run_id=result["run_id"],
                        completion=result["completion"],
                    )
            except Exception as exc:
                # Never expose local paths, source content or exception messages.
                with self._lock:
                    self._jobs[job_id].update(
                        state="FAILED", reason_code=type(exc).__name__,
                    )
            finally:
                with self._lock:
                    self._inflight -= 1
                self._queue.task_done()
