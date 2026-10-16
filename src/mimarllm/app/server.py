"""F19: offline one-user loopback-only FastAPI dashboard for MimarLLM.

All browser paths are opaque IDs. The browser CANNOT select server-side
filesystem paths. A local application token + loopback/Host/Origin checks
limit cross-site invocation; not a substitute for OS user isolation.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from importlib.resources import files
import ipaddress
import json
from pathlib import Path
import re
import secrets
import shutil
from threading import Lock
from typing import Literal
from urllib.parse import urlsplit
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from mimarllm.app.jobs import BoundedAnalysisJobs, JobQueueFull
from mimarllm.app.reviews import ReviewStore, ReviewPayload, ReviewError
from mimarllm.app.dxf_edits import DxfRevisions, EditRequest, UndoRequest, EditError
from mimarllm.core.ir import DrawingIR
from mimarllm.geometry.massing25d import MassingRequest, MassingError, build_massing_candidate
from mimarllm.pipeline import PipelineConfig, run_local_pipeline
from mimarllm.reports.exporter import export_report


_ID = re.compile(r"^[a-f0-9]{32}$")
_ALLOWED_OUTPUTS = frozenset({
    "analysis.json", "analysis.html", "analysis.md", "analysis.pdf",
    "drawingir.json", "pipeline-manifest.json",
})
_ALLOWED_HOSTS = frozenset({"localhost", "127.0.0.1"})
_LIMITS = {"dxf": 25_000_000, "pdf": 50_000_000}
_MAX_PROJECTS = 100
_MAX_RUNS = 100
_ASSET = files("mimarllm.app").joinpath("static")


class DashboardError(ValueError):
    pass


class RunPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    config: PipelineConfig = Field(default_factory=PipelineConfig)
    formats: tuple[Literal["json", "html", "md", "pdf"], ...] = (
        "json", "html",
    )

    @classmethod
    def checked(cls, raw: bytes) -> "RunPayload":
        try:
            selected = cls.model_validate_json(raw)
        except (ValidationError, ValueError) as exc:
            raise DashboardError("Analiz yapılandırması geçersiz.") from exc
        if not 1 <= len(selected.formats) <= 4 or len(set(selected.formats)) != len(selected.formats):
            raise DashboardError("Rapor biçimleri tekrarsız ve en fazla dört adet olabilir.")
        return selected


def _read_safely(path: Path, *, max_bytes: int) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise HTTPException(status_code=404, detail="Yerel kayıt bulunamadı.")
    if path.stat().st_size > max_bytes:
        raise HTTPException(status_code=413, detail="Kayıt görüntüleme sınırını aşıyor.")
    return path.read_bytes()


def _hash_file(path: Path) -> str:
    h = sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def _id_directory(parent: Path, identifier: str) -> Path:
    if not _ID.fullmatch(identifier):
        raise HTTPException(status_code=404, detail="Geçersiz kaynak kimliği.")
    path = parent / identifier
    if path.is_symlink() or not path.is_dir():
        raise HTTPException(status_code=404, detail="Kaynak bulunamadı.")
    if path.resolve() != parent.resolve() / identifier:
        raise HTTPException(status_code=404, detail="Kaynak çalışma alanı dışında.")
    return path


def create_app(workspace: str | Path) -> FastAPI:
    """The workspace is chosen ONLY by the trusted local server launcher."""
    root = Path(workspace).expanduser().resolve(strict=False)
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink() or not root.is_dir():
        raise DashboardError("Yerel çalışma alanı geçerli bir klasör olmalı.")
    projects_dir = root / "projects"
    if projects_dir.is_symlink():
        raise DashboardError("Sembolik bağlantı çalışma alanı kabul edilmez.")
    projects_dir.mkdir(exist_ok=True)
    csrf = secrets.token_urlsafe(32)
    running = Lock()
    app = FastAPI(
        title="MimarLLM Yerel Analiz",
        version="0.1.0",
        docs_url=None, redoc_url=None, openapi_url=None,
    )
    app.state.workspace = root
    app.state.local_csrf = csrf

    @app.middleware("http")
    async def local_security(request: Request, call_next):
        host = request.headers.get("host", "")
        try:
            parsed_host = urlsplit("http://" + host).hostname
        except ValueError:
            parsed_host = None
        if parsed_host not in _ALLOWED_HOSTS:
            return Response("INVALID_LOCAL_HOST", status_code=403)
        peer = request.client.host if request.client else None
        try:
            allowed_peer = peer is not None and ipaddress.ip_address(peer).is_loopback
        except ValueError:
            allowed_peer = False
        if not allowed_peer:
            return Response("NOT_LOCAL_CLIENT", status_code=403)
        origin = request.headers.get("origin")
        if origin:
            try:
                given = urlsplit(origin)
                origin_ok = (
                    given.scheme == "http"
                    and given.hostname in _ALLOWED_HOSTS
                    and given.netloc.lower() == host.lower()
                )
            except ValueError:
                origin_ok = False
            if not origin_ok:
                return Response("INVALID_ORIGIN", status_code=403)
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            provided = request.headers.get("x-mimar-csrf", "")
            if not secrets.compare_digest(provided, csrf):
                return Response("CSRF_TOKEN_REQUIRED", status_code=403)
        try:
            response = await call_next(request)
        except Exception:
            # No source document text or local path in an unexpected exception.
            response = Response("LOCAL_OPERATION_FAILED", status_code=500)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; font-src 'self'; "
            "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
        )
        if request.url.path.endswith("analysis.html"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'none'; style-src 'unsafe-inline'; img-src data:; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
            )
        return response

    def project_path(identifier: str) -> Path:
        return _id_directory(projects_dir, identifier)

    def metadata(identifier: str) -> dict:
        project = project_path(identifier)
        stored = json.loads(_read_safely(project / "project.json", max_bytes=4096))
        kind = stored.get("source_kind")
        ext = {"DXF": "dxf", "PDF": "pdf"}.get(kind)
        if (stored.get("project_id") != identifier
                or ext is None
                or stored.get("source_name") != "input." + ext
                or not isinstance(stored.get("source_sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", stored["source_sha256"])
                or not isinstance(stored.get("size_bytes"), int)
                or not 0 < stored["size_bytes"] <= _LIMITS[ext]):
            raise HTTPException(
                status_code=409,
                detail="Yerel proje metadata/source kimliği tutarsız.",
            )
        return stored

    def run_dir(project_id: str, run_id: str) -> Path:
        project = project_path(project_id)
        parent = project / "runs"
        if parent.is_symlink() or not parent.is_dir():
            raise HTTPException(status_code=404, detail="Analiz bulunamadı.")
        return _id_directory(parent, run_id)

    @app.get("/", response_class=HTMLResponse)
    def page():
        return HTMLResponse(_ASSET.joinpath("index.html").read_text("utf-8"))

    @app.get("/static/{filename}")
    def static_file(filename: str):
        if filename not in {"dashboard.css", "dashboard.js", "scene25d.js", "three.module.js"}:
            raise HTTPException(status_code=404, detail="Statik dosya yok.")
        kind = "text/css" if filename.endswith(".css") else "text/javascript"
        return Response(_ASSET.joinpath(filename).read_bytes(), media_type=kind)

    @app.get("/api/session")
    def session():
        return {
            "csrf": csrf,
            "local_only": True,
            "service": "MimarLLM F19",
            "legal_gate": "REGULATORY_LOCKED",
        }

    @app.get("/api/projects")
    def list_projects():
        result = []
        for entry in sorted(projects_dir.iterdir(), reverse=True):
            if len(result) >= _MAX_PROJECTS:
                break
            if entry.is_dir() and not entry.is_symlink() and _ID.fullmatch(entry.name):
                try:
                    result.append(metadata(entry.name))
                except (ValueError, OSError, HTTPException, json.JSONDecodeError):
                    continue
        return {"projects": result}

    @app.post("/api/projects", status_code=201)
    async def upload(request: Request):
        ext = request.headers.get("x-mimar-extension", "").lower()
        if ext not in _LIMITS:
            raise HTTPException(status_code=415, detail="Yalnız DXF veya PDF kabul edilir.")
        max_bytes = _LIMITS[ext]
        declared = request.headers.get("content-length")
        if declared:
            try:
                if int(declared) > max_bytes:
                    raise HTTPException(status_code=413, detail="Dosya yükleme sınırı aşıldı.")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Bozuk dosya uzunluğu.") from exc
        active = sum(
            1 for p in projects_dir.iterdir()
            if p.is_dir() and _ID.fullmatch(p.name) and not p.is_symlink()
        )
        if active >= _MAX_PROJECTS:
            raise HTTPException(status_code=429, detail="Proje sayısı güvenlik sınırına ulaştı.")
        project_id = uuid4().hex
        folder = projects_dir / project_id
        folder.mkdir(mode=0o700)
        path = folder / ("input." + ext)
        digest = sha256()
        total = 0
        try:
            with path.open("xb") as output:
                async for chunk in request.stream():
                    total += len(chunk)
                    if total > max_bytes:
                        raise HTTPException(status_code=413, detail="Dosya boyutu aşıldı.")
                    output.write(chunk)
                    digest.update(chunk)
            if total == 0:
                raise HTTPException(status_code=422, detail="Boş çizim dosyası.")
            recorded = {
                "project_id": project_id,
                "source_kind": ext.upper(),
                "source_name": "input." + ext,
                "size_bytes": total,
                "source_sha256": digest.hexdigest(),
                "created_utc": datetime.now(timezone.utc).isoformat(),
            }
            (folder / "runs").mkdir()
            with (folder / "project.json").open("x", encoding="utf-8") as record:
                json.dump(recorded, record, ensure_ascii=False)
            return recorded
        except BaseException:
            shutil.rmtree(folder, ignore_errors=True)
            raise

    @app.get("/api/projects/{project_id}")
    def get_project(project_id: str):
        project = metadata(project_id)
        folder = project_path(project_id)
        runs = []
        for item in sorted((folder / "runs").iterdir(), reverse=True):
            if len(runs) >= _MAX_RUNS:
                break
            if not item.is_dir() or item.is_symlink() or not _ID.fullmatch(item.name):
                continue
            manifest = item / "pipeline-manifest.json"
            if manifest.is_file() and not manifest.is_symlink():
                try:
                    obj = json.loads(_read_safely(manifest, max_bytes=512_000))
                    runs.append({
                        "run_id": item.name,
                        "completion": obj["completion"],
                        "source_sha256": obj["source_sha256"],
                        "report_finding_count": obj["report_finding_count"],
                        "stage_errors": sum(s["status"] == "ERROR" for s in obj["stages"]),
                    })
                except (ValueError, KeyError, OSError, HTTPException):
                    continue
        return {"project": project, "runs": runs}

    @app.post("/api/projects/{project_id}/runs", status_code=201)
    async def analyze(project_id: str, request: Request):
        project = metadata(project_id)
        declared = request.headers.get("content-length")
        if declared:
            try:
                if int(declared) > 256_000:
                    raise HTTPException(status_code=413, detail="JSON ayarları 256 KB sınırını aştı.")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Bozuk JSON gövde uzunluğu.") from exc
        parts = []
        total = 0
        async for chunk in request.stream():
            total += len(chunk)
            if total > 256_000:
                raise HTTPException(status_code=413, detail="JSON ayarları 256 KB sınırını aştı.")
            parts.append(chunk)
        raw = b"".join(parts)
        try:
            options = RunPayload.checked(raw)
        except DashboardError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not running.acquire(blocking=False):
            raise HTTPException(status_code=409, detail="Başka bir yerel analiz çalışıyor.")
        try:
            result = await run_in_threadpool(_generate_run, project, options)
        except (ValueError, OSError, RuntimeError) as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Kaynaklı analiz tamamlanamadı: {type(exc).__name__}",
            ) from exc
        finally:
            running.release()
        return result

    def _generate_run(project: dict, options: RunPayload) -> dict:
        pid = project["project_id"]
        base = project_path(pid)
        infile = base / project["source_name"]
        if infile.is_symlink() or not infile.is_file() or _hash_file(infile) != project["source_sha256"]:
            raise DashboardError("Özgün dosya SHA doğrulaması başarısız.")
        runs = base / "runs"
        if sum(1 for p in runs.iterdir() if p.is_dir()) >= _MAX_RUNS:
            raise DashboardError("Analiz sayısı sınırına ulaşıldı.")
        rid = uuid4().hex
        target = runs / rid
        target.mkdir(mode=0o700)
        try:
            ocr_reader = None
            if options.config.ocr_regions:
                from mimarllm.ocr.rapid_engine import RapidCpuOcr
                ocr_reader = RapidCpuOcr()
            outcome = run_local_pipeline(infile, options.config, ocr_reader=ocr_reader)
            if outcome.drawing.source_sha256 != project["source_sha256"] or _hash_file(infile) != project["source_sha256"]:
                raise DashboardError("Çizim dosyası analiz sırasında değişti.")
            ordered = tuple(dict.fromkeys(("json", "html") + options.formats))
            for fmt in ordered:
                export_report(
                    outcome.report, target / ("analysis." + fmt),
                    drawing_pdf_path=infile if fmt == "html"
                    and project["source_kind"] == "PDF" else None,
                )
            with (target / "drawingir.json").open("x", encoding="utf-8") as f:
                f.write(outcome.drawing.model_dump_json())
            with (target / "pipeline-manifest.json").open("x", encoding="utf-8") as f:
                f.write(outcome.manifest.model_dump_json(indent=2))
            return {
                "project_id": pid, "run_id": rid,
                "completion": outcome.manifest.completion,
                "manifest": outcome.manifest.model_dump(mode="json"),
            }
        except BaseException:
            shutil.rmtree(target, ignore_errors=True)
            raise

    # A finite, in-process dispatcher: statuses are ephemeral, reports persist
    # in the existing source-validated run directories.
    jobs = BoundedAnalysisJobs(_generate_run, running)
    reviews = ReviewStore()
    dxf_revisions = DxfRevisions()

    @app.post("/api/projects/{project_id}/jobs", status_code=202)
    async def queue_analysis(project_id: str, request: Request):
        project = metadata(project_id)
        if (project_path(project_id) / project["source_name"]).is_symlink():
            raise HTTPException(status_code=409, detail="Kaynak sembolik bağlantı olamaz.")
        declared = request.headers.get("content-length")
        if declared:
            try:
                if int(declared) > 256_000:
                    raise HTTPException(status_code=413, detail="JSON ayarları 256 KB sınırını aştı.")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Bozuk JSON gövde uzunluğu.") from exc
        chunks = []
        size = 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 256_000:
                raise HTTPException(status_code=413, detail="JSON ayarları 256 KB sınırını aştı.")
            chunks.append(chunk)
        try:
            options = RunPayload.checked(b"".join(chunks))
        except DashboardError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        try:
            return jobs.submit(project, options)
        except JobQueueFull as exc:
            raise HTTPException(status_code=429, detail="Yerel analiz kuyruğu dolu.") from exc

    @app.get("/api/projects/{project_id}/jobs/{job_id}")
    def job_status(project_id: str, job_id: str):
        metadata(project_id)
        if not _ID.fullmatch(job_id):
            raise HTTPException(status_code=404, detail="Analiz işi bulunamadı.")
        result = jobs.status(project_id, job_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Analiz işi bulunamadı veya oturum yeniden başladı.")
        return result

    @app.get("/api/projects/{project_id}/runs/{run_id}")
    def read_run(project_id: str, run_id: str):
        folder = run_dir(project_id, run_id)
        manifest = json.loads(_read_safely(folder / "pipeline-manifest.json", max_bytes=512_000))
        report = json.loads(_read_safely(folder / "analysis.json", max_bytes=40_000_000))
        drawing = json.loads(_read_safely(folder / "drawingir.json", max_bytes=40_000_000))
        if manifest["source_sha256"] != report["drawing_sha256"] or manifest["source_sha256"] != drawing["source_sha256"]:
            raise HTTPException(status_code=409, detail="Raporun kaynak SHA kimliği tutarsız.")
        candidate_lines = []
        for entity in drawing["entities"]:
            if len(candidate_lines) >= 400:
                break
            geom = entity["geometry"]
            if (entity["origin"] in ("CAD_NATIVE", "PDF_NATIVE")
                    and entity["type_candidate"] in ("LINE", "PDF_LINE")
                    and geom["kind"] == "SEGMENT" and len(geom["points"]) == 2):
                candidate_lines.append({
                    "entity_id": entity["entity_id"],
                    "frame_id": entity["frame_id"],
                    "origin": entity["origin"],
                    "layer": entity.get("layer"),
                    "points": geom["points"],
                    "cad_handle": entity["source"].get("cad_handle"),
                })
        available = [
            file.name for file in folder.iterdir()
            if file.name in _ALLOWED_OUTPUTS and file.is_file() and not file.is_symlink()
        ]
        return {
            "run_id": run_id, "manifest": manifest,
            "source_sha256": manifest["source_sha256"],
            "findings": report["findings"][:200],
            "frames": report["frames"][:50],
            "sources": report["sources"][:250],
            "native_lines": candidate_lines,
            "reports": sorted(available),
            "truncated": len(report["findings"]) > 200 or len(report["sources"]) > 250,
        }

    def review_context(project_id: str, run_id: str, *, include_drawing: bool = False):
        project = metadata(project_id)
        run = run_dir(project_id, run_id)
        input_file = project_path(project_id) / project["source_name"]
        if (input_file.is_symlink() or not input_file.is_file()
                or _hash_file(input_file) != project["source_sha256"]):
            raise HTTPException(status_code=409, detail="Özgün kaynak SHA doğrulaması başarısız.")
        manifest = json.loads(_read_safely(run / "pipeline-manifest.json", max_bytes=512_000))
        if manifest.get("source_sha256") != project["source_sha256"]:
            raise HTTPException(status_code=409, detail="Analiz kaynak SHA kimliği uyuşmuyor.")
        drawing = None
        if include_drawing:
            drawing = json.loads(_read_safely(run / "drawingir.json", max_bytes=40_000_000))
            if drawing.get("source_sha256") != project["source_sha256"]:
                raise HTTPException(status_code=409, detail="Çizim kaynak SHA kimliği uyuşmuyor.")
        return run, project["source_sha256"], drawing

    @app.get("/api/projects/{project_id}/runs/{run_id}/reviews")
    def list_reviews(project_id: str, run_id: str):
        folder, source_sha, _ = review_context(project_id, run_id)
        try:
            notes = reviews.list(folder, source_sha)
        except ReviewError as exc:
            raise HTTPException(status_code=409, detail="İnceleme kayıtları güvenilir değil.") from exc
        return {"source_sha256": source_sha, "review_state": "UNVERIFIED_OBSERVATION",
                "notes": notes}

    @app.post("/api/projects/{project_id}/runs/{run_id}/reviews", status_code=201)
    async def add_review(project_id: str, run_id: str, request: Request):
        folder, source_sha, drawing = review_context(project_id, run_id, include_drawing=True)
        parts, size = [], 0
        async for chunk in request.stream():
            size += len(chunk)
            if size > 4096:
                raise HTTPException(status_code=413, detail="İnceleme notu gövdesi çok büyük.")
            parts.append(chunk)
        try:
            payload = ReviewPayload.model_validate_json(b"".join(parts))
            return reviews.add(folder, source_sha, drawing, payload)
        except ReviewError as exc:
            raise HTTPException(status_code=409, detail="Kaynak eşleşmesi veya not bütçesi başarısız.") from exc
        except (ValidationError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Kaynaklı inceleme notu geçersiz.") from exc

    @app.delete("/api/projects/{project_id}/runs/{run_id}/reviews/{review_id}")
    def retract_review(project_id: str, run_id: str, review_id: str):
        if not _ID.fullmatch(review_id):
            raise HTTPException(status_code=404, detail="İnceleme notu bulunamadı.")
        folder, source_sha, _ = review_context(project_id, run_id)
        try:
            return reviews.retract(folder, source_sha, review_id)
        except ReviewError as exc:
            raise HTTPException(status_code=409, detail="İnceleme notu bulunamadı veya geri alındı.") from exc

    @app.post("/api/projects/{project_id}/runs/{run_id}/massing25d", status_code=200)
    async def create_massing25d(project_id: str, run_id: str, request: Request):
        # Same local-only middleware, CSRF and provenance checks as review notes.
        _folder, source_sha, raw_drawing = review_context(
            project_id, run_id, include_drawing=True)
        chunks = []
        length = 0
        async for chunk in request.stream():
            length += len(chunk)
            if length > 12_000:
                raise HTTPException(status_code=413, detail="2.5D senaryo isteği çok büyük.")
            chunks.append(chunk)
        try:
            payload = MassingRequest.model_validate_json(b"".join(chunks))
        except (ValidationError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="2.5D geometri isteği geçersiz.") from exc
        if payload.source_sha256 != source_sha:
            raise HTTPException(status_code=409, detail="Kaynak dosya SHA uyuşmuyor.")
        try:
            drawing = DrawingIR.model_validate(raw_drawing)
            candidate = build_massing_candidate(drawing, payload)
        except (MassingError, ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=409,
                detail="2.5D senaryosu üretilemedi: ölçü, kaynak veya kapalı yüzey kanıtı yetersiz.",
            ) from exc
        return candidate.model_dump(mode="json")

    def dxf_edit_context(project_id: str):
        project = metadata(project_id)
        if project["source_kind"] != "DXF":
            raise HTTPException(status_code=415, detail="Kalıcı geometri revizyonu yalnız DXF içindir.")
        folder = project_path(project_id)
        source = folder / "input.dxf"
        if source.is_symlink() or not source.is_file() or _hash_file(source) != project["source_sha256"]:
            raise HTTPException(status_code=409, detail="Orijinal DXF SHA doğrulaması başarısız.")
        return folder, project["source_sha256"]

    async def parse_dxf_edit_payload(request: Request, schema):
        data = bytearray()
        length = request.headers.get("content-length")
        if length:
            try:
                if int(length) > 4096:
                    raise HTTPException(status_code=413, detail="CAD düzenleme komutu çok büyük.")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Geçersiz gövde uzunluğu.") from exc
        async for chunk in request.stream():
            data.extend(chunk)
            if len(data) > 4096:
                raise HTTPException(status_code=413, detail="CAD düzenleme komutu çok büyük.")
        try:
            return schema.model_validate_json(bytes(data))
        except (ValidationError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="CAD düzenleme komutu doğrulanamadı.") from exc

    @app.get("/api/projects/{project_id}/edits")
    def dxf_edit_status(project_id: str):
        folder, sha = dxf_edit_context(project_id)
        try:
            return dxf_revisions.status(folder, sha)
        except (EditError, OSError, ValueError) as exc:
            raise HTTPException(status_code=409, detail="DXF revizyon geçmişi güvenilir değil.") from exc

    @app.post("/api/projects/{project_id}/edits", status_code=201)
    async def dxf_edit_line(project_id: str, request: Request):
        folder, sha = dxf_edit_context(project_id)
        command = await parse_dxf_edit_payload(request, EditRequest)
        try:
            return dxf_revisions.revise(folder, sha, command)
        except (EditError, OSError, ValueError) as exc:
            raise HTTPException(status_code=409, detail="DXF düzenleme kaynağı ya da revizyonu doğrulanamadı.") from exc

    @app.post("/api/projects/{project_id}/edits/undo", status_code=201)
    async def dxf_edit_undo(project_id: str, request: Request):
        folder, sha = dxf_edit_context(project_id)
        command = await parse_dxf_edit_payload(request, UndoRequest)
        try:
            return dxf_revisions.undo(folder, sha, command)
        except (EditError, OSError, ValueError) as exc:
            raise HTTPException(status_code=409, detail="CAD revizyonu geri alınamadı.") from exc

    @app.get("/api/projects/{project_id}/edits/{revision_id}/download")
    def dxf_edit_download(project_id: str, revision_id: str):
        folder, sha = dxf_edit_context(project_id)
        try:
            binary = dxf_revisions.download(folder, sha, revision_id)
        except (EditError, OSError, ValueError) as exc:
            raise HTTPException(status_code=404, detail="DXF revizyonu bulunamadı.") from exc
        return Response(
            content=binary,
            media_type="application/dxf",
            headers={"Content-Disposition": f'attachment; filename="MimarLLM-{revision_id}.dxf"'},
        )

    @app.get("/api/projects/{project_id}/runs/{run_id}/files/{filename}")
    def report_file(project_id: str, run_id: str, filename: str):
        if filename not in _ALLOWED_OUTPUTS:
            raise HTTPException(status_code=404, detail="Bu rapor dosyası desteklenmiyor.")
        folder = run_dir(project_id, run_id)
        data = _read_safely(folder / filename, max_bytes=40_000_000)
        kinds = {
            ".html": "text/html; charset=utf-8",
            ".json": "application/json",
            ".md": "text/markdown; charset=utf-8",
            ".pdf": "application/pdf",
        }
        kind = Path(filename).suffix.lower()
        headers = {}
        if filename != "analysis.html":
            headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return Response(content=data, media_type=kinds[kind], headers=headers)

    return app
