from __future__ import annotations


class TestHealth:
    def test_health_returns_200(self, client):
        r = client.get("/api/v1/health")
        assert r.status_code == 200

    def test_health_has_status_ok(self, client):
        r = client.get("/api/v1/health")
        data = r.json()
        assert data["status"] == "ok"

    def test_health_has_version(self, client):
        r = client.get("/api/v1/health")
        assert "version" in r.json()

    def test_health_has_environment(self, client):
        r = client.get("/api/v1/health")
        assert "environment" in r.json()
