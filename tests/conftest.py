from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
from fastapi.datastructures import Headers
from fastapi.testclient import TestClient
from PIL import Image
from starlette.datastructures import UploadFile


# ---------------------------------------------------------------------------
# Image fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_image(tmp_path: Path) -> Path:
    """Create a valid 224x224 RGB JPEG image on disk."""
    img = Image.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
    path = tmp_path / "test_leaf.jpg"
    img.save(path, format="JPEG")
    return path


@pytest.fixture()
def sample_png(tmp_path: Path) -> Path:
    """Create a valid 100x100 RGB PNG image on disk."""
    img = Image.fromarray(np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8))
    path = tmp_path / "test_leaf.png"
    img.save(path, format="PNG")
    return path


@pytest.fixture()
def blurry_image(tmp_path: Path) -> Path:
    """Create a uniform (zero variance) image that will be detected as blurry."""
    arr = np.full((224, 224, 3), 128, dtype=np.uint8)
    img = Image.fromarray(arr)
    path = tmp_path / "blurry.jpg"
    img.save(path, format="JPEG")
    return path


@pytest.fixture()
def clear_image(tmp_path: Path) -> Path:
    """Create an image with high variance (not blurry)."""
    arr = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    path = tmp_path / "clear.jpg"
    img.save(path, format="JPEG")
    return path


# ---------------------------------------------------------------------------
# Video fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_video(tmp_path: Path) -> Path:
    """Create a minimal valid MP4 video with random (clear) frames."""
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
    """Create a video with uniform (blurry) frames."""
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


# ---------------------------------------------------------------------------
# Mock predict result
# ---------------------------------------------------------------------------

MOCK_PREDICT_RESULT = {
    "prediction": "Common_Rust",
    "confidence": "95.2%",
    "all_scores": {
        "Common_Rust": "95.2%",
        "Healthy": "3.1%",
        "Blight": "1.7%",
    },
}


# ---------------------------------------------------------------------------
# Fake UploadFile helper
# ---------------------------------------------------------------------------

def _make_upload_file(filename: str, content_type: str, data: bytes) -> UploadFile:
    """Create an UploadFile with a given content_type (set via headers)."""
    return UploadFile(
        file=io.BytesIO(data),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


# ---------------------------------------------------------------------------
# FastAPI TestClient with mocked predict
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(tmp_path: Path):
    """TestClient that patches predict and extract_clear_frames at the route level."""
    with patch("routes.images.predict", return_value=MOCK_PREDICT_RESULT), \
         patch("routes.videos.predict", return_value=MOCK_PREDICT_RESULT), \
         patch("routes.videos.extract_clear_frames") as mock_extract:

        def _fake_extract(video_path, output_dir, **kwargs):
            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            fake_frame = out / "frame_0000.jpg"
            Image.fromarray(
                np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
            ).save(fake_frame, format="JPEG")
            return [fake_frame]

        mock_extract.side_effect = _fake_extract

        from main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


@pytest.fixture()
def real_extract_client(tmp_path: Path):
    """TestClient that patches predict but uses the real extract_clear_frames."""
    with patch("routes.images.predict", return_value=MOCK_PREDICT_RESULT), \
         patch("routes.videos.predict", return_value=MOCK_PREDICT_RESULT):

        from main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


# ---------------------------------------------------------------------------
# Upload file tuples for the TestClient files= param
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_upload_image(sample_image: Path) -> tuple[str, bytes, str]:
    """Return (filename, bytes, media_type) for an image upload."""
    return ("test_leaf.jpg", sample_image.read_bytes(), "image/jpeg")


@pytest.fixture()
def tmp_upload_video(sample_video: Path) -> tuple[str, bytes, str]:
    """Return (filename, bytes, media_type) for a video upload."""
    return ("test_video.mp4", sample_video.read_bytes(), "video/mp4")
