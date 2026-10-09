from __future__ import annotations

from unittest import mock


class TestImageEndpointSuccess:
    def test_success_response_contract(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        response = client.post("/api/v1/image", files={"file": (filename, content, media_type)})

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == filename
        assert "image_url" in data
        assert "backend" not in data
        assert "benchmark_ms" not in data
        prediction = data["prediction"]
        assert "plant_type" in prediction
        assert "plant_confidence" in prediction
        assert "disease" in prediction
        assert "disease_confidence" in prediction
        assert "all_probabilities" in prediction
        assert {"x", "y", "width", "height", "imageWidth", "imageHeight"} <= set(data["tiles"][0]["region"])

    def test_image_heatmap_is_enabled(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        sent = {}
        original = client.app.state.pipeline.process_image

        def spy(image_path, save_heatmap=False):
            sent["save_heatmap"] = save_heatmap
            return original(image_path, save_heatmap)

        with mock.patch.object(client.app.state.pipeline, "process_image", side_effect=spy):
            client.post("/api/v1/image", files={"file": (filename, content, media_type)})
        assert sent["save_heatmap"] is True

    def test_png_upload_works(self, client, sample_png):
        content = sample_png.read_bytes()
        r = client.post("/api/v1/image", files={"file": ("leaf.png", content, "image/png")})
        assert r.status_code == 200
        assert r.json()["filename"] == "leaf.png"


class TestImageEndpointValidation:
    def test_wrong_mime_type_returns_400(self, client):
        r = client.post("/api/v1/image", files={"file": ("doc.pdf", b"fake", "application/pdf")})
        assert r.status_code == 400

    def test_wrong_extension_returns_400(self, client):
        r = client.post("/api/v1/image", files={"file": ("leaf.bmp", b"fake", "image/bmp")})
        assert r.status_code == 400

    def test_video_extension_on_image_endpoint_returns_400(self, client):
        r = client.post("/api/v1/image", files={"file": ("clip.mp4", b"fake", "video/mp4")})
        assert r.status_code == 400

    def test_missing_file_returns_422(self, client):
        r = client.post("/api/v1/image")
        assert r.status_code == 422

    def test_error_message_is_helpful(self, client):
        r = client.post("/api/v1/image", files={"file": ("bad.pdf", b"fake", "application/pdf")})
        assert "detail" in r.json()
