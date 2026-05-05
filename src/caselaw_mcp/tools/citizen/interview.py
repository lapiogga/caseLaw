"""사실관계 다턴 인터뷰.

MCP는 stateless이므로 호스트 LLM이 turn=N + previous_answers 누적해 호출.
6턴 완료 시 case_profile 종합 + triage_dispute / check_statute_of_limitations
/ estimate_litigation_cost 후속 호출 권장 안내.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any

from caselaw_mcp.tools.citizen.disclaimer import attach


@lru_cache(maxsize=1)
def _load_flow() -> list[dict[str, Any]]:
    text = (
        resources.files("caselaw_mcp.citizen_data")
        .joinpath("interview_flow.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)["turns"]


def get_interview_flow() -> list[dict[str, Any]]:
    """6턴 인터뷰 플로우 전체 (LLM 사전 학습용)."""
    return _load_flow()


def interview_facts(
    turn: int = 1,
    previous_answers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """다턴 사실관계 인터뷰 — turn N의 질문 + 누적 case profile.

    Args:
        turn: 현재 턴 번호 (1~6). 기본 1.
        previous_answers: 이전 턴 답변 누적 dict.
            예: {"incident_summary": "...", "counterparty": "..."}

    Returns:
        {
            "turn": int,
            "is_final": bool,
            "topic": str,
            "question": str,
            "guidance": str,
            "examples": [...],
            "expected_field": str,        # 답변 저장 키
            "case_profile": {...},        # 누적 답변
            "next_action": str | null,    # 마지막 턴에 후속 도구 권장
            "next_call_hint": str,        # 다음 호출 방법
            "disclaimers": [...]
        }
    """
    flow = _load_flow()
    max_turn = len(flow)
    if not 1 <= turn <= max_turn:
        raise ValueError(f"turn 은 1~{max_turn} 범위여야 함: {turn}")

    spec = flow[turn - 1]
    profile = dict(previous_answers or {})

    response: dict[str, Any] = {
        "turn": turn,
        "total_turns": max_turn,
        "is_final": bool(spec.get("is_final", False)),
        "topic": spec["topic"],
        "question": spec["question"],
        "guidance": spec["guidance"],
        "examples": spec.get("examples", []),
        "expected_field": spec["field"],
        "case_profile": profile,
    }

    if turn < max_turn:
        next_spec = flow[turn]
        response["next_call_hint"] = (
            f"사용자 답변 받은 뒤 previous_answers에 '{spec['field']}' 키로 저장하고, "
            f"interview_facts(turn={turn + 1}, previous_answers=...) 호출."
        )
        response["next_topic"] = next_spec["topic"]
    else:
        response["next_action"] = (
            "인터뷰 완료. 이제 다음 도구를 순서대로 호출하면 종합 진단이 나옵니다:\n"
            "1) triage_dispute(situation=case_profile['incident_summary'], "
            "event_date=case_profile['quantitative']에서 추출)\n"
            "2) check_statute_of_limitations (triage 결과 카테고리 ID)\n"
            "3) estimate_litigation_cost (청구 금액 + case_type)"
        )
        response["case_profile_complete"] = True

    return attach(response, kinds=["standard", "ai_limitation"])
