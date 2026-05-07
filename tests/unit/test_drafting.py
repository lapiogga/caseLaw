"""drafting 모듈 단위 테스트.

면책 자동 부착(회귀 가드) + 입력 검증 + 마크다운 핵심 헤더 포함 검증.
실제 한국 법률 양식 정합성은 변호사 검토 단계에서 확인 (자동 검증 범위 외).
"""

from __future__ import annotations

import pytest

from caselaw_mcp.tools.drafting import (
    civil_complaint,
    criminal_defense,
    legal_opinion,
    preparatory_brief,
    templates,
)
from caselaw_mcp.tools.drafting.templates import DISCLAIMER_MARKER


# ─────────────────────────────────────────────
# templates.py — 입력 검증 + 마크다운 헬퍼
# ─────────────────────────────────────────────
class TestTemplates:
    def test_validate_party_rejects_missing_name(self) -> None:
        with pytest.raises(ValueError, match="name"):
            templates.validate_party({}, "원고")

    def test_validate_party_rejects_empty_name(self) -> None:
        with pytest.raises(ValueError, match="name"):
            templates.validate_party({"name": "  "}, "원고")

    def test_validate_party_rejects_non_dict(self) -> None:
        with pytest.raises(ValueError, match="dict"):
            templates.validate_party("박원고", "원고")  # type: ignore[arg-type]

    def test_validate_party_accepts_minimum(self) -> None:
        templates.validate_party({"name": "박원고"}, "원고")  # no raise

    def test_validate_amount_rejects_negative(self) -> None:
        with pytest.raises(ValueError, match="음수"):
            templates.validate_amount(-1)

    def test_validate_amount_rejects_float(self) -> None:
        with pytest.raises(ValueError, match="정수"):
            templates.validate_amount(1.5)

    def test_validate_amount_rejects_bool(self) -> None:
        with pytest.raises(ValueError, match="bool"):
            templates.validate_amount(True)

    def test_validate_amount_zero_ok(self) -> None:
        assert templates.validate_amount(0) == 0

    def test_validate_non_empty_list_rejects_empty(self) -> None:
        with pytest.raises(ValueError, match="빈 리스트"):
            templates.validate_non_empty_list([], "facts")

    def test_validate_non_empty_list_rejects_non_list(self) -> None:
        with pytest.raises(ValueError, match="list"):
            templates.validate_non_empty_list("a,b,c", "facts")  # type: ignore[arg-type]

    def test_md_party_table_uses_placeholder_for_missing(self) -> None:
        out = templates.md_party_table("원고", {"name": "박원고"})
        assert "박원고" in out
        assert "(주소 미기재)" in out
        assert "(연락처 미기재)" in out

    def test_md_chronology_numbers_items(self) -> None:
        out = templates.md_chronology(["사실 A", "사실 B"])
        assert "1. 사실 A" in out
        assert "2. 사실 B" in out

    def test_md_evidence_list_placeholder_when_empty(self) -> None:
        out = templates.md_evidence_list(None)
        assert "미기재" in out

    def test_md_evidence_list_numbers_with_갑호증(self) -> None:
        out = templates.md_evidence_list(
            [
                {"name": "차용증", "purpose": "대여 사실 입증"},
                {"name": "통장 사본", "purpose": "송금 사실 입증"},
            ]
        )
        assert "갑 제1호증" in out
        assert "차용증" in out
        assert "갑 제2호증" in out

    def test_md_precedent_block_filters_invalid(self) -> None:
        out = templates.md_precedent_block([616247, "abc", 614335])
        assert "616247" in out
        assert "614335" in out
        assert "abc" not in out

    def test_attach_disclaimer_lawyer_mode(self) -> None:
        out = templates.attach_disclaimer("# 본문\n\n내용", user_mode="lawyer")
        assert DISCLAIMER_MARKER in out
        # 변호사 모드 면책 핵심 어휘 (줄바꿈에 무관하게 등장 보장)
        assert "변호사" in out
        assert "검토" in out
        # citizen 모드 강한 경고 문구는 lawyer 에 없어야
        assert "1366" not in out
        assert "법률구조공단" not in out

    def test_attach_disclaimer_citizen_mode(self) -> None:
        out = templates.attach_disclaimer("# 본문", user_mode="citizen")
        assert DISCLAIMER_MARKER in out
        assert "1366" in out  # 여성긴급전화 안내
        assert "법률구조공단" in out

    def test_attach_disclaimer_unknown_mode_falls_back_to_lawyer(self) -> None:
        out = templates.attach_disclaimer("내용", user_mode="alien")
        assert DISCLAIMER_MARKER in out


