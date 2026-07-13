from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pytest
import torch

from controllers.predict import MaizeClassifier, _resolve_model_path, predict


class TestResolveModelPath:
    def test_existing_path_returned(self, sample_image):
        result = _resolve_model_path(sample_image)
        assert result == sample_image

    def test_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            _resolve_model_path("/nonexistent/model.pt")


class TestMaizeClassifier:
    def test_output_shape(self):
        model = MaizeClassifier(num_classes=3)
        x = torch.randn(1, 3, 224, 224)
        out = model(x)
        assert out.shape == (1, 3)

    def test_different_num_classes(self):
        model = MaizeClassifier(num_classes=5)
        x = torch.randn(2, 3, 224, 224)
        out = model(x)
        assert out.shape == (2, 5)

    def test_model_in_eval_mode(self):
        model = MaizeClassifier(num_classes=3)
        model.eval()
        assert not model.training


class TestPredict:
    def test_predict_returns_expected_keys(self, sample_image):
        model = MaizeClassifier(num_classes=3)
        model.eval()
        class_names = ["Corn_Rust", "Corn_Healthy", "Corn_Blight"]
        result = predict(sample_image, model, class_names)
        assert "prediction" in result
        assert "confidence" in result
        assert "all_scores" in result

    def test_predict_confidence_is_percentage_string(self, sample_image):
        model = MaizeClassifier(num_classes=3)
        model.eval()
        class_names = ["Corn_Rust", "Corn_Healthy", "Corn_Blight"]
        result = predict(sample_image, model, class_names)
        assert result["confidence"].endswith("%")

    def test_predict_all_scores_match_class_names(self, sample_image):
        model = MaizeClassifier(num_classes=3)
        model.eval()
        class_names = ["Corn_Rust", "Corn_Healthy", "Corn_Blight"]
        result = predict(sample_image, model, class_names)
        for name in class_names:
            clean = name.replace("Corn_", "")
            assert clean in result["all_scores"]

    def test_predict_file_not_found_raises(self):
        model = MaizeClassifier(num_classes=3)
        model.eval()
        class_names = ["Corn_Rust", "Corn_Healthy", "Corn_Blight"]
        with pytest.raises(FileNotFoundError):
            predict("/nonexistent/image.jpg", model, class_names)

    def test_predict_prediction_is_one_of_classes(self, sample_image):
        model = MaizeClassifier(num_classes=3)
        model.eval()
        class_names = ["Corn_Rust", "Corn_Healthy", "Corn_Blight"]
        result = predict(sample_image, model, class_names)
        expected = {name.replace("Corn_", "") for name in class_names}
        assert result["prediction"] in expected
