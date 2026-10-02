"""Smoke tests for the API."""
from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient) -> None:
    """The /health endpoint should return 200 with a status field."""
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "app" in body
    assert "version" in body


def test_list_tools_endpoint(client: TestClient) -> None:
    """The /api/v1/chat/tools endpoint should list default tools."""
    resp = client.get("/api/v1/chat/tools")
    assert resp.status_code == 200
    body = resp.json()
    assert "tools" in body
    assert body["count"] >= 5  # we register at least 5 default tools
    tool_names = [t["function"]["name"] for t in body["tools"]]
    assert "web_search" in tool_names
    assert "web_fetch" in tool_names
    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "run_python" in tool_names


def test_chat_requires_message(client: TestClient) -> None:
    """POST /api/v1/chat with no message should 422."""
    resp = client.post("/api/v1/chat", json={})
    assert resp.status_code == 422


def test_root_routes_loaded(client: TestClient) -> None:
    """The OpenAPI spec should expose our routes."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"].keys()
    assert "/health" in paths
    assert "/api/v1/chat" in paths
    assert "/api/v1/chat/tools" in paths
