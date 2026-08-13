from __future__ import annotations

from services.telemetry import TelemetryRepository


def test_analysis_is_replaced_per_flight(tmp_path):
    repo = TelemetryRepository(str(tmp_path / "telemetry.db"))

    repo.save_analysis(7, "first", {"diseaseTally": {"CMD": 1}})
    repo.save_analysis(7, "second", {"diseaseTally": {"CMD": 2}, "slides": []})

    assert repo.get_analysis(7) == {"diseaseTally": {"CMD": 2}, "slides": []}
