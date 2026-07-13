from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile, Request
from starlette.concurrency import run_in_threadpool

from controllers.predict import predict
from core.config import settings
from utils.utils import _validate_upload, _save_upload_to_temp


image_router = APIRouter()


@image_router.post("/image")
async def classify_image(
    request: Request,
    file: UploadFile = File(...),
) -> dict[str, Any]:
    _validate_upload(file, "image", settings.IMAGE_EXTENSIONS)
    temp_image_path = await _save_upload_to_temp(file)

    try:
        result = await run_in_threadpool(
            predict,
            temp_image_path,
            request.app.state.model,
            request.app.state.class_names,
        )
    except (OSError, ValueError) as exc:
        raise HTTPException(
            status_code=400,
            detail="Uploaded image could not be processed as a valid image.",
        ) from exc
    finally:
        temp_image_path.unlink(missing_ok=True)

    return {
        "filename": file.filename,
        "prediction": result["prediction"],
        "confidence": result["confidence"],
    }

