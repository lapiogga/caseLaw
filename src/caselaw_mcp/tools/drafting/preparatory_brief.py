"""준비서면 마크다운 골격.

변론 단계에서 우리(원고/피고) 입장 정리 → 상대방 주장 반박 → 결론 다시.
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.tools.drafting import templates


def draft(
    case_caption: str,
    case_number: str,
    our_role: str,
    our_position: list[str],
    opponent_arguments: list[str] | None = None,
    rebuttal_points: list[str] | None = None,
    our_evidence: list[dict[str, Any]] | None = None,
    related_precedents: list[int] | None = None,
    applicable_statutes: list[str] | None = None,
    user_mode: str = "lawyer",
) -> dict[str, Any]:
    """준비서면 마크다운 초안.

    Args:
        case_caption: 사건명 (예: "대여금 청구의 소").
        case_number: 사건번호 (예: "2025가단12345").
        our_role: "원고" / "피고" / "원고 대리인" 등.
        our_position: 우리 측 주장 항목 리스트. 빈 거부.
        opponent_arguments: 상대방 주장 항목 (선택, 빈 가능).
        rebuttal_points: 상대방 주장에 대한 반박 항목 (선택).
        our_evidence: 추가 제출 증거 [{"name": str, "purpose": str}].
        related_precedents: 인용 판례 prec_id.
        applicable_statutes: 적용 법조.
        user_mode: "lawyer" / "citizen".

    Returns:
        {
          "doc_type": "preparatory_brief",
          "case_caption": str,
          "case_number": str,
          "markdown": str
        }
    """
    if not isinstance(case_caption, str) or not case_caption.strip():
        raise ValueError("case_caption: 비어있지 않은 문자열 필요")
    if not isinstance(case_number, str) or not case_number.strip():
        raise ValueError("case_number: 비어있지 않은 문자열 필요")
    if not isinstance(our_role, str) or not our_role.strip():
        raise ValueError("our_role: 비어있지 않은 문자열 필요")
    templates.validate_non_empty_list(our_position, "our_position")

    case_caption = case_caption.strip()
    case_number = case_number.strip()
    our_role = our_role.strip()

    position_md = "\n".join(
        f"{i}. {str(p).strip()}" for i, p in enumerate(our_position, 1) if str(p).strip()
    )

    if opponent_arguments:
        opponent_md = "\n".join(
            f"{i}. {str(o).strip()}" for i, o in enumerate(opponent_arguments, 1) if str(o).strip()
        )
        opponent_section = f"## 2. 상대방 주장의 요지\n\n{opponent_md}\n"
    else:
        opponent_section = (
            "## 2. 상대방 주장의 요지\n\n*(해당사항 없음 또는 변호사 검토 시 보충)*\n"
        )

    if rebuttal_points:
        rebuttal_md = "\n".join(
            f"{i}. {str(r).strip()}" for i, r in enumerate(rebuttal_points, 1) if str(r).strip()
        )
        rebuttal_section = f"## 3. 반박\n\n{rebuttal_md}\n"
    else:
        rebuttal_section = "## 3. 반박\n\n*(상대방 주장이 있는 경우에만 작성)*\n"

    body = f"""# 준 비 서 면

**사건**: {case_number} {case_caption}
**작성일**: {templates.md_today_kr()}
**작성 당사자**: {our_role}

---

## 1. 우리 측 주장의 요지

{position_md}

---

{opponent_section}

---

{rebuttal_section}

---

## 4. 적용 법조

{templates.md_statute_basis(applicable_statutes)}

---

## 5. 관련 판례

{templates.md_precedent_block(related_precedents)}

---

## 6. 추가 입증방법

{templates.md_evidence_list(our_evidence)}

---

{templates.md_today_kr()}

{our_role}  ____________________  (서명)
"""

    markdown = templates.attach_disclaimer(body, user_mode=user_mode)
    return {
        "doc_type": "preparatory_brief",
        "case_caption": case_caption,
        "case_number": case_number,
        "markdown": markdown,
    }
