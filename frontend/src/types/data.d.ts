import type { ReactNode } from "react";

export interface HeatmapDatum {
  longitude: number;
  latitude: number;
  value: number; // 0–1 severity
}

export interface FlightPoint {
  longitude: number;
  latitude: number;
  height?: number;
}

export interface FlightMenuItem {
  id: string;
  name: string;
  date: string;
  duration: string;
  summary: string;
  location: string;
}

export interface TelemetryItem {
  label: string;
  value: string;
  detail: string;
  icon?: ReactNode;
}

interface TelemetryHudProps {
  cards: TelemetryItem[];
  startTime: string; // ISO or formatted
  stopTime: string;  // ISO or formatted
}
interface TelemetryElementProps {
  label: string;
  value: string;
  detail: string;
}
