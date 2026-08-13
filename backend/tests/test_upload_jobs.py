from __future__ import annotations

from pathlib import Path

from services.upload_jobs import UploadJobService


def test_upload_job_can_be_claimed_completed_and_read(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"), tmp_path / "uploads")
    video, log = service.new_job_paths("job-1", ".mp4", ".txt")
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    log.write_bytes(b"log")

    service.create("job-1", "Survey", video, log)
    job = service.claim_next()

    assert job is not None
    assert job["status"] == "importing"
    service.set_status("job-1", "processing")
    service.complete("job-1", {"flight": {"id": "7"}})

    finished = service.get("job-1")
    assert finished is not None
    assert finished["status"] == "completed"
    assert finished["result"] == {"flight": {"id": "7"}}


def test_interrupted_upload_jobs_are_queued_again(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"), tmp_path / "uploads")
    video, log = service.new_job_paths("job-1", ".mp4", ".txt")
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    log.write_bytes(b"log")
    service.create("job-1", "Survey", video, log)
    service.claim_next()

    service.requeue_interrupted()

    assert service.get("job-1")["status"] == "queued"