# ─────────────────────────────────────────────
# civil_complaint — 민사 소장
# ─────────────────────────────────────────────
class TestCivilComplaint:
    @pytest.fixture
    def base_inputs(self) -> dict:
        return {
            "plaintiff": {
                "name": "박원고",
                "address": "서울 강남구",
                "phone": "010-0000-1111",
            },
            "defendant": {"name": "김피고", "address": "서울 송파구"},
            "claim_type": "대여금",
            "claim_amount": 50_000_000,
            "facts_chronology": [
                "원고는 2022. 3. 15. 피고에게 5천만 원을 대여하였다.",
                "변제기는 2023. 3. 14. 이었으나 피고는 변제하지 않았다.",
            ],
        }

    def test_minimum_inputs_produce_valid_markdown(self, base_inputs: dict) -> None:
        result = civil_complaint.draft(**base_inputs)
        assert result["doc_type"] == "civil_complaint"
        md = result["markdown"]
        assert "# 소  장" in md
        assert "박원고" in md
        assert "김피고" in md
        assert "50,000,000원" in md
        assert "청구취지" in md
        assert "청구원인" in md
        # 면책 회귀 가드
        assert DISCLAIMER_MARKER in md

    def test_custom_court_propagates(self, base_inputs: dict) -> None:
        result = civil_complaint.draft(**base_inputs, court_name="부산지방법원")
        assert result["court_name"] == "부산지방법원"
        assert "부산지방법원" in result["markdown"]

    def test_interest_rate_appears_in_claim(self, base_inputs: dict) -> None:
        result = civil_complaint.draft(**base_inputs, interest_rate_percent=15.0)
        assert "연 15% 비율의 지연손해금" in result["markdown"]

    def test_interest_rate_none_omits_clause(self, base_inputs: dict) -> None:
        result = civil_complaint.draft(**base_inputs, interest_rate_percent=None)
        assert "지연손해금" not in result["markdown"]

    def test_evidence_list_renders_갑호증(self, base_inputs: dict) -> None:
        result = civil_complaint.draft(
            **base_inputs,
            evidence_list=[
                {"name": "차용증", "purpose": "대여 사실"},
            ],
        )
        assert "갑 제1호증" in result["markdown"]
        assert "차용증" in result["markdown"]

    def test_rejects_negative_amount(self, base_inputs: dict) -> None:
        base_inputs["claim_amount"] = -1
        with pytest.raises(ValueError, match="음수"):
            civil_complaint.draft(**base_inputs)

    def test_rejects_empty_facts(self, base_inputs: dict) -> None:
        base_inputs["facts_chronology"] = []
        with pytest.raises(ValueError, match="빈 리스트"):
            civil_complaint.draft(**base_inputs)

    def test_rejects_empty_claim_type(self, base_inputs: dict) -> None:
        base_inputs["claim_type"] = "  "
        with pytest.raises(ValueError, match="claim_type"):
            civil_complaint.draft(**base_inputs)

    def test_citizen_mode_uses_strong_disclaimer(self, base_inputs: dict) -> None:
        result = civil_complaint.draft(**base_inputs, user_mode="citizen")
        assert "법률구조공단" in result["markdown"]


