import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points on Earth (Haversine formula)."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def route_distance_km(points: list[dict]) -> float:
    """Total route distance in km from a list of {latitude, longitude} dicts."""
    if len(points) < 2:
        return 0
    return round(
        sum(
            haversine_km(
                points[i]["latitude"], points[i]["longitude"],
                points[i + 1]["latitude"], points[i + 1]["longitude"],
            )
            for i in range(len(points) - 1)
        ),
        2,
    )
