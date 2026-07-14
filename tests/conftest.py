from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image


MOCK_IMAGE_RESULT = {
    "prediction": {
        "plant_type": "Cassava",
        "plant_confidence": 0.98,
        "disease": "Cassava Mosaic Disease (CMD)",
        "disease_confidence": 0.94,
        "all_probabilities": {
            "Cassava Bacterial Blight (CBB)": 0.01,
            "Cassava Brown Streak Disease (CBSD)": 0.02,
            "Cassava Green Mottle (CGM)": 0.03,
            "Cassava Mosaic Disease (CMD)": 0.94,
            "Healthy": 0.00,
        },
    },
    "backend": "onnx",
    "benchmark_ms": {"total": 42.3},
}

MOCK_VIDEO_RESULT = {
    "frames_analyzed": 2,
    "frames_rejected": 0,
    "prediction": {
        "plant_type": "Cassava",
        "plant_confidence": 0.97,
        "disease": "Cassava Mosaic Disease (CMD)",
        "disease_confidence": 0.94,
    },
    "confidence": "94.0%",
    "per_frame_results": [
        {
            "frame": 0,
            "timestamp": 0.0,
            "prediction": {
                "plant_type": "Cassava",
                "plant_confidence": 0.98,
                "disease": "Cassava Mosaic Disease (CMD)",
                "disease_confidence": 0.94,
                "all_probabilities": {},
            },
            "image_base64": "/9j/4AAQSkZJRg==",
        },
        {
            "frame": 10,
            "timestamp": 0.333,
            "prediction": {
                "plant_type": "Cassava",
                "plant_confidence": 0.96,
                "disease": "Cassava Mosaic Disease (CMD)",
                "disease_confidence": 0.94,
                "all_probabilities": {},
            },
            "image_base64": None,
        },
    ],
    "backend": "onnx",
    "benchmark": {
        "avg_preprocessing_ms": 2.1,
        "avg_inference_ms": 45.3,
        "avg_postprocessing_ms": 0.4,
        "avg_total_ms": 47.8,
        "throughput_fps": 20.9,
        "peak_memory_mb": None,
    },
}

MOCK_PREDICTION = {
    "plant_type": "Cassava",
    "plant_confidence": 0.97,
    "disease": "Cassava Mosaic Disease (CMD)",
    "disease_confidence": 0.94,
}


@pytest.fixture()
def sample_image(tmp_path: Path) -> Path:
    img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    path = tmp_path / "test_leaf.jpg"
    img.save(path, format="JPEG")
    return path


@pytest.fixture()
def sample_png(tmp_path: Path) -> Path:
    img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
    path = tmp_path / "test_leaf.png"
    img.save(path, format="PNG")
    return path


@pytest.fixture()
def sample_video(tmp_path: Path) -> Path:
    try:
        import cv2
    except ImportError:
        pytest.skip("opencv-python-headless not installed")
    path = tmp_path / "test_video.mp4"
    fourcc = cv2.VideoWriter.fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 30, (320, 240))
    for _ in range(10):
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return path


@pytest.fixture()
def blurry_video(tmp_path: Path) -> Path:
    try:
        import cv2
    except ImportError:
        pytest.skip("opencv-python-headless not installed")
    path = tmp_path / "blurry_video.mp4"
    fourcc = cv2.VideoWriter.fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, 30, (320, 240))
    for _ in range(10):
        frame = np.full((240, 320, 3), 128, dtype=np.uint8)
        writer.write(frame)
    writer.release()
    return path


class MockPipeline:
    def process_image(self, image_path):
        return {**MOCK_IMAGE_RESULT}

    def process_video(self, video_path, out_dir=None):
        return {**MOCK_VIDEO_RESULT}


@pytest.fixture()
def client():
    with patch("core.lifespan.Pipeline", return_value=MockPipeline()):
        from main import app
        with TestClient(app) as c:
            yield c


@pytest.fixture()
def upload_client():
    with patch("core.lifespan.Pipeline", return_value=MockPipeline()):
        from main import app
        with TestClient(app) as c:
            yield c


@pytest.fixture()
def no_frame_client():
    class NoFramePipeline:
        def process_image(self, image_path):
            return {**MOCK_IMAGE_RESULT}

        def process_video(self, video_path, out_dir=None):
            raise ValueError("No clear frames could be extracted from the uploaded video.")

    with patch("core.lifespan.Pipeline", return_value=NoFramePipeline()):
        from main import app
        with TestClient(app) as c:
            yield c


@pytest.fixture()
def tmp_upload_image(sample_image: Path):
    return ("test_leaf.jpg", sample_image.read_bytes(), "image/jpeg")


@pytest.fixture()
def tmp_upload_video(sample_video: Path):
    return ("test_video.mp4", sample_video.read_bytes(), "video/mp4")
