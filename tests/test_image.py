from __future__ import annotations


class TestImageEndpointSuccess:
    def test_valid_image_returns_200(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        response = client.post(
            "/api/v1/image",
            files={"file": (filename, content, media_type)},
        )
        assert response.status_code == 200

    def test_response_has_filename(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        response = client.post(
            "/api/v1/image",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert data["filename"] == filename

    def test_response_has_prediction(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        response = client.post(
            "/api/v1/image",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert "prediction" in data
        assert isinstance(data["prediction"], str)

    def test_response_has_confidence(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        response = client.post(
            "/api/v1/image",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert "confidence" in data
        assert "%" in data["confidence"]

    def test_prediction_matches_mock(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        response = client.post(
            "/api/v1/image",
            files={"file": (filename, content, media_type)},
        )
        data = response.json()
        assert data["prediction"] == "Common_Rust"
        assert data["confidence"] == "95.2%"

    def test_png_upload_works(self, client, sample_png):
        content = sample_png.read_bytes()
        response = client.post(
            "/api/v1/image",
            files={"file": ("leaf.png", content, "image/png")},
        )
        assert response.status_code == 200
        assert response.json()["filename"] == "leaf.png"


class TestImageEndpointValidation:
    def test_wrong_mime_type_returns_400(self, client):
        response = client.post(
            "/api/v1/image",
            files={"file": ("doc.pdf", b"fake", "application/pdf")},
        )
        assert response.status_code == 400

    def test_wrong_extension_returns_400(self, client):
        response = client.post(
            "/api/v1/image",
            files={"file": ("leaf.bmp", b"fake", "image/bmp")},
        )
        assert response.status_code == 400

    def test_video_extension_on_image_endpoint_returns_400(self, client):
        response = client.post(
            "/api/v1/image",
            files={"file": ("clip.mp4", b"fake", "video/mp4")},
        )
        assert response.status_code == 400

    def test_missing_file_returns_422(self, client):
        response = client.post("/api/v1/image")
        assert response.status_code == 422

    def test_error_message_is_helpful(self, client):
        response = client.post(
            "/api/v1/image",
            files={"file": ("bad.pdf", b"fake", "application/pdf")},
        )
        data = response.json()
        assert "detail" in data
        assert "MIME type" in data["detail"] or "Invalid" in data["detail"]
