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
| GET | `/health` | Health check |
| POST | `/api/v1/image` | Classify a single image |
| POST | `/api/v1/video` | Process a video file |
| POST | `/api/v1/upload` | Upload video + DJI log for flight telemetry |
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
Video → Sampler (5 FPS) → Quality Check → Tiler (640×640, overlap)
  ├→ Plant Model (YOLOv8 ONNX) → cassava / plantain
  ├→ Disease Model (EfficientNet-B0 ONNX) → routed by plant type
  └→ Save an annotated source frame per affected video frame → output/ + metadata
```

Affected-frame evidence is served at `/api/v1/images/` with a 48-hour TTL.
Each evidence image is the original extracted video frame with a translucent
tile-level heatmap, highlighted tile bounds, and disease/confidence labels.
The overlay marks the tiles classified as affected; it is not pixel-level
segmentation.
