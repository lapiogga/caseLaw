"""소송 비용 견적 — 인지대 + 송달료 + 변호사 수임료.

법적 근거: 민사소송 등 인지법, 송달료 규칙.
변호사비는 시장 통상 범위 (자율).
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any

from caselaw_mcp.tools.citizen.disclaimer import attach


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    text = resources.files("caselaw_mcp.citizen_data").joinpath("court_fees.json").read_text(
        encoding="utf-8"
    )
    return json.loads(text)


def calc_stamp_fee(claim_amount_krw: int) -> int:
    """민사 인지대 계산 (인지법 별표 기준).

    Args:
        claim_amount_krw: 소가 (원)

    Returns:
        인지대 (원, 100원 단위 절상)
    """
    if claim_amount_krw <= 0:
        return 0
    c = float(claim_amount_krw)
    if claim_amount_krw < 10_000_000:
        fee = c * 0.005
    elif claim_amount_krw < 100_000_000:
        fee = c * 0.0045 + 5_000
    elif claim_amount_krw < 1_000_000_000:
        fee = c * 0.004 + 55_000
    else:
        fee = c * 0.0035 + 555_000
    # 100원 단위 절상
    return int(((fee + 99) // 100) * 100)


def calc_service_fee(rounds: int | None = None) -> int:
    """송달료 (당사자 수 x 1회당 x 표준 회수).

    Args:
        rounds: 송달 횟수. 기본 표준(7회).
    """
    data = _load()
    per = data["service_fee_per_round_krw"]
    rnd = rounds if rounds is not None else data["standard_service_rounds"]
    return per * rnd


def estimate_litigation_cost(
    claim_amount_krw: int,
    case_type: str = "civil_general",
) -> dict[str, Any]:
    """소송 비용 종합 견적.

    Args:
        claim_amount_krw: 소가 (원). 형사·행정·가사는 0 또는 명목값 사용.
        case_type: "civil_general" | "civil_small_claim" | "criminal_general"
                   | "criminal_dui" | "family_divorce" | "labor_dismissal"
                   | "administrative" | "real_estate" | "medical"

    Returns:
        {
            "case_type", "claim_amount_krw",
            "court_fee_stamp_krw", "service_fee_krw",
            "small_claim_eligible", "small_claim_threshold_krw",
            "lawyer_fee": {"low", "typical", "high", "note"},
            "success_fee_pct": {"min", "max"},
            "total_court_fees_krw",
            "total_typical_with_lawyer_krw",
            "total_self_litigation_krw",
            "additional_costs", "free_resources", "disclaimers"
        }
    """
    if claim_amount_krw < 0:
        raise ValueError(f"claim_amount_krw 음수 불가: {claim_amount_krw}")
    data = _load()
    fees_table = data["lawyer_fee_estimates"]
    if case_type not in fees_table:
        raise ValueError(
            f"case_type={case_type!r} 인식 불가. 유효: {list(fees_table.keys())}"
        )

    stamp = calc_stamp_fee(claim_amount_krw)
    service = calc_service_fee()
    threshold = data["small_claim_threshold_krw"]
    eligible_small = (
        case_type in ("civil_general", "civil_small_claim", "real_estate")
        and 0 < claim_amount_krw <= threshold
    )

    lawyer_fee = fees_table[case_type]
    typical_total = stamp + service + lawyer_fee["typical"]
    self_total = stamp + service

    return attach(
        {
            "case_type": case_type,
            "claim_amount_krw": claim_amount_krw,
            "court_fee_stamp_krw": stamp,
            "service_fee_krw": service,
            "total_court_fees_krw": stamp + service,
            "small_claim_eligible": eligible_small,
            "small_claim_threshold_krw": threshold,
            "lawyer_fee": lawyer_fee,
            "success_fee_pct": data["success_fee_typical_pct"],
            "total_typical_with_lawyer_krw": typical_total,
            "total_self_litigation_krw": self_total if eligible_small else None,
            "additional_costs": data["additional_costs"],
            "free_resources": data["free_resources"],
            "advice": _make_advice(case_type, claim_amount_krw, eligible_small, lawyer_fee),
        },
        kinds=["standard", "ai_limitation"],
    )


def _make_advice(
    case_type: str,
    claim: int,
    eligible_small: bool,
    lawyer_fee: dict[str, Any],
) -> list[str]:
    out: list[str] = []
    if eligible_small:
        out.append(
            f"소가가 소액사건심판 한도(3,000만 원) 이내입니다. "
            f"전자소송(https://ecfs.scourt.go.kr) 으로 셀프 진행하면 약 "
            f"{calc_stamp_fee(claim) + calc_service_fee():,}원 정도로 가능합니다."
        )
    if case_type.startswith("criminal_"):
        out.append(
            "형사 사건은 인지대 없습니다. 변호사 비용이 주된 부담."
        )
    if case_type == "medical":
        out.append("의료사고는 감정 비용(100~500만 원) 별도. 의료분쟁조정중재원 무료 조정 우선 검토.")
    if case_type == "administrative":
        out.append("행정심판은 무료. 행정소송 단계부터 인지대 발생.")
    out.append(
        f"변호사 수임료 통상: 최저 {lawyer_fee['low']:,}원 / 평균 "
        f"{lawyer_fee['typical']:,}원 / 최고 {lawyer_fee['high']:,}원."
    )
    out.append(
        "비용 부담 시 대한법률구조공단(132) 또는 지역 변호사회 무료상담을 우선 이용하세요."
    )
    return out
