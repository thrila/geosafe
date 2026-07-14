import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request
from starlette.concurrency import run_in_threadpool

from core.config import settings
from utils.utils import validate_upload, save_upload_to_temp

logger = logging.getLogger(__name__)

upload_router = APIRouter()


def _haversine_km(lat1, lon1, lat2, lon2):
    import math
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _build_slides(per_frame: list[dict]) -> list[dict]:
    slides = []
    for i, f in enumerate(per_frame):
        url = f.get("image_url")
        if url:
            disease = f.get("prediction", {}).get("disease", "Unknown")
            slides.append({
                "kind": "image",
                "src": url,
                "caption": f"Frame {f.get('frame', 0)} — {disease}",
            })
    return slides


@upload_router.post("/upload")
async def upload(
    request: Request,
    name: str = Form(...),
    video: UploadFile = File(...),
    log: UploadFile = File(...),
) -> dict[str, Any]:
    validate_upload(video, "video", settings.VIDEO_EXTENSIONS)
    log_suffix = Path(log.filename or "").suffix.lower()
    if log_suffix != ".txt":
        raise HTTPException(status_code=400, detail="Invalid log format. Only .txt log files are accepted.")

    temp_video = await save_upload_to_temp(video)
    temp_log = await save_upload_to_temp(log)

    try:
        await request.app.state.pipeline_ready.wait()
        pipeline = request.app.state.pipeline

        video_result = await run_in_threadpool(pipeline.process_video, temp_video, Path("output"))

        # Telemetry
        import sqlite3, math
        track_pts = []
        telemetry_rows = []
        flight_id = None
        start_ts = 0
        end_ts = 0
        battery_start = None
        battery_end = None

        try:
            conn = sqlite3.connect(settings.DB_PATH)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT id, name, start_ts, end_ts, total_frames FROM flights ORDER BY id DESC LIMIT 1")
            frow = cur.fetchone()
            if frow:
                flight_id = frow["id"]
                start_ts = frow["start_ts"]
                end_ts = frow["end_ts"]
                cur.execute("SELECT latitude, longitude, height, x_speed, y_speed, z_speed, battery_level, battery_temp, gps_num FROM telemetry WHERE flight_id = ? ORDER BY frame_index", (flight_id,))
                telemetry_rows = cur.fetchall()
            conn.close()
        except Exception as e:
            logger.warning("Telemetry DB not available: %s", e)

        if telemetry_rows:
            track_pts = [{"latitude": r["latitude"], "longitude": r["longitude"], "height": r["height"] or 0} for r in telemetry_rows]
            battery_start = telemetry_rows[0]["battery_level"]
            battery_end = telemetry_rows[-1]["battery_level"]
            max_speed = round(max(
                math.sqrt(r["x_speed"]**2 + r["y_speed"]**2 + r["z_speed"]**2)
                for r in telemetry_rows
            ), 1)
            max_height = round(max(r["height"] or 0 for r in telemetry_rows), 1)
            max_battery_temp = round(max(r["battery_temp"] or 0 for r in telemetry_rows), 1)
        else:
            max_speed = 0
            max_height = 0
            max_battery_temp = 0

        duration_s = (end_ts - start_ts) / 1000 if end_ts > start_ts else 0
        mins = int(duration_s // 60)
        secs = int(duration_s % 60)
        duration_str = f"{mins}:{secs:02d} min" if mins > 0 else f"{secs}s"

        # Route distance
        route_distance_km = 0
        if len(track_pts) > 1:
            route_distance_km = round(sum(
                _haversine_km(track_pts[i]["latitude"], track_pts[i]["longitude"], track_pts[i+1]["latitude"], track_pts[i+1]["longitude"])
                for i in range(len(track_pts) - 1)
            ), 2)

        start_point = track_pts[0] if track_pts else None
        end_point = track_pts[-1] if track_pts else None
        battery_drained = round((battery_start or 0) - (battery_end or 0), 1) if battery_start is not None else 0
        avg_gps = round(sum(r["gps_num"] or 0 for r in telemetry_rows) / len(telemetry_rows)) if telemetry_rows else 0

        per_frame = video_result.get("per_frame_results", [])
        diseased_frames = [f for f in per_frame if f.get("prediction", {}).get("disease", "").lower() != "healthy"]
        diseases = list(dict.fromkeys(f["prediction"]["disease"] for f in diseased_frames if f["prediction"]["disease"]))

        # Store slides in DB
        slides = _build_slides(per_frame)
        try:
            import sqlite3
            conn = sqlite3.connect(settings.DB_PATH)
            for slide in slides:
                disease = slide.get("caption", "").split("—")[-1].strip() if "—" in slide.get("caption", "") else ""
                conn.execute("INSERT INTO slides (flight_id, frame_index, image_url, disease, caption) VALUES (?, ?, ?, ?, ?)",
                    (flight_id, 0, slide["src"], disease, slide.get("caption", "")))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("Failed to store slides: %s", e)

        return {
            "flight": {
                "id": str(flight_id) if flight_id else name,
                "name": name,
                "date": f"{start_ts}",
                "duration": duration_str,
                "location": "Otuoke, Bayelsa",
                "summary": f"Survey over {name}.",
            },
            "path": [{"longitude": p["longitude"], "latitude": p["latitude"], "height": p["height"]} for p in track_pts] if track_pts else [],
            "telemetry": {
                "dateTime": str(end_ts) if end_ts else "",
                "cards": [
                    {"label": "Altitude", "value": f"{max_height} m", "detail": "Maximum height."},
                    {"label": "Speed", "value": f"{max_speed} m/s", "detail": "Max ground speed."},
                    {"label": "GPS", "value": f"{avg_gps} sats", "detail": "Average satellites."},
                    {"label": "Battery", "value": f"{battery_start or 0:.0f} %", "detail": f"Drained {battery_drained:.0f}%."},
                    {"label": "Battery Temp", "value": f"{max_battery_temp} °C", "detail": "Peak temperature."},
                    {"label": "Distance", "value": f"{route_distance_km} km", "detail": "Total route."},
                ],
            },
            "result": {
                "routeDistanceKm": route_distance_km,
                "startPoint": start_point,
                "endPoint": end_point,
                "batteryDrainedPct": battery_drained,
                "maxSpeedMs": max_speed,
                "maxHeightM": max_height,
                "batteryTempC": max_battery_temp,
                "diseasesDetected": diseases,
                "slides": slides,
            },
        }

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except (OSError, IOError) as exc:
        raise HTTPException(status_code=422, detail=f"Could not process video: {exc}")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Upload processing failed")
        raise HTTPException(status_code=500, detail="An internal error occurred.")
    finally:
        temp_video.unlink(missing_ok=True)
        temp_log.unlink(missing_ok=True)
