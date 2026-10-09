from starlette.concurrency import run_in_threadpool

from services.survey_response import build_survey_response
from services.telemetry import FlightRepository, SqliteFlightRepository
from utils.formatting import format_duration


class FlightService:
    """Orchestrates telemetry and versioned survey responses."""

    def __init__(self, repository: FlightRepository | None = None):
        self._repo = repository or SqliteFlightRepository()

    def _get_flight_response_sync(self, flight_id: int) -> dict | None:
        info = self._repo.get_flight_info(flight_id)
        if not info:
            return None

        analysis = self._repo.get_analysis(flight_id)
        if analysis and analysis.get("schemaVersion") == "1.0":
            return analysis

        td = self._repo.build_telemetry_data(flight_id)
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
        return self._repo.list_all_flights()

    def _build_upload_response_sync(
        self,
        video_result: dict,
        name: str,
        flight_id: int,
        artifact_id: str,
        pipeline_config,
    ) -> dict:
        info = self._repo.get_flight_info(flight_id) or {}
        telemetry = self._repo.build_telemetry_data(flight_id)
        telemetry_rows = self._repo.get_telemetry_rows(flight_id)
        response = build_survey_response(
            video_result,
            name,
            flight_id,
            artifact_id,
            info,
            telemetry,
            telemetry_rows,
            pipeline_config,
        )
        self._repo.save_analysis(flight_id, artifact_id, response)
        return response

    async def get_flight_response(self, flight_id: int) -> dict | None:
        return await run_in_threadpool(self._get_flight_response_sync, flight_id)

    async def list_flights_response(self) -> list[dict]:
        return await run_in_threadpool(self._list_flights_response_sync)

    async def build_upload_response(
        self,
        video_result: dict,
        name: str,
        flight_id: int,
        artifact_id: str,
        pipeline_config=None,
    ) -> dict:
        return await run_in_threadpool(
            self._build_upload_response_sync,
            video_result,
            name,
            flight_id,
            artifact_id,
            pipeline_config,
        )
