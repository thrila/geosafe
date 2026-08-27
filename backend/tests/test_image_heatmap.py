from __future__ import annotations

import cv2
import numpy as np
from unittest.mock import patch

from pipeline.config import Config
from pipeline.inference import Pipeline


class TestImageHeatmap:
    def test_save_heatmap_writes_evidence_and_returns_url(self, tmp_path):
        config = Config()
        pipeline = Pipeline(config)

        frame = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        detections = [("CMD", 0.95), ("Healthy", 0.6)]

        with patch.object(pipeline, "_infer") as infer, \
             patch("pipeline.inference.settings") as settings:
            settings.OUTPUT_DIR = tmp_path / "output"
            settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            infer.return_value = (
                {"predicted_class": "cassava", "confidence": 0.9},
                {"predicted_class": "CMD", "confidence": 0.95},
            )

            result = pipeline._process_frame(frame, save_heatmap=True)

        assert result["image_url"] is not None
        artifact_dir = tmp_path / "output" / result["image_url"].split("/")[-2]
        evidence = artifact_dir / "evidence.jpg"
        assert evidence.is_file()
        rendered = cv2.imread(str(evidence))
        assert rendered.shape[:2] == frame.shape[:2]

    def test_no_detection_returns_none_url(self, tmp_path):
        config = Config()
        pipeline = Pipeline(config)

        frame = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)

        with patch.object(pipeline, "_infer") as infer, \
             patch("pipeline.inference.settings") as settings:
            settings.OUTPUT_DIR = tmp_path / "output"
            settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            infer.return_value = (
                {"predicted_class": "cassava", "confidence": 0.9},
                {"predicted_class": "Healthy", "confidence": 0.6},
            )

            result = pipeline._process_frame(frame, save_heatmap=True)

        assert result["image_url"] is None

    def test_save_heatmap_false_does_not_write(self, tmp_path):
        config = Config()
        pipeline = Pipeline(config)

        frame = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)

        with patch.object(pipeline, "_infer") as infer, \
             patch("pipeline.inference.settings") as settings:
            settings.OUTPUT_DIR = tmp_path / "output"
            settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            infer.return_value = (
                {"predicted_class": "cassava", "confidence": 0.9},
                {"predicted_class": "CMD", "confidence": 0.95},
            )

            result = pipeline._process_frame(frame, save_heatmap=False)

        assert result["image_url"] is None
        assert list((tmp_path / "output").iterdir()) == []
