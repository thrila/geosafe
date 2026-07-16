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

    def test_benchmark_populated(self, real_pipeline, dji_video):
        with tempfile.TemporaryDirectory() as td:
            result = real_pipeline.process_video(dji_video, Path(td))

        bench = result["benchmark"]
        assert "avg_inference_ms" in bench
        assert "avg_postprocessing_ms" in bench
        assert "avg_total_ms" in bench
        assert "throughput_fps" in bench

    def test_diseased_tiles_persisted(self, real_pipeline, dji_video):
        with tempfile.TemporaryDirectory() as td:
            result = real_pipeline.process_video(dji_video, Path(td))
            images_dir = Path(td) / "images"
            metadata_dir = Path(td) / "metadata"

            diseased = [
                f for f in result["per_frame_results"]
                if f["image_url"] is not None
            ]
            if diseased:
                assert images_dir.exists()
                saved = list(images_dir.glob("*.jpg"))
                assert len(saved) > 0
                assert metadata_dir.exists()
                json_files = list(metadata_dir.glob("*.json"))
                assert len(json_files) > 0
