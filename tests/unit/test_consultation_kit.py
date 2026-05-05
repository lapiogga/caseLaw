"""prepare_consultation_kit 단위 테스트."""

from __future__ import annotations

import pytest

from caselaw_mcp.tools.citizen.consultation_kit import (
    _build_evidence_checklist,
    _build_questions,
    _estimate_session_minutes,
    prepare_consultation_kit,
)


def test_kit_minimal_input() -> None:
    profile = {
        "incident_summary": "친구한테 5천만원 빌려줬는데 안 갚음",
        "counterparty": "홍길동 010-1234-5678",
        "evidence": "차용증, 송금내역",
        "actions_taken": "전화·문자 5회",
        "desired_outcome": "5천만원 회수",
        "quantitative": "사건일: 2024-03-05, 금액: 5천만원",
    }
    r = prepare_consultation_kit(profile)
    md = r["markdown"]
    assert "변호사 상담 준비 자료" in md
    assert "5천만원" in md
    assert "1. 사건 요약" in md
    assert "11. 변호사에게 물어볼 질문 10가지" in md
    assert len(r["questions_for_lawyer"]) == 10
    assert len(r["checklist_evidence"]) >= 4
    assert any("법률 자문이 아닙니다" in d for d in r["disclaimers"])


def test_kit_with_full_context() -> None:
    profile = {
        "incident_summary": "임금체불 6개월",
        "counterparty": "ABC 회사",
        "evidence": "근로계약서, 급여명세서",
        "actions_taken": "고용노동청 진정",
        "desired_outcome": "체불임금 회수",
        "quantitative": "2025-08-01, 1500만원",
    }
    triage = {
        "candidates": [
            {
                "id": "labor.unpaid_wage",
                "name": "임금체불",
                "domain": "노동",
                "applicable_laws": ["근로기준법 제36조"],
                "typical_path": "노동청 진정 → 민사",
                "complexity": "low",
                "key_evidence": ["근로계약서", "급여명세서"],
                "common_issues": ["근로자성 인정"],
            }
        ]
    }
    statute = {
        "category": "임금 채권",
        "period_years": 3,
        "elapsed_years": 0.5,
        "remaining_years": 2.5,
        "status": "safe",
        "advice": "안전",
    }
    cost = {
        "court_fee_stamp_krw": 72500,
        "service_fee_krw": 36400,
        "lawyer_fee": {"low": 2_000_000, "typical": 4_000_000, "high": 8_000_000},
        "small_claim_eligible": True,
        "total_self_litigation_krw": 108_900,
        "total_typical_with_lawyer_krw": 4_108_900,
    }
    pro_bono = {
        "national": [{"name": "고용노동부", "phone": "1350", "scope": "임금체불"}],
        "regional_bar": [{"name": "서울지방변호사회", "phone": "02-3476-4000", "region": "서울"}],
        "emergency": [],
    }
    r = prepare_consultation_kit(
        profile,
        triage_result=triage,
        statute_result=statute,
        cost_result=cost,
        pro_bono_result=pro_bono,
    )
    md = r["markdown"]
    assert "임금체불" in md
    assert "근로기준법 제36조" in md
    assert "안전" in md
    assert "4,000,000원" in md
    assert "소액사건심판 가능" in md
    assert "고용노동부" in md
    assert "서울지방변호사회" in md
    assert r["estimated_lawyer_session_minutes"] == 30  # complexity=low


def test_kit_imminent_statute_warning() -> None:
    profile = {"incident_summary": "X"}
    statute = {
        "category": "임금 채권",
        "period_years": 3,
        "elapsed_years": 2.7,
        "remaining_years": 0.3,
        "status": "imminent",
        "advice": "임박",
    }
    r = prepare_consultation_kit(profile, statute_result=statute)
    assert any("시효" in s and ("1주일" in s or "임박" in s) for s in r["next_steps"])


def test_kit_empty_profile_raises() -> None:
    with pytest.raises(ValueError, match="비어있음"):
        prepare_consultation_kit({})


def test_kit_questions_include_complexity_specific() -> None:
    triage = {
        "candidates": [
            {
                "complexity": "high",
                "common_issues": ["과실 입증", "인과관계"],
            }
        ]
    }
    qs = _build_questions(triage, None, None)
    assert any("과실 입증" in q for q in qs)


def test_kit_session_minutes_by_complexity() -> None:
    assert _estimate_session_minutes(None) == 30
    assert _estimate_session_minutes({"candidates": [{"complexity": "very_low"}]}) == 20
    assert _estimate_session_minutes({"candidates": [{"complexity": "very_high"}]}) == 90


def test_kit_checklist_default_when_no_triage() -> None:
    cl = _build_evidence_checklist(None)
    assert len(cl) >= 4
    assert any("백업" in c for c in cl)
