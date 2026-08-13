from __future__ import annotations

import subprocess

import pytest

from services.log_importer import DJIFlightLogImporter, LogImportError


def test_importer_returns_the_parser_flight_id(tmp_path, monkeypatch):
    parser = tmp_path / "app.ts"
    parser.write_text("// parser placeholder")
    log = tmp_path / "flight.txt"
    log.write_text("log")

    from core.config import settings

    monkeypatch.setattr(settings, "DJI_PARSER_APP", parser)
    seen = {}

    def fake_run(command, **kwargs):
        seen["command"] = command
        seen["env"] = kwargs["env"]
        return subprocess.CompletedProcess(command, 0, 'parser output\n{"flightId": 27}\n', "")

    monkeypatch.setattr("services.log_importer.subprocess.run", fake_run)

    assert DJIFlightLogImporter().import_log("Survey", log) == 27
    assert seen["command"][-3:] == ["--json", "Survey", str(log)]
    assert seen["env"]["DB_PATH"]


def test_importer_rejects_success_without_a_flight_id(tmp_path, monkeypatch):
    parser = tmp_path / "app.ts"
    parser.write_text("// parser placeholder")
    log = tmp_path / "flight.txt"
    log.write_text("log")

    from core.config import settings

    monkeypatch.setattr(settings, "DJI_PARSER_APP", parser)
    monkeypatch.setattr(
        "services.log_importer.subprocess.run",
        lambda command, **kwargs: subprocess.CompletedProcess(command, 0, "done\n", ""),
    )

    with pytest.raises(LogImportError, match="without creating"):
        DJIFlightLogImporter().import_log("Survey", log)
