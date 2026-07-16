from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Optional
import json

import cv2
import numpy as np

from .preprocessing import preprocess_disease, preprocess_batch

logger = logging.getLogger(__name__)


class PlantModelONNX:
    def __init__(self, onnx_path: str | Path, intra_op_threads: int = 2):
        import onnxruntime as ort
        from ultralytics import YOLO

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = intra_op_threads
        opts.inter_op_num_threads = intra_op_threads
        self.session = ort.InferenceSession(
            str(onnx_path), opts, providers=["CPUExecutionProvider"]
        )
        self.iname = self.session.get_inputs()[0].name
        _, _, ih, iw = self.session.get_inputs()[0].shape
        self.input_size = (ih, iw)
        logger.info("Plant model input size: %s", self.input_size)
        pt_path = Path(str(onnx_path).replace(".onnx", ".pt"))
        if pt_path.exists():
            self.class_names = YOLO(str(pt_path)).names
        else:
            self.class_names = {0: "cassava", 1: "plantain"}
        logger.info("Plant model class names: %s", self.class_names)

    def predict(self, frame: np.ndarray) -> list[dict]:
        h, w = frame.shape[:2]
        ih, iw = self.input_size
        logger.debug("Plant preprocess: frame=%dx%d target=%dx%d", w, h, iw, ih)
        scale = min(iw / w, ih / h)
        nw, nh = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((ih, iw, 3), 114, dtype=np.uint8)
        dx, dy = (iw - nw) // 2, (ih - nh) // 2
        canvas[dy : dy + nh, dx : dx + nw] = resized
        inp = canvas.astype(np.float32) / 255.0
        inp = inp.transpose(2, 0, 1)[None, :]
        logger.debug("Plant model input shape=%s", inp.shape)
        out = self.session.run(None, {self.iname: inp})[0]
        logger.debug("Plant model raw output shape=%s", out.shape)
        probs = np.exp(out - out.max(axis=-1, keepdims=True))
        probs = probs / probs.sum(axis=-1, keepdims=True)
        idx = int(probs[0].argmax())
        logger.info(
            "Plant prediction: class=%s confidence=%.3f",
            self.class_names.get(idx, f"class_{idx}"),
            probs[0][idx],
        )
        return [
            {
                "predicted_index": idx,
                "predicted_class": self.class_names.get(idx, f"class_{idx}"),
                "confidence": float(probs[0][idx]),
                "all_probabilities": {
                    self.class_names.get(i, f"class_{i}"): float(probs[0][i])
                    for i in range(probs.shape[1])
                },
            }
        ]

    def _preprocess_letterbox(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        ih, iw = self.input_size
        scale = min(iw / w, ih / h)
        nw, nh = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        canvas = np.full((ih, iw, 3), 114, dtype=np.uint8)
        dx, dy = (iw - nw) // 2, (ih - nh) // 2
        canvas[dy : dy + nh, dx : dx + nw] = resized
        inp = canvas.astype(np.float32) / 255.0
        return inp.transpose(2, 0, 1)

    def predict_batch(self, frames: list[np.ndarray]) -> list[dict]:
        if not frames:
            raise ValueError("Cannot predict on empty batch")
        batch = np.stack([self._preprocess_letterbox(f) for f in frames], axis=0)
        out = self.session.run(None, {self.iname: batch})[0]
        probs = np.exp(out - out.max(axis=-1, keepdims=True))
        probs = probs / probs.sum(axis=-1, keepdims=True)
        results = []
        for i in range(probs.shape[0]):
            idx = int(probs[i].argmax())
            results.append({
                "predicted_index": idx,
                "predicted_class": self.class_names.get(idx, f"class_{idx}"),
                "confidence": float(probs[i][idx]),
                "all_probabilities": {
                    self.class_names.get(j, f"class_{j}"): float(probs[i][j])
                    for j in range(probs.shape[1])
                },
            })
        return results


class DiseaseModelONNX:
    def __init__(self, onnx_path: str | Path, meta_path: Optional[str | Path] = None, intra_op_threads: int = 2):
        import onnxruntime as ort

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = intra_op_threads
        opts.inter_op_num_threads = intra_op_threads
        self.session = ort.InferenceSession(
            str(onnx_path), opts, providers=["CPUExecutionProvider"]
        )
        if meta_path:
            with open(meta_path) as f:
                m = json.load(f)
            self.class_names = {int(k): v for k, v in m["class_names"].items()}
            self.img_size = m["img_size"]
        else:
            import torch

            ckpt = torch.load(
                Path(str(onnx_path).replace(".onnx", ".pt").replace(".int8", "")),
                map_location="cpu",
            )
            self.class_names = {int(k): v for k, v in ckpt["class_names"].items()}
            self.img_size = ckpt["img_size"]
        self.num_classes = len(self.class_names)
        self.iname = self.session.get_inputs()[0].name
        logger.info(
            "Disease model: img_size=%d classes=%s", self.img_size, self.class_names
        )

    def predict(self, img: np.ndarray) -> Dict:
        logger.debug(
            "Disease predict: input shape=%s model size=%d",
            img.shape[:2],
            self.img_size,
        )
        arr = preprocess_disease(img, self.img_size)
        logits = self.session.run(None, {self.iname: arr})[0]
        result = self._fmt(logits)
        logger.info(
            "Disease prediction: class=%s confidence=%.3f",
            result["predicted_class"],
            result["confidence"],
        )
        return result

    def predict_batch(self, images: list[np.ndarray]) -> list[Dict]:
        logger.debug(
            "Disease predict_batch: %d images, model size=%d",
            len(images),
            self.img_size,
        )
        batch = preprocess_batch(images, self.img_size)
        logits = self.session.run(None, {self.iname: batch})[0]
        results = [self._fmt(logits[i : i + 1]) for i in range(logits.shape[0])]
        logger.info("Disease predict_batch: %d results", len(results))
        return results

    def _fmt(self, logits: np.ndarray) -> Dict:
        e = np.exp(logits - logits.max(axis=-1, keepdims=True))
        probs = (e / e.sum(axis=-1, keepdims=True))[0]
        idx = int(probs.argmax())
        return {
            "predicted_class": self.class_names[idx],
            "predicted_index": idx,
            "confidence": float(probs[idx]),
            "all_probabilities": {
                self.class_names[i]: float(probs[i]) for i in range(self.num_classes)
            },
        }
