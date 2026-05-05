"""법령 검색·조회 MCP tool 구현부.

법제처 OpenAPI:
- 목록: target=law (lsEfYdListGuide — 현행법령 시행일 기준)
- 본문: target=law, ID=<법령일련번호> 또는 LM=<법령명> (lsEfYdInfoGuide)
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.cache import Cache
from caselaw_mcp.client import CaseLawClient
from caselaw_mcp.codes import resolve_search_scope
from caselaw_mcp.config import get_settings
from caselaw_mcp.parsers import extract_items

LIST_TTL = 60 * 60  # 1시간
DETAIL_TTL = 60 * 60 * 24 * 30  # 30일 (법령은 개정 시 변경)


def _cache_key(*parts: Any) -> str:
    return "law:" + ":".join(str(p) for p in parts if p is not None)


async def search_statute(
    query: str,
    *,
    effective_date: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """현행법령 목록 검색 (시행일 기준).

    Args:
        query: 법령명 또는 키워드
        effective_date: 시행일자 기준 (YYYYMMDD), 미설정 시 현재
        search_scope: "title" / "body"
        display: 1~100
        page: 1부터

    Returns:
        {"items": [{"law_id", "law_name", "promulgation_date",
                    "effective_date", "ministry", "detail_url", ...}, ...],
         "total_count", "page", "query", "count"}
    """
    display = max(1, min(100, display))
    page = max(1, page)

    extra: dict[str, Any] = {
        "display": display,
        "page": page,
        "query": query,
    }
    if effective_date:
        extra["efYd"] = effective_date
    if (scope := resolve_search_scope(search_scope)) is not None:
        extra["search"] = scope

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _cache_key("search", query, effective_date, scope, display, page)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.search(target="law", **extra)

    items = extract_items(normalized)
    result_obj = normalized.get("result") if isinstance(normalized.get("result"), dict) else {}
    response = {
        "items": items,
        "total_count": _safe_int(result_obj.get("total_count")),
        "page": _safe_int(result_obj.get("page")) or page,
        "query": query,
        "count": len(items),
    }
    await cache.set(key, response, ttl_seconds=LIST_TTL)
    return response


async def get_statute(
    law_id: str | int | None = None,
    *,
    law_name: str | None = None,
) -> dict[str, Any]:
    """법령 본문 조회.

    Args:
        law_id: 법령일련번호 (정확). search_statute 결과의 'law_id'
        law_name: 법령명 (id 모를 때)

    하나만 지정. 둘 다 없으면 ValueError.
    """
    if not law_id and not law_name:
        raise ValueError("law_id 또는 law_name 중 하나 필수")

    settings = get_settings()
    cache = Cache(settings.cache_path)

    extra: dict[str, Any] = {}
    if law_id is not None:
        lid = str(law_id).strip()
        if not lid.isdigit():
            raise ValueError(f"law_id 는 숫자여야 함: {lid!r}")
        cache_key = _cache_key("detail", "id", lid)
        kwargs = {"doc_id": lid}
    else:
        lname = str(law_name).strip()
        cache_key = _cache_key("detail", "name", lname)
        # law_name 사용 시 ID 대신 LM 파라미터
        kwargs = {"doc_id": "0", "LM": lname}  # type: ignore[assignment]

    if (cached := await cache.get(cache_key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.detail(target="law", **kwargs, **extra)

    payload = _unwrap_detail(normalized)
    if law_id is not None:
        payload["law_id"] = lid
    await cache.set(cache_key, payload, ttl_seconds=DETAIL_TTL)
    return payload


def _unwrap_detail(normalized: dict[str, Any]) -> dict[str, Any]:
    if "result" in normalized and isinstance(normalized["result"], dict):
        return normalized["result"]
    if len(normalized) == 1:
        only = next(iter(normalized.values()))
        if isinstance(only, dict):
            return only
    return normalized


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
