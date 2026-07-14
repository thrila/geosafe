from unittest.mock import patch, MagicMock, ANY
import numpy as np
import pytest


class TestPreprocessDisease:
    def test_returns_correct_shape(self):
        from pipeline.preprocessing import preprocess_disease
        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        result = preprocess_disease(img, 380)
        assert result.shape == (1, 3, 380, 380)
        assert result.dtype == np.float32

    def test_values_are_normalized(self):
        from pipeline.preprocessing import preprocess_disease
        all_same = np.full((50, 50, 3), 128, dtype=np.uint8)
        result = preprocess_disease(all_same, 50)
        assert result.shape == (1, 3, 50, 50)
        assert np.isfinite(result).all()

    def test_batch_concatenates_correctly(self):
        from pipeline.preprocessing import preprocess_batch
        imgs = [np.random.randint(0, 255, (60, 60, 3), dtype=np.uint8) for _ in range(3)]
        result = preprocess_batch(imgs, 60)
        assert result.shape == (3, 3, 60, 60)
        assert result.dtype == np.float32

    def test_empty_batch_fails(self):
        from pipeline.preprocessing import preprocess_batch
        with pytest.raises(Exception):
            preprocess_batch([], 32)


class TestDiseaseModelONNX:
    def test_initializes_input_name_and_size(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 380, 380]  # [batch, channels, height, width]
        mock_session.get_inputs.return_value = [mock_input]

        mock_meta = {"class_names": {"0": "Healthy", "1": "Cassava Mosaic"}, "img_size": 380}

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pipeline.onnx_backend.json.load", return_value=mock_meta), \
             patch("builtins.open", MagicMock()), \
             patch("pathlib.Path.exists", return_value=True):
            from pipeline.onnx_backend import DiseaseModelONNX
            model = DiseaseModelONNX("fake.onnx", meta_path="fake.json")
            assert model.iname == "input"
            assert model.img_size == 380
            assert model.num_classes > 0

    def test_predict_gives_expected_keys(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 380, 380]
        mock_session.get_inputs.return_value = [mock_input]

        mock_class_names = {0: "Healthy", 1: "Cassava Mosaic"}
        mock_meta = {
            "class_names": mock_class_names,
            "img_size": 380,
        }

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pipeline.onnx_backend.json.load", return_value=mock_meta), \
             patch("builtins.open", MagicMock()), \
             patch("pathlib.Path.exists", return_value=True):
            from pipeline.onnx_backend import DiseaseModelONNX
            model = DiseaseModelONNX("fake.onnx", meta_path="fake.json")
            logits = np.array([[1.0, 0.0]], dtype=np.float32)
            mock_session.run.return_value = [logits]
            img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
            result = model.predict(img)
            assert "predicted_class" in result
            assert "predicted_index" in result
            assert "confidence" in result
            assert "all_probabilities" in result

    def test_predict_batch_returns_list(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 380, 380]
        mock_session.get_inputs.return_value = [mock_input]

        mock_class_names = {0: "Healthy", 1: "Diseased"}
        mock_meta = {"class_names": mock_class_names, "img_size": 380}

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pipeline.onnx_backend.json.load", return_value=mock_meta), \
             patch("builtins.open", MagicMock()), \
             patch("pathlib.Path.exists", return_value=True):
            from pipeline.onnx_backend import DiseaseModelONNX
            model = DiseaseModelONNX("fake.onnx", meta_path="fake.json")
            logits = np.array([[2.0, 0.0], [0.0, 2.0]], dtype=np.float32)
            mock_session.run.return_value = [logits]
            imgs = [np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8) for _ in range(2)]
            results = model.predict_batch(imgs)
            assert len(results) == 2
            assert results[0]["predicted_class"] == "Healthy"
            assert results[1]["predicted_class"] == "Diseased"

    def test_predict_batch_empty_list(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 380, 380]
        mock_session.get_inputs.return_value = [mock_input]
        mock_meta = {"class_names": {"0": "Healthy"}, "img_size": 380}
        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pipeline.onnx_backend.json.load", return_value=mock_meta), \
             patch("builtins.open", MagicMock()), \
             patch("pathlib.Path.exists", return_value=True):
            from pipeline.onnx_backend import DiseaseModelONNX
            model = DiseaseModelONNX("fake.onnx", meta_path="fake.json")
            with pytest.raises(Exception):
                model.predict_batch([])


class TestPlantModelONNX:
    def test_initializes_correctly(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 640, 640]
        mock_session.get_inputs.return_value = [mock_input]
        mock_session.run.return_value = [np.array([[0.0, 1.0]], dtype=np.float32)]

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pathlib.Path.exists", return_value=False):
            from pipeline.onnx_backend import PlantModelONNX
            model = PlantModelONNX("fake.onnx")
            assert model.iname == "input"
            assert model.input_size == (640, 640)
            assert model.class_names[0] == "cassava"

    def test_predict_uses_letterbox_resize(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 640, 640]
        mock_session.get_inputs.return_value = [mock_input]
        mock_session.run.return_value = [np.array([[0.1, 0.9]], dtype=np.float32)]

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pathlib.Path.exists", return_value=False):
            from pipeline.onnx_backend import PlantModelONNX
            model = PlantModelONNX("fake.onnx")
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            results = model.predict(frame)
            assert len(results) == 1
            assert results[0]["predicted_class"] == "plantain"
            call_input = mock_session.run.call_args[0][1]["input"]
            assert call_input.shape == (1, 3, 640, 640)
            assert call_input.dtype == np.float32

    def test_predict_called_once_per_invoke(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 640, 640]
        mock_session.get_inputs.return_value = [mock_input]
        mock_session.run.return_value = [np.array([[0.0, 1.0]], dtype=np.float32)]

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pathlib.Path.exists", return_value=False):
            from pipeline.onnx_backend import PlantModelONNX
            model = PlantModelONNX("fake.onnx")
            frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            model.predict(frame)
            assert mock_session.run.call_count == 1

    def test_raises_on_non_image_input(self):
        mock_session = MagicMock()
        mock_input = MagicMock()
        mock_input.name = "input"
        mock_input.shape = [1, 3, 640, 640]
        mock_session.get_inputs.return_value = [mock_input]
        mock_session.run.return_value = [np.array([[0.0, 1.0]], dtype=np.float32)]

        with patch("onnxruntime.InferenceSession", return_value=mock_session), \
             patch("pathlib.Path.exists", return_value=False):
            from pipeline.onnx_backend import PlantModelONNX
            model = PlantModelONNX("fake.onnx")
            with pytest.raises(Exception):
                model.predict("definitely not an image")
