"""법률의견서 마크다운 골격.

쟁점 → 법리 → 결론 정형. 변호사 자체 검토 + 의뢰인 보고용.
"""

from __future__ import annotations

from typing import Any

from caselaw_mcp.tools.drafting import templates


def draft(
    case_facts: list[str],
    issues: list[str],
    similar_precedents: list[int] | None = None,
    applicable_statutes: list[str] | None = None,
    conclusion_summary: str | None = None,
    client_name: str | None = None,
    case_caption: str | None = None,
    user_mode: str = "lawyer",
) -> dict[str, Any]:
    """법률의견서 마크다운 초안.

    Args:
        case_facts: 사실관계 항목 리스트. 빈 거부.
        issues: 법적 쟁점 항목 리스트. 빈 거부.
        similar_precedents: 유사 판례 prec_id.
        applicable_statutes: 적용 법조.
        conclusion_summary: 결론 1~2 줄 요약. None 이면 "변호사 검토 후 보충" placeholder.
        client_name: 의뢰인 명. None 이면 "의뢰인" 표기.
        case_caption: 사건명 또는 자문 제목. None 이면 "법률 자문".
        user_mode: "lawyer" / "citizen".

    Returns:
        {
          "doc_type": "legal_opinion",
          "case_caption": str,
          "issue_count": int,
          "markdown": str
        }
    """
    templates.validate_non_empty_list(case_facts, "case_facts")
    templates.validate_non_empty_list(issues, "issues")

    caption = (case_caption or "법률 자문").strip()
    client = (client_name or "의뢰인").strip()
    conclusion = (conclusion_summary or "").strip() or "*(결론 미작성 — 변호사 검토 후 보충)*"

    issues_md = "\n".join(
        f"{i}. {str(q).strip()}" for i, q in enumerate(issues, 1) if str(q).strip()
    )

    body = f"""# 법률의견서

**사건명**: {caption}
**의뢰인**: {client}
**작성일**: {templates.md_today_kr()}

---

## 1. 사실관계

{templates.md_chronology(case_facts)}

---

## 2. 검토 쟁점

{issues_md}

---

## 3. 관련 법령

{templates.md_statute_basis(applicable_statutes)}

---

## 4. 관련 판례 분석

{templates.md_precedent_block(similar_precedents)}

> **법리 적용 메모**: 위 판례를 본건 사실관계에 적용하면…
> *(변호사가 직접 작성. caselaw `compare_precedents` / `analyze_precedent_trend` 활용 권장.)*

---

## 5. 결론

{conclusion}

---

## 6. 권장 다음 단계

- *(예: 화해 시도, 소제기, 추가 사실조사 등을 변호사가 작성)*

{templates.md_today_kr()}

작성자  ____________________  변호사 (서명)
"""

    markdown = templates.attach_disclaimer(body, user_mode=user_mode)
    return {
        "doc_type": "legal_opinion",
        "case_caption": caption,
        "issue_count": len([i for i in issues if str(i).strip()]),
        "markdown": markdown,
    }
