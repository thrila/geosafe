import json
from unittest.mock import patch, MagicMock, PropertyMock
import pytest
from fastapi.testclient import TestClient


class TestFlightsEndpointList:
    def test_flights_list_empty(self, client):
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = []
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn
            r = client.get("/api/v1/flights")
            assert r.status_code == 200
            assert r.json() == []

    def test_flights_list_with_data(self, client):
        mock_rows = [
            {"id": 1, "name": "test-flight", "start_ts": 1000, "end_ts": 2000, "total_frames": 50},
            {"id": 2, "name": "another-flight", "start_ts": 3000, "end_ts": 6000, "total_frames": 120},
        ]

        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchall.return_value = [
                MagicMock(**{k: v for k, v in row.items()})
                for row in mock_rows
            ]
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn

            r = client.get("/api/v1/flights")
            assert r.status_code == 200
            data = r.json()
            assert len(data) == 2

    def test_flights_list_on_db_error(self, client):
        with patch("sqlite3.connect", side_effect=Exception("DB error")):
            r = client.get("/api/v1/flights")
            assert r.status_code == 200
            assert r.json() == []


class TestFlightsEndpointDetail:
    def test_flight_not_found(self, client):
        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = None
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn

            r = client.get("/api/v1/flights/999")
            assert r.status_code == 404
            assert "not found" in r.text.lower()

    def test_flight_success(self, client):
        mock_flight_row = MagicMock()
        mock_flight_row.__getitem__.side_effect = lambda k: {
            "id": 1, "name": "test-flight", "start_ts": 1000, "end_ts": 2000, "total_frames": 50
        }[k]

        mock_telemetry_rows = []
        for i in range(10):
            row = MagicMock()
            row.__getitem__.side_effect = lambda k, i=i: {
                "latitude": 4.79 + i * 0.001,
                "longitude": 6.31 + i * 0.001,
                "height": float(i * 10),
                "x_speed": float(i),
                "y_speed": float(i * 0.5),
                "z_speed": 0.0,
                "battery_level": 50.0,
                "battery_temp": 45.0,
                "gps_num": 12,
            }[k]
            mock_telemetry_rows.append(row)

        with patch("sqlite3.connect") as mock_connect:
            mock_conn = MagicMock()
            mock_cur = MagicMock()
            mock_cur.fetchone.return_value = mock_flight_row
            mock_cur.fetchall.return_value = mock_telemetry_rows
            mock_conn.cursor.return_value = mock_cur
            mock_connect.return_value = mock_conn

            r = client.get("/api/v1/flights/1")
            assert r.status_code == 200
            data = r.json()
            assert "flight" in data
            assert data["flight"]["id"] == 1
            assert "path" in data
            assert len(data["path"]) == 10
            assert "telemetry" in data
            assert "result" in data
            assert data["result"]["maxHeightM"] == 90.0
            assert data["result"]["batteryDrainedPct"] == 0.0

    def test_flight_with_telemetry_errors(self, client):
        with patch("sqlite3.connect", side_effect=Exception("DB error")):
            r = client.get("/api/v1/flights/1")
            assert r.status_code == 500
