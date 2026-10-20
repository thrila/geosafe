from __future__ import annotations

from unittest import mock

import pytest


class TestVideoEndpointSuccess:
    def test_success_response_contract(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        response = client.post("/api/v1/video", files={"file": (filename, content, media_type)})

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == filename
        assert "frames_analyzed" in data
        assert "confidence" in data
        assert "backend" not in data
        assert "benchmark" not in data
        assert "plant_type" in data["prediction"]
        assert "disease" in data["prediction"]
        assert data["per_frame_results"]
        frame = data["per_frame_results"][0]
        assert "frame" in frame
        assert "timestamp" in frame
        assert "prediction" in frame
        assert "image_url" in frame
        assert "tile_region" in frame


class TestVideoEndpointValidation:
    def test_wrong_mime_type_returns_400(self, client):
        r = client.post("/api/v1/video", files={"file": ("image.jpg", b"fake", "image/jpeg")})
        assert r.status_code == 400

    def test_wrong_extension_returns_400(self, client):
        r = client.post("/api/v1/video", files={"file": ("clip.flv", b"fake", "video/x-flv")})
        assert r.status_code == 400

    def test_image_extension_on_video_endpoint_returns_400(self, client):
        r = client.post("/api/v1/video", files={"file": ("leaf.png", b"fake", "image/png")})
        assert r.status_code == 400

    def test_missing_file_returns_422(self, client):
        r = client.post("/api/v1/video")
        assert r.status_code == 422

    def test_error_message_mentions_invalid(self, client):
        r = client.post("/api/v1/video", files={"file": ("bad.exe", b"fake", "application/octet-stream")})
        assert "detail" in r.json()


class TestVideoNoFrames:
    def test_blurry_video_returns_422(self, no_frame_client, blurry_video):
        content = blurry_video.read_bytes()
        r = no_frame_client.post("/api/v1/video", files={"file": ("blurry.mp4", content, "video/mp4")})
        assert r.status_code == 422


class TestVideoPlantRejection:
    def test_unrecognized_plant_pipeline_raises(self, sample_video):
        from pipeline.config import Config
        from pipeline.inference import Pipeline
        from pipeline.metadata import FrameResult

        pipeline = Pipeline(Config())
        no_plant = FrameResult(
            image="", timestamp=0.0, frame=0, tile=0,
            plant_class="not detected", plant_conf=0.2,
            disease="not detected", disease_conf=0.0,
        )

        with mock.patch.object(pipeline, "_process_frame_batch", return_value=[no_plant]):
            with pytest.raises(ValueError, match="No recognizable plant"):
                pipeline.process_video(sample_video)

    def test_unrecognized_plant_video_returns_422(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video

        class NoPlantPipeline:
            def process_video(self, video_path, out_dir=None, public_image_prefix=None):
                raise ValueError("No recognizable plant was detected in the upload.")

        client.app.state.pipeline = NoPlantPipeline()
        response = client.post("/api/v1/video", files={"file": (filename, content, media_type)})

        assert response.status_code == 422
        assert "No recognizable plant" in response.json()["detail"]
