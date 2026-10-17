"""030: consent-only SQLite snapshots stored in operator-owned local workspace.

No database, collection or identifier is created by read-only dashboard launch.
Collection token is a 128-bit capability: only its SHA-256 digest is stored.
SQLite secure_delete reduces deletion remnants but cannot erase backups.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
import sqlite3
from threading import RLock
from uuid import uuid4

from mimarllm.analytics.models import HistoryError
from mimarllm.pedagogy.rubric import Axis
from mimarllm.pedagogy.scoring import RubricOutcome

_MAX_COLLECTIONS=20
_MAX_SNAPSHOTS=24
_SCHEMA_VERSION="030.0.1"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PrivateHistory:
    def __init__(self, workspace: Path):
        self.workspace=workspace
        self.db=workspace/"private-analytics-030.sqlite3"
        self._lock=RLock()

    def _check_path(self, create: bool) -> None:
        if (self.workspace.is_symlink() or not self.workspace.is_dir() or
                self.db.is_symlink()):
            raise HistoryError("LOCAL_HISTORY_PATH_UNSAFE")
        if not create and not self.db.is_file():
            raise HistoryError("LOCAL_HISTORY_NOT_ENABLED")
        if self.db.exists() and not self.db.is_file():
            raise HistoryError("LOCAL_HISTORY_PATH_UNSAFE")

    @contextmanager
    def _connection(self, *, create: bool=False):
        self._check_path(create)
        db_is_new=not self.db.exists()
        try:
            conn=sqlite3.connect(self.db,timeout=5)
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA journal_mode=DELETE")
            conn.execute("PRAGMA secure_delete=ON")
            if db_is_new:
                try:
                    os.chmod(self.db,0o600)
                except OSError as exc:
                    conn.close()
                    self.db.unlink(missing_ok=True)
                    raise HistoryError("LOCAL_HISTORY_PERMISSIONS_FAILED") from exc
            yield conn
        except sqlite3.DatabaseError as exc:
            raise HistoryError("LOCAL_HISTORY_DATABASE_ERROR") from exc
        finally:
            if "conn" in locals():
                conn.close()

    def _schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS collections(
                collection_hash TEXT PRIMARY KEY,
                created_utc TEXT NOT NULL,
                expires_utc TEXT NOT NULL,
                retention_days INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS snapshots(
                snapshot_id TEXT PRIMARY KEY,
                collection_hash TEXT NOT NULL REFERENCES collections(collection_hash)
                    ON DELETE CASCADE,
                created_utc TEXT NOT NULL,
                period_label TEXT NOT NULL,
                project_id TEXT NOT NULL,
                run_id TEXT NOT NULL,
                draft_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS snapshots_col_idx
                ON snapshots(collection_hash, created_utc);
        """)

    @staticmethod
    def _hash(token: str) -> str:
        if len(token)!=32 or any(c not in "0123456789abcdef" for c in token):
            raise HistoryError("LOCAL_HISTORY_TOKEN_INVALID")
        return sha256(token.encode("ascii")).hexdigest()

    @staticmethod
    def _expire(conn: sqlite3.Connection, now: datetime) -> None:
        conn.execute("DELETE FROM collections WHERE expires_utc <= ?",
                     (now.isoformat(),))

    @staticmethod
    def _authorized(conn: sqlite3.Connection, digest: str) -> tuple[str, str, int]:
        row=conn.execute(
            "SELECT created_utc,expires_utc,retention_days FROM collections WHERE collection_hash=?",
            (digest,),
        ).fetchone()
        if row is None:
            raise HistoryError("LOCAL_HISTORY_COLLECTION_UNKNOWN")
        return row

    def create(self, retention_days: int, *, now: datetime | None=None) -> dict:
        if retention_days not in (30,90,180):
            raise HistoryError("LOCAL_HISTORY_RETENTION_INVALID")
        instant=now or _now()
        with self._lock, self._connection(create=True) as conn:
            self._schema(conn)
            with conn:
                self._expire(conn,instant)
                count=conn.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
                if count>=_MAX_COLLECTIONS:
                    raise HistoryError("LOCAL_HISTORY_COLLECTION_LIMIT")
                token=secrets.token_hex(16)
                expiry=(instant+timedelta(days=retention_days)).isoformat()
                conn.execute(
                    "INSERT INTO collections VALUES (?,?,?,?)",
                    (self._hash(token),instant.isoformat(),expiry,retention_days),
                )
        return {"collection_token":token,"expires_utc":expiry,
                "retention_days":retention_days,
                "status":"LOCAL_CONSENTED_HISTORY",
                "storage":"WORKSPACE_ONLY_NOT_ENCRYPTED_AT_REST"}

    @staticmethod
    def _record(project_id: str,run_id: str,period: str,result: RubricOutcome) -> dict:
        # Never store the human review notes, name, SHA/file path, student ID or VLM.
        if len(project_id)!=32 or len(run_id)!=32:
            raise HistoryError("LOCAL_HISTORY_SOURCE_ID_INVALID")
        by_axis={axis.axis:axis for axis in result.axes}
        if set(by_axis)!=set(Axis):
            raise HistoryError("LOCAL_HISTORY_AXES_INCOMPLETE")
        axes={}
        for axis in Axis:
            section=by_axis[axis]
            value=section.draft_axis_percent
            axes[axis.value]=float(value) if value is not None else None
            if value is not None and not 0<=float(value)<=100:
                raise HistoryError("LOCAL_HISTORY_AXIS_OUT_OF_RANGE")
        if result.official_grade or result.vlm_derived_scores or result.can_modify_drawing:
            raise HistoryError("LOCAL_HISTORY_UNTRUSTED_SCORE")
        return {
            "schema_version":_SCHEMA_VERSION,
            "rubric_version":result.rubric_version,
            "academic_year":result.academic_year,
            "rubric_status":result.status,
            "reviewed_criterion_count":result.reviewed_criterion_count,
            "active_criterion_count":result.active_criterion_count,
            "axes":axes,
            "draft_total":(
                float(result.draft_points_out_of_100)
                if result.draft_points_out_of_100 is not None else None
            ),
            "official_grade":False,
            "pedagogical_progress_verified":False,
        }

    def add(self,token: str,period: str,project_id: str,run_id: str,
            result: RubricOutcome, *, now: datetime | None=None) -> dict:
        now=now or _now()
        record=self._record(project_id,run_id,period,result)
        digest=self._hash(token)
        with self._lock,self._connection() as conn:
            with conn:
                self._expire(conn,now)
                self._authorized(conn,digest)
                count=conn.execute(
                    "SELECT COUNT(*) FROM snapshots WHERE collection_hash=?",
                    (digest,),
                ).fetchone()[0]
                if count>=_MAX_SNAPSHOTS:
                    raise HistoryError("LOCAL_HISTORY_SNAPSHOT_LIMIT")
                uid=uuid4().hex
                conn.execute(
                    "INSERT INTO snapshots VALUES (?,?,?,?,?,?,?)",
                    (uid,digest,now.isoformat(),period,project_id,run_id,
                     json.dumps(record,sort_keys=True,separators=(",",":"))),
                )
        return {"snapshot_id":uid,"created_utc":now.isoformat(),
                "period_label":period,**record,
                "status":"LOCAL_DRAFT_SNAPSHOT_SAVED"}

    def list(self,token: str, *, now: datetime | None=None) -> dict:
        digest=self._hash(token)
        with self._lock,self._connection() as conn:
            with conn:
                self._expire(conn,now or _now())
                _,expiry,retention=self._authorized(conn,digest)
                rows=conn.execute(
                    "SELECT snapshot_id,created_utc,period_label,draft_json "
                    "FROM snapshots WHERE collection_hash=? "
                    "ORDER BY created_utc,snapshot_id",(digest,),
                ).fetchall()
        return {
            "status":"LOCAL_PRIVATE_HISTORY",
            "expires_utc":expiry,"retention_days":retention,
            "count":len(rows),
            "snapshots":[
                {"snapshot_id":sid,"created_utc":created,
                 "period_label":period,**json.loads(payload)}
                for sid,created,period,payload in rows
            ],
            "official_grade":False,
            "no_cloud_transfer":True,
        }

    def pair(self,token: str,first: str,second: str) -> tuple[dict,dict]:
        if first==second:
            raise HistoryError("LOCAL_HISTORY_DISTINCT_SNAPSHOTS_REQUIRED")
        all_rows=self.list(token)["snapshots"]
        selected={s["snapshot_id"]:s for s in all_rows
                  if s["snapshot_id"] in {first,second}}
        if len(selected)!=2:
            raise HistoryError("LOCAL_HISTORY_SNAPSHOT_NOT_FOUND")
        return selected[first],selected[second]

    def remove(self,token: str,snapshot_id: str,*, now: datetime | None=None) -> None:
        digest=self._hash(token)
        with self._lock,self._connection() as conn:
            with conn:
                self._expire(conn,now or _now())
                self._authorized(conn,digest)
                changed=conn.execute(
                    "DELETE FROM snapshots WHERE snapshot_id=? AND collection_hash=?",
                    (snapshot_id,digest),
                ).rowcount
                if changed!=1:
                    raise HistoryError("LOCAL_HISTORY_SNAPSHOT_NOT_FOUND")
            conn.execute("VACUUM")

    def revoke(self,token: str,*, now: datetime | None=None) -> None:
        digest=self._hash(token)
        with self._lock,self._connection() as conn:
            with conn:
                self._expire(conn,now or _now())
                changed=conn.execute(
                    "DELETE FROM collections WHERE collection_hash=?",(digest,),
                ).rowcount
                if changed!=1:
                    raise HistoryError("LOCAL_HISTORY_COLLECTION_UNKNOWN")
            conn.execute("VACUUM")
