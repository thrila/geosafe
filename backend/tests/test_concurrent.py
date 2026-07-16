from __future__ import annotations

import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


class TestPlantModelBatchPredict:
    def test_predict_batch_returns_correct_count(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 640, 640]
        mock_session.get_inputs.return_value = [mock_input]
        mock_session.run.return_value = [np.array([[0.1, 0.9], [0.8, 0.2]], dtype=np.float32)]

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pathlib.Path.exists", return_value=False):
            from pipeline.onnx_backend import PlantModelONNX
            model = PlantModelONNX("fake.onnx")
            imgs = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(2)]
            results = model.predict_batch(imgs)
            assert len(results) == 2

    def test_predict_batch_matches_singular(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 640, 640]
        mock_session.get_inputs.return_value = [mock_input]

        logits_singular = np.array([[0.3, 0.7]], dtype=np.float32)
        logits_batch = np.array([[0.3, 0.7], [0.3, 0.7]], dtype=np.float32)

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pathlib.Path.exists", return_value=False):
            from pipeline.onnx_backend import PlantModelONNX
            model = PlantModelONNX("fake.onnx")

            mock_session.run.return_value = [logits_singular]
            frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            singular_result = model.predict(frame)

            mock_session.run.return_value = [logits_batch]
            frames = [frame.copy(), frame.copy()]
            batch_results = model.predict_batch(frames)

            assert singular_result[0]["predicted_class"] == batch_results[0]["predicted_class"]
            assert singular_result[0]["confidence"] == pytest.approx(batch_results[0]["confidence"], abs=0.01)

    def test_predict_batch_empty_list_raises(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 640, 640]
        mock_session.get_inputs.return_value = [mock_input]

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pathlib.Path.exists", return_value=False):
            from pipeline.onnx_backend import PlantModelONNX
            model = PlantModelONNX("fake.onnx")
            with pytest.raises((ValueError, IndexError)):
                model.predict_batch([])


