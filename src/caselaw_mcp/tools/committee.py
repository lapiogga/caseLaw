"""위원회 결정문 통합 검색·조회 (12종 위원회).

LLM이 enum 1개로 라우팅 가능하도록 단일 tool 패턴.
지원 위원회: ppc(개인정보보호), eiac(고용보험심사), ftc(공정거래),
            acr(국민권익), fsc(금융), nlrc(노동), kcc(방송미디어통신),
            iaciac(산재보상재심사), oclt(중앙토지수용),
            ecc(중앙환경분쟁조정), sfc(증권선물), nhrck(국가인권)
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.cache import Cache
from caselaw_mcp.client import CaseLawClient
from caselaw_mcp.codes import COMMITTEE, resolve_committee, resolve_search_scope
from caselaw_mcp.config import get_settings
from caselaw_mcp.parsers import extract_items

LIST_TTL = 60 * 60
DETAIL_TTL = None


def _key(*parts: Any) -> str:
    return "cmt:" + ":".join(str(p) for p in parts if p is not None)


def _resolve_or_raise(committee: str) -> str:
    target = resolve_committee(committee)
    if target is None:
        raise ValueError(f"committee={committee!r} 인식 불가. 지원: {sorted(COMMITTEE.keys())}")
    return target


async def search_committee_decision(
    committee: str,
    query: str,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """위원회 결정문 목록 검색.

    Args:
        committee: "ppc"/"ftc"/"공정거래"/"공정위" 등 — 한·영 모두 허용
        query: 검색어
        date_from / date_to: YYYYMMDD
        search_scope: "title"/"body"
        display, page
    """
    target = _resolve_or_raise(committee)
    display = max(1, min(100, display))
    page = max(1, page)
    extra: dict[str, Any] = {"display": display, "page": page, "query": query}
    if date_from or date_to:
        extra["prncYd"] = (date_from or "") + "," + (date_to or "")
    if (scope := resolve_search_scope(search_scope)) is not None:
        extra["search"] = scope

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _key("search", target, query, date_from, date_to, scope, display, page)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.search(target=target, **extra)

    items = extract_items(normalized)
    result_obj = normalized.get("result") if isinstance(normalized.get("result"), dict) else {}
    response = {
        "committee": target,
        "items": items,
        "total_count": _safe_int(result_obj.get("total_count")),
        "page": _safe_int(result_obj.get("page")) or page,
        "query": query,
        "count": len(items),
    }
    await cache.set(key, response, ttl_seconds=LIST_TTL)
    return response


async def get_committee_decision(committee: str, doc_id: str | int) -> dict[str, Any]:
    """위원회 결정문 본문 조회."""
    target = _resolve_or_raise(committee)
    did = str(doc_id).strip()
    if not did.isdigit():
        raise ValueError(f"doc_id 는 숫자여야 함: {did!r}")

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _key("detail", target, did)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.detail(target=target, doc_id=did)

    payload = _unwrap(normalized)
    payload["committee"] = target
    payload["doc_id"] = did
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
