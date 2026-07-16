from __future__ import annotations


class TestVideoEndpointSuccess:
    def test_valid_video_returns_200(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        r = client.post("/api/v1/video", files={"file": (filename, content, media_type)})
        assert r.status_code == 200

    def test_response_has_filename(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        r = client.post("/api/v1/video", files={"file": (filename, content, media_type)})
        data = r.json()
        assert data["filename"] == filename

    def test_response_has_frames_analyzed(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        r = client.post("/api/v1/video", files={"file": (filename, content, media_type)})
        assert "frames_analyzed" in r.json()

    def test_response_has_prediction_block(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        r = client.post("/api/v1/video", files={"file": (filename, content, media_type)})
        p = r.json()["prediction"]
        assert "plant_type" in p
        assert "disease" in p

    def test_response_has_confidence(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        r = client.post("/api/v1/video", files={"file": (filename, content, media_type)})
        assert "confidence" in r.json()

    def test_response_has_per_frame_results(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        r = client.post("/api/v1/video", files={"file": (filename, content, media_type)})
        assert "per_frame_results" in r.json()

    def test_per_frame_result_structure(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        r = client.post("/api/v1/video", files={"file": (filename, content, media_type)})
        frame = r.json()["per_frame_results"][0]
        assert "frame" in frame
        assert "timestamp" in frame
        assert "prediction" in frame
        assert "image_url" in frame

    def test_response_has_backend(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        r = client.post("/api/v1/video", files={"file": (filename, content, media_type)})
        assert "backend" in r.json()

    def test_response_has_benchmark(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        r = client.post("/api/v1/video", files={"file": (filename, content, media_type)})
        assert "benchmark" in r.json()


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
