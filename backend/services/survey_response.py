"""Build the versioned, research-friendly response for a completed survey."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
import hashlib
from pathlib import Path

from core.config import settings


def _iso_utc(timestamp_ms: int | float | None) -> str | None:
    if timestamp_ms is None:
        return None
    return datetime.fromtimestamp(float(timestamp_ms) / 1000, timezone.utc).isoformat().replace("+00:00", "Z")


@lru_cache(maxsize=16)
def _sha256_file(path: str, size: int, modified_ns: int) -> str | None:
    del size, modified_ns  # Included in the cache key to invalidate changed artifacts.
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as artifact:
            for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError:
        return None
    return f"sha256:{digest.hexdigest()}"


def _artifact_digest(path: Path) -> str | None:
    try:
        stat = path.stat()
    except OSError:
        return None
    return _sha256_file(str(path), stat.st_size, stat.st_mtime_ns)


def _model_record(name: str, path: Path, input_type: str) -> dict:
    return {
        "name": name,
        "version": None,
        "artifactDigest": _artifact_digest(path),
        "labelsVersion": None,
        "inputType": input_type,
    }


def _alternatives(probabilities: dict, selected: str) -> list[dict]:
    return [
        {"name": name, "score": score}
        for name, score in sorted(
            probabilities.items(), key=lambda item: item[1], reverse=True
        )[:3]
        if name != selected
    ]


def build_survey_response(
    video_result: dict,
    name: str,
    flight_id: int,
    artifact_id: str,
    flight_info: dict,
    telemetry: dict,
    telemetry_rows: list[dict],
    pipeline_config,
) -> dict:
    """Convert frame/tile classifier output into the public survey contract.

    Each observation is deliberately a positive tile in one sampled frame. The
    current classifier does not detect individual plants or reliably match
    video time to log time, so this response does not invent plant counts or GPS.
    """
    frame_results = video_result.get("per_frame_results", [])
    by_condition: dict[str, list[dict]] = defaultdict(list)
    observations = []
    plant_counts: Counter[str] = Counter()

    for row in frame_results:
        prediction = row.get("prediction", {})
        plant = prediction.get("plant_type") or "not detected"
        disease = prediction.get("disease") or "not detected"
        if plant.lower() != "not detected":
            plant_counts[plant] += 1
        if disease.lower() in {"healthy", "not detected", ""}:
            continue

        by_condition[disease].append(row)
        frame = int(row.get("frame", 0))
        probabilities = prediction.get("all_probabilities", {})
        region = row.get("tile_region")
        observations.append({
            "id": f"{artifact_id}:f{frame}:t{int(row.get('tile', 0))}",
            "category": "tile_condition",
            "status": "model_detected",
            "plant": {
                "crop": plant,
                "confidence": prediction.get("plant_confidence", 0.0),
            },
            "condition": {
                "name": disease,
                "code": None,
                "confidence": prediction.get("disease_confidence", 0.0),
                "confidenceMeaning": "model_score",
                "alternatives": _alternatives(probabilities, disease),
            },
            "location": {
                "latitude": None,
                "longitude": None,
                "crs": "WGS84",
                "method": "unavailable",
                "accuracyMeters": None,
            },
            "observedAt": {
                "videoTimeSeconds": row.get("timestamp", 0.0),
                "frameNumber": frame,
                "utc": None,
            },
            "evidence": {
                "sourceImage": None,
                "annotatedImage": row.get("image_url"),
                "region": ({
                    "type": "tile",
                    "coordinateSpace": "source_image_pixels",
                    **region,
                } if region else None),
                "relatedFrames": [frame],
            },
            "review": {
                "decision": None,
                "reviewerId": None,
                "reviewedAt": None,
            },
        })

    conditions = []
    for condition, rows in sorted(by_condition.items()):
        scores = [
            row.get("prediction", {}).get("disease_confidence", 0.0)
            for row in rows
        ]
        conditions.append({
            "name": condition,
            "observationCount": len(rows),
            "meanConfidence": round(sum(scores) / len(scores), 4),
            "affectedAreaSquareMeters": None,
        })

    valid_gps = sum(
        1 for row in telemetry_rows
        if row.get("latitude") is not None and row.get("longitude") is not None
    )
    gps_percent = round(valid_gps / len(telemetry_rows) * 100, 1) if telemetry_rows else 0.0
    start_ts = flight_info.get("start_ts")
    end_ts = flight_info.get("end_ts")
    duration = max(0.0, (end_ts - start_ts) / 1000) if start_ts and end_ts else 0.0
    completed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    track_samples = [
        {
            "timestamp": _iso_utc(row.get("ts")),
            "latitude": row.get("latitude"),
            "longitude": row.get("longitude"),
            "altitudeMeters": row.get("altitude", row.get("height")),
            "heightMeters": row.get("height"),
            "yawDegrees": row.get("yaw"),
            "gimbalPitchDegrees": row.get("gimbal_pitch"),
            "gimbalRollDegrees": row.get("gimbal_roll"),
            "gimbalYawDegrees": row.get("gimbal_yaw"),
        }
        for row in telemetry_rows
    ]
    plant = plant_counts.most_common(1)[0][0] if plant_counts else None
    model_records = []
    if pipeline_config is not None:
        model_records.append(
            _model_record("plant_classifier", pipeline_config.plant_onnx_path, "image_tile")
        )
    for plant_class, model_name in (
        ("cassava", "cassava_disease_classifier"),
        ("plantain", "plantain_disease_classifier"),
    ):
        if pipeline_config is not None and any(
            label.lower() == plant_class for label in plant_counts
        ):
            model_records.append(
                _model_record(model_name, pipeline_config.disease_onnx_path(plant_class), "image_tile")
            )
    return {
        "schemaVersion": "1.0",
        "survey": {
            "id": str(artifact_id),
            "name": name,
            "status": "complete",
            "createdAt": completed_at,
            "crop": {"name": plant, "variety": None, "growthStage": None},
            "area": {"type": None, "id": None, "name": None},
        },
        "summary": {
            "coverage": {
                "flightDurationSeconds": round(duration, 1),
                "framesSampled": len({row.get("frame") for row in frame_results}) + int(video_result.get("frames_rejected", 0)),
                "framesAnalyzed": len({row.get("frame") for row in frame_results}),
                "framesRejected": int(video_result.get("frames_rejected", 0)),
                "tilesAnalyzed": len(frame_results),
            },
            "observationCounts": {
                "total": len(observations),
                "needsReview": len(observations),
                "confirmedByReviewer": 0,
                "unit": "tile_frame_observation",
                "uniquePlantsEstimated": False,
            },
            "conditions": conditions,
            "dataQuality": {
                "gpsCoveragePercent": gps_percent,
                "videoTelemetryAlignment": "unavailable",
                "warnings": [
                    "Observations have no GPS location because video start time is not verified against the flight log.",
                    "Counts are positive tile-frame observations, not unique plants or affected area.",
                    "Model scores are not calibrated probabilities; review findings before acting.",
                ],
            },
        },
        "observations": observations,
        "flight": {
            "id": flight_id,
            "name": flight_info.get("name", name),
            "startedAt": _iso_utc(start_ts),
            "endedAt": _iso_utc(end_ts),
            "track": {"crs": "WGS84", "samples": track_samples},
            "telemetry": {
                "routeDistanceMeters": round(telemetry.route_distance_km * 1000, 1),
                "maxSpeedMetersPerSecond": telemetry.max_speed,
                "maxAltitudeMeters": telemetry.max_height,
                "batteryDrainedPercent": telemetry.battery_drained,
                "maxBatteryTemperatureCelsius": telemetry.max_battery_temp,
                "averageGpsSatellites": telemetry.avg_gps,
            },
        },
        "processing": {
            "pipelineVersion": settings.VERSION,
            "models": model_records,
            "samplingFps": getattr(pipeline_config, "fps", None),
        },
    }
