from __future__ import annotations


class TestImageEndpointSuccess:
    def test_valid_image_returns_200(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        r = client.post("/api/v1/image", files={"file": (filename, content, media_type)})
        assert r.status_code == 200

    def test_response_has_filename(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        r = client.post("/api/v1/image", files={"file": (filename, content, media_type)})
        assert r.json()["filename"] == filename

    def test_response_has_prediction(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        r = client.post("/api/v1/image", files={"file": (filename, content, media_type)})
        data = r.json()["prediction"]
        assert "plant_type" in data
        assert "plant_confidence" in data
        assert "disease" in data
        assert "disease_confidence" in data

    def test_response_has_all_probabilities(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        r = client.post("/api/v1/image", files={"file": (filename, content, media_type)})
        data = r.json()
        assert "all_probabilities" in data["prediction"]

    def test_response_has_backend(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        r = client.post("/api/v1/image", files={"file": (filename, content, media_type)})
        assert "backend" in r.json()

    def test_response_has_benchmark(self, client, tmp_upload_image):
        filename, content, media_type = tmp_upload_image
        r = client.post("/api/v1/image", files={"file": (filename, content, media_type)})
        assert "benchmark_ms" in r.json()

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
