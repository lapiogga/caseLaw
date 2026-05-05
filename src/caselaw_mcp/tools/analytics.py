"""판례 통계·분석 helper.

LLM이 자연어로 "최근 3년 음주운전 양형 분포" 라고 물으면,
search_precedent + 본 통계 함수가 결합되어 표·트렌드 응답.

데이터 가공만 담당 (네트워크 호출은 search_precedent 위임).
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any, Literal

from caselaw_mcp.tools.precedent import search_precedent

GroupBy = Literal["year", "month", "court", "case_type", "instance"]


async def analyze_precedent_trend(
    query: str,
    *,
    group_by: GroupBy = "year",
    court: str | None = None,
    case_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sample_size: int = 100,
) -> dict[str, Any]:
    """판례 결과를 그룹별로 카운트해 트렌드 반환.

    Args:
        query: 검색어
        group_by: 'year' / 'month' / 'court' / 'case_type' / 'instance'
        court, case_type, date_from, date_to: search_precedent 와 동일
        sample_size: 분석에 사용할 최대 판례 수 (1~100, 기본 100)

    Returns:
        {
            "query": str,
            "group_by": str,
            "total_analyzed": int,        # 실제 분석한 건수
            "total_available": int|None,  # API total_count
            "distribution": [{"key": "2025", "count": 32}, ...],  # 내림차순
            "items_sample": [...],        # 분석 원본 (앞 5건)
        }
    """
    sample_size = max(1, min(100, sample_size))
    response = await search_precedent(
        query,
        court=court,
        case_type=case_type,
        date_from=date_from,
        date_to=date_to,
        display=sample_size,
    )
    items = response.get("items", [])
    counter: Counter[str] = Counter()
    for it in items:
        key = _extract_group_key(it, group_by)
        if key:
            counter[key] += 1

    distribution = [{"key": k, "count": c} for k, c in counter.most_common()]
    return {
        "query": query,
        "group_by": group_by,
        "total_analyzed": len(items),
        "total_available": response.get("total_count"),
        "distribution": distribution,
        "items_sample": items[:5],
    }


_DATE_RE = re.compile(r"(\d{4})[.\-/]?(\d{2})?[.\-/]?(\d{2})?")


def _extract_group_key(item: dict[str, Any], group_by: GroupBy) -> str | None:
    if group_by == "year":
        return _parse_year(str(item.get("judgment_date") or ""))
    if group_by == "month":
        return _parse_year_month(str(item.get("judgment_date") or ""))
    if group_by == "court":
        return str(item.get("court") or "").strip() or None
    if group_by == "case_type":
        return str(item.get("case_type") or "").strip() or None
    if group_by == "instance":
        return str(item.get("instance") or "").strip() or None
    return None


def _parse_year(date_str: str) -> str | None:
    if not date_str:
        return None
    m = _DATE_RE.match(date_str.strip())
    return m.group(1) if m else None


def _parse_year_month(date_str: str) -> str | None:
    if not date_str:
        return None
    m = _DATE_RE.match(date_str.strip())
    if not m:
        return None
    y = m.group(1)
    mm = m.group(2)
    return f"{y}-{mm}" if mm else y


# ─────────────────────────────────────────────
# 정식 인용 형식 변환
# ─────────────────────────────────────────────
async def format_citation(prec_id: str | int) -> dict[str, Any]:
    """판례를 한국 법률 표준 인용 형식으로 변환.

    예: "대법원 2025. 1. 29. 선고 2025도15970 판결"
        "헌법재판소 2019. 2. 28. 선고 2018헌바8 전원재판부 결정"

    Args:
        prec_id: 판례일련번호

    Returns:
        {"prec_id", "case_number", "court", "judgment_date",
         "citation": "대법원 YYYY. M. D. 선고 사건번호 판결",
         "short_citation": "대법원 2025도15970"}
    """
    from caselaw_mcp.tools.precedent import get_precedent

    detail = await get_precedent(prec_id)
    court = (detail.get("court") or "").strip()
    case_no = (detail.get("case_number") or "").strip()
    raw_date = str(detail.get("judgment_date") or "").strip()
    decision_type = (detail.get("decision_type") or "판결").strip()

    formatted_date = _format_korean_date(raw_date)
    citation = (
        f"{court} {formatted_date} 선고 {case_no} {decision_type}".strip()
        if formatted_date and case_no
        else f"{court} {case_no} {decision_type}".strip()
    )
    short = f"{court} {case_no}".strip()
    return {
        "prec_id": str(prec_id),
        "case_number": case_no,
        "court": court,
        "judgment_date": raw_date,
        "decision_type": decision_type,
        "citation": citation,
        "short_citation": short,
    }


def _format_korean_date(date_str: str) -> str | None:
    """'20260129' 또는 '2026.01.29' → '2026. 1. 29.'."""
    if not date_str:
        return None
    digits = re.sub(r"\D", "", date_str)
    if len(digits) != 8:
        return None
    y, m, d = digits[:4], digits[4:6], digits[6:8]
    return f"{y}. {int(m)}. {int(d)}."


# ─────────────────────────────────────────────
# 다건 판례 비교
# ─────────────────────────────────────────────
async def compare_precedents(prec_ids: list[str | int]) -> dict[str, Any]:
    """여러 판례를 한 번에 가져와 핵심 필드 비교 표 반환.

    LLM이 후속 처리(표·요약)에 바로 쓸 수 있도록 평탄한 구조로 반환.

    Args:
        prec_ids: 비교할 판례일련번호 리스트 (2~10건 권장)

    Returns:
        {"count": int, "rows": [
            {"prec_id","case_number","court","judgment_date",
             "case_name","holdings","summary","referenced_articles"}, ...
        ]}
    """
    from caselaw_mcp.tools.precedent import get_precedent

    if not prec_ids:
        raise ValueError("prec_ids 가 비어있음")
    if len(prec_ids) > 10:
        raise ValueError(f"최대 10건까지 비교 가능 (요청: {len(prec_ids)})")

    rows: list[dict[str, Any]] = []
    for pid in prec_ids:
        try:
            d = await get_precedent(pid)
        except Exception as e:
            rows.append({"prec_id": str(pid), "error": str(e)})
            continue
        rows.append(
            {
                "prec_id": str(pid),
                "case_number": d.get("case_number"),
                "court": d.get("court"),
                "judgment_date": d.get("judgment_date"),
                "case_name": d.get("case_name"),
                "holdings": _truncate(d.get("holdings"), 500),
                "summary": _truncate(d.get("summary"), 800),
                "referenced_articles": _truncate(d.get("referenced_articles"), 300),
            }
        )
    return {"count": len(rows), "rows": rows}


def _truncate(value: Any, limit: int) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    if len(s) <= limit:
        return s
    return s[:limit] + "...(생략)"
