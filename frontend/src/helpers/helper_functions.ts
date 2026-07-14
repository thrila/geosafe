import type { FlightPoint } from "../types/data";

export function calculateRouteDistanceKm(points: FlightPoint[]) {
  if (points.length < 2) {
    return 0;
  }

  let distance = 0;

  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const current = points[index];
    const radius = 6371;
    const lat1 = (previous.latitude * Math.PI) / 180;
    const lat2 = (current.latitude * Math.PI) / 180;
    const deltaLat = ((current.latitude - previous.latitude) * Math.PI) / 180;
    const deltaLon = ((current.longitude - previous.longitude) * Math.PI) / 180;
    const sinLat = Math.sin(deltaLat / 2);
    const sinLon = Math.sin(deltaLon / 2);
    const a =
      sinLat * sinLat + Math.cos(lat1) * Math.cos(lat2) * sinLon * sinLon;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    distance += radius * c;
  }

  return distance;
}

export function formatCoordinate(point: FlightPoint) {
  const height = point.height ?? 0;
  return `${point.latitude.toFixed(5)}, ${point.longitude.toFixed(5)}, ${height.toFixed(0)} m`;
}

export function formatFileSize(bytes: number) {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unitIndex = 0;

  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024;
    unitIndex += 1;
  }

  return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[unitIndex]}`;
}

const knownLocations: Record<string, string> = {
  "6.2172,4.8329": "Otuoke, Bayelsa",
  "6.5244,3.3792": "Lagos, Nigeria",
};

export async function reverseGeocode(latitude: number, longitude: number): Promise<string> {
  const key = `${latitude.toFixed(4)},${longitude.toFixed(4)}`;
  if (knownLocations[key]) return knownLocations[key];

  try {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json&addressdetails=1`,
      { headers: { "User-Agent": "map_for_drone/1.0" } }
    );
    if (!res.ok) return `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
    const data = await res.json();
    return data.display_name ?? `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
  } catch {
    return `${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
  }
}

export function formatDateTime(dateTime: string) {
  return new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
    timeZone: "UTC",
  }).format(new Date(dateTime));
}
