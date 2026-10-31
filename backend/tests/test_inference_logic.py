"""Pin the decisions the pipeline makes from raw model scores."""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pytest

from fastapi.testclient import TestClient

from pipeline.config import Config
from pipeline.inference import Pipeline, _apply_disease_threshold
from pipeline.saver import is_actionable_disease


def _prediction(name: str, confidence: float) -> dict:
    return {
        "predicted_class": name,
        "predicted_index": 0,
        "confidence": confidence,
        "all_probabilities": {name: confidence},
    }


class TestDiseaseThreshold:
    def test_confident_disease_is_kept(self):
        result = _apply_disease_threshold(_prediction("Cassava Mosaic Disease (CMD)", 0.5))

        assert result["predicted_class"] == "Cassava Mosaic Disease (CMD)"
        assert result["confidence"] == 0.5

    def test_confident_healthy_is_kept(self):
        assert _apply_disease_threshold(_prediction("Healthy", 0.9))["predicted_class"] == "Healthy"

    @pytest.mark.parametrize("name", ["Cassava Mosaic Disease (CMD)", "Healthy"])
    def test_uncertain_prediction_is_inconclusive(self, name):
        result = _apply_disease_threshold(_prediction(name, 0.45))

        assert result["predicted_class"] == "Inconclusive"
        assert result["confidence"] == 0.45


    @pytest.mark.parametrize("name", ["AugmentedSet", "OriginalSet"])
    def test_bundled_banana_labels_are_never_reported_as_findings(self, name):
        result = _apply_disease_threshold(_prediction(name, 0.99))

        assert result["predicted_class"] == "Inconclusive"
        assert result["confidence"] == 0.0
        assert result["all_probabilities"] == {}


class TestModelLoading:
    def test_all_bundled_models_load(self):
        pipeline = Pipeline(Config())

        pipeline.load_models()

        assert pipeline._plant is not None
        assert set(pipeline._disease_models) == {"cassava", "plantain"}

    def test_missing_models_raise(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Plant model not found"):
            Pipeline(Config(model_dir=tmp_path)).load_models()

    def test_missing_disease_model_raises(self):
        pipeline = Pipeline(Config())
        with patch.object(Config, "disease_onnx_path", return_value=Config().model_dir / "nope.onnx"):
            with pytest.raises(FileNotFoundError, match="Disease model not found"):
                pipeline._load_disease_model("cassava")

    def test_each_plant_uses_its_own_disease_model(self):
        config = Config()

        assert config.disease_onnx_path("cassava").name == "cassava_classifier.onnx"
        assert config.disease_onnx_path("plantain").name == "banana_classifier.onnx"

    def test_health_is_unavailable_when_models_fail_to_load(self):
        class BrokenPipeline:
            def load_models(self):
                raise FileNotFoundError("Plant model not found")

        with patch("core.lifespan.Pipeline", return_value=BrokenPipeline()):
            from main import app
            with TestClient(app) as client:
                while client.get("/api/v1/health").json()["status"] == "starting":
                    pass
                response = client.get("/api/v1/health")

        assert response.status_code == 503
        assert response.json()["status"] == "unavailable"


class TestVideoFailures:
    def test_unreadable_video_raises(self, tmp_path):
        with pytest.raises(OSError, match="Could not open video"):
            Pipeline(Config()).process_video(tmp_path / "missing.mp4", tmp_path)

    def test_decode_failure_midway_does_not_return_a_partial_result(self, tmp_path):
        def failing_frames(*args):
            yield 0, 0.0, np.zeros((64, 64, 3), dtype=np.uint8)
            raise OSError("Decoder failed")

        with patch("pipeline.inference.frame_iterator", failing_frames):
            with pytest.raises(OSError, match="Decoder failed"):
                Pipeline(Config(max_workers=1)).process_video("clip.mp4", tmp_path)


@pytest.mark.parametrize(
    ("disease", "actionable"),
    [
        ("Cassava Mosaic Disease (CMD)", True),
        ("Healthy", False),
        ("not detected", False),
        ("Inconclusive", False),
        ("", False),
    ],
)
def test_only_real_conditions_are_actionable(disease, actionable):
    assert is_actionable_disease(disease) is actionable
