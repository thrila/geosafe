# API Contract — Frontend Expected Response Shape

After a successful upload (`POST /api/v1/upload`), the backend must return a JSON object matching the shape below. The frontend uses this response to hydrate every component.

## Upload Response (`POST /api/v1/upload`)

### Request
```
POST /api/v1/upload
Content-Type: multipart/form-data

Fields:
  name   — string, 1–80 chars
  video  — File (video/*)
  log    — File (.txt, text/plain)
```

### Response `200 OK`

```json
{
  "flight": {
    "id": "otuoke-survey",
    "name": "Maize farm survey",
    "date": "2026-04-28T14:30:00.000Z",
    "duration": "8.4 min",
    "location": "Otuoke, Bayelsa",(we will need a long lat to location for this)
    "summary": "Short baseline pass over the default route."
  },
  "path": [
    { "longitude": 6.2172, "latitude": 4.8329, "height": 142 },
    { "longitude": 6.2181, "latitude": 4.8336, "height": 146 }
  ],
  "telemetry": {
    "dateTime": "2026-06-08T01:12:00.000Z",
    "cards": [
      { "label": "Altitude",  "value": "150 m",  "detail": "Steady cruising altitude." },
      { "label": "Speed",     "value": "8.4 m/s", "detail": "Ground speed." },
      { "label": "GPS",       "value": "14 sats", "detail": "Strong lock." },
      { "label": "Battery",   "value": "92 %",    "detail": "Within range." },
      { "label": "Direction", "value": "North",   "detail": "Heading." },
      { "label": "SD card",   "value": "32 GB",   "detail": "Storage remaining." }
    ]
  },
  "result": {
    "routeDistanceKm": 4.73,
    "startPoint":  { "latitude": 6.5244, "longitude": 3.3792, "height": 0 },
    "endPoint":    { "latitude": 6.5289, "longitude": 3.3841, "height": 0 },
    "batteryDrainedPct": 38,
    "maxSpeedMs": 12.4,
    "maxHeightM": 95,
    "batteryTempC": 41,
    "diseasesDetected": ["Northern corn leaf blight", "Gray leaf spot"],
    "slides": [
      { "kind": "image", "src": "https://example.com/field-a.jpg", "caption": "Field sector A" }
    ]
  }
}
```

### Error Response

```json
{
  "error": "Invalid file type. Only .txt log files are accepted."
}
```

Status codes: `400 Bad Request`, `413 Payload Too Large`, `500 Internal Server Error`.

---

## Frontend Types (mirrored in `src/types/`)

| Type | File | Used By |
|---|---|---|
| `FlightPoint` | `src/types/data.d.ts` | Cesium path drawing |
| `FlightMenuItem` | `src/types/data.d.ts` | Flight menu list |
| `LonLatHeight` | `src/types/location.d.ts` | Cesium entity helpers |
| `FlightResultProps` | `src/types/result.d.ts` | Flight result panel |
| `FlightSlide` | `src/types/result.d.ts` | Image carousel |
| `TelemetryItem` | `src/types/data.d.ts` | Telemetry HUD cards |
| `FlightOption` | `src/types/modal.d.ts` | Flight menu modal |
| `ModalProps` | `src/types/modal.d.ts` | Modal shell |

All optional fields (`?` in types) may be omitted or null from the backend response.
