"""인용 텍스트 → 판례 역검색 helper.

변호사가 변론서·논문에서 본 인용("대법원 2024. 5. 30. 선고 2023두12345 판결")만
알고 있을 때, prec_id 와 본문을 자동으로 회수.
"""

from __future__ import annotations

import re
from typing import Any

from caselaw_mcp.tools.precedent import search_precedent

# '2023도12345' 'A 2018헌바8' '2024구합12345' 등 한국 사건번호 패턴
CASE_NUMBER_RE = re.compile(r"\d{2,4}[가-힣]{1,3}\d{1,8}")


async def find_precedent_by_citation(
    citation: str,
    *,
    max_items: int = 5,
) -> dict[str, Any]:
    """인용 텍스트에서 사건번호를 추출하고 prec_id를 회수.

    Args:
        citation: 자유 형식 인용 텍스트
            예: "대법원 2024. 5. 30. 선고 2023두12345 판결"
                "헌법재판소 2018헌바8 결정"
                "2025도15970"  (사건번호만)
        max_items: 사건번호 1개당 search_precedent 회수 최대 건수

    Returns:
        {
            "input": str,
            "extracted_case_numbers": list[str],
            "matches": [
                {"case_number": "2023두12345", "candidates": [...]}
            ]
        }
        candidates 각 원소는 search_precedent 의 item (prec_id 포함).
    """
    if not citation or not citation.strip():
        raise ValueError("citation 비어있음")

    case_numbers = _extract_unique(citation)
    if not case_numbers:
        return {
            "input": citation,
            "extracted_case_numbers": [],
            "matches": [],
            "hint": "사건번호 패턴(예: 2024도1234)을 찾지 못했습니다.",
        }

    matches: list[dict[str, Any]] = []
    for case_no in case_numbers:
        try:
            r = await search_precedent(case_no, display=max_items)
        except Exception as e:
            matches.append({"case_number": case_no, "error": str(e)})
            continue
        # 사건번호와 정확히 일치하는 항목만 우선
        items = r.get("items", [])
        exact = [it for it in items if str(it.get("case_number") or "").strip() == case_no]
        candidates = exact if exact else items
        matches.append(
            {
                "case_number": case_no,
                "candidates": candidates[:max_items],
                "exact_match": bool(exact),
            }
        )

    return {
        "input": citation,
        "extracted_case_numbers": case_numbers,
        "matches": matches,
        "count": len(matches),
    }


def _extract_unique(text: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for m in CASE_NUMBER_RE.findall(text or ""):
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out