# ─────────────────────────────────────────────
# legal_opinion — 법률의견서
# ─────────────────────────────────────────────
class TestLegalOpinion:
    @pytest.fixture
    def base_inputs(self) -> dict:
        return {
            "case_facts": [
                "의뢰인은 음주운전으로 단속됨",
                "혈중알코올농도 0.08%, 사고 없음",
                "전과 없음",
            ],
            "issues": [
                "양형 감경 사유 인정 여부",
                "측정 절차 위법성",
            ],
        }

    def test_minimum_inputs(self, base_inputs: dict) -> None:
        result = legal_opinion.draft(**base_inputs)
        assert result["doc_type"] == "legal_opinion"
        assert result["issue_count"] == 2
        md = result["markdown"]
        assert "# 법률의견서" in md
        assert "사실관계" in md
        assert "검토 쟁점" in md
        assert "결론" in md
        assert DISCLAIMER_MARKER in md

    def test_with_caption_and_client(self, base_inputs: dict) -> None:
        result = legal_opinion.draft(
            **base_inputs,
            case_caption="음주운전 양형 자문",
            client_name="이의뢰",
        )
        assert "음주운전 양형 자문" in result["markdown"]
        assert "이의뢰" in result["markdown"]

    def test_conclusion_summary_propagates(self, base_inputs: dict) -> None:
        result = legal_opinion.draft(
            **base_inputs,
            conclusion_summary="벌금형 선고가 예상됨",
        )
        assert "벌금형 선고가 예상됨" in result["markdown"]

    def test_no_conclusion_uses_placeholder(self, base_inputs: dict) -> None:
        result = legal_opinion.draft(**base_inputs)
        assert "변호사 검토 후 보충" in result["markdown"]

    def test_rejects_empty_facts(self, base_inputs: dict) -> None:
        base_inputs["case_facts"] = []
        with pytest.raises(ValueError, match="빈 리스트"):
            legal_opinion.draft(**base_inputs)

    def test_rejects_empty_issues(self, base_inputs: dict) -> None:
        base_inputs["issues"] = []
        with pytest.raises(ValueError, match="빈 리스트"):
            legal_opinion.draft(**base_inputs)


# ─────────────────────────────────────────────
# preparatory_brief — 준비서면
# ─────────────────────────────────────────────
class TestPreparatoryBrief:
    @pytest.fixture
    def base_inputs(self) -> dict:
        return {
            "case_caption": "대여금 청구의 소",
            "case_number": "2025가단12345",
            "our_role": "원고 대리인",
            "our_position": [
                "변제기는 2023. 3. 14. 도래하였다",
                "피고는 변제하지 않았다",
            ],
        }

    def test_minimum_inputs(self, base_inputs: dict) -> None:
        result = preparatory_brief.draft(**base_inputs)
        assert result["doc_type"] == "preparatory_brief"
        md = result["markdown"]
        assert "준 비 서 면" in md
        assert "2025가단12345" in md
        assert "대여금 청구의 소" in md
        assert "원고 대리인" in md
        assert DISCLAIMER_MARKER in md

    def test_rebuttal_section_with_opponent_args(self, base_inputs: dict) -> None:
        result = preparatory_brief.draft(
            **base_inputs,
            opponent_arguments=["변제기가 도래하지 않았다"],
            rebuttal_points=["계약서 제3조에 따라 2023. 3. 14. 변제기 명시"],
        )
        md = result["markdown"]
        assert "변제기가 도래하지 않았다" in md
        assert "계약서 제3조" in md

    def test_rejects_empty_case_number(self, base_inputs: dict) -> None:
        base_inputs["case_number"] = ""
        with pytest.raises(ValueError, match="case_number"):
            preparatory_brief.draft(**base_inputs)

    def test_rejects_empty_our_position(self, base_inputs: dict) -> None:
        base_inputs["our_position"] = []
        with pytest.raises(ValueError, match="빈 리스트"):
            preparatory_brief.draft(**base_inputs)


