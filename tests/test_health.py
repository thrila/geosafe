from __future__ import annotations


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_returns_version(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert "version" in data

    def test_health_returns_environment(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert "environment" in data
