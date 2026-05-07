"""민사 소장 마크다운 골격 자동 생성.

대법원 전자소송 표준 + 찾기쉬운 생활법령정보 양식 기준.
필수 4 요소: 당사자 / 청구취지 / 청구원인 (6하) / 입증방법.
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.tools.drafting import templates


def draft(
    plaintiff: dict[str, Any],
    defendant: dict[str, Any],
    claim_type: str,
    claim_amount: int,
    facts_chronology: list[str],
    statute_basis: list[str] | None = None,
    related_precedents: list[int] | None = None,
    evidence_list: list[dict[str, Any]] | None = None,
    court_name: str = "서울중앙지방법원",
    interest_rate_percent: float | None = 12.0,
    user_mode: str = "lawyer",
) -> dict[str, Any]:
    """민사 소장 마크다운 초안 생성.

    Args:
        plaintiff: {"name": str (필수), "address": str, "phone": str}
        defendant: 동일 형식
        claim_type: 청구 유형 자유 텍스트 (예: "대여금", "손해배상", "물품대금")
        claim_amount: 청구 금액 (원). 음수·bool 거부.
        facts_chronology: 사실관계 항목 리스트 (6하원칙 권장).
            빈 리스트 거부.
        statute_basis: 적용 법조 (예: ["민법 제603조 (소비대차)"]).
        related_precedents: 관련 판례 prec_id 리스트.
        evidence_list: [{"name": str, "purpose": str}, ...].
        court_name: 관할 법원 (기본 서울중앙지방법원).
        interest_rate_percent: 지연손해금 비율 (None 이면 청구취지에서 생략).
        user_mode: "lawyer" (기본, 짧은 면책) / "citizen" (강한 경고).

    Returns:
        {
          "doc_type": "civil_complaint",
          "court_name": str,
          "claim_type": str,
          "claim_amount": int,
          "markdown": str (마크다운 본문 + 면책 부착)
        }
    """
    templates.validate_party(plaintiff, "원고")
    templates.validate_party(defendant, "피고")
    templates.validate_amount(claim_amount, "claim_amount")
    templates.validate_non_empty_list(facts_chronology, "facts_chronology")
    if not isinstance(claim_type, str) or not claim_type.strip():
        raise ValueError("claim_type: 비어있지 않은 문자열 필요")

    claim_type = claim_type.strip()
    formatted_amount = f"{claim_amount:,}원"
    interest_clause = ""
    if interest_rate_percent is not None and interest_rate_percent > 0:
        interest_clause = (
            f" 및 이에 대한 변제기일 다음날부터 다 갚는 날까지 "
            f"연 {interest_rate_percent:g}% 비율의 지연손해금"
        )

    body = f"""# 소  장

**사건**: {claim_type} 청구의 소
**관할 법원**: {court_name}
**작성일**: {templates.md_today_kr()}

---

## 1. 당사자

{templates.md_party_table("원고", plaintiff)}

{templates.md_party_table("피고", defendant)}

---

## 2. 청구취지

1. 피고는 원고에게 {formatted_amount}{interest_clause}을 지급하라.
2. 소송비용은 피고가 부담한다.
3. 제1항은 가집행할 수 있다.

라는 판결을 구합니다.

---

## 3. 청구원인

{templates.md_chronology(facts_chronology)}

---

## 4. 적용 법조

{templates.md_statute_basis(statute_basis)}

---

## 5. 관련 판례

{templates.md_precedent_block(related_precedents)}

---

## 6. 입증방법

{templates.md_evidence_list(evidence_list)}

---

## 7. 부속서류

1. 위 입증방법 각 1통
2. 소장 부본 1통
3. 송달료 납부서

{templates.md_today_kr()}

원고  {plaintiff.get("name", "").strip()}  (서명 또는 날인)

**{court_name}** 귀중
"""

    markdown = templates.attach_disclaimer(body, user_mode=user_mode)
    return {
        "doc_type": "civil_complaint",
        "court_name": court_name,
        "claim_type": claim_type,
        "claim_amount": claim_amount,
        "markdown": markdown,
    }
