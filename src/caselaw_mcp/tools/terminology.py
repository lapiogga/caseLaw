"""법령용어 사전 검색·조회.

법제처 OpenAPI:
- 목록: target=lstrm (lsTrmListGuide)
- 본문: target=lstrm, ID=<용어일련번호> (lsTrmInfoGuide)
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.cache import Cache
from caselaw_mcp.client import CaseLawClient
from caselaw_mcp.config import get_settings
from caselaw_mcp.parsers import extract_items

LIST_TTL = 60 * 60 * 24  # 용어는 자주 안 바뀜 → 24시간 TTL
DETAIL_TTL = None


def _key(*parts: Any) -> str:
    return "trm:" + ":".join(str(p) for p in parts if p is not None)


async def search_legal_term(
    query: str,
    *,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """법령용어 사전 검색."""
    display = max(1, min(100, display))
    page = max(1, page)
    extra: dict[str, Any] = {"display": display, "page": page, "query": query}

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _key("search", query, display, page)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.search(target="lstrm", **extra)

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


async def get_legal_term(term_id: str | int) -> dict[str, Any]:
    """법령용어 본문 조회."""
    tid = str(term_id).strip()
    if not tid.isdigit():
        raise ValueError(f"term_id 는 숫자여야 함: {tid!r}")

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _key("detail", tid)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.detail(target="lstrm", doc_id=tid)

    payload = _unwrap(normalized)
    payload["term_id"] = tid
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
