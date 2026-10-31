"""Pin the decisions the pipeline makes from raw model scores."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import cv2
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


class TestPlantGate:
    def _pipeline(self, plant_class: str, confidence: float):
        pipeline = Pipeline(Config())
        pipeline._plant = MagicMock()
        pipeline._plant.predict.return_value = [
            {"predicted_class": plant_class, "confidence": confidence}
        ]
        disease_model = MagicMock()
        disease_model.predict.return_value = _prediction("Healthy", 0.9)
        pipeline._disease_models = {"cassava": disease_model, "plantain": disease_model}
        return pipeline, disease_model

    def test_tile_at_the_threshold_is_classified(self):
        pipeline, disease_model = self._pipeline("cassava", 0.7)

        ((plant, disease),) = pipeline._infer_batch([np.zeros((8, 8, 3), dtype=np.uint8)])

        assert plant["predicted_class"] == "cassava"
        assert disease["predicted_class"] == "Healthy"
        disease_model.predict.assert_called_once()

    def test_tile_below_the_threshold_skips_the_disease_model(self):
        pipeline, disease_model = self._pipeline("cassava", 0.69)

        ((plant, disease),) = pipeline._infer_batch([np.zeros((8, 8, 3), dtype=np.uint8)])

        assert plant["predicted_class"] == "not detected"
        assert disease["predicted_class"] == "not detected"
        disease_model.predict.assert_not_called()

    def test_tiles_reach_the_disease_model_for_their_own_plant(self):
        pipeline, _ = self._pipeline("cassava", 0.9)
        cassava_model, plantain_model = MagicMock(), MagicMock()
        cassava_model.predict.return_value = _prediction("Healthy", 0.9)
        plantain_model.predict.return_value = _prediction("Healthy", 0.9)
        pipeline._disease_models = {"cassava": cassava_model, "plantain": plantain_model}
        pipeline._plant.predict.side_effect = [
            [{"predicted_class": "cassava", "confidence": 0.9}],
            [{"predicted_class": "plantain", "confidence": 0.9}],
        ]
        frames = [np.zeros((8, 8, 3), dtype=np.uint8), np.ones((8, 8, 3), dtype=np.uint8)]
        pipeline._plant_executor = MagicMock()
        pipeline._plant_executor.map.side_effect = lambda fn, items: [fn(item) for item in items]

        pipeline._infer_batch(frames)

        assert cassava_model.predict.call_args.args[0] is frames[0]
        assert plantain_model.predict.call_args.args[0] is frames[1]


class TestEvidence:
    def _analyze(self, tmp_path, disease: str):
        video = tmp_path / "clip.mp4"
        writer = cv2.VideoWriter(str(video), cv2.VideoWriter.fourcc(*"mp4v"), 5, (320, 240))
        for _ in range(4):
            writer.write(np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8))
        writer.release()
        pipeline = Pipeline(Config(fps=5, max_workers=1, batch_size=1))
        pipeline._plant = MagicMock()
        pipeline._plant.predict.return_value = [{"predicted_class": "cassava", "confidence": 0.9}]
        disease_model = MagicMock()
        disease_model.predict.return_value = _prediction(disease, 0.9)
        pipeline._disease_models["cassava"] = disease_model
        out = tmp_path / "out"
        return pipeline.process_video(video, out, "/api/v1/images/run"), out

    def test_findings_link_to_a_saved_evidence_frame(self, tmp_path):
        result, out = self._analyze(tmp_path, "Cassava Mosaic Disease (CMD)")

        row = result["per_frame_results"][0]
        name = f"evidence_f{row['frame']:06d}.jpg"
        assert row["image_url"] == f"/api/v1/images/run/{name}"
        assert (out / name).is_file()
        assert result["prediction"]["disease"] == "Cassava Mosaic Disease (CMD)"

    def test_healthy_tiles_have_no_evidence(self, tmp_path):
        result, out = self._analyze(tmp_path, "Healthy")

        assert all(row["image_url"] is None for row in result["per_frame_results"])
        assert not list(out.glob("evidence_*.jpg"))


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


    def test_frame_failure_does_not_return_a_partial_result(self, tmp_path):
        def frames(*args):
            yield 0, 0.0, np.zeros((64, 64, 3), dtype=np.uint8)

        pipeline = Pipeline(Config(max_workers=1))
        with patch("pipeline.inference.frame_iterator", frames), \
             patch.object(pipeline.quality, "check", side_effect=KeyError("bad frame")):
            with pytest.raises(RuntimeError, match="no partial result"):
                pipeline.process_video("clip.mp4", tmp_path)


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
