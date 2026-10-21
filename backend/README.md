# GeoSafe — Plant Disease Detection API

ONNX-based inference pipeline for plant classification (cassava/plantain) and disease detection from video and images.

## Requirements

- Python 3.13+
- `uv` package manager

## Quick Start

```bash
uv sync
uv run uvicorn main:app --reload
```

API reference at `http://127.0.0.1:8000/docs` (Scalar UI).

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Readiness-aware health check |
| POST | `/api/v1/image` | Classify a single image |
| POST | `/api/v1/video` | Process a video file |
| POST | `/api/v1/upload` | Upload video + DJI log for flight telemetry |
| POST | `/api/v1/upload/jobs` | Queue a durable flight upload |
| GET | `/api/v1/upload/jobs/{id}` | Poll a queued upload |
| GET | `/api/v1/flights` | List all flights |
| GET | `/api/v1/flights/{id}` | Flight detail with telemetry & results |
| GET | `/docs` | Scalar API reference |

## Telemetry Import

`POST /api/v1/upload` invokes the sibling `dji-flight-parser/app.ts` command
with the uploaded log, then uses the returned `flight_id` for that exact video
analysis. Install Bun and set `DJI_API_KEY` in the backend environment before
using this endpoint. The importer can also be run manually for batch imports.

The upload sampler defaults to `VIDEO_SAMPLE_FPS=2.0`; increase it when a
survey needs denser temporal coverage, acknowledging the additional CPU cost.

## Pipeline

```
Video → Sampler (configurable FPS, default 2 FPS)
  → Quality Check → Tiler (640×640, overlap)
  ├→ Plant Model (YOLOv8 ONNX) → cassava / plantain
  ├→ Disease Model (EfficientNet-B0 ONNX) → routed by plant type
  └→ Save an annotated source frame per affected video frame → output/ + metadata
```

Affected-frame evidence is served at `/api/v1/images/` with a 48-hour TTL.
Each evidence image is the original extracted video frame with a translucent
tile-level heatmap, highlighted tile bounds, and disease/model-score labels.
The overlay marks the tiles classified as affected; it is not pixel-level
segmentation.

The flight map shows the recorded route. Disease observations are not placed
on the map until video/log clock alignment and camera ground projection have
been verified.

## Startup readiness

The API loads its ONNX pipeline during startup. Until model loading completes,
`GET /api/v1/health` returns `503` with `starting`; if model
loading fails, it continues to return `503` with `unavailable` and the backend
logs contain the initialization error. Direct analysis uploads also return
`503` while the pipeline is starting or unavailable. Image, video, and
synchronous flight-analysis requests return the same status. Queued upload jobs
remain queued when initialization fails and can be processed after a
successful restart.

## Survey result data

Completed upload results use a versioned survey record with reviewable
tile/frame observations, image evidence regions, model scores, flight track
samples, data-quality notes, and model artifact digests. The response contract
and interpretation guidance are documented in
[`docs/INFERENCE_DATA_SCHEMA.md`](docs/INFERENCE_DATA_SCHEMA.md). Current
observations are not unique plant counts, and per-observation GPS remains unset
until video/log time alignment and camera ground projection are verified.
