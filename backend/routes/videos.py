import logging
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile, Request
from starlette.concurrency import run_in_threadpool

from core.config import settings
from utils.utils import validate_upload, save_upload_to_temp

logger = logging.getLogger(__name__)

video_router = APIRouter()


@video_router.post("/video")
async def classify_video(
    request: Request,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    validate_upload(file, "video", settings.VIDEO_EXTENSIONS)
    await request.app.state.pipeline_ready.wait()

    temp_path = await save_upload_to_temp(file)
    try:
        pipeline = request.app.state.pipeline
        with tempfile.TemporaryDirectory() as td:
            result = await run_in_threadpool(pipeline.process_video, temp_path, Path(td))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except (OSError, IOError) as exc:
        raise HTTPException(status_code=422, detail=f"Could not process video: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Video processing failed")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the video.")
    finally:
        temp_path.unlink(missing_ok=True)
    return {"filename": file.filename, **result}
