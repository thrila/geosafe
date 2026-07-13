import os
from pathlib import Path
from typing import Any

import albumentations as A
import numpy as np
import torch
import torch.nn as nn
from albumentations.pytorch import ToTensorV2
from PIL import Image
from torchvision import models

from core.config import settings


os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")
IMAGE_SIZE = 224


class MaizeClassifier(nn.Module):
    def __init__(self, num_classes: int, dropout: float = 0.3) -> None:
        super().__init__()
        self.backbone = models.efficientnet_v2_s(weights=None)
        in_features = self.backbone.classifier[1].in_features
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(p=dropout, inplace=True),
            nn.Linear(in_features, 512),
            nn.SiLU(),
            nn.Dropout(p=dropout / 2),
            nn.Linear(512, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


def _resolve_model_path(model_path: str | Path = settings.DEFAULT_MODEL) -> Path:
    resolved = Path(model_path)
    if resolved.exists():
        return resolved
    if resolved == settings.DEFAULT_MODEL and settings.LEGACY_MODEL.exists():
        return settings.LEGACY_MODEL
    raise FileNotFoundError(f"Model not found: {resolved}")


def load_model(
    model_path: str | Path = settings.DEFAULT_MODEL,
) -> tuple[nn.Module, list[str]]:
    resolved_path = _resolve_model_path(model_path)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(resolved_path, map_location=device, weights_only=True)
    class_names: list[str] = checkpoint["class_names"]

    model = MaizeClassifier(num_classes=len(class_names))
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    print(f"Model loaded from {resolved_path}  |  device: {device}")
    return model.to(device), class_names


def predict(
    image_path: str | Path,
    model: nn.Module,
    class_names: list[str],
) -> dict[str, Any]:
    image_path = Path(image_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    device = next(model.parameters()).device
    transform = A.Compose(
        [
            A.Resize(height=IMAGE_SIZE, width=IMAGE_SIZE),
            A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
            ToTensorV2(),
        ]
    )

    with Image.open(image_path) as img:
        image = np.array(img.convert("RGB"))

    tensor = transform(image=image)["image"].unsqueeze(0).to(device)

    with torch.no_grad():
        probs = torch.softmax(model(tensor), dim=1)[0]

    top_idx = probs.argmax().item()
    return {
        "prediction": class_names[top_idx].replace("Corn_", ""),
        "confidence": f"{probs[top_idx].item() * 100:.1f}%",
        "all_scores": {
            cls.replace("Corn_", ""): f"{p.item() * 100:.1f}%"
            for cls, p in zip(class_names, probs)
        },
    }


def _print_result(image_path: str | Path, result: dict) -> None:
    print(f"\nImage      : {image_path}")
    print(f"Prediction : {result['prediction']}")
    print(f"Confidence : {result['confidence']}")
    print("All scores :")
    for cls, score in result["all_scores"].items():
        print(f"  {cls:<25} {score}")


if __name__ == "__main__":
    model_path = input("Model path (press Enter for 'model.pt'): ").strip()
    model, class_names = load_model(model_path or settings.DEFAULT_MODEL)

    while True:
        image_path = input("\nImage path (or 'q' to quit): ").strip()
        if image_path.lower() == "q":
            break
        try:
            result = predict(image_path, model, class_names)
            _print_result(image_path, result)
        except FileNotFoundError as exc:
            print(f"Error: {exc}")
