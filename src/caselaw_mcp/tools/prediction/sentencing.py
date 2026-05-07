"""형사 양형 분포 예측 — `predict_sentencing`.

내부에서 search_precedent (+ 옵션으로 get_precedent) 를 호출해 표본을 모은 뒤
라벨링·집계. 라벨링은 사건명만 사용 (use_full_text=True 시 본문 추가).
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.tools.precedent import get_precedent, search_precedent
from caselaw_mcp.tools.prediction.duration import DISCLAIMER_BLOCK
from caselaw_mcp.tools.prediction.labels import (
    SENTENCING_LABELS,
    aggregate_label_distribution,
    label_sentencing,
    sample_size_warning,
)


def _aggregate(texts: list[str], query: str, court: str | None = None) -> dict[str, Any]:
    """라벨링 + 집계 + 마크다운 (동기 — 단위 테스트 용이).

    `texts` 는 사건명 또는 사건명+판시사항 합본.
    """
    labels = [label_sentencing(t) for t in texts]
    n = len(labels)
    distribution = aggregate_label_distribution(labels, SENTENCING_LABELS)
    warning = sample_size_warning(n)

    # 표본 부족(<5) 은 호출자가 ValueError 로 발사. 여기는 정상/경고만.
    label_kr = {
        "acquitted": "무죄·공소기각",
        "suspended_sentence": "선고유예 / 집행유예",
        "fine": "벌금형",
        "imprisonment": "실형 (징역·금고)",
        "unknown": "분류 불가",
    }
    rows = ["| 양형 | 건수 | 비율 |", "|---|---|---|"]
    for key in SENTENCING_LABELS:
        d = distribution[key]
        rows.append(f"| {label_kr[key]} | {d['count']} | {d['percent']:.1f}% |")
    rows.append(f"| **합계** | **{n}** | 100% |")
    matrix = "\n".join(rows)

    warn_block = ""
    if warning:
        warn_block = f"\n> ⚠️ **{warning}**\n"

    court_clause = f" / 법원={court}" if court else ""

    body = f"""# 형사 양형 분포 예측

**검색 조건**: query="{query}"{court_clause}
**표본 크기 (N)**: **{n}** 건
{warn_block}

## 양형 분포

{matrix}

## 해석 가이드

- 본 분포는 사건명 키워드 매칭 라벨링 결과로, 분류 불가(unknown) 는
  사건명만으로 양형을 추정할 수 없는 케이스입니다 (정직 보고).
- `use_full_text=True` 옵션으로 본문(판시사항)까지 라벨링하면 정확도 ↑
  (단, get_precedent N 회 추가 호출로 응답 시간 ↑).
- 의뢰인 보고 시 권장 표현:
  - "유사 사건 N={n} 건 중 약 {distribution["fine"]["percent"]:.0f}% 가 벌금형,
    {distribution["suspended_sentence"]["percent"]:.0f}% 가 집유였다"
- 본건이 다음에 해당하면 양형 가중·감경 큼:
  - 가중: 누범, 동종 전과, 음주 측정 거부, 사고 야기
  - 감경: 초범, 합의, 반성문, 주변 환경 (가장)

## 다음 단계 추천

- `analyze_precedent_trend` 로 시기별 추이 확인
- `draft_criminal_defense` 의 양형 의견 입력으로 본 결과 활용
- `compare_precedents` 로 본건과 가장 가까운 판례 찾아 인용
"""

    markdown = body + DISCLAIMER_BLOCK

    return {
        "doc_type": "sentencing_prediction",
        "search_query": query,
        "court": court,
        "sample_size": n,
        "sample_size_warning": warning,
        "label_distribution": distribution,
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
    """형사 양형 분포 예측.

    Args:
        query: 검색 키워드 (예: "음주운전").
        court: 법원 필터 (예: "대법원").
        max_samples: 검색 결과 N 상한 (5~50).
        date_from / date_to: 선고일 범위 (YYYYMMDD).
        use_full_text: True 면 각 판례 본문까지 fetch 해 라벨링 (정확도 ↑, 느림).

    Returns:
        {
          "doc_type": "sentencing_prediction",
          "sample_size": int,
          "label_distribution": {...},
          "markdown": str (면책 부착)
        }

    Raises:
        ValueError: 표본 부족 (N<5) 또는 검색 실패.
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query: 비어있지 않은 문자열 필요")
    max_samples = max(5, min(50, int(max_samples)))

    search_result = await search_precedent(
        query.strip(),
        court=court,
        case_type="형사",
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
                # full text fetch 실패해도 사건명만으로 라벨링 진행
                pass
        texts.append(snippet)

    return _aggregate(texts, query.strip(), court)
