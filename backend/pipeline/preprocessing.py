from __future__ import annotations

import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def preprocess_disease(img: np.ndarray, size: int) -> np.ndarray:
    logger.debug("preprocess_disease: input shape=%s, target size=%d", img.shape, size)
    pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    pil = pil.resize((size, size), Image.BILINEAR)
    arr = np.asarray(pil, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    arr = (arr - mean) / std
    arr = arr.transpose(2, 0, 1)[None, :]
    logger.debug("preprocess_disease: output shape=%s min=%.3f max=%.3f", arr.shape, arr.min(), arr.max())
    return arr.astype(np.float32)


def preprocess_batch(images: list[np.ndarray], size: int) -> np.ndarray:
    logger.debug("preprocess_batch: %d images, target size=%d", len(images), size)
    result = np.concatenate([preprocess_disease(i, size) for i in images], axis=0)
    logger.debug("preprocess_batch: output shape=%s", result.shape)
    return result
