import logging
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from core.config import settings
from services.flights import FlightService
from utils.utils import validate_upload, save_upload_to_temp

logger = logging.getLogger(__name__)

upload_router = APIRouter()
_flight_service = FlightService()


@upload_router.post("/upload")
async def upload(
    request: Request,
    name: str = Form(...),
    video: UploadFile = File(...),
    log: UploadFile = File(...),
) -> dict:
    validate_upload(video, "video", settings.VIDEO_EXTENSIONS)
    log_suffix = Path(log.filename or "").suffix.lower()
    if log_suffix != ".txt":
        raise HTTPException(
            status_code=400,
            detail="Invalid log format. Only .txt log files are accepted.",
        )

    temp_video = await save_upload_to_temp(video)
    temp_log = await save_upload_to_temp(log)

    try:
        await request.app.state.pipeline_ready.wait()
        pipeline = request.app.state.pipeline

        video_result = await run_in_threadpool(
            pipeline.process_video, temp_video, Path("output")
        )
        return await _flight_service.build_upload_response(video_result, name)

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
