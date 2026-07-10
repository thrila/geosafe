"""
plant_sampler.py

Pipeline:
  1. Extract frames from an aerial farm video at a given sample rate.
  2. Detect individual plants in each frame with a YOLO model.
  3. Crop a fixed-dimension patch centered on each detection.
  4. Batch the patches and pipe them to a specialized model (classifier,
     disease detector, etc.) via a pluggable inference function.

Design notes:
  - Detection and inference are decoupled behind clear function boundaries
    so you can swap YOLOv8 for another detector, or swap the "specialized
    model" call for a local torch model / FastAPI endpoint / Claude Vision
    call without touching the sampling logic.
  - Crops are deterministic given (frame, box, patch_size) -- no randomness,
    consistent with keeping the pipeline auditable.
  - Frame + detection metadata is written alongside patches so you can trace
    any prediction back to its exact source frame/timestamp/box.

Usage:
  python plant_sampler.py \
      --video farm.mp4 \
      --weights yolov8_plants.pt \
      --patch-size 224 224 \
      --sample-every 15 \
      --conf 0.35 \
      --out-dir ./samples
"""

import argparse
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterator, List

import cv2
import numpy as np


# --------------------------------------------------------------------------
# Data structures
# --------------------------------------------------------------------------

@dataclass
class Detection:
    frame_index: int
    timestamp_sec: float
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float
    class_id: int


@dataclass
class Patch:
    detection: Detection
    image: np.ndarray  # BGR, shape = (patch_h, patch_w, 3)
    patch_id: str


# --------------------------------------------------------------------------
# 1. Frame extraction
# --------------------------------------------------------------------------

def extract_frames(video_path: str, sample_every: int = 1) -> Iterator[tuple]:
    """Yield (frame_index, timestamp_sec, frame) for every `sample_every`th frame."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_index = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_index % sample_every == 0:
            timestamp_sec = frame_index / fps
            yield frame_index, timestamp_sec, frame
        frame_index += 1

    cap.release()


# --------------------------------------------------------------------------
# 2. Plant detection
# --------------------------------------------------------------------------

class PlantDetector:
    """Thin wrapper around a YOLO model (Ultralytics) for plant localization."""

    def __init__(self, weights_path: str, conf_threshold: float = 0.35, device: str = "cpu"):
        from ultralytics import YOLO  # deferred import, keep this optional
        self.model = YOLO(weights_path)
        self.conf_threshold = conf_threshold
        self.device = device

    def detect(self, frame: np.ndarray, frame_index: int, timestamp_sec: float) -> List[Detection]:
        results = self.model.predict(
            source=frame,
            conf=self.conf_threshold,
            device=self.device,
            verbose=False,
        )

        detections = []
        for r in results:
            boxes = r.boxes
            if boxes is None:
                continue
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                detections.append(
                    Detection(
                        frame_index=frame_index,
                        timestamp_sec=timestamp_sec,
                        x1=int(x1), y1=int(y1), x2=int(x2), y2=int(y2),
                        confidence=float(box.conf[0]),
                        class_id=int(box.cls[0]),
                    )
                )
        return detections


# --------------------------------------------------------------------------
# 3. Cropping to a fixed dimension
# --------------------------------------------------------------------------

def crop_patch(frame: np.ndarray, det: Detection, patch_size: tuple) -> np.ndarray:
    """
    Crop a fixed-size (w, h) patch centered on the detection box.
    Clips to frame bounds and pads with black if the center crop would
    run off the edge (keeps output dimensions exactly patch_size).
    """
    target_w, target_h = patch_size
    frame_h, frame_w = frame.shape[:2]

    cx = (det.x1 + det.x2) // 2
    cy = (det.y1 + det.y2) // 2

    x1 = cx - target_w // 2
    y1 = cy - target_h // 2
    x2 = x1 + target_w
    y2 = y1 + target_h

    # Compute overlap with valid frame region
    src_x1, src_y1 = max(x1, 0), max(y1, 0)
    src_x2, src_y2 = min(x2, frame_w), min(y2, frame_h)

    dst_x1 = src_x1 - x1
    dst_y1 = src_y1 - y1
    dst_x2 = dst_x1 + (src_x2 - src_x1)
    dst_y2 = dst_y1 + (src_y2 - src_y1)

    patch = np.zeros((target_h, target_w, 3), dtype=frame.dtype)
    patch[dst_y1:dst_y2, dst_x1:dst_x2] = frame[src_y1:src_y2, src_x1:src_x2]
    return patch


# --------------------------------------------------------------------------
# 4. Pipe to specialized model
# --------------------------------------------------------------------------

def run_specialized_model(patches: List[Patch]) -> List[dict]:
    """
    Placeholder for the downstream model call.

    Swap this out for whatever "specialized model" means in your setup, e.g.:

      - A local torch classifier (your EfficientNetV2-S maize model):
          batch = torch.stack([preprocess(p.image) for p in patches])
          with torch.no_grad():
              logits = model(batch)
          preds = logits.softmax(dim=1)

      - A FastAPI endpoint:
          resp = requests.post(API_URL, files=[("images", encode(p.image)) for p in patches])

      - Claude Vision (per-patch, since it takes single images):
          send each p.image as base64 with a classification prompt

    Returning stubbed results here so the pipeline runs end-to-end.
    """
    return [
        {"patch_id": p.patch_id, "prediction": "STUB - replace run_specialized_model()"}
        for p in patches
    ]


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Sample plant patches from aerial video and run inference.")
    parser.add_argument("--video", required=True, help="Path to input video")
    parser.add_argument("--weights", required=True, help="Path to YOLO weights for plant detection")
    parser.add_argument("--patch-size", type=int, nargs=2, default=[224, 224], metavar=("W", "H"))
    parser.add_argument("--sample-every", type=int, default=15, help="Process every Nth frame")
    parser.add_argument("--conf", type=float, default=0.35, help="Detection confidence threshold")
    parser.add_argument("--device", default="cpu", help="cpu, cuda, or mps")
    parser.add_argument("--out-dir", default="./samples", help="Where to write patches + metadata")
    parser.add_argument("--save-patches", action="store_true", help="Write patch images to disk")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    detector = PlantDetector(args.weights, conf_threshold=args.conf, device=args.device)
    all_results = []

    for frame_index, timestamp_sec, frame in extract_frames(args.video, args.sample_every):
        detections = detector.detect(frame, frame_index, timestamp_sec)
        if not detections:
            continue

        patches = []
        for i, det in enumerate(detections):
            crop = crop_patch(frame, det, tuple(args.patch_size))
            patch_id = f"f{frame_index:06d}_d{i:03d}"
            patches.append(Patch(detection=det, image=crop, patch_id=patch_id))

            if args.save_patches:
                cv2.imwrite(str(out_dir / f"{patch_id}.png"), crop)

        predictions = run_specialized_model(patches)

        for p, pred in zip(patches, predictions):
            record = asdict(p.detection)
            record["patch_id"] = p.patch_id
            record["prediction"] = pred["prediction"]
            all_results.append(record)

        print(f"[frame {frame_index}] {len(detections)} plant(s) detected -> patches sampled")

    with open(out_dir / "results.json", "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nDone. {len(all_results)} patches processed. Metadata: {out_dir / 'results.json'}")


if __name__ == "__main__":
    main()
