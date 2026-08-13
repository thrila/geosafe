import logging

from starlette.concurrency import run_in_threadpool

from services.slides import build_slides
from services.telemetry import TelemetryData, TelemetryRepository
from utils.formatting import format_duration

logger = logging.getLogger(__name__)


class FlightService:
    """Orchestrates telemetry + slides into API response dicts."""

    def __init__(self):
        self._repo = TelemetryRepository()

    def _get_flight_response_sync(self, flight_id: int) -> dict | None:
        """Synchronous helper — builds the GET /flights/{id} response."""
        info = self._repo.get_flight_info(flight_id)
        if not info:
            return None

        td = self._repo.build_telemetry_data(flight_id)

        analysis = self._repo.get_analysis(flight_id)
        result = {
            "routeDistanceKm": td.route_distance_km,
            "startPoint": td.start_point,
            "endPoint": td.end_point,
            "batteryDrainedPct": td.battery_drained,
            "maxSpeedMs": td.max_speed,
            "maxHeightM": td.max_height,
            "batteryTempC": td.max_battery_temp,
        }
        if analysis:
            result.update(analysis)

        return {
            "flight": {
                "id": info["id"],
                "name": info["name"],
                "date": str(info["start_ts"]),
                "duration": format_duration(info["start_ts"], info["end_ts"]),
                "location": f"{td.mean_lat}, {td.mean_lon}",
                "totalFrames": info["total_frames"],
            },
            "path": td.track_pts,
            "telemetry": {
                "dateTime": str(info["end_ts"]),
                "cards": [
                    {"label": "Route", "value": f"{td.route_distance_km} km", "detail": "Total distance."},
                    {"label": "Max Speed", "value": f"{td.max_speed} m/s", "detail": "Ground speed."},
                    {"label": "Max Height", "value": f"{td.max_height} m", "detail": "Peak altitude."},
                    {"label": "Battery", "value": f"{td.battery_start or 0:.0f} %", "detail": f"Drained {td.battery_drained:.0f}%."},
                    {"label": "Battery Temp", "value": f"{td.max_battery_temp} °C", "detail": "Peak temperature."},
                    {"label": "GPS", "value": f"{td.avg_gps} sats", "detail": "Average."},
                ],
            },
            "result": result,
        }

    def _list_flights_response_sync(self) -> list[dict]:
        """Synchronous helper — builds the GET /flights response."""
        return self._repo.list_all_flights()

    def _build_upload_response_sync(self, video_result: dict, name: str, flight_id: int, artifact_id: str) -> dict:
        """Synchronous helper — builds the POST /upload response."""
        td = self._repo.build_telemetry_data(flight_id)

        per_frame = video_result.get("per_frame_results", [])

        disease_tally: dict[str, int] = {}
        unidentified = 0
        for f in per_frame:
            disease = f.get("prediction", {}).get("disease", "")
            if not disease or disease.lower() == "healthy":
                continue
            if disease.lower() == "not detected":
                unidentified += 1
            else:
                disease_tally[disease] = disease_tally.get(disease, 0) + 1

        diseases = list(disease_tally.keys())
        diseased_frames = [
            f for f in per_frame
            if f.get("prediction", {}).get("disease", "").lower() not in ("healthy", "not detected")
        ]

        slides = build_slides(diseased_frames)
        analysis = {
            "diseasesDetected": diseases,
            "diseaseTally": disease_tally,
            "unidentifiedPlants": unidentified,
            "slides": slides,
        }
        self._repo.save_analysis(flight_id, artifact_id, analysis)

        return {
            "flight": {
                "id": str(flight_id),
                "name": name,
                "date": str(td.start_ts),
                "duration": format_duration(td.start_ts, td.end_ts),
                "location": f"{td.mean_lat}, {td.mean_lon}",
                "summary": f"Survey over {name}.",
            },
            "path": [
                {
                    "longitude": p["longitude"],
                    "latitude": p["latitude"],
                    "height": p["height"],
                }
                for p in td.track_pts
            ] if td.track_pts else [],
            "telemetry": {
                "dateTime": str(td.end_ts) if td.end_ts else "",
                "cards": [
                    {"label": "Altitude", "value": f"{td.max_height} m", "detail": "Maximum height."},
                    {"label": "Speed", "value": f"{td.max_speed} m/s", "detail": "Max ground speed."},
                    {"label": "GPS", "value": f"{td.avg_gps} sats", "detail": "Average satellites."},
                    {"label": "Battery", "value": f"{td.battery_start or 0:.0f} %", "detail": f"Drained {td.battery_drained:.0f}%."},
                    {"label": "Direction", "value": f"{td.route_distance_km} km", "detail": "Total route distance."},
                    {"label": "SD card", "value": f"{td.max_battery_temp} °C", "detail": "Peak battery temperature."},
                ],
            },
            "result": {
                "routeDistanceKm": td.route_distance_km,
                "startPoint": td.start_point,
                "endPoint": td.end_point,
                "batteryDrainedPct": td.battery_drained,
                "maxSpeedMs": td.max_speed,
                "maxHeightM": td.max_height,
                "batteryTempC": td.max_battery_temp,
                "diseasesDetected": diseases,
                "diseaseTally": disease_tally,
                "unidentifiedPlants": unidentified,
                "slides": slides,
            },
        }

    async def get_flight_response(self, flight_id: int) -> dict | None:
        """Build the full GET /flights/{id} response, or None if not found."""
        return await run_in_threadpool(self._get_flight_response_sync, flight_id)

    async def list_flights_response(self) -> list[dict]:
        """Build the GET /flights response."""
        return await run_in_threadpool(self._list_flights_response_sync)

    async def build_upload_response(
        self, video_result: dict, name: str, flight_id: int, artifact_id: str
    ) -> dict:
        """Build the full POST /upload response from pipeline output + DB telemetry."""
        return await run_in_threadpool(
            self._build_upload_response_sync, video_result, name, flight_id, artifact_id
        )
