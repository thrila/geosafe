# GeoSafe

Drone-based plant disease detection platform. Upload flight video + DJI logs to get AI-powered disease analysis overlaid on a 3D map.

## Structure

```
geosafe/
├── backend/            FastAPI — ONNX inference, telemetry, flight API
├── frontend/           React + Cesium — 3D map visualization
└── dji-flight-parser/  Bun — DJI log parsing into SQLite
```

## Quick Start

Each sub-project has its own README. To run the full stack:

```bash
# 1. Import DJI flight logs
cd dji-flight-parser
bun install
bun run app.ts <flight-name> <log.txt>

# 2. Start the backend
cd backend
uv sync
uv run uvicorn main:app --reload

# 3. Start the frontend
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Environment Variables

Each project uses a `.env` file for configuration. See individual READMEs for details.

| Project | Key Variables |
|---------|--------------|
| `backend` | `HOST`, `PORT`, `DB_PATH`, `CORS_ORIGINS` |
| `frontend` | `VITE_CESIUM_ION_TOKEN`, `VITE_API_BASE_URL` |
| `dji-flight-parser` | `DJI_API_KEY`, `DB_PATH`, `RECORDS_DIR` |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload video + DJI log |
| GET | `/api/v1/flights` | List all flights |
| GET | `/api/v1/flights/{id}` | Flight detail + telemetry |
| GET | `/api/v1/health` | Health check |
| GET | `/docs` | Scalar API reference |
