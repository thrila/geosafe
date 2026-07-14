from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple
import cv2
import numpy as np


def frame_iterator(
    source: str | Path, target_fps: float = 5.0
) -> Iterator[Tuple[int, float, np.ndarray]]:
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise IOError(f"Could not open video: {source}")
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    interval = max(1, int(round(src_fps / target_fps)))
    idx = 0
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % interval == 0:
            yield idx, idx / src_fps, frame
        idx += 1
    cap.release()
