from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.mark.integration
class TestRealVideoPipeline:
    """Integration tests using actual DJI drone footage.
    Requires DJI_0032.MP4 in backend/ and real ONNX models.
    """

    def test_pipeline_processes_dji_video(self, real_pipeline, dji_video):
        with tempfile.TemporaryDirectory() as td:
            result = real_pipeline.process_video(dji_video, Path(td))

        assert result["frames_analyzed"] > 0
        assert result["frames_rejected"] >= 0
        assert "prediction" in result
        assert "plant_type" in result["prediction"]
        assert "disease" in result["prediction"]
        assert "confidence" in result

    def test_per_frame_results_structure(self, real_pipeline, dji_video):
        with tempfile.TemporaryDirectory() as td:
            result = real_pipeline.process_video(dji_video, Path(td))

        assert len(result["per_frame_results"]) == result["frames_analyzed"]
        for frame in result["per_frame_results"]:
            assert "frame" in frame
            assert "timestamp" in frame
            assert "prediction" in frame
            assert "image_url" in frame
            pred = frame["prediction"]
            assert "plant_type" in pred
            assert "plant_confidence" in pred
            assert "disease" in pred
            assert "disease_confidence" in pred

    def test_every_tile_writes_metadata(self, real_pipeline, dji_video):
        with tempfile.TemporaryDirectory() as td:
            result = real_pipeline.process_video(dji_video, Path(td))

            saved = list((Path(td) / "metadata").glob("*.json"))
            assert len(saved) == len(result["per_frame_results"])
