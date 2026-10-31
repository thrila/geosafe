from __future__ import annotations

import numpy as np
import pytest

from pipeline.tiler import Tiler


@pytest.mark.parametrize(
    ("width", "height"),
    [(1920, 1080), (3840, 2160), (641, 641), (700, 300), (300, 700), (640, 640), (320, 240)],
)
def test_tiles_cover_every_pixel(width, height):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    covered = np.zeros((height, width), dtype=bool)

    for _, tile in Tiler((640, 640), 0.1).split(frame):
        covered[tile.y:tile.y + tile.h, tile.x:tile.x + tile.w] = True

    assert covered.all()


def test_full_hd_frame_produces_eight_tiles():
    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)

    tiles = Tiler((640, 640), 0.1).split(frame)

    assert len(tiles) == 8
    assert [tile.tile_idx for _, tile in tiles] == list(range(8))


def test_tile_pixels_match_their_coordinates():
    frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

    for pixels, tile in Tiler((640, 640), 0.1).split(frame):
        assert pixels.shape == (640, 640, 3)
        assert np.array_equal(pixels, frame[tile.y:tile.y + 640, tile.x:tile.x + 640])
