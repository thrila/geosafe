import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from core.config import settings
from services.flights import FlightService
from services.log_importer import DJIFlightLogImporter, LogImportError
from services.upload_jobs import UploadJobService, new_job_id
from utils.utils import validate_upload, save_upload_to_path, save_upload_to_temp

logger = logging.getLogger(__name__)

upload_router = APIRouter()
_flight_service = FlightService()
_log_importer = DJIFlightLogImporter()
_upload_jobs = UploadJobService()


def _validate_flight_upload(name: str, video: UploadFile, log: UploadFile) -> str:
    name = name.strip()
    if not 1 <= len(name) <= 80:
        raise HTTPException(status_code=422, detail="Flight name must be 1 to 80 characters.")
    validate_upload(video, "video", settings.VIDEO_EXTENSIONS)
    log_suffix = Path(log.filename or "").suffix.lower()
    if log_suffix != ".txt":
        raise HTTPException(
            status_code=400,
            detail="Invalid log format. Only .txt log files are accepted.",
        )
    return name


@upload_router.post("/upload")
async def upload(
    request: Request,
    name: str = Form(...),
    video: UploadFile = File(...),
    log: UploadFile = File(...),
) -> dict:
    name = _validate_flight_upload(name, video, log)

    temp_video = await save_upload_to_temp(video)
    temp_log = await save_upload_to_temp(log)

    try:
        try:
            flight_id = await run_in_threadpool(_log_importer.import_log, name, temp_log)
        except LogImportError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

        await request.app.state.pipeline_ready.wait()
        pipeline = request.app.state.pipeline
        artifact_id = uuid4().hex
        artifact_dir = settings.OUTPUT_DIR / artifact_id

        video_result = await run_in_threadpool(
            pipeline.process_video,
            temp_video,
            artifact_dir,
            f"/api/v1/images/{artifact_id}",
        )
        return await _flight_service.build_upload_response(
            video_result, name, flight_id, artifact_id
        )

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except (OSError, IOError) as exc:
        raise HTTPException(status_code=422, detail=f"Could not process video: {exc}")
    except HTTPException:
        raise
    except Exception:
        logger.exception("Upload processing failed")
        raise HTTPException(status_code=500, detail="An internal error occurred.")
    finally:
        temp_video.unlink(missing_ok=True)
        temp_log.unlink(missing_ok=True)


@upload_router.post("/upload/jobs", status_code=202)
async def create_upload_job(
    name: str = Form(...),
    video: UploadFile = File(...),
    log: UploadFile = File(...),
) -> dict:
    """Persist a flight upload and return immediately; a worker processes it later."""
    name = _validate_flight_upload(name, video, log)
    job_id = new_job_id()
    video_suffix = Path(video.filename or "").suffix.lower()
    log_suffix = Path(log.filename or "").suffix.lower()
    video_path, log_path = _upload_jobs.new_job_paths(job_id, video_suffix, log_suffix)
    try:
        await save_upload_to_path(video, video_path)
        await save_upload_to_path(log, log_path)
        job = _upload_jobs.create(job_id, name, video_path, log_path)
        return {key: value for key, value in job.items() if key not in {"videoPath", "logPath"}}
    except Exception:
        for path in (video_path, log_path):
            path.unlink(missing_ok=True)
        if video_path.parent.exists():
            try:
                video_path.parent.rmdir()
            except OSError:
                pass
        raise


@upload_router.get("/upload/jobs/{job_id}")
async def get_upload_job(job_id: str) -> dict:
    job = _upload_jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found.")
    return {key: value for key, value in job.items() if key not in {"videoPath", "logPath"}}
