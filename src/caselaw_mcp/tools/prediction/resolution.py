"""분쟁 해결 옵션 비교 — `dispute_resolution_options`.

소송 vs 조정 vs 화해 vs 중재의 시간·비용·예상 결과를 의사결정 매트릭스로.
시드 기반 (실제 사건 통계 부족 → 변호사 경험 보강 필요).
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.tools.prediction.duration import (
    DISCLAIMER_BLOCK,
)

# ─────────────────────────────────────────────
# 비교 매트릭스 시드
# 시간/비용/결과 통제력/판례 형성/관계 보존을 1~5 척도 로 비교
# (실제 데이터 보강 시 시드 갱신)
# ─────────────────────────────────────────────
_OPTION_MATRIX = {
    "lawsuit": {
        "label_kr": "소송 (정식 재판)",
        "time_weight": 5,  # 가장 길다
        "cost_weight": 5,  # 가장 비싸다
        "control": 2,  # 결과 통제력 낮음 (재판부 결정)
        "binding": 5,  # 강제 집행력 최고
        "relation": 1,  # 상대방과 관계 악화
        "use_when": [
            "상대방이 협상 거부",
            "법적 강제력 필요",
            "선례를 남기고 싶음",
            "청구금액이 매우 큼",
        ],
        "avoid_when": ["관계 유지가 더 중요", "신속 해결 필요"],
    },
    "mediation": {
        "label_kr": "조정 (법원 또는 ADR)",
        "time_weight": 2,
        "cost_weight": 2,
        "control": 4,  # 합의로 자기결정
        "binding": 4,  # 조정조서 = 확정판결과 동일 효력
        "relation": 4,
        "use_when": [
            "상대방과 대화 가능",
            "신속 해결 우선",
            "관계 유지 원함",
            "복잡한 사실관계로 재판 장기화 우려",
        ],
        "avoid_when": [
            "상대방이 무성의·악의적",
            "법리적 선례가 필요",
        ],
    },
    "settlement": {
        "label_kr": "화해 / 합의",
        "time_weight": 1,  # 가장 빠르다
        "cost_weight": 1,  # 가장 저렴
        "control": 5,  # 자기결정 최대
        "binding": 3,  # 공정증서 작성 시 강제집행 가능
        "relation": 5,
        "use_when": [
            "양 당사자 협상 의지",
            "최단 시간 우선",
            "법적 명확성 less 중요",
            "비용 최소화",
        ],
        "avoid_when": [
            "상대방 신뢰 불가",
            "대중적·선례적 영향 필요",
        ],
    },
    "arbitration": {
        "label_kr": "중재",
        "time_weight": 3,
        "cost_weight": 4,
        "control": 3,
        "binding": 5,
        "relation": 3,
        "use_when": [
            "계약서에 중재 조항 명시",
            "상사·국제 분쟁",
            "비공개 처리 원함",
        ],
        "avoid_when": [
            "중재 조항 없음",
            "선례를 남기고 싶음",
        ],
    },
}


def options(
    dispute_type: str = "civil",
    claim_amount: int | None = None,
    relationship_priority: bool = False,
    speed_priority: bool = False,
    cost_priority: bool = False,
) -> dict[str, Any]:
    """분쟁 해결 4 옵션 비교 + 본건에 가장 적합한 옵션 추천.

    Args:
        dispute_type: "civil" / "criminal" / "commercial" / "family" 등 자유 텍스트.
            criminal 은 화해·조정 적용 한계 자동 안내.
        claim_amount: 청구금액 (원). None 가능.
        relationship_priority: 관계 유지 우선 시 True (조정·화해 가산점).
        speed_priority: 신속 해결 우선 시 True (화해·조정 가산점).
        cost_priority: 비용 최소 우선 시 True (화해 가산점).

    Returns:
        {
          "doc_type": "dispute_resolution_comparison",
          "options": dict,  # 4 옵션 매트릭스 + 본건 점수
          "recommendation": str,  # 가장 추천하는 옵션 키 ("settlement"/"mediation"/...)
          "markdown": str (면책 부착)
        }
    """
    if not isinstance(dispute_type, str):
        dispute_type = "civil"
    dt_lower = dispute_type.strip().lower()

    is_criminal = "criminal" in dt_lower or "형사" in dispute_type

    # 본건 점수 계산 (가산점 모델)
    scores: dict[str, int] = {}
    for key, opt in _OPTION_MATRIX.items():
        score = 0
        # 기본 척도 (관계·속도·비용 우선시)
        if relationship_priority:
            score += opt["relation"]
        if speed_priority:
            score += 6 - opt["time_weight"]  # time_weight 작을수록 빠름
        if cost_priority:
            score += 6 - opt["cost_weight"]
        # 우선 옵션 비활성 시에도 균형 점수
        if not (relationship_priority or speed_priority or cost_priority):
            score = 6 - opt["time_weight"] + 6 - opt["cost_weight"] + opt["binding"]
        # 형사 사건 은 settlement (양형 합의 외) 효과 제한
        if is_criminal and key in {"settlement", "mediation"}:
            score = max(0, score - 3)
        scores[key] = score

    recommendation = max(scores, key=lambda k: scores[k])

    # 마크다운 비교표
    rows = [
        "| 옵션 | 시간 | 비용 | 통제력 | 강제력 | 관계보존 | 본건 점수 |",
        "|---|---|---|---|---|---|---|",
    ]
    for key, opt in _OPTION_MATRIX.items():
        time_str = "🟢" * (6 - opt["time_weight"]) + "⬜" * (opt["time_weight"] - 1)
        cost_str = "🟢" * (6 - opt["cost_weight"]) + "⬜" * (opt["cost_weight"] - 1)
        rows.append(
            f"| {opt['label_kr']} | {time_str} | {cost_str} | "
            f"{opt['control']}/5 | {opt['binding']}/5 | {opt['relation']}/5 | "
            f"**{scores[key]}** |"
        )

    matrix_md = "\n".join(rows)

    rec_label = _OPTION_MATRIX[recommendation]["label_kr"]
    rec_use = "\n".join(f"- {x}" for x in _OPTION_MATRIX[recommendation]["use_when"])
    rec_avoid = "\n".join(f"- {x}" for x in _OPTION_MATRIX[recommendation]["avoid_when"])

    body_lines = [
        "# 분쟁 해결 옵션 비교",
        "",
        f"**분쟁 유형**: {dispute_type}",
    ]
    if claim_amount is not None:
        body_lines.append(f"**청구금액**: {claim_amount:,}원")
    body_lines.extend(
        [
            f"**우선순위**: 관계보존={relationship_priority} / 속도={speed_priority} / 비용={cost_priority}",
            "",
            "## 비교 매트릭스",
            "",
            matrix_md,
            "",
            f"## 본건 추천: **{rec_label}**",
            "",
            "### 적합한 경우",
            "",
            rec_use,
            "",
            "### 피해야 하는 경우",
            "",
            rec_avoid,
            "",
            "## 해석 가이드",
            "",
            "- 점수는 사용자 우선순위(관계/속도/비용) + 옵션 특성을 합산한 휴리스틱.",
            "- 형사 사건은 화해·조정 효과가 제한적이라 자동 차감 (피해자 합의서 별도).",
            '- 의뢰인이 **"빨리 끝내고 싶다"** 면 화해, **"법적 보호 강하게"** 면 소송 우선.',
            "- 계약서에 중재 조항이 있으면 중재가 유일한 옵션일 수 있음 (확인 필수).",
        ]
    )
    body = "\n".join(body_lines)

    markdown = body + DISCLAIMER_BLOCK

    return {
        "doc_type": "dispute_resolution_comparison",
        "dispute_type": dispute_type,
        "claim_amount": claim_amount,
        "options": {k: {**v, "本件 score": scores[k]} for k, v in _OPTION_MATRIX.items()},
        "recommendation": recommendation,
        "recommendation_label_kr": rec_label,
        "markdown": markdown,
    }
