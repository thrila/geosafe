import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from core.config import settings

logger = logging.getLogger(__name__)

flights_router = APIRouter()


@flights_router.get("/flights")
async def list_flights() -> list[dict[str, Any]]:
    try:
        import sqlite3
        conn = sqlite3.connect(settings.DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, name, start_ts, end_ts, total_frames FROM flights ORDER BY id")
        flights = []
        for row in cur.fetchall():
            duration_s = (row["end_ts"] - row["start_ts"]) / 1000 if row["end_ts"] and row["start_ts"] else 0
            mins = int(duration_s // 60)
            secs = int(duration_s % 60)
            duration_str = f"{mins}:{secs:02d} min" if mins > 0 else f"{secs}s"

            cur.execute("SELECT AVG(latitude) as mean_lat, AVG(longitude) as mean_lon FROM telemetry WHERE flight_id = ?", (row["id"],))
            coords = cur.fetchone()
            mean_lat = round(coords["mean_lat"], 5) if coords and coords["mean_lat"] else 0
            mean_lon = round(coords["mean_lon"], 5) if coords and coords["mean_lon"] else 0

            flights.append({
                "id": row["id"],
                "name": row["name"],
                "date": str(row["start_ts"]),
                "duration": duration_str,
                "location": f"{mean_lat}, {mean_lon}",
                "latitude": mean_lat,
                "longitude": mean_lon,
                "totalFrames": row["total_frames"],
            })
        conn.close()
        return flights
    except Exception:
        logger.exception("Failed to list flights")
        return []


@flights_router.get("/flights/{flight_id}")
async def get_flight(flight_id: int) -> dict[str, Any]:
    import math
    try:
        import sqlite3
        conn = sqlite3.connect(settings.DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, name, start_ts, end_ts, total_frames FROM flights WHERE id = ?", (flight_id,))
        frow = cur.fetchone()
        if not frow:
            raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found.")

        cur.execute(
            "SELECT latitude, longitude, height, x_speed, y_speed, z_speed, battery_level, battery_temp, gps_num FROM telemetry WHERE flight_id = ? ORDER BY frame_index",
            (flight_id,),
        )
        rows = cur.fetchall()
        conn.close()

        track = [{"latitude": r["latitude"], "longitude": r["longitude"], "height": r["height"] or 0} for r in rows]
        max_speed = round(max(math.sqrt(r["x_speed"]**2 + r["y_speed"]**2 + r["z_speed"]**2) for r in rows), 1) if rows else 0
        max_height = round(max(r["height"] or 0 for r in rows), 1) if rows else 0
        max_battery_temp = round(max(r["battery_temp"] or 0 for r in rows), 1) if rows else 0
        battery_start = rows[0]["battery_level"] if rows else 0
        battery_end = rows[-1]["battery_level"] if rows else 0
        battery_drained = round(battery_start - battery_end, 1)
        avg_gps = round(sum(r["gps_num"] or 0 for r in rows) / len(rows)) if rows else 0

        def _haversine_km(lat1, lon1, lat2, lon2):
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
            return 6371 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        route_km = round(sum(
            _haversine_km(track[i]["latitude"], track[i]["longitude"], track[i+1]["latitude"], track[i+1]["longitude"])
            for i in range(len(track) - 1)
        ), 2) if len(track) > 1 else 0

        mean_lat = round(sum(r["latitude"] for r in rows) / len(rows), 5) if rows else 0
        mean_lon = round(sum(r["longitude"] for r in rows) / len(rows), 5) if rows else 0

        duration_s = (frow["end_ts"] - frow["start_ts"]) / 1000 if frow["end_ts"] and frow["start_ts"] else 0
        mins = int(duration_s // 60)
        secs = int(duration_s % 60)
        duration_str = f"{mins}:{secs:02d} min" if mins > 0 else f"{secs}s"

        return {
            "flight": {
                "id": frow["id"],
                "name": frow["name"],
                "date": str(frow["start_ts"]),
                "duration": duration_str,
                "location": f"{mean_lat}, {mean_lon}",
                "latitude": mean_lat,
                "longitude": mean_lon,
                "totalFrames": frow["total_frames"],
            },
            "path": track,
            "telemetry": {
                "dateTime": str(frow["end_ts"]),
                "cards": [
                    {"label": "Route", "value": f"{route_km} km", "detail": "Total distance."},
                    {"label": "Max Speed", "value": f"{max_speed} m/s", "detail": "Ground speed."},
                    {"label": "Max Height", "value": f"{max_height} m", "detail": "Peak altitude."},
                    {"label": "Battery", "value": f"{battery_start:.0f} %", "detail": f"Drained {battery_drained:.0f}%."},
                    {"label": "Battery Temp", "value": f"{max_battery_temp} °C", "detail": "Peak temperature."},
                    {"label": "GPS", "value": f"{avg_gps} sats", "detail": "Average."},
                ],
            },
            "result": {
                "routeDistanceKm": route_km,
                "startPoint": track[0] if track else None,
                "endPoint": track[-1] if track else None,
                "batteryDrainedPct": battery_drained,
                "maxSpeedMs": max_speed,
                "maxHeightM": max_height,
                "batteryTempC": max_battery_temp,
            },
        }

    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to get flight %d", flight_id)
        raise HTTPException(status_code=500, detail="An internal error occurred.")
