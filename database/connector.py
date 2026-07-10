"""
flight_telemetry.py

Class-based interface for reading DJI flight telemetry from SQLite.

Usage:
    with FlightDB("telemetry.db") as db:
        flight = db.flight(1)
        print(flight.track())
        print(flight.battery_drain())
"""

import sqlite3
from typing import Optional
from schemas.database_schema import TrackPoint, BatteryDrain
import json
from dataclasses import asdict, is_dataclass



# ---------------------------------------------------------------------------
# SQL
# ---------------------------------------------------------------------------

_TRACK_SQL = """
SELECT
    ts,
    frame_index,
    latitude,
    longitude,
    height,
    altitude,
    gps_num,
    gps_level
FROM telemetry
WHERE flight_id = ?
  AND latitude  IS NOT NULL
  AND longitude IS NOT NULL
ORDER BY frame_index ASC;
"""

_BATTERY_SQL = """
SELECT battery_level
FROM telemetry
WHERE flight_id = ?
  AND battery_level IS NOT NULL
ORDER BY frame_index ASC;
"""

_FLIGHT_SQL = """
SELECT id, name, start_ts, end_ts, total_frames
FROM flights
WHERE id = ?;
"""

_ALL_FLIGHTS_SQL = """
SELECT id, name, start_ts, end_ts, total_frames
FROM flights
ORDER BY id;
"""


# ---------------------------------------------------------------------------
# Flight
# ---------------------------------------------------------------------------

class Flight:
    def __init__(self, flight_id: int, name: str, start_ts: int, end_ts: int,
                 total_frames: int, conn: sqlite3.Connection) -> None:
        self.id = flight_id
        self.name = name
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.total_frames = total_frames
        self._conn = conn

    def track(self) -> list[TrackPoint]:
        """All lat/lon points for this flight ordered by frame index."""
        cur = self._conn.cursor()
        cur.execute(_TRACK_SQL, (self.id,))
        return [
            TrackPoint(
                ts=row[0],
                frame_index=row[1],
                latitude=row[2],
                longitude=row[3],
                height=row[4] or 0.0,
                altitude=row[5] or 0.0,
                gps_num=row[6] or 0,
                gps_level=row[7] or 0,
            )
            for row in cur.fetchall()
        ]

    def battery_drain(self) -> Optional[BatteryDrain]:
        """Battery % at the start and end of the flight, and how much was used."""
        cur = self._conn.cursor()
        cur.execute(_BATTERY_SQL, (self.id,))
        rows = cur.fetchall()
        if not rows:
            return None
        start = rows[0][0]
        end = rows[-1][0]
        return BatteryDrain(
            start_level_pct=start,
            end_level_pct=end,
            drained_pct=start - end,
        )

    def __repr__(self) -> str:
        return f"<Flight id={self.id} name={self.name!r}>"


# ---------------------------------------------------------------------------
# FlightDB
# ---------------------------------------------------------------------------

class FlightDB:
    def __init__(self, db_path: str, read_only: bool = True) -> None:
        uri = f"file:{db_path}?mode=ro" if read_only else db_path
        self._conn = sqlite3.connect(uri, uri=read_only, check_same_thread=False)

    def flight(self, flight_id: int) -> Flight:
        """Get a specific flight by id. Raises ValueError if not found."""
        cur = self._conn.cursor()
        cur.execute(_FLIGHT_SQL, (flight_id,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"No flight with id={flight_id}")
        return Flight(*row, conn=self._conn)

    def flights(self) -> list[Flight]:
        """Get all flights ordered by id."""
        cur = self._conn.cursor()
        cur.execute(_ALL_FLIGHTS_SQL)
        return [Flight(*row, conn=self._conn) for row in cur.fetchall()]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "FlightDB":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"<FlightDB>"



def to_json(obj):
    if isinstance(obj, list):
        return [to_json(x) for x in obj]

    if is_dataclass(obj):
        return asdict(obj)

    if hasattr(obj, "__dict__"):
        return {
            k: to_json(v)
            for k, v in obj.__dict__.items()
            if not k.startswith("_")
        }

    return obj
