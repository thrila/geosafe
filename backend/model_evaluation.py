"""Evaluate disease predictions against a labelled image CSV without extra packages."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from pipeline.config import Config
from pipeline.inference import Pipeline


def evaluate(dataset: Path) -> dict:
    """Return accuracy and macro metrics for a CSV with image,disease columns."""
    with dataset.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    if not rows or not {"image", "disease"}.issubset(rows[0]):
        raise ValueError("Dataset CSV must include image,disease headers and at least one row.")

    pipeline = Pipeline(Config())
    pairs: list[tuple[str, str]] = []
    for row in rows:
        image = (dataset.parent / row["image"]).resolve()
        if not image.is_file():
            raise FileNotFoundError(f"Dataset image does not exist: {image}")
        prediction = pipeline.process_image(image)["prediction"]["disease"]
        pairs.append((row["disease"].strip(), prediction.strip()))

    labels = sorted({label for pair in pairs for label in pair})
    per_class = {}
    for label in labels:
        true_positive = sum(expected == actual == label for expected, actual in pairs)
        false_positive = sum(expected != label and actual == label for expected, actual in pairs)
        false_negative = sum(expected == label and actual != label for expected, actual in pairs)
        precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
        recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[label] = {
            "support": sum(expected == label for expected, _ in pairs),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        }

    correct = sum(expected == actual for expected, actual in pairs)
    return {
        "samples": len(pairs),
        "accuracy": round(correct / len(pairs), 4),
        "macroPrecision": round(sum(item["precision"] for item in per_class.values()) / len(labels), 4),
        "macroRecall": round(sum(item["recall"] for item in per_class.values()) / len(labels), 4),
        "macroF1": round(sum(item["f1"] for item in per_class.values()) / len(labels), 4),
        "classMetrics": per_class,
        "predictions": Counter(actual for _, actual in pairs),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path, help="CSV with image,disease columns")
    parser.add_argument("--output", type=Path, default=Path("model-evaluation.json"))
    args = parser.parse_args()
    result = evaluate(args.dataset)
    args.output.write_text(json.dumps(result, indent=2, default=dict), encoding="utf-8")
    print(json.dumps(result, indent=2, default=dict))


if __name__ == "__main__":
    main()
