"""citation_lookup — 인용 텍스트 사건번호 추출 단위 테스트."""

from __future__ import annotations

import pytest

from caselaw_mcp.tools.citation_lookup import (
    _extract_unique,
    find_precedent_by_citation,
)


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("대법원 2024. 5. 30. 선고 2023두12345 판결", ["2023두12345"]),
        ("헌법재판소 2018헌바8 결정", ["2018헌바8"]),
        ("2025도15970", ["2025도15970"]),
        ("두 사건: 2023도1, 2024다99999", ["2023도1", "2024다99999"]),
        ("중복 케이스 2023도1, 2023도1, 2023도1", ["2023도1"]),
        ("사건번호 없음", []),
        ("", []),
    ],
)
def test_extract_unique(inp: str, expected: list[str]) -> None:
    assert _extract_unique(inp) == expected


async def test_find_precedent_by_citation_empty_input_raises() -> None:
    with pytest.raises(ValueError, match="비어있음"):
        await find_precedent_by_citation("")


async def test_find_precedent_by_citation_no_pattern_returns_hint() -> None:
    r = await find_precedent_by_citation("아무런 사건번호 없음")
    assert r["extracted_case_numbers"] == []
    assert r["matches"] == []
    assert "hint" in r
