"""소멸시효·공소시효 점검 단위 테스트."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from caselaw_mcp.tools.citizen.limitation import (
    check_statute_of_limitations,
    list_limitation_categories,
)


def test_list_categories_returns_seed_data() -> None:
    cats = list_limitation_categories()
    assert len(cats) >= 25
    ids = [c["id"] for c in cats]
    for must in ("civil.general", "tort", "wage", "criminal.dui", "labor.unfair_dismissal"):
        assert must in ids


def test_check_safe() -> None:
    """일반 채권 10년, 1년 전 → safe."""
    one_year_ago = (date.today() - timedelta(days=365)).isoformat()
    r = check_statute_of_limitations("civil.general", one_year_ago)
    assert r["status"] == "safe"
    assert r["remaining_years"] > 8.5
    assert any("법률 자문이 아닙니다" in d for d in r["disclaimers"])


def test_check_imminent() -> None:
    """일반 채권 10년, 9.5년 전 → imminent (잔여 < 1년)."""
    nine_half = (date.today() - timedelta(days=int(9.5 * 365.25))).isoformat()
    r = check_statute_of_limitations("civil.general", nine_half)
    assert r["status"] == "imminent"
    # statute_imminent 면책 자동 부착
    assert any("시효" in d and "변호사" in d for d in r["disclaimers"])


def test_check_expired() -> None:
    """임금 채권 3년, 5년 전 → expired."""
    five_yrs = (date.today() - timedelta(days=int(5 * 365.25))).isoformat()
    r = check_statute_of_limitations("wage", five_yrs)
    assert r["status"] == "expired"
    assert "만료" in r["advice"]


def test_check_warning() -> None:
    """임금 채권 3년, 1.5년 전 → warning (잔여 1~2년)."""
    one_half = (date.today() - timedelta(days=int(1.5 * 365.25))).isoformat()
    r = check_statute_of_limitations("wage", one_half)
    assert r["status"] == "warning"


def test_check_indefinite() -> None:
    """미성년자 성폭력 손해배상 → period_years = null → indefinite."""
    r = check_statute_of_limitations("tort_minor_sexual", "2020-01-01")
    assert r["status"] == "indefinite"


def test_check_invalid_category_raises() -> None:
    with pytest.raises(ValueError, match="인식 불가"):
        check_statute_of_limitations("nonexistent.id", "2024-01-01")


def test_check_invalid_date_raises() -> None:
    with pytest.raises(ValueError):
        check_statute_of_limitations("civil.general", "")


def test_check_interruption_events_present_for_civil() -> None:
    """일반 채권은 시효 중단 가능 → interruption_events 포함."""
    r = check_statute_of_limitations("civil.general", "2024-01-01")
    assert r["interruption_applicable"] is True
    assert len(r["interruption_events"]) >= 4
    names = [e["name"] for e in r["interruption_events"]]
    assert "재판상 청구" in names
    assert "압류·가압류·가처분" in names


def test_check_no_interruption_for_criminal() -> None:
    """공소시효는 일반적으로 중단 사유 적용 제한 → interruption_events 빈 리스트 + note."""
    r = check_statute_of_limitations("criminal.dui", "2024-01-01")
    assert r["interruption_applicable"] is False
    assert r["interruption_events"] == []
    assert "interruption_note" in r


def test_check_yyyymmdd_format_accepted() -> None:
    """YYYYMMDD 형식도 허용."""
    r = check_statute_of_limitations("civil.general", "20240101")
    assert r["event_date"] == "2024-01-01"


def test_check_short_deadline_unfair_dismissal() -> None:
    """부당해고 90일, 30일 전 → imminent."""
    thirty_days_ago = (date.today() - timedelta(days=30)).isoformat()
    r = check_statute_of_limitations("labor.unfair_dismissal", thirty_days_ago)
    # 90일 한도 0.247년 - 30/365.25 = 0.165 잔여
    assert r["status"] in ("imminent", "warning")
    assert r["remaining_years"] is not None
    assert r["remaining_years"] < 0.5
