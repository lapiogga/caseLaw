"""Phase 3 — 위원회·특별심판·중앙부처 코드 리졸버 테스트."""

from __future__ import annotations

import pytest

from caselaw_mcp.codes import (
    resolve_central_dept,
    resolve_committee,
    resolve_special_tribunal,
)


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("ftc", "ftc"),
        ("FTC", "ftc"),
        ("공정거래", "ftc"),
        ("공정위", "ftc"),
        ("공정거래위원회", "ftc"),
        ("ppc", "ppc"),
        ("개인정보", "ppc"),
        ("개인정보보호위원회", "ppc"),
        ("nlrc", "nlrc"),
        ("노동위", "nlrc"),
        ("산재", "iaciac"),
        ("증선위", "sfc"),
        ("국가인권", "nhrck"),
        ("unknown_value", None),
        ("", None),
    ],
)
def test_resolve_committee(inp: str, expected: str | None) -> None:
    assert resolve_committee(inp) == expected


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("tax", "specialDeccTt"),
        ("조세심판원", "specialDeccTt"),
        ("조세", "specialDeccTt"),
        ("maritime", "specialDeccKmst"),
        ("해양안전", "specialDeccKmst"),
        ("acrh", "specialDeccAcr"),
        ("appeal", "specialDeccAdap"),
        ("소청", "specialDeccAdap"),
        ("소청심사위원회", "specialDeccAdap"),
        ("xxx", None),
        ("", None),
    ],
)
def test_resolve_special_tribunal(inp: str, expected: str | None) -> None:
    assert resolve_special_tribunal(inp) == expected


@pytest.mark.parametrize(
    ("inp", "expected"),
    [
        ("moj", "moj"),
        ("MOJ", "moj"),
        ("법무부", "moj"),
        ("고용노동부", "moel"),
        ("노동부", "moel"),
        ("국토교통부", "molit"),
        ("국토부", "molit"),
        ("환경부", "me"),
        ("국세청", "nts"),
        ("관세청", "kcs"),
        ("식약처", "mfds"),
        ("특허청", "kipo"),
        ("해경청", "kcg"),
        ("unknown", None),
        ("", None),
    ],
)
def test_resolve_central_dept(inp: str, expected: str | None) -> None:
    assert resolve_central_dept(inp) == expected
