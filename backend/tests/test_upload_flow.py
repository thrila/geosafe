from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from services.flight_processing import FlightProcessingService


async def test_flight_processing_reuses_import_and_analysis_stages(tmp_path: Path):
    importer = MagicMock()
    importer.import_log.return_value = 42
    flights = MagicMock()
    flights.build_upload_response = AsyncMock(return_value={"flight": {"id": "42"}})
    pipeline = MagicMock()
    pipeline.process_video.return_value = {"frames_analyzed": 1}
    service = FlightProcessingService(importer, flights)

    response = await service.process_upload(
        pipeline,
        "Survey",
        tmp_path / "video.mp4",
        tmp_path / "flight.txt",
        "artifact-1",
        tmp_path / "artifacts" / "artifact-1",
    )

    assert response == {"flight": {"id": "42"}}
    importer.import_log.assert_called_once_with("Survey", (tmp_path / "flight.txt").resolve())
    pipeline.process_video.assert_called_once_with(
        (tmp_path / "video.mp4").resolve(),
        tmp_path / "artifacts" / "artifact-1",
        "/api/v1/images/artifact-1",
    )


def test_upload_uses_the_flight_id_created_from_its_log(upload_client, tmp_upload_video):
    video_name, video_content, video_type = tmp_upload_video
    response_payload = {"flight": {"id": "42"}, "result": {}}

    with patch.object(
        upload_client.app.state.flight_processing,
        "process_upload",
        new_callable=AsyncMock,
        return_value=response_payload,
    ) as process_upload:
        response = upload_client.post(
            "/api/v1/upload",
            data={"name": "Otuoke survey"},
            files={
                "video": (video_name, video_content, video_type),
                "log": ("flight.txt", b"DJI log", "text/plain"),
            },
        )

    assert response.status_code == 200
    assert response.json() == response_payload
    assert process_upload.await_count == 1
    assert process_upload.await_args.args[1] == "Otuoke survey"
    assert len(process_upload.await_args.args[4]) == 32
