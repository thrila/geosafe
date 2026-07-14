import type { FlightResultProps, FlightSlide } from "../types/result";

export const slides: FlightSlide[] = [];

export const diseasesDetected: string[] = [];

export const demoFlightResult: FlightResultProps = {
  routeDistanceKm: 0,
  startPoint: { latitude: 0, longitude: 0, height: 0 },
  endPoint: { latitude: 0, longitude: 0, height: 0 },
  batteryDrainedPct: 0,
  maxSpeedMs: 0,
  maxHeightM: 0,
  batteryTempC: 0,
  diseasesDetected: [],
  slides: [],
};
