from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path
from statistics import mean


import cv2

from .benchmark import now, Bench
from .config import Config
from .metadata import FrameResult
from .quality import QualityCheck
from .sampler import frame_iterator
from .saver import persist
from .tiler import Tiler

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.5


def _apply_disease_threshold(dr: dict, threshold: float = CONFIDENCE_THRESHOLD) -> dict:
    if dr.get("confidence", 0) < threshold:
        return {
            "predicted_class": "Healthy",
            "predicted_index": -1,
            "confidence": 1.0 - dr.get("confidence", 0),
            "all_probabilities": dr.get("all_probabilities", {}),
        }
    return dr


RECOGNIZED_PLANTS = {"cassava", "plantain"}


class Pipeline:
    def __init__(self, config: Config):
        self.config = config
        self.quality = QualityCheck(config.blur_threshold, config.min_brightness, config.max_brightness)
        self._plant = None
        self._disease_models: dict[str, object] = {}
        self._tiler = Tiler(config.tile_size, config.tile_overlap)

    def _load_plant_model(self):
        if self._plant is not None:
            return
        from .onnx_backend import PlantModelONNX
        onnx_path = self.config.plant_onnx_path
        logger.info("Loading plant model from %s exists=%s", onnx_path, onnx_path.exists())
        if not onnx_path.exists():
            logger.warning("Plant model not found at %s — using fallback", onnx_path)
            self._plant = None
            return
        self._plant = PlantModelONNX(onnx_path)
        logger.info("Plant model loaded")

    def _load_disease_model(self, plant_class: str) -> object:
        if plant_class not in RECOGNIZED_PLANTS:
            return None
        if plant_class in self._disease_models:
            return self._disease_models[plant_class]
        from .onnx_backend import DiseaseModelONNX
        onnx_path = self.config.disease_onnx_path(plant_class)
        meta_path = self.config.disease_meta_path(plant_class)
        logger.info("Loading disease model for '%s' from %s meta=%s", plant_class, onnx_path, meta_path)
        if not onnx_path.exists():
            logger.warning("Disease model not found for '%s' at %s", plant_class, onnx_path)
            self._disease_models[plant_class] = None
            return None
        dm = DiseaseModelONNX(str(onnx_path), meta_path=str(meta_path) if meta_path.exists() else None)
        self._disease_models[plant_class] = dm
        logger.info("Disease model for '%s' loaded", plant_class)
        return dm

    def plant_model(self):
        self._load_plant_model()
        return self._plant

    def _infer(self, frame):
        self._load_plant_model()

        if self._plant is not None:
            try:
                plants = self._plant.predict(frame)
                plant = plants[0] if plants else {"predicted_class": "unknown", "confidence": 0}
            except Exception as e:
                logger.warning("Plant inference failed: %s", e)
                plant = {"predicted_class": "unknown", "confidence": 0}
        else:
            plant = {"predicted_class": "cassava", "confidence": 1.0}

        plant_class = plant.get("predicted_class", "").lower()
        if plant_class not in RECOGNIZED_PLANTS:
            disease = {
                "predicted_class": "Unrecognized plant",
                "predicted_index": -1,
                "confidence": 1.0,
                "all_probabilities": {"Unrecognized plant": 1.0},
            }
            return plant, disease

        dm = self._load_disease_model(plant_class)
        if dm is None:
            disease = {
                "predicted_class": "Healthy",
                "confidence": 1.0,
                "all_probabilities": {"Healthy": 1.0},
            }
        else:
            disease = _apply_disease_threshold(dm.predict(frame))

        return plant, disease

    def process_video(self, video_path, out_dir=None):
        out = out_dir or self.config.output_dir
        bench = Bench()
        frames = []
        rejected = 0
        for fi, ts, frame in frame_iterator(video_path, self.config.fps):
            r = self.quality.check(frame, fi, ts)
            if r:
                rejected += 1
                frames.append(FrameResult(
                    image="", timestamp=round(ts, 3), frame=fi, tile=0,
                    plant_class="", plant_conf=0, disease="", disease_conf=0,
                    backend="onnx", rejected=True, reject_reason=r,
                ))
                continue
            for tile_img, tc in self._tiler.split(frame):
                t0 = now()
                pr, dr = self._infer(tile_img)
                bench.inf.append(now() - t0)
                bench.total.append(now() - t0)
                fp = persist(tile_img, pr, dr, out, tc.tile_idx, fi, ts, "onnx")
                frames.append(fp)
        valid = [f for f in frames if not f.rejected]
        if not valid:
            raise ValueError("No clear frames could be extracted from the uploaded video.")
        agg = {
            "plant_type": Counter(f.plant_class for f in valid).most_common(1)[0][0],
            "plant_confidence": round(mean(f.plant_conf for f in valid), 2),
            "disease": Counter(f.disease for f in valid).most_common(1)[0][0],
            "disease_confidence": round(mean(f.disease_conf for f in valid), 2),
        }
        avg_conf = mean(f.disease_conf for f in valid)
        return {
            "frames_analyzed": len(valid),
            "frames_rejected": rejected,
            "prediction": agg,
            "confidence": f"{avg_conf:.1%}",
            "per_frame_results": [{
                "frame": f.frame,
                "tile": f.tile,
                "timestamp": f.timestamp,
                "prediction": {
                    "plant_type": f.plant_class,
                    "plant_confidence": f.plant_conf,
                    "disease": f.disease,
                    "disease_confidence": f.disease_conf,
                    "all_probabilities": f.disease_probs or {},
                },
                "image_url": f.image_url if not f.rejected and f.disease.lower() != "healthy" else None,
            } for f in valid],
            "backend": "onnx",
            "benchmark": bench.to_dict(),
        }

    def process_image(self, image_path):
        frame = cv2.imread(str(image_path))
        if frame is None:
            raise ValueError(f"Could not read image: {image_path}")
        r = self.quality.check(frame, 0, 0)
        if r:
            raise ValueError(f"Image failed quality check: {r}")
        t0 = now()
        pr, dr = self._infer(frame)
        elapsed = now() - t0
        return {
            "prediction": {
                "plant_type": pr.get("predicted_class", ""),
                "plant_confidence": pr.get("confidence", 0),
                "disease": dr.get("predicted_class", ""),
                "disease_confidence": dr.get("confidence", 0),
                "all_probabilities": dr.get("all_probabilities", {}),
            },
            "backend": "onnx",
            "benchmark_ms": {"total": round(elapsed * 1000, 1)},
        }
