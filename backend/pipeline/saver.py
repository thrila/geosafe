from __future__ import annotations

import json
from pathlib import Path
import cv2, numpy as np
from core.config import settings
from .metadata import FrameResult
from .tiler import TileCoord


def is_actionable_disease(disease: str) -> bool:
    """Whether a tile should be shown as an affected area in flight evidence."""
    return disease.strip().lower() not in {"", "healthy", "not detected"}


def persist_annotated_frame(
    frame: np.ndarray,
    detections: list[tuple[TileCoord, str, float]],
    base_dir: Path,
    fi: int,
    public_image_prefix: str | None = None,
) -> str | None:
    """Save one source frame with a tile-level heatmap and labelled affected areas.

    Tile classification does not identify disease pixels. The overlay therefore
    represents the affected *tile areas*, preserving that distinction while
    giving the user the original frame needed to inspect the field context.
    """
    if not detections:
        return None

    height, width = frame.shape[:2]
    heat = np.zeros((height, width), dtype=np.uint8)
    for tile, _, confidence in detections:
        intensity = int(120 + 135 * max(0.0, min(float(confidence), 1.0)))
        cv2.rectangle(
            heat,
            (tile.x, tile.y),
            (min(tile.x + tile.w, width - 1), min(tile.y + tile.h, height - 1)),
            intensity,
            thickness=-1,
        )

    # A blurred colour map gives nearby/overlapping positive tiles a heatmap
    # appearance; strong borders retain the actual tile boundaries.
    blur_radius = max(7, min(width, height) // 28)
    heat = cv2.GaussianBlur(heat, (0, 0), blur_radius)
    heatmap = cv2.applyColorMap(heat, cv2.COLORMAP_JET)
    alpha = (heat.astype(np.float32) / 255.0 * 0.58)[..., np.newaxis]
    annotated = (frame.astype(np.float32) * (1 - alpha) + heatmap.astype(np.float32) * alpha).astype(np.uint8)

    for tile, disease, confidence in detections:
        start = (tile.x, tile.y)
        end = (min(tile.x + tile.w, width - 1), min(tile.y + tile.h, height - 1))
        cv2.rectangle(annotated, start, end, (0, 225, 255), thickness=2)
        label = f"{disease} {confidence:.0%}"
        label_y = max(18, tile.y + 20)
        cv2.putText(
            annotated,
            label,
            (tile.x + 6, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            annotated,
            label,
            (tile.x + 6, label_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            1,
            cv2.LINE_AA,
        )

    name = f"evidence_f{fi:06d}.jpg"
    output = base_dir / name
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), annotated):
        raise OSError(f"Could not save annotated flight evidence: {output}")
    return f"{public_image_prefix.rstrip('/')}/{name}" if public_image_prefix else None


def persist(
    img: np.ndarray,
    plant_r: dict,
    disease_r: dict,
    base_dir: Path,
    idx: int,
    fi: int,
    ts: float,
    backend: str,
    public_image_prefix: str | None = None,
    image_url: str | None = None,
    save_tile: bool = True,
) -> FrameResult:
    diseased = is_actionable_disease(disease_r.get("predicted_class", ""))
    name = f"f{fi:06d}_t{idx:03d}.jpg"
    if diseased and save_tile and image_url is None:
        # Kept for callers that need individual tiles. Flight analysis passes
        # save_tile=False and supplies a full-frame evidence URL instead.
        p = base_dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(p), img)
        image_url = f"{public_image_prefix.rstrip('/')}/{name}" if public_image_prefix else None
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
