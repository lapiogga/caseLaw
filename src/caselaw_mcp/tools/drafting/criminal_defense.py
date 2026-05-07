"""형사 변호인 의견서 마크다운 골격.

공소사실 요지 → 변호인 의견 → 양형 자료 (감경 사유) → 유사 판례.
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.tools.drafting import templates


def draft(
    defendant: dict[str, Any],
    case_number: str,
    charges: list[str],
    our_arguments: list[str],
    mitigating_factors: list[str] | None = None,
    similar_precedents: list[int] | None = None,
    applicable_statutes: list[str] | None = None,
    requested_outcome: str | None = None,
    user_mode: str = "lawyer",
) -> dict[str, Any]:
    """형사 변호인 의견서 마크다운 초안.

    Args:
        defendant: {"name": str (필수), "address": str, ...}
        case_number: 사건번호 (예: "2025고단12345").
        charges: 공소사실 항목 리스트. 빈 거부.
        our_arguments: 변호인 주장 항목. 빈 거부.
        mitigating_factors: 양형 감경 사유 (예: ["초범", "합의", "반성문"]).
        similar_precedents: 유사 판례 prec_id (양형 비교용).
        applicable_statutes: 적용 법조 (예: ["도로교통법 제148조의2"]).
        requested_outcome: 요청 처분 (예: "선고유예", "벌금형 선고", "공소기각").
            None 이면 placeholder.
        user_mode: "lawyer" / "citizen".

    Returns:
        {
          "doc_type": "criminal_defense",
          "case_number": str,
          "defendant_name": str,
          "charge_count": int,
          "markdown": str
        }
    """
    templates.validate_party(defendant, "피고인")
    if not isinstance(case_number, str) or not case_number.strip():
        raise ValueError("case_number: 비어있지 않은 문자열 필요")
    templates.validate_non_empty_list(charges, "charges")
    templates.validate_non_empty_list(our_arguments, "our_arguments")

    case_number = case_number.strip()
    defendant_name = str(defendant.get("name", "")).strip()
    requested = (requested_outcome or "").strip() or "*(요청 처분 미기재 — 변호사 검토 시 보충)*"

    charges_md = "\n".join(
        f"{i}. {str(c).strip()}" for i, c in enumerate(charges, 1) if str(c).strip()
    )
    arguments_md = "\n".join(
        f"{i}. {str(a).strip()}" for i, a in enumerate(our_arguments, 1) if str(a).strip()
    )

    if mitigating_factors:
        mit_md = "\n".join(f"- {str(m).strip()}" for m in mitigating_factors if str(m).strip())
    else:
        mit_md = "*(양형 감경 사유 미기재 — 변호사 검토 시 보충)*"

    body = f"""# 변 호 인 의 견 서

**사건**: {case_number}
**피고인**: {defendant_name}
**작성일**: {templates.md_today_kr()}

---

## 1. 피고인 인적사항

{templates.md_party_table("피고인", defendant)}

---

## 2. 공소사실의 요지

{charges_md}

---

## 3. 변호인의 의견

{arguments_md}

---

## 4. 양형에 관한 의견

### 감경 사유

{mit_md}

### 요청 처분

{requested}

---

## 5. 적용 법조

{templates.md_statute_basis(applicable_statutes)}

---

## 6. 유사 판례 (양형 비교)

{templates.md_precedent_block(similar_precedents)}

> **참고**: caselaw `analyze_precedent_trend` 또는 `evaluate_case_strength` 로
> 유사 사건 양형 분포를 사전 분석한 결과를 본 항목에 인용하세요.

---

{templates.md_today_kr()}

피고인 변호인  ____________________  변호사 (서명)
"""

    markdown = templates.attach_disclaimer(body, user_mode=user_mode)
    return {
        "doc_type": "criminal_defense",
        "case_number": case_number,
        "defendant_name": defendant_name,
        "charge_count": len([c for c in charges if str(c).strip()]),
        "markdown": markdown,
    }
