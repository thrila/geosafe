CREATE TABLE flights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    drone_model TEXT, -- Not attainable from flight logs
    start_time TEXT, --Attainable
    end_time TEXT, --Attainable
    total_frames INTEGER, -- Attainable not really useful
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE telemetry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    flight_id INTEGER NOT NULL,

    timestamp TEXT,
    fly_time REAL,

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
    sd_card_state TEXT,

    aileron REAL,
    elevator REAL,
    throttle REAL,
    rudder REAL,

    battery_level REAL,
    battery_voltage REAL,
    battery_current REAL,
    battery_temp REAL,
    battery_capacity REAL,
    battery_full_capacity REAL,

    FOREIGN KEY (flight_id) REFERENCES flights(id)
);


-- Used for Optimizations
CREATE INDEX idx_telemetry_time
ON telemetry(timestamp);

CREATE INDEX idx_telemetry_flight_time
ON telemetry(flight_id, timestamp);

CREATE INDEX idx_telemetry_gps
ON telemetry(latitude, longitude);
