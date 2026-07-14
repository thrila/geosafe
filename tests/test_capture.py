from __future__ import annotations

import numpy as np

from pipeline.quality import QualityCheck


class TestQualityCheck:
    def test_uniform_frame_is_blurry(self):
        qc = QualityCheck(blur_t=100.0)
        r = qc.check(np.full((100, 100, 3), 128, dtype=np.uint8), 0, 0)
        assert r is not None and "blurry" in r

    def test_edge_frame_not_blurry(self):
        qc = QualityCheck(blur_t=100.0)
        f = np.zeros((100, 100, 3), dtype=np.uint8)
        f[:, :50] = 0
        f[:, 50:] = 255
        r = qc.check(f, 0, 0)
        assert r is None or "blurry" not in r

    def test_dark_frame_rejected(self):
        qc = QualityCheck(blur_t=1.0, min_b=50.0)
        f = np.full((100, 100, 3), 10, dtype=np.uint8)
        f[::2, :] = 30
        r = qc.check(f, 0, 0)
        assert r is not None and "dark" in r

    def test_bright_frame_rejected(self):
        qc = QualityCheck(blur_t=1.0, max_b=200.0)
        f = np.full((100, 100, 3), 240, dtype=np.uint8)
        f[::2, :] = 220
        r = qc.check(f, 0, 0)
        assert r is not None and "bright" in r
