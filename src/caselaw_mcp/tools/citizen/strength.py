"""유사 판례 결과 라벨링·승소율 분포 (참고용).

원칙:
- 단정 금지 — "통상", "참고" 표현
- search_precedent 결과 사건명에서 결과 키워드 추출 (LLM 라벨링 미사용)
- 분류 불가 항목은 'unclassified' 로 별도 카운트
- 면책 자동 부착
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from caselaw_mcp.tools.citizen.disclaimer import attach
from caselaw_mcp.tools.precedent import search_precedent

# 사건명·요약에서 추출되는 결과 라벨.
# 매칭 순서가 중요 — 구체적인 라벨(일부승·공소기각)을 일반 라벨(원고승·기각) 보다 먼저 두어야 한다.
OUTCOME_KEYWORDS: dict[str, list[str]] = {
    "원고일부승": ["일부 인용", "일부인용", "일부 승소"],
    "공소기각": ["공소기각", "공소 기각"],
    "원고승": ["청구 인용", "전부인용", "인용", "원고승"],
    "각하": ["각하"],
    "기각": ["청구 기각", "청구기각", "기각"],
    "조정·화해": ["조정성립", "강제조정", "조정", "화해"],
    "취소": ["처분 취소", "원심파기", "파기환송", "취소"],
    "유죄": ["유죄", "징역", "집행유예", "벌금형"],
    "무죄": ["무죄"],
}


def _label_outcome(text: str) -> str | None:
    """사건명·내용에서 결과 라벨 추정. 매칭 실패 시 None."""
    if not text:
        return None
    for label, keywords in OUTCOME_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                return label
    return None


async def evaluate_case_strength(
    query: str,
    *,
    sample_size: int = 30,
    court: str | None = None,
    case_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """유사 판례 회수 → 결과 라벨링 → 분포 통계 (참고용).

    Args:
        query: 검색어 (예: "음주운전 면허취소", "임금체불 사직")
        sample_size: 분석할 최대 판례 수 (1~100, 기본 30)
        court / case_type / date_from / date_to: search_precedent 와 동일

    Returns:
        {
            "query", "sample_size", "analyzed", "total_available",
            "outcome_distribution": {"원고승": 8, "기각": 3, ...},
            "outcome_distribution_pct": {"원고승": 53.3, ...},
            "unclassified_count": int,
            "win_rate_estimate_pct": float | null,    # 원고승+일부승 비율
            "representative_cases": [...],            # 라벨별 대표 사례 1건씩
            "summary_text": str,                      # LLM에게 그대로 전달 가능
            "disclaimers": [...]                      # 항상 standard + ai_limitation
        }
    """
    if not query or not query.strip():
        raise ValueError("query 비어있음")
    sample_size = max(1, min(100, sample_size))

    res = await search_precedent(
        query,
        court=court,
        case_type=case_type,
        date_from=date_from,
        date_to=date_to,
        display=sample_size,
    )
    items = res.get("items", [])

    counter: Counter[str] = Counter()
    representatives: dict[str, dict[str, Any]] = {}
    unclassified = 0

    for it in items:
        text = (it.get("case_name") or "") + " " + (it.get("decision_type") or "")
        label = _label_outcome(text)
        if label is None:
            unclassified += 1
            continue
        counter[label] += 1
        if label not in representatives:
            representatives[label] = {
                "case_number": it.get("case_number"),
                "court": it.get("court"),
                "judgment_date": it.get("judgment_date"),
                "case_name": it.get("case_name"),
                "prec_id": it.get("prec_id"),
            }

    analyzed = sum(counter.values())
    total = analyzed + unclassified

    pct_dist = (
        {k: round(v / analyzed * 100, 1) for k, v in counter.most_common()}
        if analyzed > 0
        else {}
    )

    win_count = counter.get("원고승", 0) + counter.get("원고일부승", 0)
    win_rate = round(win_count / analyzed * 100, 1) if analyzed > 0 else None

    summary_text = _make_summary(query, counter, win_rate, total, unclassified)

    return attach(
        {
            "query": query,
            "sample_size": sample_size,
            "total_in_sample": total,
            "analyzed": analyzed,
            "unclassified_count": unclassified,
            "total_available": res.get("total_count"),
            "outcome_distribution": dict(counter.most_common()),
            "outcome_distribution_pct": pct_dist,
            "win_rate_estimate_pct": win_rate,
            "representative_cases": representatives,
            "summary_text": summary_text,
            "method_note": (
                "사건명·구분 키워드 매칭으로 결과를 추정합니다. "
                "분류 불가(unclassified)는 사건명만으로 결과 판단 어려운 경우입니다. "
                "정확한 결과는 각 판례 본문을 확인하세요."
            ),
        },
        kinds=["standard", "ai_limitation"],
    )


def _make_summary(
    query: str,
    counter: Counter[str],
    win_rate: float | None,
    total: int,
    unclassified: int,
) -> str:
    if total == 0:
        return f"'{query}' 관련 판례를 찾지 못했습니다. 검색어를 다르게 시도해 보세요."

    parts = [f"'{query}' 유사 판례 {total}건 분석 결과 (참고용)."]
    if win_rate is not None:
        parts.append(f"원고승 비율 통상 약 {win_rate}% (원고전부+일부승 합산).")
    if counter:
        top3 = ", ".join(f"{k} {v}건" for k, v in counter.most_common(3))
        parts.append(f"가장 흔한 결과: {top3}.")
    if unclassified > 0:
        parts.append(f"※ {unclassified}건은 사건명만으로 결과 분류 어려움.")
    parts.append("개별 사건 결과는 사실관계·증거·법원에 따라 달라질 수 있습니다.")
    return " ".join(parts)
