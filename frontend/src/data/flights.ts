import type { FlightMenuItem } from "../types/data";

export const flightOptions: FlightMenuItem[] = [
  {
    id: "otuoke-survey",
    name: "Maize farm survey",
    date: "2026-04-28",
    duration: "8.4 min",
    location: "Otuoke, Bayelsa",
    summary: "Short baseline pass over the default route.",
  },
  {
    id: "riverbank-pass",
    name: "Riverbank Pass",
    date: "2026-05-03",
    duration: "12.2 min",
    location: "Otuoke, Bayelsa",
    summary: "Higher sweep with a wider tracking path.",
  },
  {
    id: "sunset-loop",
    name: "Sunset Loop",
    date: "2026-05-20",
    duration: "15.1 min",
    location: "Otuoke, Bayelsa",
    summary: "Longer loop recorded near the end of the session.",
  },
];

export const defaultFlightId = flightOptions[0]?.id ?? "otuoke-survey";

export function getFlightById(flightId: string) {
  return flightOptions.find((flight) => flight.id === flightId) ?? null;
}
