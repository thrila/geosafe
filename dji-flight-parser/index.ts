import { DJILog } from "dji-log-parser-js";
import { readdirSync, readFileSync, existsSync, mkdirSync } from "fs";
import * as path from "path";
import { Database } from "bun:sqlite";
import { logInfo, logError, logCreated, logSuccess } from "./logs";

const RECORDS_DIR = "./flight_raw_records";
const DB_PATH = "./telemetry.db";

// --------------------
// Ensure input dir
// --------------------
function ensureDir(dir: string) {
  if (!existsSync(dir)) {
    mkdirSync(dir);
    logSuccess(`put DJI flight .txt files in ${dir}`);
    process.exit(0);
  }
}

ensureDir(RECORDS_DIR);

// --------------------
// DB CLASS
// --------------------
class TelemetryDB {
  private db: Database;

  // prepared statements (IMPORTANT for performance)
  private insertFlightStmt;
  private insertTelemetryStmt;

  constructor(dbPath: string) {
    this.db = new Database(dbPath);
    this.init();

    this.insertFlightStmt = this.db.prepare(`
      INSERT INTO flights (
        name, source_file, start_ts, end_ts, total_frames, created_at
      ) VALUES (?, ?, ?, ?, ?, ?)
    `);

    this.insertTelemetryStmt = this.db.prepare(`
      INSERT INTO telemetry (
        flight_id, frame_index, ts,
        latitude, longitude, height, altitude,
        x_speed, y_speed, z_speed,
        pitch, roll, yaw,
        gps_num, gps_level, is_gps_used,
        flyc_state, flyc_command, flight_action,
        is_on_ground, is_motor_on, is_vibrating,
        gimbal_pitch, gimbal_roll, gimbal_yaw,
        is_photo, is_video,
        battery_level, battery_voltage, battery_current,
        battery_temp, battery_capacity, battery_full_capacity,
        raw_json
      ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
      )
    `);
  }

  private init() {
    this.db.run("PRAGMA journal_mode = WAL;");
    this.db.run("PRAGMA synchronous = NORMAL;");
    this.db.run("PRAGMA temp_store = MEMORY;");

    this.db.run(`
      CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        source_file TEXT,
        start_ts INTEGER,
        end_ts INTEGER,
        total_frames INTEGER,
        created_at INTEGER
      );
    `);

    this.db.run(`
      CREATE TABLE IF NOT EXISTS telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_id INTEGER,
        frame_index INTEGER,
        ts INTEGER,

        latitude REAL,
        longitude REAL,
        height REAL,
        altitude REAL,

        x_speed REAL,
        y_speed REAL,
        z_speed REAL,

        pitch REAL,
        roll REAL,
        yaw REAL,

        gps_num INTEGER,
        gps_level INTEGER,
        is_gps_used INTEGER,

        flyc_state TEXT,
        flyc_command TEXT,
        flight_action TEXT,

        is_on_ground INTEGER,
        is_motor_on INTEGER,
        is_vibrating INTEGER,

        gimbal_pitch REAL,
        gimbal_roll REAL,
        gimbal_yaw REAL,

        is_photo INTEGER,
        is_video INTEGER,

        battery_level REAL,
        battery_voltage REAL,
        battery_current REAL,
        battery_temp REAL,
        battery_capacity REAL,
        battery_full_capacity REAL,

        raw_json TEXT
      );
    `);
  }

  // --------------------
  // Insert flight
  // --------------------
  insertFlight(
    name: string,
    sourceFile: string,
    startTs: number,
    endTs: number,
    totalFrames: number
  ): number {
    const res = this.insertFlightStmt.run(
      name,
      sourceFile,
      startTs,
      endTs,
      totalFrames,
      Date.now()
    );

    return Number(res.lastInsertRowid);
  }

  // --------------------
  // Insert telemetry
  // --------------------
  insertTelemetry(values: any[]) {
    this.insertTelemetryStmt.run(values);
  }

  // --------------------
  // Transaction wrapper
  // --------------------
  transaction(fn: () => void) {
    return this.db.transaction(fn)();
  }
}

// --------------------
// INIT DB
// --------------------
const db = new TelemetryDB(DB_PATH);

// --------------------
// PROCESS FILE
// --------------------
async function processFile(filePath: string) {
  logInfo(`Processing ${filePath}`);

  const buffer = readFileSync(filePath);
  const parser = new DJILog(buffer);

  const keychains = await parser.fetchKeychains(
    "64b1fa043371eac1a1e39ce982a2c13"
  );

  const frames = await parser.frames(keychains);

  if (!frames.length) return;

  // convert timestamps
  const timestamps: number[] = frames
    .map((f) =>
      f.custom?.dateTime ? new Date(f.custom.dateTime).getTime() : null
    )
    .filter(Boolean) as number[];

  const startTs = Math.min(...timestamps);
  const endTs = Math.max(...timestamps);

  const flightId = db.insertFlight(
    path.basename(filePath),
    path.basename(filePath),
    startTs,
    endTs,
    frames.length
  );

  // --------------------
  // Bulk insert (FAST)
  // --------------------
  db.transaction(() => {
    for (let i = 0; i < frames.length; i++) {
      const f = frames[i];

      const ts = f.custom?.dateTime
        ? new Date(f.custom.dateTime).getTime()
        : null;

      if (!ts) continue;

      db.insertTelemetry([
        flightId,
        i,
        ts,

        f.osd?.latitude,
        f.osd?.longitude,
        f.osd?.height,
        f.osd?.altitude,

        f.osd?.xSpeed,
        f.osd?.ySpeed,
        f.osd?.zSpeed,

        f.osd?.pitch,
        f.osd?.roll,
        f.osd?.yaw,

        f.osd?.gpsNum,
        f.osd?.gpsLevel,
        f.osd?.isGpsUsed ? 1 : 0,

        f.osd?.flycState,
        f.osd?.flycCommand,
        f.osd?.flightAction,

        f.osd?.isOnGround ? 1 : 0,
        f.osd?.isMotorOn ? 1 : 0,
        f.osd?.isVibrating ? 1 : 0,

        f.gimbal?.pitch,
        f.gimbal?.roll,
        f.gimbal?.yaw,

        f.camera?.isPhoto ? 1 : 0,
        f.camera?.isVideo ? 1 : 0,

        f.battery?.chargeLevel,
        f.battery?.voltage,
        f.battery?.current,
        f.battery?.temperature,
        f.battery?.currentCapacity,
        f.battery?.fullCapacity,

        JSON.stringify(f)
      ]);
    }
  });
  logSuccess(`Inserted ${frames.length} frames → flight ${flightId}`);
}

// --------------------
// MAIN
// --------------------
const files = readdirSync(RECORDS_DIR).filter((f) => f.endsWith(".txt"));

for (const file of files) {
  await processFile(path.join(RECORDS_DIR, file));
}

logSuccess(`Done`);
