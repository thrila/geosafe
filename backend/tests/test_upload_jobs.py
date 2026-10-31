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


def test_claimed_job_records_each_worker_stage(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"))
    video, log = LocalUploadStorage(tmp_path / "uploads").new_job_paths("job-1", ".mp4", ".txt")
    service.create("job-1", "Survey", video, log)
    service.claim_next("worker-1", lease_seconds=60)

    assert service.record_flight_id("job-1", "worker-1", 7, 60) is True
    assert service.begin_processing("job-1", "worker-1", "artifact-1", 60) is True
    assert service.renew_claim("job-1", "worker-1", 60) is True

    job = service.get("job-1")
    assert job["status"] == "processing"
    assert job["flightId"] == 7
    assert job["artifactId"] == "artifact-1"


def test_worker_stages_are_rejected_for_a_different_worker(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"))
    video, log = LocalUploadStorage(tmp_path / "uploads").new_job_paths("job-1", ".mp4", ".txt")
    service.create("job-1", "Survey", video, log)
    service.claim_next("worker-1", lease_seconds=60)

    assert service.record_flight_id("job-1", "worker-2", 7, 60) is False
    assert service.begin_processing("job-1", "worker-2", "artifact-1", 60) is False
    assert service.renew_claim("job-1", "worker-2", 60) is False


def test_repeatedly_interrupted_job_fails_instead_of_retrying_forever(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"), max_attempts=2)
    video, log = LocalUploadStorage(tmp_path / "uploads").new_job_paths("job-1", ".mp4", ".txt")
    service.create("job-1", "Survey", video, log)

    assert service.claim_next("worker-1", lease_seconds=0) is not None
    assert service.claim_next("worker-2", lease_seconds=0) is not None
    assert service.claim_next("worker-3", lease_seconds=0) is None

    job = service.get("job-1")
    assert job["status"] == "failed"
    assert job["error"] == "Processing was interrupted too many times."


def test_live_job_on_its_last_attempt_is_not_failed(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"), max_attempts=1)
    video, log = LocalUploadStorage(tmp_path / "uploads").new_job_paths("job-1", ".mp4", ".txt")
    service.create("job-1", "Survey", video, log)
    service.claim_next("worker-1", lease_seconds=60)

    assert service.claim_next("worker-2", lease_seconds=60) is None

    assert service.get("job-1")["status"] == "importing"


def test_claim_does_not_take_a_live_lease(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"))
    video, log = LocalUploadStorage(tmp_path / "uploads").new_job_paths("job-1", ".mp4", ".txt")
    service.create("job-1", "Survey", video, log)

    assert service.claim_next("worker-1", lease_seconds=60) is not None
    assert service.claim_next("worker-2", lease_seconds=60) is None


def test_failed_job_is_reported_as_failed(tmp_path: Path):
    service = UploadJobService(str(tmp_path / "jobs.db"))
    video, log = LocalUploadStorage(tmp_path / "uploads").new_job_paths("job-1", ".mp4", ".txt")
    service.create("job-1", "Survey", video, log)
    service.claim_next("worker-1", lease_seconds=60)

    assert service.fail("job-1", "worker-1", "Bad log.") is True

    job = service.get("job-1")
    assert job["status"] == "failed"
    assert job["error"] == "Bad log."


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
