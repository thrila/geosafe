from __future__ import annotations

from pathlib import Path
from typing import Iterator, Tuple
import cv2
import numpy as np


def frame_iterator(
    source: str | Path,
    target_fps: float = 5.0,
) -> Iterator[Tuple[int, float, np.ndarray]]:
    cap = cv2.VideoCapture(str(source))
    if not cap.isOpened():
        raise IOError(f"Could not open video: {source}")

    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    interval = max(1, round(src_fps / target_fps))

    idx = 0

    try:
        while True:
            if idx % interval == 0:
                # Decode this frame into a NumPy array.
                ok = cap.grab()
                if not ok:
                    break

                ok, frame = cap.retrieve()
                if not ok:
                    break

                yield idx, idx / src_fps, frame
            else:
                # Skip materializing this frame.
                if not cap.grab():
                    break

            idx += 1
    finally:
        cap.release()
