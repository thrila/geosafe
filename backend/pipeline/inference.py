from __future__ import annotations

import logging
import queue
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from statistics import mean

import cv2
import numpy as np

from .benchmark import now, Bench
from .config import Config
from .metadata import FrameResult
from .quality import QualityCheck
from .sampler import frame_iterator
from .saver import persist
from .tiler import Tiler

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.5
PLANT_CONFIDENCE_THRESHOLD = 0.7
RECOGNIZED_PLANTS = {"cassava", "plantain"}


def _apply_disease_threshold(dr: dict, threshold: float = CONFIDENCE_THRESHOLD) -> dict:
    if dr.get("predicted_class", "").lower() == "healthy":
        return dr
    if dr.get("confidence", 0) < threshold:
        return {
            "predicted_class": "Healthy",
            "predicted_index": -1,
            "confidence": 1.0 - dr.get("confidence", 0),
            "all_probabilities": dr.get("all_probabilities", {}),
        }
    return dr


class Pipeline:
    def __init__(self, config: Config):
        self.config = config
        self.quality = QualityCheck(config.blur_threshold, config.min_brightness, config.max_brightness)
        self._plant = None
        self._disease_models: dict[str, object] = {}
        self._tiler = Tiler(config.tile_size, config.tile_overlap)
        self._model_lock = threading.Lock()

    def _load_plant_model(self):
        if self._plant is not None:
            return
        with self._model_lock:
            if self._plant is not None:
                return
            from .onnx_backend import PlantModelONNX
            onnx_path = self.config.plant_onnx_path
            logger.info("Loading plant model from %s exists=%s", onnx_path, onnx_path.exists())
            if not onnx_path.exists():
                logger.warning("Plant model not found at %s — using fallback", onnx_path)
                self._plant = None
                return
            self._plant = PlantModelONNX(onnx_path, intra_op_threads=self.config.intra_op_threads)
            logger.info("Plant model loaded")

    def _load_disease_model(self, plant_class: str) -> object:
        if plant_class not in RECOGNIZED_PLANTS:
            return None
        if plant_class in self._disease_models:
            return self._disease_models[plant_class]
        with self._model_lock:
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
            dm = DiseaseModelONNX(
                str(onnx_path),
                meta_path=str(meta_path) if meta_path.exists() else None,
                intra_op_threads=self.config.intra_op_threads,
            )
            self._disease_models[plant_class] = dm
            logger.info("Disease model for '%s' loaded", plant_class)
            return dm

    def plant_model(self):
        self._load_plant_model()
        return self._plant

    def _infer(self, frame):
        self._load_plant_model()

        if self._plant is None:
            plant = {"predicted_class": "not detected", "confidence": 0.0}
            disease = {
                "predicted_class": "not detected",
                "predicted_index": -1,
                "confidence": 0.0,
                "all_probabilities": {"not detected": 1.0},
            }
            return plant, disease

        try:
            plants = self._plant.predict(frame)
            plant = plants[0] if plants else {"predicted_class": "not detected", "confidence": 0}
        except Exception as e:
            logger.warning("Plant inference failed: %s", e)
            plant = {"predicted_class": "not detected", "confidence": 0}

        plant_class = plant.get("predicted_class", "").lower()
        plant_conf = plant.get("confidence", 0)

        if plant_class not in RECOGNIZED_PLANTS or plant_conf < PLANT_CONFIDENCE_THRESHOLD:
            plant = {"predicted_class": "not detected", "confidence": plant_conf}
            disease = {
                "predicted_class": "not detected",
                "predicted_index": -1,
                "confidence": 0.0,
                "all_probabilities": {"not detected": 1.0},
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

    def _infer_batch(self, frames: list[np.ndarray]) -> list[tuple[dict, dict]]:
        self._load_plant_model()

        not_detected_plant = {"predicted_class": "not detected", "confidence": 0.0}
        not_detected_disease = {
            "predicted_class": "not detected",
            "predicted_index": -1,
            "confidence": 0.0,
            "all_probabilities": {"not detected": 1.0},
        }

        if self._plant is None:
            return [(not_detected_plant, not_detected_disease)] * len(frames)

        results = []

        plant_results = []
        for f in frames:
            try:
                plants = self._plant.predict(f)
                plant_results.append(plants[0] if plants else {"predicted_class": "not detected", "confidence": 0})
            except Exception as e:
                logger.warning("Plant inference failed: %s", e)
                plant_results.append({"predicted_class": "not detected", "confidence": 0})

        by_class: dict[str, list[tuple[int, np.ndarray]]] = {}
        for i, (plant, frame) in enumerate(zip(plant_results, frames)):
            plant_class = plant.get("predicted_class", "").lower()
            plant_conf = plant.get("confidence", 0)
            if plant_class in RECOGNIZED_PLANTS and plant_conf >= PLANT_CONFIDENCE_THRESHOLD:
                by_class.setdefault(plant_class, []).append((i, frame))

        disease_results: dict[int, dict] = {}
        for plant_class, items in by_class.items():
            dm = self._load_disease_model(plant_class)
            if dm is None:
                for idx, _ in items:
                    disease_results[idx] = {
                        "predicted_class": "Healthy",
                        "confidence": 1.0,
                        "all_probabilities": {"Healthy": 1.0},
                    }
            elif len(items) > 1:
                batch_frames = [f for _, f in items]
                try:
                    batch_disease = dm.predict_batch(batch_frames)
                    for (idx, _), dr in zip(items, batch_disease):
                        disease_results[idx] = _apply_disease_threshold(dr)
                except Exception as e:
                    logger.warning("Batch disease inference failed, falling back: %s", e)
                    for idx, f in items:
                        disease_results[idx] = _apply_disease_threshold(dm.predict(f))
            else:
                idx, f = items[0]
                disease_results[idx] = _apply_disease_threshold(dm.predict(f))

        for i, plant in enumerate(plant_results):
            plant_class = plant.get("predicted_class", "").lower()
            plant_conf = plant.get("confidence", 0)
            if plant_class not in RECOGNIZED_PLANTS or plant_conf < PLANT_CONFIDENCE_THRESHOLD:
                results.append(({"predicted_class": "not detected", "confidence": plant_conf}, not_detected_disease))
            else:
                results.append((plant, disease_results[i]))

        return results

    def _process_frame_batch(self, batch: list[tuple[int, float, list[tuple]]], out_dir: Path, bench: Bench) -> list[FrameResult]:
        all_tiles = []
        tile_meta = []
        for fi, ts, tiles in batch:
            for tile_img, tc in tiles:
                all_tiles.append(tile_img)
                tile_meta.append((fi, ts, tc.tile_idx))

        if not all_tiles:
            return []

        t0 = now()
        infer_results = self._infer_batch(all_tiles)
        inf_elapsed = now() - t0

        t1 = now()
        results = []
        for i, ((fi, ts, tile_idx), (pr, dr)) in enumerate(zip(tile_meta, infer_results)):
            fp = persist(all_tiles[i], pr, dr, out_dir, tile_idx, fi, ts, "onnx")
            results.append(fp)
        post_elapsed = now() - t1

        bench.append(inf=inf_elapsed, post=post_elapsed, total=inf_elapsed + post_elapsed)
        return results

    def process_video(self, video_path, out_dir=None):
        out = out_dir or self.config.output_dir
        bench = Bench()
        frames = []
        rejected_count = [0]

        frame_queue: queue.Queue = queue.Queue(maxsize=self.config.max_workers * 2)
        results_lock = threading.Lock()
        batch_lock = threading.Lock()
        shared_batch: list = []
        total_frames = [0]
        total_frames_lock = threading.Lock()
        processed_count = [0]
        progress_lock = threading.Lock()

        def producer():
            try:
                for fi, ts, frame in frame_iterator(video_path, self.config.fps):
                    with total_frames_lock:
                        total_frames[0] += 1
                    frame_queue.put((fi, ts, frame))
            except Exception as e:
                logger.error("Producer error: %s", e)
            finally:
                for _ in range(self.config.max_workers):
                    frame_queue.put(None)
            logger.info("Producer finished: %d frames extracted", total_frames[0])

        def worker():
            local_results = []
            local_rejected = 0

            while True:
                item = frame_queue.get()
                if item is None:
                    break

                try:
                    fi, ts, frame = item
                    r = self.quality.check(frame, fi, ts)
                    if r:
                        local_rejected += 1
                        local_results.append(FrameResult(
                            image="", timestamp=round(ts, 3), frame=fi, tile=0,
                            plant_class="", plant_conf=0, disease="", disease_conf=0,
                            backend="onnx", rejected=True, reject_reason=r,
                        ))
                    else:
                        tiles = self._tiler.split(frame)
                        to_process = None
                        with batch_lock:
                            shared_batch.append((fi, ts, tiles))
                            if len(shared_batch) >= self.config.batch_size:
                                to_process = shared_batch[:]
                                shared_batch.clear()
                        if to_process:
                            try:
                                processed = self._process_frame_batch(to_process, out, bench)
                                local_results.extend(processed)
                            except Exception as e:
                                logger.error("Worker batch processing failed, returning batch for retry: %s", e)
                                with batch_lock:
                                    shared_batch[0:0] = to_process
                except Exception as e:
                    logger.error("Worker error processing frame: %s", e)

                with progress_lock:
                    processed_count[0] += 1
                    count = processed_count[0]
                with total_frames_lock:
                    tf = total_frames[0]
                if count % 10 == 0 or count == tf:
                    logger.info("Progress: %d/%d frames processed (%.0f%%)", count, tf, (count / max(tf, 1)) * 100)

            to_process = None
            with batch_lock:
                if shared_batch:
                    to_process = shared_batch[:]
                    shared_batch.clear()
            if to_process:
                try:
                    processed = self._process_frame_batch(to_process, out, bench)
                    local_results.extend(processed)
                except Exception as e:
                    logger.error("Worker error processing final batch: %s", e)

            with results_lock:
                frames.extend(local_results)
                rejected_count[0] += local_rejected

        logger.info("Starting video processing: %s", video_path)
        producer_thread = threading.Thread(target=producer, daemon=True)
        producer_thread.start()

        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = [executor.submit(worker) for _ in range(self.config.max_workers)]
            for f in as_completed(futures):
                try:
                    f.result()
                except Exception as e:
                    logger.error("Worker error: %s", e)

        producer_thread.join(timeout=10)
        if producer_thread.is_alive():
            logger.warning("Producer thread did not finish in time, some frames may be unprocessed")

        valid = [f for f in frames if not f.rejected]
        logger.info("Video processing complete: %d valid, %d rejected, %d total", len(valid), rejected_count[0], len(frames))
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
            "frames_rejected": rejected_count[0],
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

        tiles = self._tiler.split(frame)
        tile_imgs = [img for img, _ in tiles]

        t0 = now()
        if len(tile_imgs) == 1:
            pr, dr = self._infer(tile_imgs[0])
            infer_results = [(pr, dr)]
        else:
            infer_results = self._infer_batch(tile_imgs)
        elapsed = now() - t0

        tile_results = []
        all_plant_classes = []
        all_disease_classes = []
        for (img, tc), (pr, dr) in zip(tiles, infer_results):
            plant_class = pr.get("predicted_class", "")
            disease = dr.get("predicted_class", "")
            all_plant_classes.append(plant_class)
            all_disease_classes.append(disease)
            tile_results.append({
                "tile": tc.tile_idx,
                "prediction": {
                    "plant_type": plant_class,
                    "plant_confidence": pr.get("confidence", 0),
                    "disease": disease,
                    "disease_confidence": dr.get("confidence", 0),
                    "all_probabilities": dr.get("all_probabilities", {}),
                },
            })

        from collections import Counter
        agg_plant = Counter(all_plant_classes).most_common(1)[0][0] if all_plant_classes else "not detected"
        valid_tiles = [t for t in tile_results if t["prediction"]["plant_type"] != "not detected"]
        if valid_tiles:
            agg_plant_conf = mean(t["prediction"]["plant_confidence"] for t in valid_tiles)
        else:
            agg_plant_conf = 0.0

        diseased_tiles = [t for t in valid_tiles if t["prediction"]["disease"].lower() != "healthy"]
        if diseased_tiles:
            worst = max(diseased_tiles, key=lambda t: t["prediction"]["disease_confidence"])
            agg_disease = worst["prediction"]["disease"]
            agg_disease_conf = worst["prediction"]["disease_confidence"]
        elif valid_tiles:
            agg_disease = "Healthy"
            agg_disease_conf = mean(t["prediction"]["disease_confidence"] for t in valid_tiles)
        else:
            agg_disease = "not detected"
            agg_disease_conf = 0.0

        return {
            "prediction": {
                "plant_type": agg_plant,
                "plant_confidence": round(agg_plant_conf, 4),
                "disease": agg_disease,
                "disease_confidence": round(agg_disease_conf, 4),
            },
            "tiles": tile_results,
            "backend": "onnx",
            "benchmark_ms": {"total": round(elapsed * 1000, 1)},
        }
