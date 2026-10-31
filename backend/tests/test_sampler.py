from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from pipeline.sampler import frame_iterator


def _write_video(path: Path, frames: int, fps: int = 30) -> Path:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter.fourcc(*"mp4v"), fps, (64, 64))
    for _ in range(frames):
        writer.write(np.zeros((64, 64, 3), dtype=np.uint8))
    writer.release()
    return path


def test_samples_at_the_target_rate(tmp_path: Path):
    video = _write_video(tmp_path / "clip.mp4", frames=30)

    samples = list(frame_iterator(video, target_fps=10))

    assert [index for index, _, _ in samples] == list(range(0, 30, 3))


def test_timestamps_follow_the_source_frame_rate(tmp_path: Path):
    video = _write_video(tmp_path / "clip.mp4", frames=31)

    samples = list(frame_iterator(video, target_fps=2))

    assert [index for index, _, _ in samples] == [0, 15, 30]
    assert [timestamp for _, timestamp, _ in samples] == pytest.approx([0.0, 0.5, 1.0])


def test_target_above_source_rate_keeps_every_frame(tmp_path: Path):
    video = _write_video(tmp_path / "clip.mp4", frames=5)

    assert len(list(frame_iterator(video, target_fps=120))) == 5


def test_missing_video_raises(tmp_path: Path):
    with pytest.raises(IOError, match="Could not open video"):
        list(frame_iterator(tmp_path / "missing.mp4"))
