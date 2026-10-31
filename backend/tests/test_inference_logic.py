"""Pin the decisions the pipeline makes from raw model scores."""

from __future__ import annotations

import pytest

from pipeline.inference import _apply_disease_threshold
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
