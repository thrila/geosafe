from __future__ import annotations

import io
from pathlib import Path

import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.datastructures import UploadFile

from utils.utils import (
    _confidence_to_float,
    _format_confidence,
    _validate_upload,
    _save_upload_to_temp,
)


def _make_file(filename: str, content_type: str) -> UploadFile:
    """Create an UploadFile with a specific content_type via headers."""
    return UploadFile(
        file=b"",
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


class TestValidateUpload:
    def test_valid_image_jpg(self):
        f = _make_file("leaf.jpg", "image/jpeg")
        result = _validate_upload(f, "image", (".jpg", ".jpeg", ".png", ".webp"))
        assert result == ".jpg"

    def test_valid_image_png(self):
        f = _make_file("leaf.png", "image/png")
        result = _validate_upload(f, "image", (".jpg", ".jpeg", ".png", ".webp"))
        assert result == ".png"

    def test_valid_video_mp4(self):
        f = _make_file("clip.mp4", "video/mp4")
        result = _validate_upload(f, "video", (".mp4", ".avi", ".mov", ".mkv"))
        assert result == ".mp4"

    def test_wrong_mime_type_raises_400(self):
        f = _make_file("leaf.jpg", "application/pdf")
        with pytest.raises(HTTPException) as exc_info:
            _validate_upload(f, "image", (".jpg", ".jpeg", ".png", ".webp"))
        assert exc_info.value.status_code == 400

    def test_wrong_extension_raises_400(self):
        f = _make_file("leaf.bmp", "image/bmp")
        with pytest.raises(HTTPException) as exc_info:
            _validate_upload(f, "image", (".jpg", ".jpeg", ".png", ".webp"))
        assert exc_info.value.status_code == 400

    def test_mime_type_case_insensitive(self):
        f = _make_file("leaf.jpg", "IMAGE/JPEG")
        result = _validate_upload(f, "image", (".jpg", ".jpeg", ".png", ".webp"))
        assert result == ".jpg"

    def test_extension_case_insensitive(self):
        f = _make_file("leaf.JPG", "image/jpeg")
        result = _validate_upload(f, "image", (".jpg", ".jpeg", ".png", ".webp"))
        assert result == ".jpg"

    def test_video_with_wrong_mime(self):
        f = _make_file("clip.mp4", "audio/mpeg")
        with pytest.raises(HTTPException) as exc_info:
            _validate_upload(f, "video", (".mp4", ".avi", ".mov", ".mkv"))
        assert exc_info.value.status_code == 400

    def test_error_detail_message(self):
        f = _make_file("bad.exe", "application/octet-stream")
        with pytest.raises(HTTPException) as exc_info:
            _validate_upload(f, "image", (".jpg", ".jpeg", ".png", ".webp"))
        assert "MIME type" in exc_info.value.detail


class TestConfidenceConversion:
    def test_to_float_basic(self):
        assert _confidence_to_float("87.3%") == 87.3

    def test_to_float_zero(self):
        assert _confidence_to_float("0.0%") == 0.0

    def test_to_float_hundred(self):
        assert _confidence_to_float("100.0%") == 100.0

    def test_format_confidence(self):
        assert _format_confidence(87.3) == "87.3%"

    def test_format_confidence_zero(self):
        assert _format_confidence(0.0) == "0.0%"

    def test_format_confidence_whole_number(self):
        assert _format_confidence(50.0) == "50.0%"


class TestSaveUploadToTemp:
    @pytest.mark.asyncio
    async def test_saves_file_with_correct_suffix(self, tmp_path):
        f = UploadFile(
            file=io.BytesIO(b"\xff\xd8\xff\xe0fake_jpeg_data"),
            filename="test.jpg",
            headers=Headers({"content-type": "image/jpeg"}),
        )
        path = await _save_upload_to_temp(f)
        try:
            assert path.exists()
            assert path.suffix == ".jpg"
            assert path.read_bytes() == b"\xff\xd8\xff\xe0fake_jpeg_data"
        finally:
            path.unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_saves_png_file(self):
        f = UploadFile(
            file=io.BytesIO(b"\x89PNGfake"),
            filename="photo.png",
            headers=Headers({"content-type": "image/png"}),
        )
        path = await _save_upload_to_temp(f)
        try:
            assert path.suffix == ".png"
        finally:
            path.unlink(missing_ok=True)
