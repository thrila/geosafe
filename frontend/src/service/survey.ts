import type { FlightResultProps } from "../types/result";
import type { TelemetryItem } from "../types/data";

type SurveyRecord = {
  schemaVersion: string;
  flight: {
    id: number;
    name: string;
    startedAt: string | null;
    track: {
      crs: string;
      samples: {
        latitude: number | null;
        longitude: number | null;
        heightMeters: number | null;
      }[];
    };
    telemetry: {
      routeDistanceMeters: number;
      maxSpeedMetersPerSecond: number;
      maxAltitudeMeters: number;
      batteryDrainedPercent: number;
      maxBatteryTemperatureCelsius: number;
      averageGpsSatellites: number;
    };
  };
  survey: { id: string; name: string; createdAt: string };
  summary: {
    coverage: { flightDurationSeconds: number };
    dataQuality: { videoTelemetryAlignment: string };
    conditions: { name: string; observationCount: number }[];
  };
  observations: {
    location: {
      latitude: number | null;
      longitude: number | null;
    };
    condition: { name: string; confidence: number };
    observedAt: { frameNumber: number };
    evidence: { annotatedImage: string | null };
  }[];
};

export function isSurveyRecord(value: unknown): value is SurveyRecord {
  return !!value && typeof value === "object" &&
    (value as SurveyRecord).schemaVersion === "1.0";
}

export function surveyResultView(survey: SurveyRecord): FlightResultProps {
  const telemetry = survey.flight.telemetry;
  const points = survey.flight.track.samples.filter(
    (sample) => sample.latitude !== null && sample.longitude !== null,
  );
  const point = (sample?: (typeof points)[number]) => sample
    ? { longitude: sample.longitude!, latitude: sample.latitude!, height: sample.heightMeters ?? undefined }
    : undefined;

  return {
    routeDistanceKm: telemetry.routeDistanceMeters / 1000,
    startPoint: point(points[0]),
    endPoint: point(points[points.length - 1]),
    batteryDrainedPct: telemetry.batteryDrainedPercent,
    maxSpeedMs: telemetry.maxSpeedMetersPerSecond,
    maxHeightM: telemetry.maxAltitudeMeters,
    batteryTempC: telemetry.maxBatteryTemperatureCelsius,
    diseasesDetected: survey.summary.conditions.map((condition) => condition.name),
    diseaseTally: Object.fromEntries(
      survey.summary.conditions.map((condition) => [condition.name, condition.observationCount]),
    ),
    unidentifiedPlants: 0,
    slides: survey.observations.flatMap((observation) =>
      observation.evidence.annotatedImage
        ? [{
            kind: "image" as const,
            src: observation.evidence.annotatedImage,
            caption: `Frame ${observation.observedAt.frameNumber} — ${observation.condition.name} (${(observation.condition.confidence * 100).toFixed(0)}% model score)`,
          }]
        : [],
    ),
  };
}

export function surveyTelemetryCards(survey: SurveyRecord): TelemetryItem[] {
  const data = survey.flight.telemetry;
  return [
    { label: "Route", value: `${(data.routeDistanceMeters / 1000).toFixed(2)} km`, detail: "Total distance." },
    { label: "Max Speed", value: `${data.maxSpeedMetersPerSecond.toFixed(1)} m/s`, detail: "Ground speed." },
    { label: "Max Height", value: `${data.maxAltitudeMeters.toFixed(1)} m`, detail: "Peak altitude." },
    { label: "Battery", value: `${data.batteryDrainedPercent.toFixed(1)}% used`, detail: "Change during flight." },
    { label: "Battery Temp", value: `${data.maxBatteryTemperatureCelsius.toFixed(1)} °C`, detail: "Peak temperature." },
    { label: "GPS", value: `${data.averageGpsSatellites} sats`, detail: "Average satellites." },
  ];
}

export function surveyTrack(survey: SurveyRecord) {
  return survey.flight.track.samples
    .filter((sample) => sample.latitude !== null && sample.longitude !== null)
    .map((sample) => ({
      longitude: sample.longitude!,
      latitude: sample.latitude!,
      height: sample.heightMeters ?? undefined,
    }));
}

export function surveyFindings(survey: SurveyRecord) {
  return survey.observations.flatMap((observation) => {
    const { latitude, longitude } = observation.location;
    if (latitude === null || longitude === null) return [];
    return [{
      latitude,
      longitude,
      value: observation.condition.confidence,
      label: observation.condition.name,
    }];
  });
}