class TestThreadSafeModelLoading:
    def test_concurrent_load_plant_model_no_duplicate(self):
        from pipeline.config import Config
        from pipeline.inference import Pipeline

        config = Config()
        pipeline = Pipeline(config)

        threads = [threading.Thread(target=pipeline.plant_model) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert pipeline._plant is not None

    def test_concurrent_load_disease_model_no_duplicate(self):
        from pipeline.config import Config
        from pipeline.inference import Pipeline

        config = Config()
        pipeline = Pipeline(config)

        mock_plant = MagicMock()
        mock_plant.predict.return_value = [{"predicted_class": "cassava", "confidence": 0.99}]
        pipeline._plant = mock_plant

        with patch("pipeline.onnx_backend.DiseaseModelONNX"):
            threads = [threading.Thread(target=pipeline._load_disease_model, args=("cassava",)) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        assert "cassava" in pipeline._disease_models


class TestConcurrentProcessVideo:
    def test_batch_inference_same_results_as_singular(self):
        from pipeline.config import Config
        from pipeline.inference import Pipeline

        config = Config()
        pipeline = Pipeline(config)

        mock_plant = MagicMock()
        mock_plant.predict.return_value = [{"predicted_class": "cassava", "confidence": 0.95}]
        mock_plant.predict_batch.return_value = [
            {"predicted_class": "cassava", "confidence": 0.95},
            {"predicted_class": "cassava", "confidence": 0.95},
            {"predicted_class": "cassava", "confidence": 0.95},
            {"predicted_class": "cassava", "confidence": 0.95},
        ]
        pipeline._plant = mock_plant

        mock_disease = MagicMock()
        mock_disease.predict.return_value = {
            "predicted_class": "Healthy",
            "predicted_index": 4,
            "confidence": 0.9,
            "all_probabilities": {"Healthy": 0.9},
        }
        mock_disease.predict_batch.return_value = [
            {"predicted_class": "Healthy", "predicted_index": 4, "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
            {"predicted_class": "Healthy", "predicted_index": 4, "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
            {"predicted_class": "Healthy", "predicted_index": 4, "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
            {"predicted_class": "Healthy", "predicted_index": 4, "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
        ]
        pipeline._disease_models["cassava"] = mock_disease

        tiles = [np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8) for _ in range(4)]

        singular_results = []
        for tile in tiles:
            singular_results.append(pipeline._infer(tile))

        batch_results = pipeline._infer_batch(tiles)

        assert len(batch_results) == len(singular_results)
        for singular, batch in zip(singular_results, batch_results):
            assert singular[0]["predicted_class"] == batch[0]["predicted_class"]
            assert singular[1]["predicted_class"] == batch[1]["predicted_class"]

    def test_bench_counts_accurate_with_threads(self):
        from pipeline.benchmark import Bench

        bench = Bench()
        lock = threading.Lock()

        def worker():
            for _ in range(100):
                bench.append(inf=0.01, total=0.01)

        threads = [threading.Thread(target=worker) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(bench.inf) == 400
        assert len(bench.total) == 400


class TestBatchInferenceEdgeCases:
    def test_batch_single_tile(self):
        from pipeline.config import Config
        from pipeline.inference import Pipeline

        config = Config()
        pipeline = Pipeline(config)

        mock_plant = MagicMock()
        mock_plant.predict.return_value = [{"predicted_class": "cassava", "confidence": 0.95}]
        mock_plant.predict_batch.return_value = [
            {"predicted_class": "cassava", "confidence": 0.95},
        ]
        pipeline._plant = mock_plant

        mock_disease = MagicMock()
        mock_disease.predict.return_value = {
            "predicted_class": "Healthy",
            "predicted_index": 4,
            "confidence": 0.9,
            "all_probabilities": {"Healthy": 0.9},
        }
        mock_disease.predict_batch.return_value = [
            {"predicted_class": "Healthy", "predicted_index": 4, "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
        ]
        pipeline._disease_models["cassava"] = mock_disease

        tile = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        results = pipeline._infer_batch([tile])
        assert len(results) == 1

    def test_batch_mixed_plant_classes(self):
        from pipeline.config import Config
        from pipeline.inference import Pipeline

        config = Config()
        pipeline = Pipeline(config)

        call_count = {"cassava": 0, "plantain": 0}

        def mock_predict(frame):
            plant_class = "cassava" if call_count["cassava"] <= call_count["plantain"] else "plantain"
            call_count[plant_class] += 1
            return [{"predicted_class": plant_class, "confidence": 0.9}]

        def mock_predict_batch(frames):
            results = []
            for _ in frames:
                plant_class = "cassava" if call_count["cassava"] <= call_count["plantain"] else "plantain"
                call_count[plant_class] += 1
                results.append({"predicted_class": plant_class, "confidence": 0.9})
            return results

        mock_plant = MagicMock()
        mock_plant.predict.side_effect = mock_predict
        mock_plant.predict_batch.side_effect = mock_predict_batch
        pipeline._plant = mock_plant

        mock_disease = MagicMock()
        mock_disease.predict.return_value = {
            "predicted_class": "Healthy",
            "predicted_index": 4,
            "confidence": 0.9,
            "all_probabilities": {"Healthy": 0.9},
        }
        mock_disease.predict_batch.return_value = [
            {"predicted_class": "Healthy", "predicted_index": 4, "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
        ] * 6
        pipeline._disease_models["cassava"] = mock_disease
        pipeline._disease_models["plantain"] = mock_disease

        tiles = [np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8) for _ in range(6)]
        results = pipeline._infer_batch(tiles)
        assert len(results) == 6


class TestSharedBatchBuffer:
    """Tests for the shared batch buffer in process_video."""

    def _make_synthetic_video(self, path: Path, num_frames: int = 12, fps: float = 5.0):
        import cv2
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(path), fourcc, int(fps), (320, 240))
        for i in range(num_frames):
            frame = np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8)
            writer.write(frame)
        writer.release()

    def _mock_pipeline(self, config):
        from pipeline.inference import Pipeline
        pipeline = Pipeline(config)

        mock_plant = MagicMock()
        mock_plant.predict.return_value = [{"predicted_class": "cassava", "confidence": 0.95}]
        mock_plant.predict_batch.return_value = [
            {"predicted_class": "cassava", "confidence": 0.95},
        ] * 64
        pipeline._plant = mock_plant

        mock_disease = MagicMock()
        mock_disease.predict.return_value = {
            "predicted_class": "Healthy",
            "predicted_index": 4,
            "confidence": 0.9,
            "all_probabilities": {"Healthy": 0.9},
        }
        mock_disease.predict_batch.return_value = [
            {"predicted_class": "Healthy", "predicted_index": 4, "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
        ] * 64
        pipeline._disease_models["cassava"] = mock_disease
        return pipeline

    def test_all_frames_processed_no_loss(self, tmp_path):
        from pipeline.config import Config
        video = tmp_path / "test.mp4"
        self._make_synthetic_video(video, num_frames=12)
        config = Config(max_workers=4, batch_size=4)
        pipeline = self._mock_pipeline(config)

        with tempfile.TemporaryDirectory() as td:
            result = pipeline.process_video(video, Path(td))

        assert result["frames_analyzed"] + result["frames_rejected"] == 12
        assert result["frames_analyzed"] > 0

    def test_single_worker_process_video(self, tmp_path):
        from pipeline.config import Config
        video = tmp_path / "test.mp4"
        self._make_synthetic_video(video, num_frames=8)
        config = Config(max_workers=1, batch_size=4)
        pipeline = self._mock_pipeline(config)

        with tempfile.TemporaryDirectory() as td:
            result = pipeline.process_video(video, Path(td))

        assert result["frames_analyzed"] + result["frames_rejected"] == 8

    def test_large_batch_size_still_works(self, tmp_path):
        from pipeline.config import Config
        video = tmp_path / "test.mp4"
        self._make_synthetic_video(video, num_frames=6)
        config = Config(max_workers=2, batch_size=100)
        pipeline = self._mock_pipeline(config)

        with tempfile.TemporaryDirectory() as td:
            result = pipeline.process_video(video, Path(td))

        assert result["frames_analyzed"] + result["frames_rejected"] == 6

    def test_bench_has_entries_per_batch(self, tmp_path):
        from pipeline.config import Config
        video = tmp_path / "test.mp4"
        self._make_synthetic_video(video, num_frames=12)
        config = Config(max_workers=2, batch_size=4)
        pipeline = self._mock_pipeline(config)

        with tempfile.TemporaryDirectory() as td:
            result = pipeline.process_video(video, Path(td))

        bench = result["benchmark"]
        assert bench["avg_inference_ms"] > 0
        assert bench["throughput_fps"] > 0


class TestBatchRetryOnFailure:
    """Tests that failed batches are returned to shared_batch for retry."""

    def test_batch_failure_returns_items(self, tmp_path):
        import cv2
        import tempfile
        from pipeline.config import Config
        from pipeline.inference import Pipeline

        video = tmp_path / "test.mp4"
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(video), fourcc, 5, (320, 240))
        for _ in range(8):
            writer.write(np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8))
        writer.release()

        config = Config(max_workers=2, batch_size=4)
        pipeline = Pipeline(config)

        mock_plant = MagicMock()
        mock_plant.predict.return_value = [{"predicted_class": "cassava", "confidence": 0.95}]
        mock_plant.predict_batch.return_value = [
            {"predicted_class": "cassava", "confidence": 0.95},
        ] * 64
        pipeline._plant = mock_plant

        mock_disease = MagicMock()
        mock_disease.predict.return_value = {
            "predicted_class": "Healthy", "predicted_index": 4,
            "confidence": 0.9, "all_probabilities": {"Healthy": 0.9},
        }
        mock_disease.predict_batch.return_value = [
            {"predicted_class": "Healthy", "predicted_index": 4,
             "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
        ] * 64
        pipeline._disease_models["cassava"] = mock_disease

        call_count = [0]
        original_infer_batch = pipeline._infer_batch

        def flaky_infer_batch(frames):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Simulated inference failure")
            return original_infer_batch(frames)

        pipeline._infer_batch = flaky_infer_batch

        with tempfile.TemporaryDirectory() as td:
            result = pipeline.process_video(video, Path(td))

        assert result["frames_analyzed"] + result["frames_rejected"] == 8
        assert call_count[0] > 1


class TestConcurrentWorkerSafety:
    """Tests that verify thread-safety of shared state."""

    def test_rejected_count_accuracy(self, tmp_path):
        import cv2
        import tempfile
        from pipeline.config import Config
        from pipeline.inference import Pipeline

        video = tmp_path / "test.mp4"
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(video), fourcc, 5, (320, 240))
        for _ in range(10):
            writer.write(np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8))
        writer.release()

        config = Config(max_workers=4, batch_size=3)
        pipeline = Pipeline(config)

        mock_plant = MagicMock()
        mock_plant.predict.return_value = [{"predicted_class": "cassava", "confidence": 0.95}]
        mock_plant.predict_batch.return_value = [
            {"predicted_class": "cassava", "confidence": 0.95},
        ] * 64
        pipeline._plant = mock_plant

        mock_disease = MagicMock()
        mock_disease.predict.return_value = {
            "predicted_class": "Healthy", "predicted_index": 4,
            "confidence": 0.9, "all_probabilities": {"Healthy": 0.9},
        }
        mock_disease.predict_batch.return_value = [
            {"predicted_class": "Healthy", "predicted_index": 4,
             "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
        ] * 64
        pipeline._disease_models["cassava"] = mock_disease

        with tempfile.TemporaryDirectory() as td:
            result = pipeline.process_video(video, Path(td))

        total = result["frames_analyzed"] + result["frames_rejected"]
        assert total == 10
        assert result["frames_rejected"] >= 0

    def test_producer_consumer_no_deadlock(self, tmp_path):
        import cv2
        import tempfile
        from pipeline.config import Config
        from pipeline.inference import Pipeline

        video = tmp_path / "test.mp4"
        fourcc = cv2.VideoWriter.fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(video), fourcc, 5, (320, 240))
        for _ in range(6):
            writer.write(np.random.randint(0, 255, (240, 320, 3), dtype=np.uint8))
        writer.release()

        config = Config(max_workers=4, batch_size=8)
        pipeline = self._mock_pipeline(config)

        with tempfile.TemporaryDirectory() as td:
            result = pipeline.process_video(video, Path(td))

        assert result["frames_analyzed"] + result["frames_rejected"] == 6

    def _mock_pipeline(self, config):
        from pipeline.inference import Pipeline
        pipeline = Pipeline(config)

        mock_plant = MagicMock()
        mock_plant.predict.return_value = [{"predicted_class": "cassava", "confidence": 0.95}]
        mock_plant.predict_batch.return_value = [
            {"predicted_class": "cassava", "confidence": 0.95},
        ] * 64
        pipeline._plant = mock_plant

        mock_disease = MagicMock()
        mock_disease.predict.return_value = {
            "predicted_class": "Healthy", "predicted_index": 4,
            "confidence": 0.9, "all_probabilities": {"Healthy": 0.9},
        }
        mock_disease.predict_batch.return_value = [
            {"predicted_class": "Healthy", "predicted_index": 4,
             "confidence": 0.9, "all_probabilities": {"Healthy": 0.9}},
        ] * 64
        pipeline._disease_models["cassava"] = mock_disease
        return pipeline
