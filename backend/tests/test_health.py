from __future__ import annotations


def test_health_response_contract(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"]
    assert data["environment"]
