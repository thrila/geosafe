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
# 1. Install the DJI log parser used by the upload flow
cd dji-flight-parser
bun install

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

## Docker

Set `DJI_API_KEY`, then start the complete stack with persistent telemetry and
upload-job storage:

```bash
docker compose up --build
```

The application is served at `http://localhost:8080`; the API is at
`http://localhost:8000`. The `geosafe-data` volume retains the SQLite database,
queued uploads, and generated evidence across container restarts.

## Environment Variables

Each project uses a `.env` file for configuration. See individual READMEs for details.

| Project | Key Variables |
|---------|--------------|
| `backend` | `HOST`, `PORT`, `DB_PATH`, `CORS_ORIGINS` |
| `frontend` | `VITE_CESIUM_ION_TOKEN`, `VITE_API_BASE_URL` |
| `dji-flight-parser` | `DJI_API_KEY`, `DB_PATH`, `RECORDS_DIR` |

`POST /api/v1/upload` imports the supplied DJI log and binds its created flight
record to that exact video analysis. Bun and `DJI_API_KEY` must therefore be
available to the backend process. Set `VIDEO_SAMPLE_FPS` (default `2.0`) to
trade processing time against temporal coverage.

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/upload` | Upload video + DJI log |
| POST | `/api/v1/upload/jobs` | Queue a durable upload; returns `202` |
| GET | `/api/v1/upload/jobs/{id}` | Poll a queued upload's status and result |
| GET | `/api/v1/flights` | List all flights |
| GET | `/api/v1/flights/{id}` | Flight detail + telemetry |
| GET | `/api/v1/health` | Health check |
| GET | `/docs` | Scalar API reference |

## Model evaluation and disease mapping

The repository includes an evaluation command, but deliberately does not claim
accuracy for the bundled generic plant models. Evaluate a properly labelled
plantain dataset before production use:

```bash
cd backend
uv run python model_evaluation.py path/to/labels.csv --output model-evaluation.json
```

The CSV must contain `image,disease` headers; image paths are relative to the
CSV. A disease heatmap must not be enabled until video timestamps are aligned
to telemetry timestamps and the camera pose, altitude, and ground projection
assumptions have been calibrated. Until then the UI shows the verified flight
route only.

Flight-result slides show the original sampled video frame, overlaid with a
tile-level heatmap and affected-tile labels. This visualises model evidence in
context; it is not a pixel-level disease segmentation map.
