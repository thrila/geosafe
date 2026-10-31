"""Drive queued uploads through the real worker loop and SQLite job repository."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest

from services.log_importer import LogImportError


def _submit(client, upload) -> str:
    filename, content, media_type = upload
    response = client.post(
        "/api/v1/upload/jobs",
        data={"name": "North field"},
        files={
            "video": (filename, content, media_type),
            "log": ("flight.txt", b"DJI log", "text/plain"),
        },
    )
    assert response.status_code == 202
    return response.json()["id"]


def _wait_until_finished(client, job_id: str, timeout: float = 10.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = client.get(f"/api/v1/upload/jobs/{job_id}").json()
        if job["status"] in {"completed", "failed"}:
            return job
        time.sleep(0.02)
    pytest.fail(f"Job {job_id} did not finish within {timeout}s")


@pytest.fixture()
def worker_client(upload_client):
    state = upload_client.app.state
    with patch.object(state.log_importer, "import_log", return_value=42) as import_log, \
         patch.object(
             state.flight_service,
             "build_upload_response",
             new_callable=AsyncMock,
             return_value={"schemaVersion": "1.0"},
         ):
        upload_client.import_log = import_log
        yield upload_client


def test_worker_completes_a_queued_upload(worker_client, tmp_upload_video):
    job_id = _submit(worker_client, tmp_upload_video)

    job = _wait_until_finished(worker_client, job_id)

    assert job["status"] == "completed"
    assert job["result"] == {"schemaVersion": "1.0"}
    assert job["flightId"] == 42
    assert len(job["artifactId"]) == 32
    worker_client.import_log.assert_called_once()


def test_worker_reports_log_import_failures(worker_client, tmp_upload_video):
    worker_client.import_log.side_effect = LogImportError("Bad DJI log.")
    job_id = _submit(worker_client, tmp_upload_video)

    job = _wait_until_finished(worker_client, job_id)

    assert job["status"] == "failed"
    assert job["error"] == "Bad DJI log."
    assert job["result"] is None


def test_worker_reports_video_failures(worker_client, tmp_upload_video):
    worker_client.app.state.pipeline.process_video = lambda *args: (_ for _ in ()).throw(
        ValueError("No clear frames could be extracted from the uploaded video.")
    )
    job_id = _submit(worker_client, tmp_upload_video)

    job = _wait_until_finished(worker_client, job_id)

    assert job["status"] == "failed"
    assert "No clear frames" in job["error"]


def test_worker_hides_unexpected_failures(worker_client, tmp_upload_video):
    worker_client.app.state.pipeline.process_video = lambda *args: (_ for _ in ()).throw(
        KeyError("secret internals")
    )
    job_id = _submit(worker_client, tmp_upload_video)

    job = _wait_until_finished(worker_client, job_id)

    assert job["status"] == "failed"
    assert job["error"] == "An internal error occurred."


def test_worker_survives_a_failure_it_cannot_record(worker_client, tmp_upload_video):
    state = worker_client.app.state
    worker_client.import_log.side_effect = LogImportError("Bad DJI log.")

    with patch.object(state.upload_jobs, "fail", side_effect=OSError("disk full")) as fail:
        _submit(worker_client, tmp_upload_video)
        deadline = time.monotonic() + 10
        while not fail.called and time.monotonic() < deadline:
            time.sleep(0.02)
        assert fail.called

    worker_client.import_log.side_effect = None
    job = _wait_until_finished(worker_client, _submit(worker_client, tmp_upload_video))

    assert job["status"] == "completed"


def test_job_api_does_not_expose_server_paths(worker_client, tmp_upload_video):
    job = worker_client.get(
        f"/api/v1/upload/jobs/{_submit(worker_client, tmp_upload_video)}"
    ).json()

    assert not {"videoPath", "logPath", "workerId", "leaseExpiresAt"} & set(job)
