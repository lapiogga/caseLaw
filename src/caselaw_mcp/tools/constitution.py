"""헌법재판소 결정례 검색·조회 (헌재결정례).

법제처 OpenAPI:
- 목록: target=detc (detcListGuide)
- 본문: target=detc, ID=<결정례일련번호> (detcInfoGuide)
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.cache import Cache
from caselaw_mcp.client import CaseLawClient
from caselaw_mcp.codes import resolve_search_scope
from caselaw_mcp.config import get_settings
from caselaw_mcp.parsers import extract_items

LIST_TTL = 60 * 60
DETAIL_TTL = None  # 결정문 불변


def _key(*parts: Any) -> str:
    return "detc:" + ":".join(str(p) for p in parts if p is not None)


async def search_constitutional_decision(
    query: str,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """헌법재판소 결정례 목록 검색.

    Args:
        query: 검색어 (사건명·요지·전문)
        date_from / date_to: 결정일자 범위 YYYYMMDD
        search_scope: "title"/"body"
        display, page
    """
    display = max(1, min(100, display))
    page = max(1, page)
    extra: dict[str, Any] = {"display": display, "page": page, "query": query}
    if date_from or date_to:
        extra["prncYd"] = (date_from or "") + "," + (date_to or "")
    if (scope := resolve_search_scope(search_scope)) is not None:
        extra["search"] = scope

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _key("search", query, date_from, date_to, scope, display, page)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.search(target="detc", **extra)

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


async def get_constitutional_decision(detc_id: str | int) -> dict[str, Any]:
    """헌재결정례 본문 조회. detc_id = search_constitutional_decision 의 결정례일련번호."""
    did = str(detc_id).strip()
    if not did.isdigit():
        raise ValueError(f"detc_id 는 숫자여야 함: {did!r}")

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _key("detail", did)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.detail(target="detc", doc_id=did)

    payload = _unwrap(normalized)
    payload["detc_id"] = did
    await cache.set(key, payload, ttl_seconds=DETAIL_TTL)
    return payload


def _unwrap(normalized: dict[str, Any]) -> dict[str, Any]:
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
