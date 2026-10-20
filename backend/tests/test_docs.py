from __future__ import annotations


def test_docs_returns_html(client):
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
