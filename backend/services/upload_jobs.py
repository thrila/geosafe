"""Durable SQLite-backed queue state for long-running flight uploads."""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Protocol
from uuid import uuid4

from core.config import settings


class UploadJobRepository(Protocol):
    """Durable upload-job persistence contract used by HTTP and worker code."""

    def create(self, job_id: str, name: str, video_path, log_path) -> dict: ...
    def get(self, job_id: str) -> dict | None: ...
    def requeue_expired(self, now: int | None = None) -> int: ...
    def claim_next(self, worker_id: str, lease_seconds: int) -> dict | None: ...
    def record_flight_id(self, job_id: str, worker_id: str, flight_id: int, lease_seconds: int) -> bool: ...
    def begin_processing(self, job_id: str, worker_id: str, artifact_id: str, lease_seconds: int) -> bool: ...
    def renew_claim(self, job_id: str, worker_id: str, lease_seconds: int) -> bool: ...
    def complete(self, job_id: str, worker_id: str, result: dict) -> bool: ...
    def fail(self, job_id: str, worker_id: str, error: str) -> bool: ...


class SqliteUploadJobRepository:
    """SQLite implementation of the durable upload-job persistence contract."""
    def __init__(
        self,
        db_path: str = settings.DB_PATH,
    ) -> None:
        self._db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS upload_jobs (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    video_path TEXT NOT NULL,
                    log_path TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    worker_id TEXT,
                    lease_expires_at INTEGER,
                    flight_id INTEGER,
                    artifact_id TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            existing_columns = {
                row["name"] for row in conn.execute("PRAGMA table_info(upload_jobs)")
            }
            for name, definition in (
                ("worker_id", "TEXT"),
                ("lease_expires_at", "INTEGER"),
                ("flight_id", "INTEGER"),
                ("artifact_id", "TEXT"),
            ):
                if name not in existing_columns:
                    conn.execute(f"ALTER TABLE upload_jobs ADD COLUMN {name} {definition}")
            conn.commit()
        finally:
            conn.close()

    def create(self, job_id: str, name: str, video_path, log_path) -> dict:
        now = int(time.time())
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT INTO upload_jobs
                    (id, name, video_path, log_path, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'queued', ?, ?)
                """,
                (job_id, name, str(video_path), str(log_path), now, now),
            )
            conn.commit()
        finally:
            conn.close()
        return self.get(job_id) or {}

    def get(self, job_id: str) -> dict | None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT * FROM upload_jobs WHERE id = ?", (job_id,)).fetchone()
        finally:
            conn.close()
        return self._row_to_dict(row) if row else None

    def set_status(self, job_id: str, worker_id: str, status: str, lease_seconds: int) -> bool:
        """Advance a claimed job while retaining the worker's active lease."""
        return self._update_claimed(
            job_id, worker_id=worker_id, status=status, lease_seconds=lease_seconds
        )

    def record_flight_id(self, job_id: str, worker_id: str, flight_id: int, lease_seconds: int) -> bool:
        return self._update_claimed(
            job_id,
            worker_id,
            status="importing",
            lease_seconds=lease_seconds,
            flight_id=flight_id,
        )

    def begin_processing(
        self,
        job_id: str,
        worker_id: str,
        artifact_id: str,
        lease_seconds: int,
    ) -> bool:
        return self._update_claimed(
            job_id,
            worker_id,
            status="processing",
            lease_seconds=lease_seconds,
            artifact_id=artifact_id,
        )

    def renew_claim(self, job_id: str, worker_id: str, lease_seconds: int) -> bool:
        return self._update_claimed(
            job_id, worker_id, status=None, lease_seconds=lease_seconds
        )

    def complete(self, job_id: str, worker_id: str, result: dict) -> bool:
        return self._finish_claimed(
            job_id, worker_id, "completed", result_json=json.dumps(result), error=None
        )

    def fail(self, job_id: str, worker_id: str, error: str) -> bool:
        return self._finish_claimed(job_id, worker_id, "failed", error=error[:1000])

    def _update_claimed(
        self,
        job_id: str,
        *,
        worker_id: str,
        status: str | None,
        lease_seconds: int,
        flight_id: int | None = None,
        artifact_id: str | None = None,
    ) -> bool:
        now = int(time.time())
        assignments = ["updated_at = ?", "lease_expires_at = ?"]
        values: list[object] = [now, now + lease_seconds]
        if status is not None:
            assignments.append("status = ?")
            values.append(status)
        if flight_id is not None:
            assignments.append("flight_id = ?")
            values.append(flight_id)
        if artifact_id is not None:
            assignments.append("artifact_id = ?")
            values.append(artifact_id)
        conn = self._connect()
        try:
            cursor = conn.execute(
                f"UPDATE upload_jobs SET {', '.join(assignments)} "
                "WHERE id = ? AND worker_id = ? AND status IN ('importing', 'processing')",
                (*values, job_id, worker_id),
            )
            conn.commit()
            return cursor.rowcount == 1
        finally:
            conn.close()

    def _finish_claimed(
        self,
        job_id: str,
        worker_id: str,
        status: str,
        *,
        result_json: str | None = None,
        error: str | None = None,
    ) -> bool:
        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                UPDATE upload_jobs
                SET status = ?, result_json = ?, error = ?, worker_id = NULL,
                    lease_expires_at = NULL, updated_at = ?
                WHERE id = ? AND worker_id = ? AND status IN ('importing', 'processing')
                """,
                (status, result_json, error, int(time.time()), job_id, worker_id),
            )
            conn.commit()
            return cursor.rowcount == 1
        finally:
            conn.close()

    def requeue_expired(self, now: int | None = None) -> int:
        """Make only abandoned claims available; never steal a live worker's job."""
        now = int(time.time()) if now is None else now
        conn = self._connect()
        try:
            cursor = conn.execute(
                """
                UPDATE upload_jobs
                SET status = 'queued', worker_id = NULL, lease_expires_at = NULL, updated_at = ?
                WHERE status IN ('importing', 'processing')
                  AND COALESCE(lease_expires_at, 0) <= ?
                """,
                (now, now),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()

    def claim_next(self, worker_id: str, lease_seconds: int) -> dict | None:
        """Atomically lease the oldest available job across application workers."""
        now = int(time.time())
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                """
                SELECT * FROM upload_jobs
                WHERE status = 'queued'
                   OR (status IN ('importing', 'processing')
                       AND COALESCE(lease_expires_at, 0) <= ?)
                ORDER BY created_at, id LIMIT 1
                """,
                (now,),
            ).fetchone()
            if row is None:
                conn.commit()
                return None
            cursor = conn.execute(
                """
                UPDATE upload_jobs
                SET status = 'importing', worker_id = ?, lease_expires_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (worker_id, now + lease_seconds, now, row["id"]),
            )
            if cursor.rowcount != 1:
                conn.rollback()
                return None
            conn.commit()
            claimed = dict(row)
            claimed["status"] = "importing"
            claimed["worker_id"] = worker_id
            claimed["lease_expires_at"] = now + lease_seconds
            return self._row_to_dict(claimed)
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row: sqlite3.Row | dict) -> dict:
        result = json.loads(row["result_json"]) if row["result_json"] else None
        return {
            "id": row["id"],
            "name": row["name"],
            "status": row["status"],
            "result": result,
            "error": row["error"],
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "videoPath": row["video_path"],
            "logPath": row["log_path"],
            "flightId": row["flight_id"],
            "artifactId": row["artifact_id"],
            "workerId": row["worker_id"],
            "leaseExpiresAt": row["lease_expires_at"],
        }


def new_job_id() -> str:
    return uuid4().hex


# Kept as a compatibility import while callers migrate to UploadJobRepository.
UploadJobService = SqliteUploadJobRepository
