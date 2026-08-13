# GeoSafe improvement summary

## What has been completed

### Uploads are now bound to their own DJI flight record

- Added `backend/services/log_importer.py`, which calls the repository's Bun
  DJI parser with the uploaded `.txt` file and reads the `flightId` it creates.
- Updated `dji-flight-parser/app.ts` with a `--json` mode so the backend can
  consume that ID reliably.
- Changed `POST /api/v1/upload` to import the supplied log first, then use
  that exact `flight_id` to construct the response. The previous unsafe
  `get_latest_flight_id()` association is no longer used by uploads.
- The backend now reports a useful `422` error if Bun, the parser, or the DJI
  log import is unavailable or fails.

### Analysis artifacts are isolated per flight

- Every successful upload gets a UUID artifact directory under `output/`.
- Disease images and metadata are saved under that unique directory rather
  than shared filenames such as `f000000_t000.jpg`.
- Public image paths are flight-scoped, e.g.
  `/api/v1/images/<artifact-id>/f000007_t002.jpg`.
- Flight analysis (disease tally and slides) is persisted in the new
  `analysis_runs` SQLite table and is restored when a historical flight is
  opened.
- Cleanup now removes expired artifact directories rather than using a stale
  timestamp or treating all files as one global upload.

### Upload and runtime hardening

- Upload writing is chunked instead of reading the entire file into memory.
- Added a configurable upload limit (`MAX_UPLOAD_BYTES`, default 1 GB).
- Added a readiness-aware health endpoint: it returns `503` while model
  startup has not completed.
- Sampling rate is now environment-configured (`VIDEO_SAMPLE_FPS`, default
  2 FPS) to make large video uploads substantially quicker by default.
- Documentation was updated to explain that Bun and `DJI_API_KEY` are required
  for the upload path.

### Frontend integrity and presentation

- Removed the random/scattered map overlay that was presented as a heatmap.
  It did not use disease detections and would have been misleading.
- Image URLs from the API are resolved against the configured API base URL,
  so flight evidence images work outside a localhost-only deployment.
- Updated the browser title to `GeoSafe — Drone Crop Health Survey`.

### Flight-path improvement started and implemented

The map route has been changed from a thin plain line plus a rectangular
boundary to a clearer route visualization:

- bright glow route line;
- white arrow line over the route to show direction of travel;
- explicit `START` and `END` markers;
- a drone model positioned at the latest recorded location and oriented from
  its final movement segment;
- camera automatically frames an uploaded or selected flight;
- removed the rectangular boundary, which was only a bounding box and did not
  represent a surveyed field.

The route code also now handles a one-point flight safely, instead of assuming
there is always a second GPS sample.

## Tests and verification completed

- Full backend non-integration suite: **85 passed in 34.25s**.
- Added tests for:
  - parser flight-ID handoff;
  - erroring when a parser returns no flight ID;
  - analysis storage replacement per flight;
  - artifact URL scoping;
  - upload response binding to the imported `flight_id`.
- Frontend production build passed before the final flight-path styling patch.

## Remaining work / next steps

1. Run `npm run build` and manually inspect the new Cesium route after the
   final path patch. The patch was applied immediately before the user asked
   for this summary, so it still needs final verification.
2. Replace generic plantain outputs (`AugmentedSet` / `OriginalSet`) with a
   properly trained and evaluated plantain disease model. This cannot be fixed
   safely in application code; it requires appropriate labelled data and model
   evaluation.
3. Add genuine disease map observations only after defining video timestamp to
   telemetry timestamp alignment (and camera/georeferencing assumptions).
   Until then, GeoSafe correctly shows the flight route rather than pretending
   it has geolocated disease detections.
4. Move long video work to persistent background jobs with progress/status
   endpoints for multi-user deployments.
5. Add a public portfolio package: Docker setup, CI, model evaluation metrics,
   architecture diagram, sample data, demo screenshots/video, limitations, and
   a license.
6. Reduce the large Cesium frontend bundle through lazy loading/code splitting
   when polishing deployment performance.

## Important operational requirements

- The backend process needs Bun available on `PATH` (or `BUN_BINARY` set).
- It also needs `DJI_API_KEY` for DJI log parsing.
- The parser and backend must point at the same telemetry database; the backend
  explicitly supplies its `DB_PATH` to the parser for each upload.
