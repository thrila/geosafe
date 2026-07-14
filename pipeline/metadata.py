from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class FrameResult:
    image: str
    timestamp: float
    frame: int
    tile: int
    plant_class: str
    plant_conf: float
    disease: str
    disease_conf: float
    disease_probs: Optional[Dict[str, float]] = None
    backend: str = "onnx"
    rejected: bool = False
    reject_reason: Optional[str] = None
    image_b64: Optional[str] = None
    image_url: Optional[str] = None
