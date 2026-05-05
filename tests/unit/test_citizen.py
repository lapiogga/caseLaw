"""Citizen Mode 단위 테스트 — disclaimer / mode / triage."""

from __future__ import annotations

from pathlib import Path

import pytest

from caselaw_mcp.tools.citizen import disclaimer, mode, triage


# ─────────────────────────────────────────────
# disclaimer
# ─────────────────────────────────────────────
def test_disclaimer_standard_exists() -> None:
    text = disclaimer.get_disclaimer("standard")
    assert "법률 자문이 아닙니다" in text


def test_disclaimer_unknown_kind_falls_back_to_standard() -> None:
    text = disclaimer.get_disclaimer("nonexistent_kind")
    assert "법률 자문이 아닙니다" in text


def test_disclaimer_list_all() -> None:
    all_d = disclaimer.list_disclaimers()
    for k in (
        "standard",
        "statute_imminent",
        "criminal_serious",
        "victim_support_needed",
        "ai_limitation",
        "data_freshness",
    ):
        assert k in all_d
        assert isinstance(all_d[k], str)
        assert len(all_d[k]) > 10


def test_disclaimer_attach_default() -> None:
    out = disclaimer.attach({"x": 1})
    assert out["x"] == 1
    assert "disclaimers" in out
    assert len(out["disclaimers"]) == 1


def test_disclaimer_attach_multi() -> None:
    out = disclaimer.attach({"y": 2}, kinds=["standard", "statute_imminent", "ai_limitation"])
    assert len(out["disclaimers"]) == 3


def test_disclaimer_attach_immutable() -> None:
    src = {"z": 3}
    _ = disclaimer.attach(src, kinds=["standard"])
    assert "disclaimers" not in src  # 원본 불변


# ─────────────────────────────────────────────
# mode
# ─────────────────────────────────────────────
@pytest.fixture
def isolated_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """get_settings().cache_path 를 tmp_path로 격리해 mode.json 충돌 방지."""
    from caselaw_mcp import config as cfg

    fake = cfg.Settings(
        oc="test_oc", cache_path=tmp_path / "cache.db"
    )
    monkeypatch.setattr(cfg, "get_settings", lambda: fake)
    # mode 모듈도 같은 get_settings 를 import 해서 사용
    import caselaw_mcp.tools.citizen.mode as m
    monkeypatch.setattr(m, "get_settings", lambda: fake)
    return tmp_path


def test_mode_default_when_no_file(isolated_mode: Path) -> None:
    out = mode.get_user_mode()
    assert out["mode"] == "lawyer"
    assert out["source"] == "default"


def test_mode_set_and_get(isolated_mode: Path) -> None:
    set_out = mode.set_user_mode("citizen")
    assert set_out["mode"] == "citizen"
    assert set_out["changed"] is True

    get_out = mode.get_user_mode()
    assert get_out["mode"] == "citizen"
    assert get_out["source"] == "file"


def test_mode_invalid_raises(isolated_mode: Path) -> None:
    with pytest.raises(ValueError, match="mode must be one of"):
        mode.set_user_mode("expert")


def test_is_citizen_mode_helper(isolated_mode: Path) -> None:
    assert mode.is_citizen_mode() is False
    mode.set_user_mode("citizen")
    assert mode.is_citizen_mode() is True


# ─────────────────────────────────────────────
# triage
# ─────────────────────────────────────────────
def test_triage_loan_match() -> None:
    r = triage.triage_dispute(
        "3년 전 친구한테 5천만 원 빌려줬는데 안 갚고 있음. 차용증은 카톡으로만 있음."
    )
    ids = [c["id"] for c in r["candidates"]]
    assert "civil.loan" in ids
    assert r["candidates"][0]["domain"] == "민사"
    assert "disclaimers" in r
    assert any("법률 자문이 아닙니다" in d for d in r["disclaimers"])


def test_triage_dui_match_criminal_disclaimer() -> None:
    r = triage.triage_dispute("음주운전으로 단속됨. 면허 취소 통보받음.")
    ids = [c["id"] for c in r["candidates"]]
    assert "criminal.dui" in ids
    # 형사 사건 → criminal_serious 면책 자동 부착
    assert any("형사" in d or "신고" in d for d in r["disclaimers"])


def test_triage_unpaid_wage() -> None:
    r = triage.triage_dispute("회사가 6개월 임금 안 줘서 퇴사함. 퇴직금도 못 받음.")
    ids = [c["id"] for c in r["candidates"]]
    assert "labor.unpaid_wage" in ids
    primary = r["candidates"][0]
    assert primary["limitation_period_years"] == 3


def test_triage_with_event_date_safe() -> None:
    r = triage.triage_dispute(
        "친구한테 돈 빌려줬는데 안 갚음", event_date="2024-01-15"
    )
    primary = r["candidates"][0]
    assert "안전" in primary.get("limitation_status", "")


def test_triage_with_event_date_imminent() -> None:
    """단기 시효 케이스 — 사기 손해배상 (3년 시효), 2.5년 경과."""
    from datetime import date, timedelta

    long_ago = (date.today() - timedelta(days=int(2.7 * 365))).isoformat()
    r = triage.triage_dispute("사기당해서 손해배상 받고 싶음", event_date=long_ago)
    # imminent 또는 만료 경고 부착 (statute_imminent 면책)
    assert any("시효" in d or "임박" in d for d in r["disclaimers"])


def test_triage_with_event_date_expired() -> None:
    """시효 만료 케이스 — 임금채권 3년, 5년 전."""
    from datetime import date, timedelta

    long_ago = (date.today() - timedelta(days=5 * 365)).isoformat()
    r = triage.triage_dispute("회사가 임금 안 줘서 퇴사함", event_date=long_ago)
    primary = r["candidates"][0]
    assert "만료" in primary.get("limitation_status", "")


def test_triage_no_match_returns_guidance() -> None:
    r = triage.triage_dispute("별일 없습니다 그냥 안부 물어봅니다")
    assert r["candidates"] == []
    assert r["matched_count"] == 0
    assert any("키워드" in s or "변호사" in s for s in r["next_steps"])


def test_triage_empty_input_raises() -> None:
    with pytest.raises(ValueError, match="비어있음"):
        triage.triage_dispute("")


def test_triage_top_k_clamped() -> None:
    # top_k > 5 라도 5로 제한
    r = triage.triage_dispute(
        "음주운전 사기 폭행 명예훼손 임대차 임금체불 양육비 면허취소 의료사고", top_k=99
    )
    assert len(r["candidates"]) <= 5


def test_triage_includes_support_resources_when_available() -> None:
    """가정 분쟁 (이혼) 카테고리에 support_resources 포함 검증."""
    r = triage.triage_dispute("이혼하고 싶음, 위자료와 양육권 문제")
    primary = r["candidates"][0]
    if primary["id"] == "family.divorce":
        assert "support_resources" in primary
