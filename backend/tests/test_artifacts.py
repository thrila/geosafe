from __future__ import annotations

import numpy as np

from pipeline.saver import persist, persist_annotated_frame
from pipeline.tiler import TileCoord


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
    assert (tmp_path / result.image).is_file()


def test_annotated_evidence_is_a_full_source_frame_with_a_public_url(tmp_path):
    frame = np.zeros((80, 120, 3), dtype=np.uint8)
    url = persist_annotated_frame(
        frame,
        [(TileCoord(x=20, y=10, w=50, h=40, tile_idx=2), "CMD", 0.95)],
        tmp_path,
        fi=7,
        public_image_prefix="/api/v1/images/flight-artifact",
    )

    saved = tmp_path / "evidence_f000007.jpg"
    evidence = __import__("cv2").imread(str(saved))
    assert url == "/api/v1/images/flight-artifact/evidence_f000007.jpg"
    assert evidence.shape[:2] == frame.shape[:2]
    assert evidence[30, 45].sum() > 0
