"""Filesystem storage for durable upload payloads.

Job state belongs in a repository; the uploaded bytes belong in this adapter.
Keeping those concerns separate lets the job repository move to another database
without changing where or how upload files are retained.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from core.config import settings


class UploadStorage(Protocol):
    def new_job_paths(
        self, job_id: str, video_suffix: str, log_suffix: str
    ) -> tuple[Path, Path]: ...


class LocalUploadStorage:
    """Local-disk implementation for job-owned video and flight-log payloads."""

    def __init__(self, job_dir: Path = settings.UPLOAD_JOB_DIR) -> None:
        self.job_dir = Path(job_dir).resolve()
        self.job_dir.mkdir(parents=True, exist_ok=True)

    def new_job_paths(
        self, job_id: str, video_suffix: str, log_suffix: str
    ) -> tuple[Path, Path]:
        directory = self.job_dir / job_id
        return directory / f"video{video_suffix}", directory / f"flight{log_suffix}"
