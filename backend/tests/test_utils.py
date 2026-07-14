from __future__ import annotations

import io

from fastapi import HTTPException
from fastapi.datastructures import Headers
from starlette.datastructures import UploadFile

from utils.utils import validate_upload, confidence_to_float, format_confidence


def _uf(filename: str, content_type: str) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(b"test"),
        headers=Headers({"content-type": content_type}),
    )


class TestValidateUpload:
    def test_valid_jpg(self):
        assert validate_upload(_uf("leaf.jpg", "image/jpeg"), "image", (".jpg", ".jpeg")) == ".jpg"

    def test_valid_png(self):
        assert validate_upload(_uf("leaf.png", "image/png"), "image", (".png", ".jpg", ".jpeg")) == ".png"

    def test_valid_video_mp4(self):
        assert validate_upload(_uf("clip.mp4", "video/mp4"), "video", (".mp4", ".avi")) == ".mp4"

    def test_wrong_mime_raises_400(self):
        uf = _uf("leaf.jpg", "video/mp4")
        try:
            validate_upload(uf, "image", (".jpg", ".jpeg"))
            assert False, "should raise"
        except HTTPException as e:
            assert e.status_code == 400

    def test_wrong_extension_raises_400(self):
        uf = _uf("leaf.bmp", "image/bmp")
        try:
            validate_upload(uf, "image", (".jpg", ".jpeg"))
            assert False, "should raise"
        except HTTPException as e:
            assert e.status_code == 400

    def test_case_insensitive_extension(self):
        assert validate_upload(_uf("leaf.JPG", "image/jpeg"), "image", (".jpg", ".jpeg")) == ".jpg"

    def test_error_message_contains_detail(self):
        try:
            validate_upload(_uf("bad.pdf", "application/pdf"), "image", (".jpg", ".jpeg"))
        except HTTPException as e:
            assert "Invalid" in e.detail


class TestConfidenceConversion:
    def test_to_float_removes_percent(self):
        assert confidence_to_float("95.2%") == 95.2

    def test_format_confidence(self):
        assert format_confidence(95.2) == "95.2%"
