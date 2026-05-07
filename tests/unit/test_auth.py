"""Bearer 토큰 ASGI 미들웨어 단위 테스트."""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from typing import Any
from unittest.mock import patch

import pytest

from caselaw_mcp.auth import BearerAuthMiddleware, get_auth_token


# ─────────────────────────────────────────────
# 도우미: ASGI mock
# ─────────────────────────────────────────────
class _DummyApp:
    """미들웨어가 통과시킬 때 호출되는 inner ASGI app."""

    def __init__(self) -> None:
        self.called = False

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Callable[[], Awaitable[dict[str, Any]]],
        send: Callable[[dict[str, Any]], Awaitable[None]],
    ) -> None:
        self.called = True
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"ok", "more_body": False})


def _http_scope(authorization: str | None = None) -> dict[str, Any]:
    headers: list[tuple[bytes, bytes]] = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode("latin-1")))
    return {"type": "http", "headers": headers, "method": "POST", "path": "/mcp"}


async def _noop_receive() -> dict[str, Any]:
    return {"type": "http.request", "body": b"", "more_body": False}


class _Sink:
    """send 호출을 수집."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    async def __call__(self, event: dict[str, Any]) -> None:
        self.events.append(event)


# ─────────────────────────────────────────────
# get_auth_token
# ─────────────────────────────────────────────
def test_get_auth_token_unset_returns_none() -> None:
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("CASELAW_AUTH_TOKEN", None)
        assert get_auth_token() is None


def test_get_auth_token_empty_string_returns_none() -> None:
    with patch.dict(os.environ, {"CASELAW_AUTH_TOKEN": "   "}):
        assert get_auth_token() is None


def test_get_auth_token_set_returns_value() -> None:
    with patch.dict(os.environ, {"CASELAW_AUTH_TOKEN": "secret-abc"}):
        assert get_auth_token() == "secret-abc"


# ─────────────────────────────────────────────
# BearerAuthMiddleware — 인증 비활성
# ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_passthrough_when_token_unset() -> None:
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token=None)
    sink = _Sink()
    await mw(_http_scope(), _noop_receive, sink)
    assert inner.called is True
    assert sink.events[0]["status"] == 200


@pytest.mark.asyncio
async def test_passthrough_when_token_empty_string() -> None:
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="")
    sink = _Sink()
    await mw(_http_scope(), _noop_receive, sink)
    assert inner.called is True


# ─────────────────────────────────────────────
# BearerAuthMiddleware — 인증 활성
# ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_valid_bearer_passes() -> None:
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret-123")
    sink = _Sink()
    await mw(_http_scope("Bearer secret-123"), _noop_receive, sink)
    assert inner.called is True
    assert sink.events[0]["status"] == 200


@pytest.mark.asyncio
async def test_missing_authorization_header_rejects() -> None:
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret-123")
    sink = _Sink()
    await mw(_http_scope(authorization=None), _noop_receive, sink)
    assert inner.called is False
    assert sink.events[0]["status"] == 401
    assert b"unauthorized" in sink.events[1]["body"]


@pytest.mark.asyncio
async def test_wrong_token_rejects() -> None:
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret-123")
    sink = _Sink()
    await mw(_http_scope("Bearer wrong-token"), _noop_receive, sink)
    assert inner.called is False
    assert sink.events[0]["status"] == 401


@pytest.mark.asyncio
async def test_non_bearer_scheme_rejects() -> None:
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret-123")
    sink = _Sink()
    await mw(_http_scope("Basic dXNlcjpwYXNz"), _noop_receive, sink)
    assert inner.called is False
    assert sink.events[0]["status"] == 401


@pytest.mark.asyncio
async def test_case_insensitive_bearer_keyword() -> None:
    """`bearer ` (소문자) 도 RFC 6750 기준 허용."""
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret-123")
    sink = _Sink()
    await mw(_http_scope("bearer secret-123"), _noop_receive, sink)
    assert inner.called is True


@pytest.mark.asyncio
async def test_lifespan_scope_passes_through() -> None:
    """ASGI lifespan 메시지(http 가 아닌 type)는 인증 없이 통과 — Starlette 시작 필수."""
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret-123")
    sink = _Sink()
    lifespan_scope = {"type": "lifespan"}
    await mw(lifespan_scope, _noop_receive, sink)
    assert inner.called is True


@pytest.mark.asyncio
async def test_401_response_includes_www_authenticate() -> None:
    inner = _DummyApp()
    mw = BearerAuthMiddleware(inner, expected_token="secret-123")
    sink = _Sink()
    await mw(_http_scope(), _noop_receive, sink)
    headers = dict(sink.events[0]["headers"])
    assert headers.get(b"www-authenticate", b"").startswith(b"Bearer")
