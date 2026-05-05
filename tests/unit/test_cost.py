"""소송 비용 견적 단위 테스트."""

from __future__ import annotations

import pytest

from caselaw_mcp.tools.citizen.cost import (
    calc_service_fee,
    calc_stamp_fee,
    estimate_litigation_cost,
)


# ─────────────────────────────────────────────
# 인지대 계산 (인지법 별표)
# ─────────────────────────────────────────────
@pytest.mark.parametrize(
    ("claim", "expected_min", "expected_max"),
    [
        # 1,000만 원 미만: claim * 0.005
        (5_000_000, 25_000, 25_000),       # 5백만 → 25,000
        (9_000_000, 45_000, 45_000),       # 9백만 → 45,000
        # 1천만 ~ 1억: claim * 0.0045 + 5,000
        (10_000_000, 50_000, 50_000),      # 1천만 → 50,000
        (50_000_000, 230_000, 230_000),    # 5천만 → 230,000
        (100_000_000, 455_000, 455_100),   # 1억 경계는 다음 단계 (≥1억)
        # 1억 ~ 10억: claim * 0.004 + 55,000
        (500_000_000, 2_055_000, 2_055_100),  # 5억 → 2,055,000
        # 10억 초과: claim * 0.0035 + 555,000
        (2_000_000_000, 7_555_000, 7_555_100),  # 20억 → 7,555,000
    ],
)
def test_calc_stamp_fee(claim: int, expected_min: int, expected_max: int) -> None:
    fee = calc_stamp_fee(claim)
    assert expected_min <= fee <= expected_max


def test_calc_stamp_fee_zero() -> None:
    assert calc_stamp_fee(0) == 0
    assert calc_stamp_fee(-100) == 0


def test_calc_stamp_fee_rounded_up_to_100() -> None:
    """100원 단위 절상 검증."""
    fee = calc_stamp_fee(1_001)  # 1,001 * 0.005 = 5.005 → 100원 절상 = 100
    assert fee % 100 == 0
    assert fee >= 5


def test_calc_service_fee_default() -> None:
    """기본 7회 x 5,200원 = 36,400원."""
    assert calc_service_fee() == 5_200 * 7


def test_calc_service_fee_custom() -> None:
    assert calc_service_fee(10) == 5_200 * 10


# ─────────────────────────────────────────────
# 종합 견적
# ─────────────────────────────────────────────
def test_estimate_civil_general() -> None:
    """5천만 원 일반 민사."""
    r = estimate_litigation_cost(50_000_000, "civil_general")
    assert r["case_type"] == "civil_general"
    assert r["claim_amount_krw"] == 50_000_000
    assert r["court_fee_stamp_krw"] == 230_000
    assert r["service_fee_krw"] == 36_400
    assert r["total_court_fees_krw"] == 266_400
    assert r["small_claim_eligible"] is False  # 3천만 초과
    assert r["lawyer_fee"]["typical"] > 0
    assert r["total_typical_with_lawyer_krw"] > 5_000_000
    assert any("법률 자문이 아닙니다" in d for d in r["disclaimers"])


def test_estimate_small_claim_eligible() -> None:
    """2천만 원 → 소액사건심판 가능."""
    r = estimate_litigation_cost(20_000_000, "civil_general")
    assert r["small_claim_eligible"] is True
    assert r["total_self_litigation_krw"] is not None
    assert r["total_self_litigation_krw"] < 200_000  # 매우 저렴
    assert any("소액사건심판" in s for s in r["advice"])


def test_estimate_criminal_no_stamp() -> None:
    """형사는 인지대 없음 (소가 0)."""
    r = estimate_litigation_cost(0, "criminal_dui")
    assert r["court_fee_stamp_krw"] == 0
    assert r["service_fee_krw"] == 36_400
    assert r["lawyer_fee"]["typical"] > 0
    assert any("형사" in s for s in r["advice"])


def test_estimate_medical_extra_costs_noted() -> None:
    """의료사고는 감정 비용 별도 advice."""
    r = estimate_litigation_cost(100_000_000, "medical")
    assert any("감정" in s for s in r["advice"])
    assert "additional_costs" in r


def test_estimate_invalid_case_type_raises() -> None:
    with pytest.raises(ValueError, match="인식 불가"):
        estimate_litigation_cost(10_000_000, "unknown_type")


def test_estimate_negative_claim_raises() -> None:
    with pytest.raises(ValueError, match="음수 불가"):
        estimate_litigation_cost(-1, "civil_general")


def test_estimate_includes_free_resources() -> None:
    r = estimate_litigation_cost(10_000_000, "civil_general")
    names = [x["name"] for x in r["free_resources"]]
    assert any("법률구조공단" in n for n in names)
    assert any("고용노동부" in n for n in names)


def test_estimate_administrative_advice() -> None:
    r = estimate_litigation_cost(0, "administrative")
    assert any("행정심판" in s for s in r["advice"])
