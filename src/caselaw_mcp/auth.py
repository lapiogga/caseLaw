"""HTTP transport용 Bearer 토큰 인증 ASGI 미들웨어.

`CASELAW_AUTH_TOKEN` 환경변수가 설정되어 있으면 모든 HTTP 요청의
`Authorization: Bearer <token>` 헤더를 검증한다.

미설정 시 인증을 비활성 (로컬 개발·신뢰 네트워크 한정).
미들웨어는 stdio transport 에는 적용되지 않는다 (HTTP 분기에서만 wrap).
"""

from __future__ import annotations

import os
import secrets
from collections.abc import Awaitable, Callable
from typing import Any

ASGIScope = dict[str, Any]
ASGIReceive = Callable[[], Awaitable[dict[str, Any]]]
ASGISend = Callable[[dict[str, Any]], Awaitable[None]]
ASGIApp = Callable[[ASGIScope, ASGIReceive, ASGISend], Awaitable[None]]


class BearerAuthMiddleware:
    """Bearer 토큰 검증 ASGI 미들웨어.

    - `expected_token` 이 None/빈 문자열 → 모든 요청 통과 (인증 비활성)
    - 설정 시 `Authorization: Bearer <expected_token>` 일치만 통과, 그 외 401
    - 비교는 `secrets.compare_digest` 로 타이밍 공격 방어
    """

    def __init__(self, app: ASGIApp, expected_token: str | None) -> None:
        self.app = app
        self._expected = (expected_token or "").strip() or None

    async def __call__(
        self,
        scope: ASGIScope,
        receive: ASGIReceive,
        send: ASGISend,
    ) -> None:
        if self._expected is None or scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        provided = self._extract_bearer(scope)
        if provided is None or not secrets.compare_digest(provided, self._expected):
            await self._reject(send)
            return

        await self.app(scope, receive, send)

    @staticmethod
    def _extract_bearer(scope: ASGIScope) -> str | None:
        for name, value in scope.get("headers", []):
            if name == b"authorization":
                raw = value.decode("latin-1", errors="replace")
                if raw.lower().startswith("bearer "):
                    return raw[7:].strip()
                return None
        return None

    @staticmethod
    async def _reject(send: ASGISend) -> None:
        body = b'{"error":"unauthorized","message":"missing or invalid bearer token"}'
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"www-authenticate", b'Bearer realm="caselaw-mcp"'),
                    (b"content-length", str(len(body)).encode("ascii")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body, "more_body": False})


def get_auth_token() -> str | None:
    """환경변수에서 인증 토큰 조회. 빈 문자열은 None 으로 정규화."""
    token = os.environ.get("CASELAW_AUTH_TOKEN", "").strip()
    return token or None
