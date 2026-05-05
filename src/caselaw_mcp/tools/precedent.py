"""판례 검색·조회 MCP tool 구현부.

법제처 OpenAPI:
- 목록: target=prec  (precListGuide)
- 본문: target=prec, ID=<판례일련번호>  (precInfoGuide)
"""

from __future__ import annotations

import re
from typing import Any

from caselaw_mcp.cache import Cache
from caselaw_mcp.client import CaseLawClient
from caselaw_mcp.codes import resolve_case_type, resolve_court, resolve_search_scope
from caselaw_mcp.config import get_settings
from caselaw_mcp.parsers import extract_items

# 캐시 TTL (초)
LIST_TTL = 60 * 60  # 1시간
DETAIL_TTL = None  # 영구 (판례 본문 불변)


def _cache_key(*parts: Any) -> str:
    return "prec:" + ":".join(str(p) for p in parts if p is not None)


async def search_precedent(
    query: str,
    *,
    court: str | None = None,
    case_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """판례 목록 검색.

    Args:
        query: 검색어 (사건명·요지·전문 중 search_scope 에 따라)
        court: 법원명 (예: "대법원", "supreme", "고등법원"). None=전체
        case_type: 사건종류 ("형사"/"criminal"/"400102" 등). None=전체
        date_from: 선고일자 시작 (YYYYMMDD)
        date_to: 선고일자 종료 (YYYYMMDD)
        search_scope: "title"(사건명) 또는 "body"(본문). 기본 사건명+본문 통합
        display: 1회 응답 건수 (1~100, 기본 20)
        page: 페이지 (1부터)

    Returns:
        {
            "items": [{"prec_id", "case_number", "court", "case_name",
                       "case_type", "judgment_date", "detail_url", ...}, ...],
            "total_count": int (가능 시),
            "page": int,
            "query": str,
        }
    """
    display = max(1, min(100, display))
    page = max(1, page)

    extra: dict[str, Any] = {
        "display": display,
        "page": page,
        "query": query,
    }
    if (court_name := resolve_court(court)) is not None:
        extra["curt"] = court_name
    if (ct_code := resolve_case_type(case_type)) is not None:
        extra["nb"] = ct_code  # 법제처 표기 — 실호출 검증으로 보정 가능
    if date_from:
        extra["prncYd"] = date_from + ("," + date_to if date_to else "")
    elif date_to:
        extra["prncYd"] = "," + date_to
    if (scope := resolve_search_scope(search_scope)) is not None:
        extra["search"] = scope

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _cache_key(
        "search",
        query,
        court_name,
        ct_code,
        date_from,
        date_to,
        scope,
        display,
        page,
    )
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.search(target="prec", **extra)

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


async def get_precedent(prec_id: str | int) -> dict[str, Any]:
    """판례 본문 조회.

    Args:
        prec_id: 판례일련번호 (search_precedent 결과의 'prec_id')

    Returns:
        판시사항·판결요지·참조조문·참조판례·전문 포함 dict
    """
    pid = str(prec_id).strip()
    if not pid.isdigit():
        raise ValueError(f"prec_id 는 숫자여야 함: {pid!r}")

    settings = get_settings()
    cache = Cache(settings.cache_path)
    key = _cache_key("detail", pid)
    if (cached := await cache.get(key)) is not None:
        return cached

    async with CaseLawClient(settings) as client:
        normalized = await client.detail(target="prec", doc_id=pid)

    # 본문은 result 안의 단일 객체이거나 PrecService 키일 수 있음
    payload = _unwrap_detail(normalized)
    payload["prec_id"] = pid
    await cache.set(key, payload, ttl_seconds=DETAIL_TTL)
    return payload


def _unwrap_detail(normalized: dict[str, Any]) -> dict[str, Any]:
    """본문 응답에서 의미 있는 layer 만 추출."""
    # 정규화 후 원본 한국어 최상위 키 (PrecService 등) 가 그대로 남기도 한다.
    if "result" in normalized and isinstance(normalized["result"], dict):
        return normalized["result"]
    # 단일 키만 있는 경우 (xmltodict 결과) 그 안쪽으로
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


# ─────────────────────────────────────────────
# 관련 판례 추천
# ─────────────────────────────────────────────
async def find_related_precedents(
    prec_id: str | int,
    *,
    max_items: int = 10,
) -> dict[str, Any]:
    """판례 본문의 '참조판례' 필드 + 사건명 키워드로 관련 판례 추천.

    Args:
        prec_id: 시작 판례
        max_items: 최대 반환 건수 (기본 10)

    Returns:
        {
            "source_prec_id": str,
            "referenced_text": str,    # 본문에 적힌 참조판례 텍스트 (가공 전)
            "referenced_cases": list[str],  # 추출된 사건번호들
            "candidates": [{"case_number","prec_id","court","judgment_date","case_name","source"}, ...]
        }
        source: "referenced" (본문에 명시된 참조판례) | "keyword" (사건명 키워드 검색)
    """
    detail = await get_precedent(prec_id)
    referenced_text = str(detail.get("referenced_precedents") or "")
    referenced_cases = _extract_case_numbers(referenced_text)

    candidates: list[dict[str, Any]] = []
    seen_prec_ids: set[str] = set()

    # 1) 명시적 참조판례 검색
    for case_no in referenced_cases:
        if len(candidates) >= max_items:
            break
        try:
            r = await search_precedent(case_no, display=3)
        except Exception:
            continue
        for item in r["items"]:
            pid = str(item.get("prec_id") or "")
            if not pid or pid in seen_prec_ids or pid == str(prec_id):
                continue
            candidates.append(
                {
                    "case_number": item.get("case_number"),
                    "prec_id": pid,
                    "court": item.get("court"),
                    "judgment_date": item.get("judgment_date"),
                    "case_name": item.get("case_name"),
                    "source": "referenced",
                }
            )
            seen_prec_ids.add(pid)

    # 2) 사건명 키워드 검색 (보조)
    case_name = str(detail.get("case_name") or "")
    keyword = _extract_keyword(case_name)
    if keyword and len(candidates) < max_items:
        try:
            r = await search_precedent(keyword, display=max_items)
            for item in r["items"]:
                if len(candidates) >= max_items:
                    break
                pid = str(item.get("prec_id") or "")
                if not pid or pid in seen_prec_ids or pid == str(prec_id):
                    continue
                candidates.append(
                    {
                        "case_number": item.get("case_number"),
                        "prec_id": pid,
                        "court": item.get("court"),
                        "judgment_date": item.get("judgment_date"),
                        "case_name": item.get("case_name"),
                        "source": "keyword",
                    }
                )
                seen_prec_ids.add(pid)
        except Exception:
            pass

    return {
        "source_prec_id": str(prec_id),
        "referenced_text": referenced_text,
        "referenced_cases": referenced_cases,
        "candidates": candidates[:max_items],
        "count": len(candidates[:max_items]),
    }


_CASE_NUMBER_RE = re.compile(r"\d{2,4}[가-힣]{1,3}\d{1,8}")


def _extract_case_numbers(text: str) -> list[str]:
    """'2004도4869' '2018헌바8' 같은 사건번호 추출 (중복 제거, 순서 유지)."""
    seen: set[str] = set()
    out: list[str] = []
    for m in _CASE_NUMBER_RE.findall(text or ""):
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


def _extract_keyword(case_name: str) -> str | None:
    """사건명 첫 괄호 [...] 또는 첫 토큰을 키워드로 추출."""
    if not case_name:
        return None
    # '[...]' 안 첫 단어
    if (start := case_name.find("[")) >= 0 and (end := case_name.find("]", start)) > start:
        inner = case_name[start + 1 : end].strip()
        if inner:
            return inner.split()[0]
    # 첫 한국어 단어 (특수문자 제외)
    for token in case_name.replace("·", " ").replace("(", " ").split():
        if token and any("가" <= c <= "힣" for c in token):
            return token
    return None
