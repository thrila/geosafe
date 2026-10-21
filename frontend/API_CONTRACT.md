# Frontend API Contract

The backend contract is the source of truth for request and response details:
[`backend/API_CONTRACT.md`](../backend/API_CONTRACT.md). New flight analyses
return the versioned survey record described in
[`backend/docs/INFERENCE_DATA_SCHEMA.md`](../backend/docs/INFERENCE_DATA_SCHEMA.md).
The frontend also accepts legacy flight responses when opening older records.

## Endpoints used by the frontend

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/v1/upload` | Submit a flight video and DJI `.txt` log. |
| `POST` | `/api/v1/upload/jobs` | Queue a durable flight upload. |
| `GET` | `/api/v1/upload/jobs/{id}` | Poll a queued flight upload. |
| `GET` | `/api/v1/flights` | List saved flights. |
| `GET` | `/api/v1/flights/{id}` | Load a saved flight and its results. |
| `GET` | `/api/v1/health` | Check API and analysis-pipeline readiness. |
| `POST` | `/api/v1/image` | Classify a single image. |

The flight map visualizes GPS route data. Disease observations appear in the
results panel; the frontend does not geolocate them on the map until video and
flight-log time alignment and camera ground projection are calibrated.

Analysis requests can return `503` while the backend is starting or if its
inference pipeline failed to initialize. The health endpoint reports
`starting`, `unavailable`, or `ok` in its `status` field.
