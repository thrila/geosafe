import type { FlightPoint, HeatmapDatum } from "../types/data.d.ts"

export const flightPath: FlightPoint[] = [
  { longitude: 6.2172, latitude: 4.8329, height: 142 },
  { longitude: 6.2181, latitude: 4.8336, height: 146 },
  { longitude: 6.2194, latitude: 4.8342, height: 150 },
  { longitude: 6.2211, latitude: 4.835, height: 154 },
  { longitude: 6.2228, latitude: 4.8357, height: 151 },
  { longitude: 6.2243, latitude: 4.8361, height: 147 },
  { longitude: 6.2261, latitude: 4.8368, height: 143 },
];

export const otuokeLocation = {
  longitude: 6.2211,
  latitude: 4.835,
  height: 150,
};

export const heatmapArea: FlightPoint[] = [
  { longitude: 6.2180, latitude: 4.8330, height: 0 },
  { longitude: 6.2205, latitude: 4.8325, height: 0 },
  { longitude: 6.2230, latitude: 4.8335, height: 0 },
  { longitude: 6.2240, latitude: 4.8355, height: 0 },
  { longitude: 6.2225, latitude: 4.8370, height: 0 },
  { longitude: 6.2195, latitude: 4.8365, height: 0 },
];

export const heatmapData: HeatmapDatum[] = [
  { longitude: 6.2185, latitude: 4.8332, value: 0.1 },
  { longitude: 6.2195, latitude: 4.8338, value: 0.3 },
  { longitude: 6.2205, latitude: 4.8340, value: 0.6 },
  { longitude: 6.2215, latitude: 4.8345, value: 0.8 },
  { longitude: 6.2220, latitude: 4.8350, value: 0.9 },
  { longitude: 6.2225, latitude: 4.8355, value: 0.7 },
  { longitude: 6.2230, latitude: 4.8360, value: 0.5 },
  { longitude: 6.2235, latitude: 4.8365, value: 0.4 },
  { longitude: 6.2210, latitude: 4.8355, value: 0.2 },
  { longitude: 6.2200, latitude: 4.8345, value: 0.5 },
  { longitude: 6.2190, latitude: 4.8350, value: 0.6 },
  { longitude: 6.2215, latitude: 4.8360, value: 0.3 },
];
