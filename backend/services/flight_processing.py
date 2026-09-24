"""Application service for the reusable flight-analysis workflow."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from starlette.concurrency import run_in_threadpool

from services.flights import FlightService
from services.log_importer import DJIFlightLogImporter


class VideoPipeline(Protocol):
    def process_video(
        self,
        video_path: Path,
        out_dir: Path,
        public_image_prefix: str | None = None,
    ) -> dict: ...


class FlightProcessingService:
    """Coordinates import, analysis, and response creation without owning storage."""

    def __init__(self, importer: DJIFlightLogImporter, flights: FlightService) -> None:
        self._importer = importer
        self._flights = flights

    async def import_log(self, name: str, log_path: Path) -> int:
        return await run_in_threadpool(
            self._importer.import_log, name, Path(log_path).resolve()
        )

    async def analyze_video(
        self,
        pipeline: VideoPipeline,
        name: str,
        video_path: Path,
        flight_id: int,
        artifact_id: str,
        artifact_dir: Path,
    ) -> dict:
        video_result = await run_in_threadpool(
            pipeline.process_video,
            Path(video_path).resolve(),
            artifact_dir,
            f"/api/v1/images/{artifact_id}",
        )
        return await self._flights.build_upload_response(
            video_result, name, flight_id, artifact_id
        )

    async def process_upload(
        self,
        pipeline: VideoPipeline,
        name: str,
        video_path: Path,
        log_path: Path,
        artifact_id: str,
        artifact_dir: Path,
    ) -> dict:
        flight_id = await self.import_log(name, log_path)
        return await self.analyze_video(
            pipeline,
            name,
            video_path,
            flight_id,
            artifact_id,
            artifact_dir,
        )
