export type FlightSlide =
  | { kind: "image"; src: string; caption?: string };

export type FlightResultProps = {
  routeDistanceKm: number;
  startPoint?: {
    latitude: number;
    longitude: number;
    height?: number;
  };
  endPoint?: {
    latitude: number;
    longitude: number;
    height?: number;
  };
  batteryDrainedPct: number;
  maxSpeedMs: number;
  maxHeightM: number;
  batteryTempC: number;
  diseasesDetected: string[];
  slides?: FlightSlide[];
};
