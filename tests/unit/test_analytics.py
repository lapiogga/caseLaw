"""analytics.py — 통계·인용·비교 helper 단위 테스트 (네트워크 무관)."""

from __future__ import annotations

import pytest

from caselaw_mcp.tools.analytics import (
    _extract_group_key,
    _format_korean_date,
    _parse_year,
    _parse_year_month,
    _truncate,
)


# ─────────────────────────────────────────────
# 날짜 파싱
# ─────────────────────────────────────────────
@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("2026.01.29", "2026"),
        ("20260129", "2026"),
        ("2026-01-29", "2026"),
        ("2026", "2026"),
        ("", None),
        (None, None),
    ],
)
def test_parse_year(inp: str | None, expected: str | None) -> None:
    if inp is None:
        assert _parse_year("") is None
    else:
        assert _parse_year(inp) == expected


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("2026.01.29", "2026-01"),
        ("20260129", "2026-01"),
        ("2026", "2026"),
        ("", None),
    ],
)
def test_parse_year_month(inp: str, expected: str | None) -> None:
    assert _parse_year_month(inp) == expected


# ─────────────────────────────────────────────
# group key 추출
# ─────────────────────────────────────────────
def test_extract_group_key_year() -> None:
    item = {"judgment_date": "2025.06.15", "court": "대법원", "case_type": "형사"}
    assert _extract_group_key(item, "year") == "2025"
    assert _extract_group_key(item, "month") == "2025-06"
    assert _extract_group_key(item, "court") == "대법원"
    assert _extract_group_key(item, "case_type") == "형사"


def test_extract_group_key_missing_field() -> None:
    item = {"judgment_date": ""}
    assert _extract_group_key(item, "year") is None
    assert _extract_group_key(item, "court") is None


# ─────────────────────────────────────────────
# 한국 표준 날짜 포맷
# ─────────────────────────────────────────────
@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("20260129", "2026. 1. 29."),
        ("2026.01.29", "2026. 1. 29."),
        ("2026-01-29", "2026. 1. 29."),
        ("2025.12.11", "2025. 12. 11."),
        ("", None),
        ("2026", None),  # 길이 부족
        ("abcdefgh", None),
    ],
)
def test_format_korean_date(inp: str, expected: str | None) -> None:
    assert _format_korean_date(inp) == expected


# ─────────────────────────────────────────────
# truncate
# ─────────────────────────────────────────────
def test_truncate_short_passthrough() -> None:
    assert _truncate("짧은텍스트", 100) == "짧은텍스트"


def test_truncate_long_cuts() -> None:
    out = _truncate("a" * 200, 50)
    assert out is not None
    assert out.endswith("...(생략)")
    assert len(out) == 50 + len("...(생략)")


def test_truncate_none() -> None:
    assert _truncate(None, 100) is None
