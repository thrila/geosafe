from __future__ import annotations

import pytest

from pipeline.aggregation import summarize_condition, summarize_tiles

CMD = "Cassava Mosaic Disease (CMD)"
CBB = "Cassava Bacterial Blight (CBB)"


class TestSummarizeCondition:
    def test_a_minority_finding_outranks_healthy_tiles(self):
        assert summarize_condition([("Healthy", 0.9)] * 9 + [(CMD, 0.8)]) == (CMD, 0.8)

    def test_most_common_finding_wins(self):
        condition, score = summarize_condition([(CBB, 0.9), (CMD, 0.6), (CMD, 0.8)])

        assert condition == CMD
        assert score == pytest.approx(0.7)

    def test_finding_outranks_inconclusive_tiles(self):
        assert summarize_condition([("Inconclusive", 0.3), (CMD, 0.8)])[0] == CMD

    def test_uncertain_tile_prevents_a_healthy_result(self):
        assert summarize_condition([("Healthy", 0.9), ("Inconclusive", 0.4)]) == ("Inconclusive", 0.4)

    def test_all_healthy_is_healthy(self):
        condition, score = summarize_condition([("Healthy", 0.8), ("Healthy", 0.6)])

        assert condition == "Healthy"
        assert score == pytest.approx(0.7)

    def test_nothing_assessed_is_not_detected(self):
        assert summarize_condition([("not detected", 0.0)]) == ("not detected", 0.0)


class TestSummarizeTiles:
    def test_unrecognized_tiles_cannot_outvote_a_crop(self):
        tiles = [("not detected", 0.5, "not detected", 0.0)] * 9
        tiles.append(("cassava", 0.9, CMD, 0.8))

        summary = summarize_tiles(tiles)

        assert summary == {
            "plant_type": "cassava",
            "plant_confidence": 0.9,
            "disease": CMD,
            "disease_confidence": 0.8,
        }

    def test_only_tiles_of_the_main_crop_decide_the_condition(self):
        tiles = [("cassava", 0.9, "Healthy", 0.8)] * 2 + [("plantain", 0.9, CMD, 0.8)]

        summary = summarize_tiles(tiles)

        assert summary["plant_type"] == "cassava"
        assert summary["disease"] == "Healthy"

    def test_no_recognized_tiles_returns_none(self):
        assert summarize_tiles([("not detected", 0.4, "not detected", 0.0)]) is None
