from __future__ import annotations

from pathlib import Path

from services.upload_jobs import UploadJobService
from services.upload_storage import LocalUploadStorage


def test_upload_job_can_be_claimed_completed_and_read(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"))
    storage = LocalUploadStorage(tmp_path / "uploads")
    assert storage.job_dir.is_absolute()
    video, log = storage.new_job_paths("job-1", ".mp4", ".txt")
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    log.write_bytes(b"log")

    service.create("job-1", "Survey", video, log)
    worker_id = "worker-1"
    job = service.claim_next(worker_id, lease_seconds=60)

    assert job is not None
    assert job["status"] == "importing"
    assert Path(job["videoPath"]).is_absolute()
    assert Path(job["logPath"]).is_absolute()
    service.set_status("job-1", worker_id, "processing", lease_seconds=60)
    service.complete("job-1", worker_id, {"flight": {"id": "7"}})

    finished = service.get("job-1")
    assert finished is not None
    assert finished["status"] == "completed"
    assert finished["result"] == {"flight": {"id": "7"}}


def test_interrupted_upload_jobs_are_queued_again(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"))
    video, log = LocalUploadStorage(tmp_path / "uploads").new_job_paths("job-1", ".mp4", ".txt")
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    log.write_bytes(b"log")
    service.create("job-1", "Survey", video, log)
    job = service.claim_next("worker-1", lease_seconds=60)

    assert job is not None
    service.requeue_expired(now=job["leaseExpiresAt"] + 1)

    assert service.get("job-1")["status"] == "queued"


def test_active_upload_job_is_not_requeued(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"))
    video, log = LocalUploadStorage(tmp_path / "uploads").new_job_paths("job-1", ".mp4", ".txt")
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    log.write_bytes(b"log")
    service.create("job-1", "Survey", video, log)

    job = service.claim_next("worker-1", lease_seconds=60)

    assert job is not None
    assert service.requeue_expired(now=job["leaseExpiresAt"] - 1) == 0
    assert service.get("job-1")["status"] == "importing"


def test_only_the_claiming_worker_can_finish_a_job(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"))
    video, log = LocalUploadStorage(tmp_path / "uploads").new_job_paths("job-1", ".mp4", ".txt")
    video.parent.mkdir(parents=True)
    video.write_bytes(b"video")
    log.write_bytes(b"log")
    service.create("job-1", "Survey", video, log)

    job = service.claim_next("worker-1", lease_seconds=60)

    assert job is not None
    assert service.complete("job-1", "worker-2", {"flight": {}}) is False
    assert service.get("job-1")["status"] == "importing"
