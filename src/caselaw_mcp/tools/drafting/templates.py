"""drafting 모듈 공통 마크다운 헬퍼.

- 당사자 표 / 사실 연혁 표 / 인용 블록 / 증거 목록 / 적용법조 블록
- 모든 draft_* 출력 끝에 자동 부착되는 면책 블록 (회귀 가드)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

# ─────────────────────────────────────────────
# 면책 블록 (모든 draft_* 출력 끝에 자동 부착)
# 변호사 모드는 짧은 면책, 일반인 모드는 강한 경고 + 추천 다음 단계.
# DISCLAIMER_MARKER 는 단위 테스트가 회귀 가드용으로 grep 한다 — 변경 금지.
# ─────────────────────────────────────────────
DISCLAIMER_MARKER = "본 문서는 caselaw MCP 가 자동 생성한 **초안**입니다."

DISCLAIMER_LAWYER = f"""
---
> ⚠️ **면책**: {DISCLAIMER_MARKER}
> 법적 효력이 없으며, 법원 제출·상대방 송달 전 반드시 자격 있는 변호사의
> 검토를 받으십시오. 본 도구는 변호사 작업 보조용이며, 직접 법률 자문을
> 제공하지 않습니다.
"""

DISCLAIMER_CITIZEN = f"""
---
## ⚠️ 매우 중요 — 반드시 읽으세요

{DISCLAIMER_MARKER}

**이 문서를 그대로 법원에 제출하면 안 됩니다.** 사용 전 다음을 확인하세요:

1. **변호사 검토 필수** — 무료 상담을 위해 `recommend_pro_bono` 도구로
   거주 지역의 무료 법률상담 기관을 찾으세요 (대한법률구조공단 132,
   여성긴급전화 1366 등).
2. **사실관계 정확성** — AI 가 만든 초안이라 실제 사건과 다를 수 있습니다.
   생년월일·주소·금액·날짜를 직접 다시 확인하세요.
3. **법률 효력 없음** — 본 도구는 변호사가 아니며, 직접 법률 자문을
   제공하지 않습니다.

---
"""


def attach_disclaimer(markdown: str, user_mode: str = "lawyer") -> str:
    """초안 마크다운 끝에 면책 부착. 빈 문자열에도 부착 (회귀 방지)."""
    if user_mode == "citizen":
        return markdown.rstrip() + "\n" + DISCLAIMER_CITIZEN
    return markdown.rstrip() + "\n" + DISCLAIMER_LAWYER


# ─────────────────────────────────────────────
# 입력 검증 (시스템 경계)
# ─────────────────────────────────────────────
def validate_party(party: dict[str, Any], role: str) -> None:
    """당사자 dict 최소 검증. 빈 이름·dict 거부."""
    if not isinstance(party, dict):
        raise ValueError(f"{role}: dict 가 필요합니다 (got {type(party).__name__})")
    name = party.get("name", "").strip() if isinstance(party.get("name"), str) else ""
    if not name:
        raise ValueError(f"{role}: 'name' 필수 (빈 문자열·누락 거부)")


def validate_amount(amount: Any, field: str = "amount") -> int:
    """청구금액 검증. 음수·소수점·문자열 거부."""
    if isinstance(amount, bool):  # bool 은 int 의 subclass 라 명시 거부
        raise ValueError(f"{field}: bool 거부 (정수 KRW 값 필요)")
    if not isinstance(amount, int):
        raise ValueError(f"{field}: 정수 필요 (got {type(amount).__name__})")
    if amount < 0:
        raise ValueError(f"{field}: 음수 거부 (got {amount})")
    return amount


def validate_non_empty_list(items: Any, field: str) -> list[Any]:
    """빈 리스트 거부 (사실관계·증거 등 필수 다항목)."""
    if not isinstance(items, list):
        raise ValueError(f"{field}: list 필요 (got {type(items).__name__})")
    if len(items) == 0:
        raise ValueError(f"{field}: 빈 리스트 거부")
    return items


# ─────────────────────────────────────────────
# 마크다운 헬퍼
# ─────────────────────────────────────────────
def md_party_table(role: str, party: dict[str, Any]) -> str:
    """당사자 정보를 마크다운 표로."""
    name = party.get("name", "").strip()
    address = party.get("address", "").strip() or "(주소 미기재)"
    phone = party.get("phone", "").strip() or "(연락처 미기재)"
    return (
        f"### {role}\n\n"
        f"| 항목 | 내용 |\n"
        f"|---|---|\n"
        f"| 성명 | {name} |\n"
        f"| 주소 | {address} |\n"
        f"| 연락처 | {phone} |\n"
    )


def md_chronology(facts: list[str]) -> str:
    """사실관계 6하원칙 항목별 번호 매기기."""
    lines = []
    for i, fact in enumerate(facts, 1):
        clean = str(fact).strip()
        if clean:
            lines.append(f"{i}. {clean}")
    if not lines:
        return "(사실관계 미기재)"
    return "\n".join(lines)


def md_evidence_list(evidence: list[dict[str, Any]] | None) -> str:
    """증거 목록 마크다운 표. None·빈 리스트는 placeholder."""
    if not evidence:
        return "*(증거 목록 미기재 — 변호사 검토 시 추가)*"
    rows = ["| 번호 | 증거 명칭 | 입증 취지 |", "|---|---|---|"]
    for i, item in enumerate(evidence, 1):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip() or "(미기재)"
        purpose = str(item.get("purpose", "")).strip() or "(미기재)"
        rows.append(f"| 갑 제{i}호증 | {name} | {purpose} |")
    return "\n".join(rows)


def md_statute_basis(statutes: list[str] | None) -> str:
    """적용 법조 마크다운 리스트."""
    if not statutes:
        return "*(적용 법조 미기재 — 변호사 검토 시 추가)*"
    return "\n".join(f"- {str(s).strip()}" for s in statutes if str(s).strip())


def md_precedent_block(prec_ids: list[int] | None) -> str:
    """관련 판례 인용 블록. prec_id 만 받아 본문 조회는 안 함 (호출자 책임)."""
    if not prec_ids:
        return "*(관련 판례 없음)*"
    lines = []
    for pid in prec_ids:
        try:
            pid_int = int(pid)
            lines.append(
                f"- 판례일련번호 `{pid_int}` (caselaw `get_precedent({pid_int})` 로 본문 조회)"
            )
        except (TypeError, ValueError):
            continue
    return "\n".join(lines) if lines else "*(유효한 prec_id 없음)*"


def md_today_kr() -> str:
    """오늘 날짜 한국 형식 (YYYY. M. D.)."""
    now = datetime.now(UTC)
    return f"{now.year}. {now.month}. {now.day}."
