from __future__ import annotations

from dataclasses import dataclass
import logging

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TileCoord:
    x: int
    y: int
    w: int
    h: int
    tile_idx: int


class Tiler:
    def __init__(self, tile_size: tuple[int, int], overlap: float = 0.1):
        self.tile_w, self.tile_h = tile_size
        self.stride_w = max(1, int(self.tile_w * (1 - overlap)))
        self.stride_h = max(1, int(self.tile_h * (1 - overlap)))

    def split(self, frame: np.ndarray) -> list[tuple[np.ndarray, TileCoord]]:
        h, w = frame.shape[:2]
        if w <= self.tile_w and h <= self.tile_h:
            return [(frame, TileCoord(0, 0, w, h, 0))]
        xs = list(range(0, w - self.tile_w + 1, self.stride_w))
        if xs[-1] + self.tile_w < w:
            xs.append(w - self.tile_w)
        ys = list(range(0, h - self.tile_h + 1, self.stride_h))
        if ys[-1] + self.tile_h < h:
            ys.append(h - self.tile_h)
        tiles = []
        idx = 0
        for y in ys:
            for x in xs:
                tiles.append((frame[y:y + self.tile_h, x:x + self.tile_w].copy(), TileCoord(x, y, self.tile_w, self.tile_h, idx)))
                idx += 1
        logger.debug("Tiler: frame=%dx%d tile=%dx%d stride=%dx%d -> %d tiles", w, h, self.tile_w, self.tile_h, self.stride_w, self.stride_h, len(tiles))
        return tiles
