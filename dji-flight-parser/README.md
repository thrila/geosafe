# DJI Flight Parser

Parses DJI flight log `.txt` files and imports telemetry data into SQLite for the GeoSafe backend.

## Requirements

- Bun runtime
- Python 3.13+ (for `main.py` helper)

## Quick Start

```bash
bun install
```

### Import a flight log

```bash
bun run app.ts <flight-name> <path-to-log.txt>
```

### Batch import all logs

Place `.txt` files in `./flight_raw_records/` then:

```bash
bun run index.ts
```

## Environment Variables

Create a `.env` file:

```
DJI_API_KEY=<your-dji-api-key>
DB_PATH=./telemetry.db
RECORDS_DIR=./flight_raw_records
```

## Output

Telemetry is written to `telemetry.db` (SQLite) with two tables:

- `flights` — flight metadata (name, timestamps, frame count)
- `telemetry` — per-frame GPS, speed, battery, gimbal, and sensor data
