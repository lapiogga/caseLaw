"""사건 소요 기간 예측 — `estimate_case_duration`.

사법연감 평균 기반 시드 (`prediction_data/duration_baselines.json`).
머신러닝 없음, 사용자 입력에 매핑해 평균 + 95% CI 회수.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any

DISCLAIMER_MARKER = "본 예측은 caselaw MCP 가 사법연감 시드로 산출한 참고 자료입니다."

DISCLAIMER_BLOCK = f"""
---
> ⚠️ **면책**: {DISCLAIMER_MARKER}
> 본건의 결과를 보장하지 않으며, 법원·재판부·구체 사실관계에 따라 크게
> 달라질 수 있습니다. 변호사가 자체 사건 데이터로 보강하세요.
"""


@lru_cache(maxsize=1)
def _load_baselines() -> dict[str, Any]:
    text = (
        resources.files("caselaw_mcp.prediction_data")
        .joinpath("duration_baselines.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


def _resolve_alias(value: str, alias_map: dict[str, list[str]], default: str) -> str:
    """사용자 입력(영문/한글)을 표준 키로 정규화. 매칭 실패 시 default."""
    if not isinstance(value, str):
        return default
    v = value.strip().lower()
    for canonical, aliases in alias_map.items():
        if v == canonical.lower() or v in [a.lower() for a in aliases]:
            return canonical
    return default


def estimate(
    case_type: str = "민사",
    instance: str = "1심",
    complexity: str = "보통",
) -> dict[str, Any]:
    """사건 1·2·3심 소요 기간 예측 (월).

    Args:
        case_type: "민사" / "형사" (alias: civil/criminal).
        instance: "1심" / "2심" / "3심" (alias: 1st/2nd/3rd, trial/appeal/supreme).
        complexity: "단순" / "보통" / "복잡" (alias: simple/normal/complex).

    Returns:
        {
          "doc_type": "case_duration_estimate",
          "case_type": str,
          "instance": str,
          "complexity": str,
          "mean_months": int,
          "ci_low_months": int,
          "ci_high_months": int,
          "markdown": str (면책 부착)
        }
    """
    baselines = _load_baselines()

    case_type_norm = _resolve_alias(case_type, baselines["case_type_aliases"], "civil")
    instance_norm = _resolve_alias(instance, baselines["instance_aliases"], "1심")
    complexity_norm = _resolve_alias(complexity, baselines["complexity_aliases"], "보통")

    try:
        record = baselines[case_type_norm][instance_norm][complexity_norm]
    except KeyError as e:
        raise ValueError(
            f"baseline 미존재: case_type={case_type_norm}, instance={instance_norm}, "
            f"complexity={complexity_norm}"
        ) from e

    mean = int(record["mean"])
    lo = int(record["ci_low"])
    hi = int(record["ci_high"])

    case_type_kr = "민사" if case_type_norm == "civil" else "형사"
    body = f"""# 사건 소요 기간 예측

| 항목 | 값 |
|---|---|
| 사건 유형 | {case_type_kr} |
| 심급 | {instance_norm} |
| 복잡도 | {complexity_norm} |
| **평균** | **약 {mean} 개월** |
| 95% 신뢰구간 | {lo} ~ {hi} 개월 |

## 해석 가이드

- 평균 {mean} 개월은 사법연감 데이터 기반 추정입니다.
- 신뢰구간 폭 ({lo} ~ {hi} 개월) 이 클수록 재판부·시기 편차가 큽니다.
- 의뢰인에게 "**평균은 약 {mean} 개월이지만 길게는 {hi} 개월까지 갈 수 있다**"
  로 설명하면 기대 관리에 안전합니다.
- 본건이 다음에 해당하면 평균보다 길어집니다:
  - 증인 다수
  - 감정 신청
  - 외국 송달
  - 항소·재항고 대비

## 다음 단계 추천

- `estimate_litigation_cost` 로 비용 견적
- `predict_civil_outcome` 또는 `predict_sentencing` 로 결과 예측
"""

    markdown = body + DISCLAIMER_BLOCK

    return {
        "doc_type": "case_duration_estimate",
        "case_type": case_type_kr,
        "instance": instance_norm,
        "complexity": complexity_norm,
        "mean_months": mean,
        "ci_low_months": lo,
        "ci_high_months": hi,
        "markdown": markdown,
    }
