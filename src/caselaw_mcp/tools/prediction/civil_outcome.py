"""민사 결과 분포 예측 — `predict_civil_outcome`.

내부에서 search_precedent (+ 옵션 본문) 호출 → 인용/일부인용/기각/취하/분류불가 분포.
인정 금액(awarded amount) 추출 (있는 경우) 도 포함.
"""

from __future__ import annotations

import statistics
from typing import Any

from caselaw_mcp.tools.precedent import get_precedent, search_precedent
from caselaw_mcp.tools.prediction.duration import DISCLAIMER_BLOCK
from caselaw_mcp.tools.prediction.labels import (
    CIVIL_LABELS,
    aggregate_label_distribution,
    extract_awarded_amount,
    label_civil_outcome,
    sample_size_warning,
)


def _aggregate(texts: list[str], query: str, court: str | None = None) -> dict[str, Any]:
    """라벨링 + 집계 + 인정 금액 분포 + 마크다운."""
    labels = [label_civil_outcome(t) for t in texts]
    n = len(labels)
    distribution = aggregate_label_distribution(labels, CIVIL_LABELS)
    warning = sample_size_warning(n)

    # 인정 금액 추출 (인용/일부인용 케이스에서만)
    granted_amounts: list[int] = []
    for text, label in zip(texts, labels, strict=False):
        if label in {"granted", "partial"}:
            amt = extract_awarded_amount(text)
            if amt is not None and amt > 0:
                granted_amounts.append(amt)

    amount_stats: dict[str, Any] | None = None
    if granted_amounts:
        amount_stats = {
            "count": len(granted_amounts),
            "mean": int(statistics.mean(granted_amounts)),
            "median": int(statistics.median(granted_amounts)),
            "min": min(granted_amounts),
            "max": max(granted_amounts),
        }

    label_kr = {
        "granted": "전부 인용 (원고 승소)",
        "partial": "일부 인용",
        "dismissed": "기각 (원고 패소)",
        "withdrawn": "취하·화해",
        "unknown": "분류 불가",
    }
    rows = ["| 결과 | 건수 | 비율 |", "|---|---|---|"]
    for key in CIVIL_LABELS:
        d = distribution[key]
        rows.append(f"| {label_kr[key]} | {d['count']} | {d['percent']:.1f}% |")
    rows.append(f"| **합계** | **{n}** | 100% |")
    matrix = "\n".join(rows)

    warn_block = ""
    if warning:
        warn_block = f"\n> ⚠️ **{warning}**\n"

    court_clause = f" / 법원={court}" if court else ""

    amount_block = ""
    if amount_stats:
        amount_block = f"""

## 인정 금액 분포 (인용/일부인용 케이스)

| 항목 | 값 |
|---|---|
| 표본 | {amount_stats["count"]} 건 |
| 평균 | {amount_stats["mean"]:,}원 |
| 중앙값 | {amount_stats["median"]:,}원 |
| 최소 | {amount_stats["min"]:,}원 |
| 최대 | {amount_stats["max"]:,}원 |
"""
    else:
        amount_block = (
            "\n*(인정 금액 분포: 본문에서 금액 추출 실패 — `use_full_text=True` 시 추출 가능)*\n"
        )

    granted_pct = distribution["granted"]["percent"]
    partial_pct = distribution["partial"]["percent"]

    body = f"""# 민사 결과 분포 예측

**검색 조건**: query="{query}"{court_clause}
**표본 크기 (N)**: **{n}** 건
{warn_block}

## 결과 분포

{matrix}
{amount_block}

## 해석 가이드

- 사건명 + 판시사항 키워드 매칭 라벨링 결과. 분류 불가(unknown) 는 정직 보고.
- 전부 인용 + 일부 인용 = **{granted_pct + partial_pct:.1f}%** (원고 측 우호 결과 합산).
- 의뢰인 보고 권장 표현:
  - "유사 사건 N={n} 건 중 약 {granted_pct + partial_pct:.0f}% 가 원고 우호적
    결과 (전부+일부 인용)"
- 본건의 입증 강도가 약하면 평균보다 기각 확률이 큽니다.
- `use_full_text=True` 로 본문 라벨링 시 정확도 ↑ (느림, 캐시 활용).

## 다음 단계 추천

- `evaluate_case_strength` 로 본건 정량 평가
- `estimate_case_duration` 으로 예상 소요 기간
- `dispute_resolution_options` 로 소송 vs 조정 비교
- `draft_civil_complaint` 의 청구취지·청구원인 작성 시 본 결과 인용
"""

    markdown = body + DISCLAIMER_BLOCK

    return {
        "doc_type": "civil_outcome_prediction",
        "search_query": query,
        "court": court,
        "sample_size": n,
        "sample_size_warning": warning,
        "label_distribution": distribution,
        "amount_stats": amount_stats,
        "markdown": markdown,
    }


async def predict(
    query: str,
    court: str | None = None,
    max_samples: int = 20,
    date_from: str | None = None,
    date_to: str | None = None,
    use_full_text: bool = False,
) -> dict[str, Any]:
    """민사 결과 분포 예측.

    Args:
        query: 검색 키워드 (예: "대여금 변제").
        court: 법원 필터 (예: "대법원").
        max_samples: 검색 결과 N 상한 (5~50).
        date_from / date_to: 선고일 범위 (YYYYMMDD).
        use_full_text: True 면 각 판례 본문까지 fetch 해 라벨링 + 인정 금액 추출
            (정확도 ↑, 느림).

    Returns:
        {
          "doc_type": "civil_outcome_prediction",
          "sample_size": int,
          "label_distribution": {...},
          "amount_stats": dict | None,
          "markdown": str (면책 부착)
        }

    Raises:
        ValueError: 표본 부족 (N<5).
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query: 비어있지 않은 문자열 필요")
    max_samples = max(5, min(50, int(max_samples)))

    search_result = await search_precedent(
        query.strip(),
        court=court,
        case_type="민사",
        date_from=date_from,
        date_to=date_to,
        display=max_samples,
        page=1,
    )
    items = search_result.get("items", []) or []
    n_raw = len(items)
    if n_raw < 5:
        raise ValueError(
            f"표본 부족 (N={n_raw}, 최소 5 필요). 검색 키워드를 넓히세요. "
            "court/date_from/date_to 필터를 완화하거나 max_samples 를 늘리세요."
        )

    texts: list[str] = []
    for item in items:
        snippet = " ".join(
            str(item.get(k, "")) for k in ("case_name", "judgment_summary", "key_issue")
        )
        if use_full_text and item.get("prec_id"):
            try:
                full = await get_precedent(int(item["prec_id"]))
                snippet += " " + " ".join(
                    str(full.get(k, "")) for k in ("판시사항", "판결요지", "주문", "이유")
                )
            except Exception:
                pass
        texts.append(snippet)

    return _aggregate(texts, query.strip(), court)
