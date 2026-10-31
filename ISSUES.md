# Known issues

Findings from the October 2026 code review. Severity reflects the effect on a
user, not the size of the fix.

## Critical

- [x] **C1. Every UI flight upload fails.** `record_flight_id`, `begin_processing`
  and `renew_claim` pass `worker_id` positionally to the keyword-only
  `_update_claimed`, raising `TypeError` (since `9ef3e71`).
- [ ] **C2. The plantain disease model does not detect disease.** Its classes are
  `AugmentedSet` and `OriginalSet`: the notebook pointed `ImageFolder` one level
  too high, so it learned whether an image was augmented. Needs retraining on the
  real BananaLSD disease folders. Until then its output is reported as Inconclusive.
- [ ] **C3. The plant gate does not reject non-crop footage.** The shipped model has
  only cassava and plantain classes (the notebook's `other` class is missing). A
  clip of a person and a building scored plantain at about 0.99 on all 80 tiles.
  Needs retraining with a negative class. Non-crop footage now ends as Inconclusive
  rather than a false all-clear, but it is still labelled plantain.
- [x] **C4. Meaningless output is shown as "Clean".** Zero observations renders the
  "Clean" badge even when no tile was confidently assessed.

## High: pipeline logic

- [x] **H1.** Low-confidence disease predictions are reported as "Healthy".
- [x] **H2.** A missing disease model reports Healthy at 100% confidence.
- [x] **H3.** Models load lazily, so startup and `/health` report ready before any
  model has loaded. Model paths depend on the working directory.
- [x] **H4.** Decode errors in the producer are only logged, so a broken video can
  return a partial result. Per-frame worker errors are dropped the same way.
- [x] **H5.** A flight is rejected when most tiles are unrecognized, even if other
  tiles found disease. Images use worst-tile logic, so the two paths disagree.

## High: job queue and storage

- [x] **H6.** A failure inside `jobs.fail` kills the worker task silently.
- [x] **H7.** Jobs have no retry limit, so a crashing job is reclaimed forever.
- [x] **H8.** Upload payloads are never deleted. Payloads from jobs that finished
  before this fix stay in `upload_jobs/` and can be removed by hand.
- [ ] **H9.** Losing a lease does not stop processing.
- [ ] **H10.** The log is imported before analysis, so failures leave orphan flights.
- [ ] **H11.** Evidence images expire after 48 hours while saved results still link
  to them.

## Tests

- [x] **T1.** API tests run the real worker against the developer's `telemetry.db`.
- [x] **T2.** The upload worker loop has no tests.
- [x] **T3.** Pipeline logic is unpinned: thresholds, preprocessing, tiling, sampling
  and aggregation can all change without a test failing (15 of 18 injected bugs
  survived).
- [x] **T4.** `test_diseased_tiles_persisted` can never reach its assertions.
- [x] **T5.** The "no_duplicate" model-loading tests never count loads.
- [ ] **T6.** CI skips the integration tests, and they only check that keys exist.
- [ ] **T7.** The frontend has no tests.

## Frontend

- [x] **F1.** Each tile becomes a slide, so the same frame repeats in the carousel.
- [x] **F2.** `unidentifiedPlants` is hardcoded to 0.
- [x] **F3.** Selecting flights quickly can show a stale response.
- [x] **F4.** One failed poll ends the upload wait while the job keeps running.
- [ ] **F5.** The job ID is not saved, so a refresh loses the job.
- [x] **F6.** Only image upload shows the backend's error detail.
- [x] **F7.** Dead code: `data/flights.ts`, `models/test.ts`, `uploadFile`.
- [x] **F8.** Misspelled names: `componets`, `telementry`, `telementary`.
- [ ] **F9.** `App.tsx` owns modals, fetching and two response formats.
- [ ] **F10.** Survey types are hand-written and can drift from the API.
