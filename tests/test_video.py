from __future__ import annotations


class TestVideoEndpointSuccess:
    def test_valid_video_returns_200(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        response = client.post(
            "/api/v1/video",
            files={"file": (filename, content, media_type)},
        )
        assert response.status_code == 200

    def test_response_has_filename(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        response = client.post(
            "/api/v1/video",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert data["filename"] == filename

    def test_response_has_frames_analyzed(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        response = client.post(
            "/api/v1/video",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert "frames_analyzed" in data
        assert isinstance(data["frames_analyzed"], int)
        assert data["frames_analyzed"] == 1

    def test_response_has_prediction(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        response = client.post(
            "/api/v1/video",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert "prediction" in data
        assert data["prediction"] == "Common_Rust"

    def test_response_has_confidence(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        response = client.post(
            "/api/v1/video",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert "confidence" in data
        assert "%" in data["confidence"]

    def test_response_has_per_frame_results(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        response = client.post(
            "/api/v1/video",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert "per_frame_results" in data
        assert isinstance(data["per_frame_results"], list)

    def test_per_frame_result_structure(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        response = client.post(
            "/api/v1/video",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert len(data["per_frame_results"]) > 0
        frame = data["per_frame_results"][0]
        assert "filename" in frame
        assert "prediction" in frame
        assert "confidence" in frame

    def test_aggregated_prediction_is_most_common(self, client, tmp_upload_video):
        filename, content, media_type = tmp_upload_video
        response = client.post(
            "/api/v1/video",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        predictions = [r["prediction"] for r in data["per_frame_results"]]
        assert data["prediction"] == "Common_Rust"


class TestVideoEndpointValidation:
    def test_wrong_mime_type_returns_400(self, client):
        response = client.post(
            "/api/v1/video",
            files={"file": ("image.jpg", b"fake", "image/jpeg")},
        )
        assert response.status_code == 400

    def test_wrong_extension_returns_400(self, client):
        response = client.post(
            "/api/v1/video",
            files={"file": ("clip.flv", b"fake", "video/x-flv")},
        )
        assert response.status_code == 400

    def test_image_extension_on_video_endpoint_returns_400(self, client):
        response = client.post(
            "/api/v1/video",
            files={"file": ("leaf.png", b"fake", "image/png")},
        )
        assert response.status_code == 400

    def test_missing_file_returns_422(self, client):
        response = client.post("/api/v1/video")
        assert response.status_code == 422

    def test_error_message_mentions_invalid(self, client):
        response = client.post(
            "/api/v1/video",
            files={"file": ("bad.exe", b"fake", "application/octet-stream")},
        )
        data = response.json()
        assert "detail" in data


class TestVideoNoFrames:
    def test_blurry_video_returns_422(self, real_extract_client, blurry_video):
        content = blurry_video.read_bytes()
        response = real_extract_client.post(
            "/api/v1/video",
            files={"file": ("blurry.mp4", content, "video/mp4")},
        )
        assert response.status_code == 422

    def test_no_frames_message_is_helpful(self, real_extract_client, blurry_video):
        content = blurry_video.read_bytes()
        response = real_extract_client.post(
            "/api/v1/video",
            files={"file": ("blurry.mp4", content, "video/mp4")},
        )
        data = response.json()
        assert "No clear frames" in data["detail"]
