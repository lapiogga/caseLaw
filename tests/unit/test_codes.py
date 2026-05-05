"""codes.py — 코드 매핑 단위 테스트."""

from __future__ import annotations

import pytest

from caselaw_mcp.codes import (
    resolve_case_type,
    resolve_court,
    resolve_search_scope,
)


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("형사", "400102"),
        ("criminal", "400102"),
        ("CRIMINAL", "400102"),
        ("400102", "400102"),
        ("민사", "400101"),
        ("civil", "400101"),
        ("admin", "400105"),
        ("administrative", "400105"),
        ("unknown", None),
        (None, None),
        ("", None),
    ],
)
def test_resolve_case_type(inp: str | None, expected: str | None) -> None:
    assert resolve_case_type(inp) == expected


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("supreme", "대법원"),
        ("constitutional", "헌법재판소"),
        ("대법원", "대법원"),
        ("고등법원", "고등법원"),
        (None, None),
    ],
)
def test_resolve_court(inp: str | None, expected: str | None) -> None:
    assert resolve_court(inp) == expected


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("title", 1),
        ("body", 2),
        (1, 1),
        (2, 2),
        (3, None),
        ("none", None),
        (None, None),
    ],
)
def test_resolve_search_scope(inp: str | int | None, expected: int | None) -> None:
    assert resolve_search_scope(inp) == expected
