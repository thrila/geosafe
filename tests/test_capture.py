from __future__ import annotations

import numpy as np
import pytest

from controllers.capture import is_blurry, preprocess, extract_clear_frames


class TestIsBlurry:
    def test_blurry_uniform_image(self):
        frame = np.full((240, 320, 3), 128, dtype=np.uint8)
        blurry, variance = is_blurry(frame)
        assert blurry == True
        assert variance == 0.0

    def test_clear_random_image(self):
        frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
        blurry, variance = is_blurry(frame)
        assert blurry == False
        assert variance > 0

    def test_custom_threshold(self):
        frame = np.full((240, 320, 3), 128, dtype=np.uint8)
        blurry, variance = is_blurry(frame, threshold=0.0)
        assert blurry == False


class TestPreprocess:
    def test_output_size(self):
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = preprocess(frame, size=224)
        assert result.shape == (224, 224, 3)

    def test_square_input(self):
        frame = np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8)
        result = preprocess(frame, size=224)
        assert result.shape == (224, 224, 3)

    def test_already_correct_size(self):
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        result = preprocess(frame, size=224)
        assert result.shape == (224, 224, 3)


class TestExtractClearFrames:
    def test_extracts_frames_from_video(self, sample_video, tmp_path):
        output_dir = tmp_path / "frames"
        frames = extract_clear_frames(sample_video, output_dir)
        assert len(frames) > 0
        for f in frames:
            assert f.exists()
            assert f.suffix == ".jpg"

    def test_returns_list_of_paths(self, sample_video, tmp_path):
        output_dir = tmp_path / "frames"
        frames = extract_clear_frames(sample_video, output_dir)
        assert isinstance(frames, list)
        assert all(isinstance(f, type(output_dir / "x")) for f in frames)

    def test_invalid_video_raises_value_error(self, tmp_path):
        fake_video = tmp_path / "nonexistent.mp4"
        with pytest.raises(ValueError, match="Could not open video"):
            extract_clear_frames(fake_video, tmp_path / "out")

    def test_blurry_video_returns_empty(self, blurry_video, tmp_path):
        output_dir = tmp_path / "frames"
        frames = extract_clear_frames(blurry_video, output_dir)
        assert len(frames) == 0

    def test_creates_output_dir(self, sample_video, tmp_path):
        output_dir = tmp_path / "new_dir" / "nested"
        extract_clear_frames(sample_video, output_dir)
        assert output_dir.exists()