# ─────────────────────────────────────────────
# criminal_defense — 형사 변호인 의견서
# ─────────────────────────────────────────────
class TestCriminalDefense:
    @pytest.fixture
    def base_inputs(self) -> dict:
        return {
            "defendant": {"name": "이피고", "address": "서울 마포구"},
            "case_number": "2025고단12345",
            "charges": ["도로교통법 위반 (음주운전)"],
            "our_arguments": [
                "혈중알코올농도 측정 절차에 위법이 있음",
                "초범으로 재범 우려가 낮음",
            ],
        }

    def test_minimum_inputs(self, base_inputs: dict) -> None:
        result = criminal_defense.draft(**base_inputs)
        assert result["doc_type"] == "criminal_defense"
        assert result["defendant_name"] == "이피고"
        assert result["charge_count"] == 1
        md = result["markdown"]
        assert "변 호 인 의 견 서" in md
        assert "이피고" in md
        assert "2025고단12345" in md
        assert "공소사실의 요지" in md
        assert "변호인의 의견" in md
        assert DISCLAIMER_MARKER in md

    def test_mitigating_factors_render(self, base_inputs: dict) -> None:
        result = criminal_defense.draft(
            **base_inputs,
            mitigating_factors=["초범", "반성문 제출", "합의서 첨부"],
        )
        md = result["markdown"]
        assert "초범" in md
        assert "반성문 제출" in md
        assert "합의서 첨부" in md

    def test_requested_outcome_propagates(self, base_inputs: dict) -> None:
        result = criminal_defense.draft(**base_inputs, requested_outcome="선고유예")
        assert "선고유예" in result["markdown"]

    def test_rejects_missing_defendant_name(self, base_inputs: dict) -> None:
        base_inputs["defendant"] = {"address": "서울"}
        with pytest.raises(ValueError, match="name"):
            criminal_defense.draft(**base_inputs)

    def test_rejects_empty_charges(self, base_inputs: dict) -> None:
        base_inputs["charges"] = []
        with pytest.raises(ValueError, match="빈 리스트"):
            criminal_defense.draft(**base_inputs)

    def test_rejects_empty_arguments(self, base_inputs: dict) -> None:
        base_inputs["our_arguments"] = []
        with pytest.raises(ValueError, match="빈 리스트"):
            criminal_defense.draft(**base_inputs)


# ─────────────────────────────────────────────
# 면책 회귀 가드 (모든 doc type 에 대해 disclaimer 누락 시 fail)
# ─────────────────────────────────────────────
def _all_drafts_minimum() -> list[tuple[str, dict]]:
    """4 doc type 모두 최소 입력으로 생성한 결과 (회귀 가드용)."""
    return [
        (
            "civil_complaint",
            civil_complaint.draft(
                plaintiff={"name": "박원고"},
                defendant={"name": "김피고"},
                claim_type="대여금",
                claim_amount=10_000_000,
                facts_chronology=["사실"],
            ),
        ),
        (
            "legal_opinion",
            legal_opinion.draft(case_facts=["사실"], issues=["쟁점"]),
        ),
        (
            "preparatory_brief",
            preparatory_brief.draft(
                case_caption="x",
                case_number="2025가단1",
                our_role="원고",
                our_position=["주장"],
            ),
        ),
        (
            "criminal_defense",
            criminal_defense.draft(
                defendant={"name": "이피고"},
                case_number="2025고단1",
                charges=["혐의"],
                our_arguments=["의견"],
            ),
        ),
    ]


@pytest.mark.parametrize("doc_type,result", _all_drafts_minimum())
def test_all_doc_types_attach_disclaimer(doc_type: str, result: dict) -> None:
    """4 doc type 모두 출력에 disclaimer marker 가 반드시 존재 (회귀 가드)."""
    assert DISCLAIMER_MARKER in result["markdown"], f"{doc_type}: disclaimer 누락"
    assert result["doc_type"] == doc_type
    # 마크다운 구분자 끝부분 확인
    assert (
        result["markdown"].rstrip().endswith(("도움", "경고", "정보 제공", "확인하세요", "---"))
        or "면책" in result["markdown"]
    )
