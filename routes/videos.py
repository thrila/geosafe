from fastapi import APIRouter, File, HTTPException, UploadFile, Request
from core.config import settings
from utils.utils import _validate_upload, _save_upload_to_temp, _format_confidence, _confidence_to_float
from starlette.concurrency import run_in_threadpool
from collections import Counter
from statistics import mean
from typing import Any
import tempfile
from controllers.predict import predict
from controllers.capture import extract_clear_frames


video_router = APIRouter()



@video_router.post("/video")
async def classify_video(request: Request ,file: UploadFile = File(...)) -> dict[str, Any]:
    _validate_upload(file, "video", settings.VIDEO_EXTENSIONS)
    temp_video_path = await _save_upload_to_temp(file)

    try:
        with tempfile.TemporaryDirectory() as frames_dir:
            try:
                frame_paths = await run_in_threadpool(
                    extract_clear_frames,
                    temp_video_path,
                    frames_dir,
                )
            except (OSError, ValueError) as exc:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded video could not be processed.",
                ) from exc

            if not frame_paths:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "No clear frames could be extracted from the uploaded video. "
                        "Try a longer or clearer video."
                    ),
                )

            per_frame_results: list[dict[str, str]] = []
            for frame_path in frame_paths:
                result = await run_in_threadpool(
                    predict,
                    frame_path,
                    request.app.state.model,
                    request.app.state.class_names,
                )
                per_frame_results.append(
                    {
                        "filename": frame_path.name,
                        "prediction": result["prediction"],
                        "confidence": result["confidence"],
                    }
                )

            most_common_prediction = Counter(
                result["prediction"] for result in per_frame_results
            ).most_common(1)[0][0]
            average_confidence = mean(
                _confidence_to_float(result["confidence"]) for result in per_frame_results
            )

            return {
                "filename": file.filename,
                "frames_analyzed": len(per_frame_results),
                "prediction": most_common_prediction,
                "confidence": _format_confidence(average_confidence),
                "per_frame_results": per_frame_results,
            }
    finally:
        temp_video_path.unlink(missing_ok=True)

