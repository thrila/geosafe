# Backend API Contract

## Flight survey result

`POST /api/v1/upload` accepts a multipart form with `name` (1–80 characters),
`video`, and a DJI `.txt` flight log. On success it returns the versioned survey
record documented in [Inference data schema](docs/INFERENCE_DATA_SCHEMA.md).
`POST /api/v1/upload/jobs` returns a job whose `result` uses the same schema
after processing completes. `GET /api/v1/flights/{id}` returns that saved survey
record for newly analyzed flights. Older records may still use the legacy detail
shape until they are reprocessed.

Every successful survey response has these top-level fields:

| Field | Purpose |
|---|---|
| `schemaVersion` | Contract version; currently `1.0`. |
| `survey` | Survey identity, name, status, crop, and optional field metadata. |
| `summary` | Coverage, observation counts, condition totals, and data quality. |
| `observations` | Reviewable model findings with class scores and image evidence. |
| `flight` | GPS track and flight telemetry. |
| `processing` | Pipeline/model provenance and sampling settings. |

Observation scores are model scores, not calibrated probabilities. Findings
require human review. The current model classifies image tiles, so an observation
means a positive tile in a sampled frame; it does not mean a unique plant or a
measured affected area. GPS is intentionally left unset for observations until
the video start time can be verified against the flight-log clock. The flight
track remains available independently.

## Upload job endpoints

- `POST /api/v1/upload/jobs` returns `202 Accepted` and a job ID.
- `GET /api/v1/upload/jobs/{job_id}` returns `queued`, `importing`,
  `processing`, `completed`, or `failed`. A completed job includes its survey
  response in `result`.

## Other endpoints

- `GET /api/v1/health` reports service readiness.
- `POST /api/v1/image` classifies an image and returns image/tile predictions.
- `POST /api/v1/video` analyzes a video and returns frame/tile predictions.
- `GET /api/v1/flights` lists flight summaries.
- `GET /docs` serves the Scalar API reference.

Image classification tile results include a `region` in source-image pixel
coordinates. Annotated evidence labels each positive tile with its raw model
score. The frontend map's disease layer accepts geolocated observations and
explains when locations are unavailable; current uploads do not receive
observation GPS until video/log time alignment is verified.

Validation errors use FastAPI's standard `detail` response. Upload size errors
return `413`; invalid or unreadable media returns `400` or `422` as applicable.
