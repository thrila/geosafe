from dataclasses import dataclass


@dataclass(frozen=True)
class TrackPoint:
    ts: int              # unix milliseconds
    frame_index: int
    latitude: float
    longitude: float
    height: float        # metres above takeoff
    altitude: float      # metres MSL
    gps_num: int         # satellites locked
    gps_level: int       # signal quality (0–5)


@dataclass(frozen=True)
class BatteryDrain:
    start_level_pct: float
    end_level_pct: float
    drained_pct: float   # start - end
