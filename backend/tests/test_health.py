from unittest.mock import patch

from fastapi.testclient import TestClient


def _client() -> TestClient:
    with patch("app.main.ensure_index"):
        from app.main import app
        return TestClient(app)


def test_health_returns_ok():
    client = _client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_has_request_id_header():
    client = _client()
    response = client.get("/health")
    assert "x-request-id" in response.headers
    assert len(response.headers["x-request-id"]) > 0


def test_health_echoes_provided_request_id():
    client = _client()
    response = client.get("/health", headers={"x-request-id": "test-rid-123"})
    assert response.headers["x-request-id"] == "test-rid-123"


def test_unknown_route_returns_404_with_request_id():
    client = _client()
    response = client.get("/no-such-route")
    assert response.status_code == 404
    body = response.json()
    assert "request_id" in body
    assert "error" in body


def test_missing_auth_returns_401():
    client = _client()
    response = client.get("/api/personas")
    assert response.status_code == 401
    body = response.json()
    assert "error" in body
    assert "request_id" in body
