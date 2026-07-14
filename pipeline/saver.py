from __future__ import annotations

import json
from pathlib import Path
import cv2, numpy as np
from .metadata import FrameResult


def persist(img: np.ndarray, plant_r: dict, disease_r: dict, base_dir: Path,
            idx: int, fi: int, ts: float, backend: str) -> FrameResult:
    diseased = disease_r.get("predicted_class", "").lower() != "healthy"
    name = f"f{fi:06d}_t{idx:03d}.jpg"
    image_url = None
    if diseased:
        p = base_dir / "images" / name
        p.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(p), img)
        image_url = f"/api/v1/images/{name}"
    md = {
        "image": name, "timestamp": round(ts, 3), "frame": fi, "tile": idx,
        "plant_class": plant_r.get("predicted_class", ""),
        "plant_confidence": plant_r.get("confidence", 0),
        "disease": disease_r.get("predicted_class", ""),
        "disease_confidence": disease_r.get("confidence", 0),
        "all_probabilities": disease_r.get("all_probabilities", {}),
        "backend": backend, "diseased": diseased,
    }
    md_dir = base_dir / "metadata"
    md_dir.mkdir(parents=True, exist_ok=True)
    with open(md_dir / (Path(name).stem + ".json"), "w") as f:
        json.dump(md, f, indent=2)
    return FrameResult(image=name, timestamp=round(ts, 3), frame=fi, tile=idx,
        plant_class=plant_r.get("predicted_class", ""),
        plant_conf=plant_r.get("confidence", 0),
        disease=disease_r.get("predicted_class", ""),
        disease_conf=disease_r.get("confidence", 0),
        disease_probs=disease_r.get("all_probabilities"),
        backend=backend, image_url=image_url)
