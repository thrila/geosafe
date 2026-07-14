import type { TelemetryItem } from "../types/data";
import { TrendingUp, BarChart, Battery, HardDrive, Navigation, Compass } from "react-feather";
export const ICON_SIZE = 16;

export const telemetrySample = {
  dateTime: "2026-06-08T01:12:00.000Z",
};

export const telemetryCards: TelemetryItem[] = [
  { label: "Altitude",  value: " — — ", detail: " — — ",  icon: <TrendingUp size={ICON_SIZE} /> },
  { label: "Speed",     value: " — — ", detail: " — — ",  icon: <Navigation size={ICON_SIZE} /> },
  { label: "GPS",       value: " — — ", detail: " — — ",  icon: <BarChart size={ICON_SIZE} /> },
  { label: "Battery",   value: " — — ", detail: " — — ",  icon: <Battery size={ICON_SIZE} /> },
  { label: "Direction", value: " — — ", detail: " — — ",  icon: <Compass size={ICON_SIZE} /> },
  { label: "SD card",   value: " — — ", detail: " — — ",  icon: <HardDrive size={ICON_SIZE} /> },
];
