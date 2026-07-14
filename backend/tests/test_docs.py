from __future__ import annotations


class TestDocEndpoint:
    def test_docs_returns_200(self, client):
        response = client.get("/docs")
        assert response.status_code == 200

    def test_docs_returns_html(self, client):
        response = client.get("/docs")
        assert "text/html" in response.headers["content-type"]
