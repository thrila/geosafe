from fastapi import APIRouter, UploadFile, File, Form,HTTPException, Request
from starlette.concurrency import run_in_threadpool
from pathlib import Path
from core.config import settings
from utils.utils import _save_upload_to_temp, get_telemetary, _confidence_to_float,_format_confidence
from statistics import mean
import tempfile
from controllers.capture import extract_clear_frames
from controllers.predict import predict
from collections import Counter
from database.connector import FlightDB, to_json
import json

upload_router = APIRouter()


@upload_router.post("/upload")
async def upload(
    request: Request,
    name: str = Form(...),
    video: UploadFile = File(...),
    log: UploadFile = File(...)
):
    print("route entered")

    video_ext = Path(video.filename).suffix.lower()
    log_ext = Path(log.filename).suffix.lower()

    if video.content_type not in {"video/mp4", "video/x-matroska"}:
        raise HTTPException(400, "Invalid MIME type")
    
    if video_ext not in settings.VIDEO_EXTENSIONS:
        raise HTTPException(400, "Invalid video format")

    if log_ext != ".txt":
        raise HTTPException(400, "Invalid log format")

    temp_video_path = await _save_upload_to_temp(video)
    log_path = await _save_upload_to_temp(log)
    _ = get_telemetary(name, log_path)
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

        with FlightDB("telemetry.db") as db:
            #NOTE: How do i get the number?
            flight = db.flight(1)

            data = {
                "flight": {
                    "id": flight.id,
                    "name": flight.name,
                    "start_ts": flight.start_ts,
                    "end_ts": flight.end_ts,
                    "total_frames": flight.total_frames,
                },
                "battery": to_json(flight.battery_drain()),
                "track": to_json(flight.track()),
            }

            print(json.dumps(data, indent=2))

            return {
                "filename": video.filename,
                "frames_analyzed": len(per_frame_results),
                "prediction": most_common_prediction,
                "confidence": _format_confidence(average_confidence),
                "per_frame_results": per_frame_results,
                "log": log_path,
                "data": data,
            }
    finally:
        temp_video_path.unlink(missing_ok=True)
