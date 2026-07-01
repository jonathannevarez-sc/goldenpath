"""API key gate for hosted MCP transports (SSE / streamable-http)."""

from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp


def _request_has_api_key(request: Request, api_key: str) -> bool:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return secrets.compare_digest(auth[7:].strip(), api_key)

    header = request.headers.get("x-mcp-api-key", "")
    if header:
        return secrets.compare_digest(header.strip(), api_key)

    return False


class ApiKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, api_key: str) -> None:
        super().__init__(app)
        self._api_key = api_key

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path == "/health":
            return await call_next(request)
        if not _request_has_api_key(request, self._api_key):
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


def wrap_with_api_key(app: Starlette, api_key: str) -> Starlette:
    app.add_middleware(ApiKeyMiddleware, api_key=api_key)
    return app