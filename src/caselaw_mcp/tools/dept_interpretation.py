"""중앙부처 1차 법령해석 통합 검색·조회 (39개 부처 통합).

법제처 API target은 'cgmExpc<Dept>' 형태로 구성된다.
예: 고용노동부 → cgmExpcMoel*, 법무부 → cgmExpcMoj*

LLM이 부처명만 알면 자동 라우팅.
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.cache import Cache
from caselaw_mcp.client import CaseLawClient
from caselaw_mcp.codes import (
    CENTRAL_DEPT,
    resolve_central_dept,
    resolve_search_scope,
)
from caselaw_mcp.config import get_settings
from caselaw_mcp.parsers import extract_items

LIST_TTL = 60 * 60
DETAIL_TTL = None


def _key(*parts: Any) -> str:
    return "dept:" + ":".join(str(p) for p in parts if p is not None)


def _build_target(dept_short: str) -> str:
    """'moj' → 'cgmExpcMoj' 형태로 API target 생성."""
    suffix = CENTRAL_DEPT[dept_short]  # 'Moj'
    return f"cgmExpc{suffix}"


def _resolve_or_raise(dept: str) -> str:
    short = resolve_central_dept(dept)
    if short is None:
        raise ValueError(f"dept={dept!r} 인식 불가. 지원 약어: {sorted(CENTRAL_DEPT.keys())}")
    return short


async def search_central_dept_interpretation(
    dept: str,
    query: str,
    *,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """중앙부처 법령해석 목록 검색 (부처별 1차 해석)."""
    short = _resolve_or_raise(dept)
    target = _build_target(short)
    display = max(1, min(100, display))
    page = max(1, page)
    extra: dict[str, Any] = {"display": display, "page": page, "query": query}
    if date_from or date_to:
        extra["prncYd"] = (date_from or "") + "," + (date_to or "")
    if (scope := resolve_search_scope(search_scope)) is not None:
        extra["search"] = scope

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _key("search", short, query, date_from, date_to, scope, display, page)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.search(target=target, **extra)

    items = extract_items(normalized)
    result_obj = normalized.get("result") if isinstance(normalized.get("result"), dict) else {}
    response = {
        "dept": short,
        "items": items,
        "total_count": _safe_int(result_obj.get("total_count")),
        "page": _safe_int(result_obj.get("page")) or page,
        "query": query,
        "count": len(items),
    }
    await cache.set(key, response, ttl_seconds=LIST_TTL)
    return response


async def get_central_dept_interpretation(dept: str, doc_id: str | int) -> dict[str, Any]:
    """중앙부처 법령해석 본문 조회.

    참고: 일부 부처(재정경제부 moef, 국세청 nts)는 본문 조회 미지원 (가이드 표 기준).
    """
    short = _resolve_or_raise(dept)
    target = _build_target(short)
    did = str(doc_id).strip()
    if not did.isdigit():
        raise ValueError(f"doc_id 는 숫자여야 함: {did!r}")

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _key("detail", short, did)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.detail(target=target, doc_id=did)

    payload = _unwrap(normalized)
    payload["dept"] = short
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
