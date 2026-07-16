from __future__ import annotations

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess_disease(img: np.ndarray, size: int) -> np.ndarray:
    logger.debug("preprocess_disease: input shape=%s, target size=%d", img.shape, size)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    resized = cv2.resize(rgb, (size, size), interpolation=cv2.INTER_LINEAR)
    arr = resized.astype(np.float32) / 255.0
    arr = (arr - _MEAN) / _STD
    arr = arr.transpose(2, 0, 1)[None, :]
    logger.debug("preprocess_disease: output shape=%s min=%.3f max=%.3f", arr.shape, arr.min(), arr.max())
    return arr


def preprocess_batch(images: list[np.ndarray], size: int) -> np.ndarray:
    logger.debug("preprocess_batch: %d images, target size=%d", len(images), size)
    batch = np.stack(
        [cv2.cvtColor(img, cv2.COLOR_BGR2RGB) for img in images], axis=0
    )
    batch = np.stack(
        [cv2.resize(img, (size, size), interpolation=cv2.INTER_LINEAR) for img in batch],
        axis=0,
    )
    batch = batch.astype(np.float32) / 255.0
    batch = (batch - _MEAN) / _STD
    result = batch.transpose(0, 3, 1, 2)
    logger.debug("preprocess_batch: output shape=%s", result.shape)
    return result
