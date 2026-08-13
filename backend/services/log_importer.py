"""Import the DJI log supplied with an upload into the telemetry database."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)


class LogImportError(RuntimeError):
    """Raised when an upload's DJI log cannot be imported safely."""


class DJIFlightLogImporter:
    """Small adapter around the repository's Bun-based DJI parser.

    The parser is deliberately called with an explicit database path and its
    returned flight id is used throughout the upload. This removes the unsafe
    "latest flight" association that existed previously.
    """

    def import_log(self, name: str, log_path: Path) -> int:
        parser_path = settings.dji_parser_app_path
        if not parser_path.is_file():
            raise LogImportError(f"DJI parser was not found at {parser_path}.")

        env = os.environ.copy()
        env["DB_PATH"] = str(settings.db_path.resolve())
        if settings.DJI_API_KEY:
            env["DJI_API_KEY"] = settings.DJI_API_KEY
        command = [settings.BUN_BINARY, "run", str(parser_path), "--json", name, str(log_path)]

        try:
            completed = subprocess.run(
                command,
                cwd=str(settings.PROJECT_ROOT),
                env=env,
                capture_output=True,
                text=True,
                timeout=settings.LOG_IMPORT_TIMEOUT_SECONDS,
                check=False,
            )
        except FileNotFoundError as exc:
            raise LogImportError(
                "Bun is required to import DJI logs. Install Bun or configure BUN_BINARY."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise LogImportError("DJI log import timed out.") from exc

        if completed.returncode != 0:
            logger.warning("DJI log import failed: %s", completed.stderr.strip())
            raise LogImportError("DJI log import failed. Check the log format and DJI API configuration.")

        for line in reversed(completed.stdout.splitlines()):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            flight_id = payload.get("flightId")
            if isinstance(flight_id, int):
                return flight_id

        raise LogImportError("DJI log import completed without creating a flight record.")
