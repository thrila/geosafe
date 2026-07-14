# GeoSafe Frontend

React + TypeScript + Vite application for visualizing drone flight data and plant disease detection results on a 3D Cesium map.

## Requirements

- Node.js 18+
- npm

## Quick Start

```bash
npm install
npm run dev
```

The app runs at `http://localhost:5173` and expects the backend at `http://127.0.0.1:8000`.

## Environment Variables

Copy `.env.local.example` to `.env.local` and fill in:

| Variable | Description |
|----------|-------------|
| `VITE_CESIUM_ION_TOKEN` | Cesium Ion access token |
| `VITE_API_BASE_URL` | Backend API base URL (e.g. `http://127.0.0.1:8000/api/v1`) |

## Features

- 3D Cesium map with aerial imagery
- Upload flight video + DJI log for analysis
- Flight path visualization with drone models
- Boundary polygon and heatmap overlay
- Telemetry HUD (altitude, speed, GPS, battery)
- Flight results panel (diseases detected, route stats)
- Previous flights menu with map fly-to
