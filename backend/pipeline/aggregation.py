"""Combine per-tile predictions into one result.

Kept free of models and I/O so the rules can be tested directly. Image and video
analysis share them, so the same tiles always produce the same conclusion.
"""

from __future__ import annotations

from collections import Counter
from statistics import mean

from .saver import INCONCLUSIVE, is_actionable_disease

NOT_DETECTED = "not detected"


def summarize_condition(tiles: list[tuple[str, float]]) -> tuple[str, float]:
    """Reduce (condition, score) pairs for one crop to a single condition.

    Any finding outranks an uncertain tile, and an uncertain tile outranks a
    healthy one: a field is only healthy if every assessed tile says so.
    """
    findings = [tile for tile in tiles if is_actionable_disease(tile[0])]
    if findings:
        condition = Counter(name for name, _ in findings).most_common(1)[0][0]
    elif any(name == INCONCLUSIVE for name, _ in tiles):
        condition = INCONCLUSIVE
    elif any(name.lower() == "healthy" for name, _ in tiles):
        condition = "Healthy"
    else:
        return NOT_DETECTED, 0.0
    return condition, mean(score for name, score in tiles if name == condition)


def summarize_tiles(tiles: list[tuple[str, float, str, float]]) -> dict | None:
    """Summarize (plant, plant score, condition, condition score) tuples.

    Unrecognized tiles such as soil or sky are ignored, so they cannot outvote
    the tiles that show a crop. Returns None when no tile shows a crop.
    """
    recognized = [tile for tile in tiles if tile[0] != NOT_DETECTED]
    if not recognized:
        return None
    plant = Counter(tile[0] for tile in recognized).most_common(1)[0][0]
    plant_tiles = [tile for tile in recognized if tile[0] == plant]
    condition, confidence = summarize_condition([(tile[2], tile[3]) for tile in plant_tiles])
    return {
        "plant_type": plant,
        "plant_confidence": mean(tile[1] for tile in plant_tiles),
        "disease": condition,
        "disease_confidence": confidence,
    }
