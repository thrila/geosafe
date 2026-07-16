from __future__ import annotations

from pathlib import Path


class Config:
    def __init__(
        self,
        fps: float = 5.0,
        blur_threshold: float = 100.0,
        min_brightness: float = 30.0,
        max_brightness: float = 230.0,
        output_dir: Path = Path("output"),
        tile_size: tuple[int, int] = (640, 640),
        tile_overlap: float = 0.1,
        max_workers: int = 4,
        batch_size: int = 8,
        intra_op_threads: int = 2,
    ):
        self.fps = fps
        self.blur_threshold = blur_threshold
        self.min_brightness = min_brightness
        self.max_brightness = max_brightness
        self.output_dir = output_dir
        self.tile_size = tile_size
        self.tile_overlap = tile_overlap
        self.max_workers = max_workers
        self.batch_size = batch_size
        self.intra_op_threads = intra_op_threads

    @property
    def plant_onnx_path(self) -> Path:
        return (Path("models/new_models") / "best.onnx").resolve()

    DISEASE_MODEL_MAP = {"cassava": "cassava", "plantain": "banana"}

    def disease_onnx_path(self, plant: str) -> Path:
        stem = self.DISEASE_MODEL_MAP.get(plant, plant)
        return (Path("models/new_models") / f"{stem}_classifier.onnx").resolve()

    def disease_meta_path(self, plant: str) -> Path:
        stem = self.DISEASE_MODEL_MAP.get(plant, plant)
        return (Path("models/new_models") / f"{stem}_meta.json").resolve()
