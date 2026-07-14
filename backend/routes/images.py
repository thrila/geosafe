import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile, Request
from starlette.concurrency import run_in_threadpool

from core.config import settings
from utils.utils import validate_upload, save_upload_to_temp

logger = logging.getLogger(__name__)

image_router = APIRouter()


@image_router.post("/image")
async def classify_image(
    request: Request,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    validate_upload(file, "image", settings.IMAGE_EXTENSIONS)
    await request.app.state.pipeline_ready.wait()

    temp_path = await save_upload_to_temp(file)
    try:
        pipeline = request.app.state.pipeline
        result = await run_in_threadpool(pipeline.process_image, temp_path)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        logger.exception("Image processing failed")
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the image.")
    finally:
        temp_path.unlink(missing_ok=True)
    return {"filename": file.filename, **result}
