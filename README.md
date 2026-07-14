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

The `utils/import-logs.exe` binary (Bun-compiled) imports DJI `.txt` flight logs into a SQLite database for telemetry analysis.

## Pipeline

```
Video → Sampler (5 FPS) → Quality Check → Tiler (640×640, overlap)
  ├→ Plant Model (YOLOv8 ONNX) → cassava / plantain
  ├→ Disease Model (EfficientNet-B0 ONNX) → routed by plant type
  └→ Save diseased tiles → output/images/ + metadata
```

Diseased frame images are served at `/api/v1/images/` with a 48-hour TTL.
