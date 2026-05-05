"""법제처 OpenAPI HTTP 클라이언트.

특징:
- 비동기 (httpx.AsyncClient)
- OC 자동 주입 + URL 마스킹 로깅 (시크릿 노출 방지)
- 429/5xx 지수 백오프 재시도 (tenacity)
- type=JSON 우선, XML fallback
- 간단한 rate limit (asyncio.Semaphore)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from caselaw_mcp.config import Settings, get_settings
from caselaw_mcp.parsers import parse_json, parse_xml

# 법제처 OpenAPI 베이스 URL
BASE_SEARCH = "https://www.law.go.kr/DRF/lawSearch.do"
BASE_SERVICE = "https://www.law.go.kr/DRF/lawService.do"

logger = logging.getLogger(__name__)

# httpx 자체 INFO 로그가 URL 전체(OC 키 포함)를 평문 노출하므로 silence.
# 디버깅이 필요한 사용자는 logging.getLogger("httpx").setLevel(logging.INFO) 로 override.
logging.getLogger("httpx").setLevel(logging.WARNING)


def _mask_oc(value: str, oc: str) -> str:
    """문자열에서 OC 키를 ***로 치환. 로그·에러 메시지에 사용."""
    if not oc:
        return value
    return value.replace(oc, "***OC***")


class CaseLawAPIError(Exception):
    """법제처 API 호출 실패."""

    def __init__(self, message: str, *, status: int | None = None, body: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class CaseLawClient:
    """법제처 OpenAPI 비동기 클라이언트.

    사용:
        async with CaseLawClient() as c:
            data = await c.search(target="prec", query="음주운전")
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.oc:
            raise CaseLawAPIError(
                "CASELAW_OC 환경변수 미설정. .env에 'CASELAW_OC=<본인 ID>' 추가 필요."
            )
        self._client: httpx.AsyncClient | None = None
        self._sem = asyncio.Semaphore(self.settings.rate_limit_per_sec)

    async def __aenter__(self) -> CaseLawClient:
        self._client = httpx.AsyncClient(
            timeout=self.settings.http_timeout,
            follow_redirects=True,
            headers={"User-Agent": "caselaw-mcp/0.0.1"},
        )
        return self

    async def __aexit__(self, *_exc: object) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ─────────────────────────────────────────
    # 공개 API
    # ─────────────────────────────────────────
    async def search(
        self,
        target: str,
        *,
        query: str | None = None,
        prefer_json: bool = True,
        **extra: Any,
    ) -> dict[str, Any]:
        """목록 조회 (lawSearch.do).

        Args:
            target: 'prec' | 'law' | 'detc' | 'expc' | 'decc' | ...
            query: 검색어
            prefer_json: True 면 type=JSON 시도, 실패 시 XML fallback
            **extra: display, page, prncYd, curt 등 그대로 전달
        """
        params = self._build_params(target=target, query=query, **extra)
        return await self._call(BASE_SEARCH, params, prefer_json=prefer_json)

    async def detail(
        self,
        target: str,
        *,
        doc_id: str | int,
        prefer_json: bool = True,
        **extra: Any,
    ) -> dict[str, Any]:
        """본문 조회 (lawService.do).

        Args:
            target: 'prec' | 'law' | 'detc' | ...
            doc_id: 일련번호 (정수 문자열)
            prefer_json: True 면 type=JSON 우선
        """
        params = self._build_params(target=target, ID=str(doc_id), **extra)
        return await self._call(BASE_SERVICE, params, prefer_json=prefer_json)

    # ─────────────────────────────────────────
    # 내부
    # ─────────────────────────────────────────
    def _build_params(self, **kwargs: Any) -> dict[str, Any]:
        """OC 자동 주입 + None 값 제거."""
        params: dict[str, Any] = {"OC": self.settings.oc}
        for k, v in kwargs.items():
            if v is None:
                continue
            params[k] = v
        return params

    async def _call(
        self, url: str, params: dict[str, Any], *, prefer_json: bool
    ) -> dict[str, Any]:
        """JSON 우선 + XML fallback + 재시도."""
        if prefer_json:
            try:
                return await self._call_with_type(url, params, content_type="JSON")
            except CaseLawAPIError as e:
                # JSON 미지원 엔드포인트일 가능성 → XML 재시도
                logger.warning(
                    "JSON 호출 실패 → XML fallback 시도: %s",
                    _mask_oc(str(e), self.settings.oc),
                )
        return await self._call_with_type(url, params, content_type="XML")

    async def _call_with_type(
        self, url: str, params: dict[str, Any], *, content_type: str
    ) -> dict[str, Any]:
        params = {**params, "type": content_type}
        if self._client is None:
            raise CaseLawAPIError("Client not opened. 'async with CaseLawClient()' 사용 필요.")
        client = self._client
        oc = self.settings.oc

        async def _request() -> httpx.Response:
            async with self._sem:
                resp = await client.get(url, params=params)
                # 4xx 중 403/404 는 재시도 의미 없음
                if resp.status_code in (429,) or 500 <= resp.status_code < 600:
                    resp.raise_for_status()
                return resp

        # TLS handshake / connect 단계 실패는 Python 3.14 + httpx async 조합에서
        # 첫 호출 시 종종 발생 → ConnectError·TimeoutException 도 retry 대상.
        retryable = (
            httpx.HTTPStatusError,
            httpx.ConnectError,
            httpx.ConnectTimeout,
            httpx.ReadTimeout,
            httpx.RemoteProtocolError,
        )
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(5),
                wait=wait_exponential(multiplier=1, min=1, max=8),
                retry=retry_if_exception_type(retryable),
                reraise=True,
            ):
                with attempt:
                    response = await _request()
        except RetryError as e:
            raise CaseLawAPIError(f"재시도 한도 초과: {e}") from e

        # 마스킹된 URL을 로그에
        logger.info(
            "GET %s -> %d", _mask_oc(str(response.request.url), oc), response.status_code
        )

        if response.status_code >= 400:
            raise CaseLawAPIError(
                f"HTTP {response.status_code}",
                status=response.status_code,
                body=_mask_oc(response.text[:500], oc),
            )

        # 빈 응답(법제처가 일부 target 에 200 + 0 bytes 반환) → 정상 빈 결과로 변환
        if not response.content or not response.text.strip():
            logger.info("빈 응답(0 bytes) 수신 → empty result 로 처리")
            return {"result": {"items": [], "total_count": 0, "empty_response": True}}

        # 응답 파싱
        ct = response.headers.get("content-type", "").lower()
        if "json" in ct or content_type == "JSON":
            try:
                return parse_json(response.json())
            except ValueError as e:
                raise CaseLawAPIError(
                    f"JSON 파싱 실패 (응답이 JSON 아님): {_mask_oc(response.text[:300], oc)}"
                ) from e
        return parse_xml(response.text)
