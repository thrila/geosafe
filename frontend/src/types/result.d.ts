export type FlightSlide =
  | { kind: "image"; src: string; caption?: string };

export type SurveyConclusion = "findings" | "healthy" | "inconclusive";

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
  conclusion?: SurveyConclusion;
  diseasesDetected: string[];
  diseaseTally?: Record<string, number>;
  unidentifiedPlants?: number;
  slides?: FlightSlide[];
};
