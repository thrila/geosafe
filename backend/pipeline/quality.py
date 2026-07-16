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
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        r = self._blur(gray)
        if r: return r
        r = self._bright(gray)
        return r

    def _blur(self, gray: np.ndarray):
        v = cv2.Laplacian(gray, cv2.CV_64F).var()
        return None if v >= self.blur_t else f"blurry (var={v:.1f}<{self.blur_t})"

    def _bright(self, gray: np.ndarray):
        b = gray.mean()
        if b < self.min_b: return f"dark (b={b:.1f}<{self.min_b})"
        if b > self.max_b: return f"bright (b={b:.1f}>{self.max_b})"
        return None
