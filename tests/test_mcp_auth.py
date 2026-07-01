"""Tests for mcp/goldenpath_mcp/auth.py."""

from __future__ import annotations

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from goldenpath_mcp.auth import wrap_with_api_key


def _make_app() -> Starlette:
    async def health(_: Request) -> PlainTextResponse:
        return PlainTextResponse("ok")

    async def secret(_: Request) -> PlainTextResponse:
        return PlainTextResponse("secret")

    app = Starlette(
        routes=[
            Route("/health", health),
            Route("/mcp", secret),
        ]
    )
    return wrap_with_api_key(app, "test-api-key")


@pytest.fixture
def client() -> TestClient:
    return TestClient(_make_app())


def test_health_bypasses_auth(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.text == "ok"


def test_missing_api_key_returns_401(client: TestClient) -> None:
    response = client.get("/mcp")
    assert response.status_code == 401
    assert response.json() == {"error": "unauthorized"}


def test_invalid_api_key_returns_401(client: TestClient) -> None:
    response = client.get(
        "/mcp",
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code == 401


def test_bearer_token_allows_access(client: TestClient) -> None:
    response = client.get("/mcp", headers={"Authorization": "Bearer test-api-key"})
    assert response.status_code == 200
    assert response.text == "secret"


def test_x_mcp_api_key_header_allows_access(client: TestClient) -> None:
    response = client.get("/mcp", headers={"X-MCP-API-Key": "test-api-key"})
    assert response.status_code == 200