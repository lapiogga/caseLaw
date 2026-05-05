"""recommend_pro_bono 단위 테스트."""

from __future__ import annotations

from caselaw_mcp.tools.citizen.pro_bono import (
    _domain_chain,
    _matches_domain,
    recommend_pro_bono,
)


def test_domain_chain_basic() -> None:
    assert _domain_chain("civil.loan") == ["civil.loan", "civil", "all"]
    assert _domain_chain("criminal.sexual") == ["criminal.sexual", "criminal", "all"]
    assert _domain_chain("") == ["all"]


def test_matches_domain() -> None:
    assert _matches_domain(["all"], ["civil.loan", "civil", "all"]) is True
    assert _matches_domain(["civil"], ["civil.loan", "civil", "all"]) is True
    assert _matches_domain(["criminal"], ["civil.loan", "civil", "all"]) is False


def test_recommend_no_filter_returns_national() -> None:
    r = recommend_pro_bono()
    assert len(r["national"]) > 0
    assert any("법률구조공단" in n["name"] for n in r["national"])
    assert "법률 자문이 아닙니다" in r["disclaimers"][0]


def test_recommend_emergency_only() -> None:
    r = recommend_pro_bono(include_emergency_only=True)
    assert len(r["emergency"]) > 0
    assert all(e.get("emergency") for e in r["emergency"])
    # 비응급 카테고리는 비어있어야 함
    assert r["national"] == []
    assert r["regional_bar"] == []
    assert r["online_self_litigation"] == []


def test_recommend_with_region() -> None:
    r = recommend_pro_bono(region="서울")
    assert any("서울" in e["region"] for e in r["regional_bar"])
    assert any("서울" in e["region"] for e in r["regional_klac"])


def test_recommend_with_domain_labor() -> None:
    r = recommend_pro_bono(domain="labor")
    # 도메인 특화에 노무사 무료상담 포함
    assert any("노무사" in e["name"] for e in r["domain_specialized"])


def test_recommend_with_domain_civil_loan() -> None:
    """civil.loan → civil → all 체인으로 매칭."""
    r = recommend_pro_bono(domain="civil.loan")
    # 법률구조공단(domains=["all"]) 매칭
    assert any("법률구조공단" in n["name"] for n in r["national"])


def test_recommend_with_domain_consumer() -> None:
    r = recommend_pro_bono(domain="consumer")
    names = [n["name"] for n in r["national"]]
    assert any("소비자상담센터" in n for n in names)


def test_recommend_max_items_clamped() -> None:
    r = recommend_pro_bono(max_items=999)
    # max_items 30으로 클램프 후 national은 최대 30
    assert len(r["national"]) <= 30


def test_recommend_includes_online_self_litigation() -> None:
    r = recommend_pro_bono()
    assert any("전자소송" in e["name"] for e in r["online_self_litigation"])
