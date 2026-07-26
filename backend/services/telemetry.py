import logging
import math
import sqlite3
from dataclasses import dataclass, field

from core.config import settings
from utils.geo import route_distance_km

logger = logging.getLogger(__name__)


@dataclass
class TelemetryData:
    """Aggregated telemetry metrics for a single flight."""

    flight_id: int | None = None
    track_pts: list[dict] = field(default_factory=list)
    max_speed: float = 0
    max_height: float = 0
    max_battery_temp: float = 0
    battery_start: float | None = None
    battery_end: float | None = None
    avg_gps: int = 0
    mean_lat: float = 0
    mean_lon: float = 0
    start_ts: int = 0
    end_ts: int = 0
    route_distance_km: float = 0

    @property
    def battery_drained(self) -> float:
        if self.battery_start is not None:
            return round(self.battery_start - (self.battery_end or 0), 1)
        return 0

    @property
    def start_point(self) -> dict | None:
        return self.track_pts[0] if self.track_pts else None

    @property
    def end_point(self) -> dict | None:
        return self.track_pts[-1] if self.track_pts else None


class TelemetryRepository:
    """All SQLite access for flights and telemetry lives here."""

    def __init__(self, db_path: str = settings.DB_PATH):
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_latest_flight_id(self) -> int | None:
        """Return the ID of the most recently inserted flight, or None."""
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute("SELECT id FROM flights ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            conn.close()
            return row["id"] if row else None
        except Exception as e:
            logger.warning("Telemetry DB not available: %s", e)
            return None

    def get_flight_info(self, flight_id: int) -> dict | None:
        """Return basic flight metadata, or None if not found."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, start_ts, end_ts, total_frames "
            "FROM flights WHERE id = ?",
            (flight_id,),
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row["id"],
            "name": row["name"],
            "start_ts": row["start_ts"],
            "end_ts": row["end_ts"],
            "total_frames": row["total_frames"],
        }

    def get_telemetry_rows(self, flight_id: int) -> list[dict]:
        """Return all telemetry rows for a flight, ordered by frame_index."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT latitude, longitude, height, x_speed, y_speed, z_speed, "
            "battery_level, battery_temp, gps_num "
            "FROM telemetry WHERE flight_id = ? ORDER BY frame_index",
            (flight_id,),
        )
        rows = [
            {
                "latitude": r["latitude"],
                "longitude": r["longitude"],
                "height": r["height"],
                "x_speed": r["x_speed"],
                "y_speed": r["y_speed"],
                "z_speed": r["z_speed"],
                "battery_level": r["battery_level"],
                "battery_temp": r["battery_temp"],
                "gps_num": r["gps_num"],
            }
            for r in cur.fetchall()
        ]
        conn.close()
        return rows

    def build_telemetry_data(self, flight_id: int) -> TelemetryData:
        """Fetch flight info + telemetry rows and compute derived metrics."""
        td = TelemetryData(flight_id=flight_id)

        try:
            info = self.get_flight_info(flight_id)
            if not info:
                return td

            td.start_ts = info["start_ts"]
            td.end_ts = info["end_ts"]

            rows = self.get_telemetry_rows(flight_id)
            if not rows:
                return td

            td.track_pts = [
                {
                    "latitude": r["latitude"],
                    "longitude": r["longitude"],
                    "height": r["height"] or 0,
                }
                for r in rows
            ]
            td.max_speed = round(
                max(
                    math.sqrt(r["x_speed"] ** 2 + r["y_speed"] ** 2 + r["z_speed"] ** 2)
                    for r in rows
                ),
                1,
            )
            td.max_height = round(max(r["height"] or 0 for r in rows), 1)
            td.max_battery_temp = round(max(r["battery_temp"] or 0 for r in rows), 1)
            td.battery_start = rows[0]["battery_level"]
            td.battery_end = rows[-1]["battery_level"]
            td.avg_gps = round(sum(r["gps_num"] or 0 for r in rows) / len(rows))
            td.mean_lat = round(sum(r["latitude"] for r in rows) / len(rows), 5)
            td.mean_lon = round(sum(r["longitude"] for r in rows) / len(rows), 5)
            td.route_distance_km = route_distance_km(td.track_pts)

        except Exception as e:
            logger.warning("Failed to build telemetry data: %s", e)

        return td

    def insert_slides(self, flight_id: int | None, slides: list[dict]) -> None:
        """Persist generated slides to the slides table."""
        if not flight_id or not slides:
            return
        try:
            conn = self._connect()
            for slide in slides:
                disease = (
                    slide.get("caption", "").split("—")[-1].strip()
                    if "—" in slide.get("caption", "")
                    else ""
                )
                conn.execute(
                    "INSERT INTO slides "
                    "(flight_id, frame_index, image_url, disease, caption) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (flight_id, 0, slide["src"], disease, slide.get("caption", "")),
                )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.warning("Failed to store slides: %s", e)

    def list_all_flights(self) -> list[dict]:
        """Return summary info for every flight."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, start_ts, end_ts, total_frames "
            "FROM flights ORDER BY id"
        )
        flights = []
        for row in cur.fetchall():
            duration_s = (
                (row["end_ts"] - row["start_ts"]) / 1000
                if row["end_ts"] and row["start_ts"]
                else 0
            )
            mins = int(duration_s // 60)
            secs = int(duration_s % 60)
            duration_str = f"{mins}:{secs:02d} min" if mins > 0 else f"{secs}s"

            cur.execute(
                "SELECT AVG(latitude) as mean_lat, AVG(longitude) as mean_lon "
                "FROM telemetry WHERE flight_id = ?",
                (row["id"],),
            )
            coords = cur.fetchone()
            mean_lat = round(coords["mean_lat"], 5) if coords and coords["mean_lat"] else 0
            mean_lon = round(coords["mean_lon"], 5) if coords and coords["mean_lon"] else 0

            flights.append({
                "id": row["id"],
                "name": row["name"],
                "date": str(row["start_ts"]),
                "duration": duration_str,
                "location": f"{mean_lat}, {mean_lon}",
                "totalFrames": row["total_frames"],
            })
        conn.close()
        return flights
