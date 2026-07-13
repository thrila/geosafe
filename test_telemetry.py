# test_telemetry.py
from database.connector import FlightDB

with FlightDB("telemetry.db") as db:
    flight = db.flight(1)
    print(flight)
    print(flight.battery_drain())
    print(flight.track())
