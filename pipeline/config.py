from __future__ import annotations

from pathlib import Path


class Config:
    fps: float = 5.0
    blur_threshold: float = 100.0
    min_brightness: float = 30.0
    max_brightness: float = 230.0
    output_dir: Path = Path("output")
    tile_size: tuple[int, int] = (640, 640)
    tile_overlap: float = 0.1

    @property
    def plant_onnx_path(self) -> Path:
        for base in [Path("Notebooks"), Path("models/new_models"), Path("models")]:
            for pattern in ["cassava_plantain_run/*/weights/best.onnx", "best.onnx"]:
                matches = list(base.glob(pattern))
                if matches:
                    return matches[0].resolve()
        return Path("models/new_models/best.onnx").resolve()

    DISEASE_MODEL_MAP = {"cassava": "cassava", "plantain": "banana"}

    def disease_onnx_path(self, plant: str) -> Path:
        stem = self.DISEASE_MODEL_MAP.get(plant, plant)
        return (Path("models/new_models") / f"{stem}_classifier.onnx").resolve()

    def disease_meta_path(self, plant: str) -> Path:
        stem = self.DISEASE_MODEL_MAP.get(plant, plant)
        return (Path("models/new_models") / f"{stem}_meta.json").resolve()
