from __future__ import annotations

from unittest.mock import AsyncMock, patch


def test_upload_uses_the_flight_id_created_from_its_log(upload_client, tmp_upload_video):
    video_name, video_content, video_type = tmp_upload_video
    response_payload = {"flight": {"id": "42"}, "result": {}}

    with patch("routes.upload._log_importer.import_log", return_value=42) as import_log, patch(
        "routes.upload._flight_service.build_upload_response",
        new_callable=AsyncMock,
        return_value=response_payload,
    ) as build_response:
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
    import_log.assert_called_once()
    assert build_response.await_args.args[2] == 42
    assert len(build_response.await_args.args[3]) == 32
