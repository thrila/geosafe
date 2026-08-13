from __future__ import annotations

import numpy as np

from pipeline.saver import persist


def test_diseased_artifact_has_a_flight_scoped_public_url(tmp_path):
    result = persist(
        np.zeros((8, 8, 3), dtype=np.uint8),
        {"predicted_class": "cassava", "confidence": 0.9},
        {"predicted_class": "CMD", "confidence": 0.95},
        tmp_path,
        idx=2,
        fi=7,
        ts=1.4,
        backend="onnx",
        public_image_prefix="/api/v1/images/flight-artifact",
    )

    assert result.image_url == "/api/v1/images/flight-artifact/f000007_t002.jpg"
    assert (tmp_path / "images" / result.image).is_file()
