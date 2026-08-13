"""Durable SQLite-backed queue state for long-running flight uploads."""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from uuid import uuid4

from core.config import settings


class UploadJobService:
    def __init__(
        self,
        db_path: str = settings.DB_PATH,
        job_dir: Path = settings.UPLOAD_JOB_DIR,
    ) -> None:
        self._db_path = db_path
        self.job_dir = job_dir
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        self.job_dir.mkdir(parents=True, exist_ok=True)
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
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def new_job_paths(self, job_id: str, video_suffix: str, log_suffix: str) -> tuple[Path, Path]:
        directory = self.job_dir / job_id
        return directory / f"video{video_suffix}", directory / f"flight{log_suffix}"

    def create(self, job_id: str, name: str, video_path: Path, log_path: Path) -> dict:
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

    def set_status(self, job_id: str, status: str) -> None:
        self._update(job_id, status=status)

    def complete(self, job_id: str, result: dict) -> None:
        self._update(job_id, status="completed", result_json=json.dumps(result), error=None)

    def fail(self, job_id: str, error: str) -> None:
        self._update(job_id, status="failed", error=error[:1000])

    def _update(
        self,
        job_id: str,
        *,
        status: str,
        result_json: str | None = None,
        error: str | None = None,
    ) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                UPDATE upload_jobs
                SET status = ?, result_json = ?, error = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, result_json, error, int(time.time()), job_id),
            )
            conn.commit()
        finally:
            conn.close()

    def requeue_interrupted(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                UPDATE upload_jobs SET status = 'queued', updated_at = ?
                WHERE status IN ('importing', 'processing')
                """,
                (int(time.time()),),
            )
            conn.commit()
        finally:
            conn.close()

    def claim_next(self) -> dict | None:
        """Atomically reserve the oldest queued job across application workers."""
        conn = self._connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM upload_jobs WHERE status = 'queued' ORDER BY created_at, id LIMIT 1"
            ).fetchone()
            if row is None:
                conn.commit()
                return None
            conn.execute(
                "UPDATE upload_jobs SET status = 'importing', updated_at = ? WHERE id = ?",
                (int(time.time()), row["id"]),
            )
            conn.commit()
            claimed = dict(row)
            claimed["status"] = "importing"
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
        }


def new_job_id() -> str:
    return uuid4().hex
