"""server 모듈 기본 동작 테스트."""

from __future__ import annotations

from caselaw_mcp import __version__
from caselaw_mcp.server import lookup_case_codes, mcp, ping


def test_version_is_string() -> None:
    assert isinstance(__version__, str)
    assert __version__.count(".") >= 2


def test_mcp_instance_initialized() -> None:
    assert mcp.name == "caselaw-mcp"


def test_ping_returns_expected_keys() -> None:
    result = ping()
    assert result["status"] == "ok"
    assert result["version"] == __version__
    assert result["phase"] == "12-multi-client"
    assert "time_utc" in result
    assert isinstance(result["oc_configured"], bool)


def test_lookup_case_codes_structure() -> None:
    codes = lookup_case_codes()
    assert "case_type" in codes
    assert "case_type_en" in codes
    assert "court_aliases" in codes
    assert "search_scope" in codes
    assert codes["case_type"]["형사"] == "400102"
    assert codes["case_type_en"]["criminal"] == "400102"
    assert codes["court_aliases"]["supreme"] == "대법원"
    assert codes["search_scope"]["title"] == 1
