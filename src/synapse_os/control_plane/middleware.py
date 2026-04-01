"""Authentication middleware for the Control Plane API."""

from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send


class AuthMiddleware:
    def __init__(self, app: ASGIApp, api_token: str | None) -> None:
        self.app = app
        self._api_token = api_token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self._api_token is None:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if path == "/health":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        auth_header = headers.get(b"authorization", b"").decode()
        if not auth_header.startswith("Bearer "):
            await _send_json(receive, send, 401, {"detail": "Unauthorized"})
            return

        token = auth_header[7:]
        if token != self._api_token:
            await _send_json(receive, send, 401, {"detail": "Unauthorized"})
            return

        await self.app(scope, receive, send)


async def _send_json(receive: Receive, send: Send, status: int, content: dict[str, object]) -> None:
    import json

    body = json.dumps(content).encode()
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
