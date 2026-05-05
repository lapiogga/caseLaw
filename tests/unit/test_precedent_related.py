"""find_related_precedents — helper 함수 단위 테스트 (네트워크 무관)."""

from __future__ import annotations

from caselaw_mcp.tools.precedent import _extract_case_numbers, _extract_keyword


def test_extract_case_numbers_basic() -> None:
    text = "대법원 2004. 10. 15. 선고 2004도4869 판결, 헌법재판소 2018헌바8 결정"
    out = _extract_case_numbers(text)
    assert "2004도4869" in out
    assert "2018헌바8" in out


def test_extract_case_numbers_dedup_and_order() -> None:
    text = "2004도4869, 2004도4869, 2012도10269"
    out = _extract_case_numbers(text)
    assert out == ["2004도4869", "2012도10269"]


def test_extract_case_numbers_empty() -> None:
    assert _extract_case_numbers("") == []
    assert _extract_case_numbers("no cases here") == []


def test_extract_keyword_from_brackets() -> None:
    name = "도로교통법위반(음주운전)[음주측정 적법성 판단 기준]"
    assert _extract_keyword(name) == "음주측정"


def test_extract_keyword_from_first_token() -> None:
    name = "사기·도로교통법위반(음주운전)"
    kw = _extract_keyword(name)
    assert kw is not None
    assert "가" <= kw[0] <= "힣"


def test_extract_keyword_empty() -> None:
    assert _extract_keyword("") is None
    assert _extract_keyword("ABC123") is None
