"""interview_facts 다턴 인터뷰 단위 테스트."""

from __future__ import annotations

import pytest

from caselaw_mcp.tools.citizen.interview import get_interview_flow, interview_facts


def test_flow_has_six_turns() -> None:
    flow = get_interview_flow()
    assert len(flow) == 6
    assert flow[0]["turn"] == 1
    assert flow[-1]["turn"] == 6
    assert flow[-1].get("is_final") is True


def test_first_turn_question() -> None:
    r = interview_facts(turn=1)
    assert r["turn"] == 1
    assert r["is_final"] is False
    assert "시간 순서" in r["question"]
    assert r["expected_field"] == "incident_summary"
    assert r["case_profile"] == {}
    assert "next_call_hint" in r
    assert any("법률 자문이 아닙니다" in d for d in r["disclaimers"])


def test_middle_turn_carries_previous_answers() -> None:
    prev = {"incident_summary": "친구한테 5천만 원 빌려줬는데 안 갚음"}
    r = interview_facts(turn=2, previous_answers=prev)
    assert r["turn"] == 2
    assert r["case_profile"] == prev
    assert r["expected_field"] == "counterparty"


def test_final_turn_has_next_action() -> None:
    prev = {
        "incident_summary": "...",
        "counterparty": "...",
        "evidence": "...",
        "actions_taken": "...",
        "desired_outcome": "...",
    }
    r = interview_facts(turn=6, previous_answers=prev)
    assert r["is_final"] is True
    assert r["expected_field"] == "quantitative"
    assert "next_action" in r
    assert "triage_dispute" in r["next_action"]
    assert r["case_profile_complete"] is True


def test_invalid_turn_raises() -> None:
    with pytest.raises(ValueError, match="turn"):
        interview_facts(turn=0)
    with pytest.raises(ValueError, match="turn"):
        interview_facts(turn=7)


def test_each_turn_has_examples() -> None:
    for t in range(1, 7):
        r = interview_facts(turn=t)
        assert isinstance(r["examples"], list)
        assert len(r["examples"]) >= 1
