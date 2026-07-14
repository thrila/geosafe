from __future__ import annotations

from typing import Optional
import cv2
import numpy as np


class QualityCheck:
    def __init__(self, blur_t=100.0, min_b=30.0, max_b=230.0):
        self.blur_t = blur_t
        self.min_b = min_b
        self.max_b = max_b

    def check(self, frame: np.ndarray, fi: int, ts: float) -> Optional[str]:
        r = self._blur(frame)
        if r: return r
        r = self._bright(frame)
        return r

    def _blur(self, frame):
        v = cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
        return None if v >= self.blur_t else f"blurry (var={v:.1f}<{self.blur_t})"

    def _bright(self, frame):
        b = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).mean()
        if b < self.min_b: return f"dark (b={b:.1f}<{self.min_b})"
        if b > self.max_b: return f"bright (b={b:.1f}>{self.max_b})"
        return None
