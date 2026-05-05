"""evaluate_case_strength — 결과 라벨링·통계 단위 테스트.

실 API 호출 없이 search_precedent 를 monkeypatch 로 mock.
"""

from __future__ import annotations

from typing import Any

import pytest

from caselaw_mcp.tools.citizen.strength import (
    OUTCOME_KEYWORDS,
    _label_outcome,
    evaluate_case_strength,
)


# ─────────────────────────────────────────────
# 라벨링 헬퍼
# ─────────────────────────────────────────────
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("음주운전 사건 - 청구 인용", "원고승"),
        ("임금체불 일부 인용", "원고일부승"),
        ("청구 기각", "기각"),
        ("각하 결정", "각하"),
        ("조정 성립", "조정·화해"),
        ("처분 취소", "취소"),
        ("징역 1년 집행유예 2년", "유죄"),
        ("무죄 판결", "무죄"),
        ("공소기각", "공소기각"),
        ("일반 사건명", None),
        ("", None),
    ],
)
def test_label_outcome(text: str, expected: str | None) -> None:
    assert _label_outcome(text) == expected


def test_outcome_keywords_coverage() -> None:
    """모든 라벨이 적어도 1개 키워드를 가짐."""
    for label, kws in OUTCOME_KEYWORDS.items():
        assert len(kws) >= 1
        assert all(isinstance(k, str) and k for k in kws)


# ─────────────────────────────────────────────
# evaluate_case_strength 통계 (mock)
# ─────────────────────────────────────────────
async def test_evaluate_with_mock_results(monkeypatch: pytest.MonkeyPatch) -> None:
    """search_precedent 를 mock 해서 라벨링·분포 검증."""
    import caselaw_mcp.tools.citizen.strength as s

    fake_items = [
        {"case_name": "A 청구 인용", "case_number": "2024다1", "court": "대법원",
         "judgment_date": "20240101", "prec_id": "1"},
        {"case_name": "B 청구 인용", "case_number": "2024다2", "court": "대법원",
         "judgment_date": "20240201", "prec_id": "2"},
        {"case_name": "C 일부 인용", "case_number": "2024다3", "court": "고등법원",
         "judgment_date": "20240301", "prec_id": "3"},
        {"case_name": "D 청구 기각", "case_number": "2024다4", "court": "지방법원",
         "judgment_date": "20240401", "prec_id": "4"},
        {"case_name": "E 일반 사건명 결과 모름", "case_number": "2024다5",
         "court": "지방법원", "judgment_date": "20240501", "prec_id": "5"},
    ]

    async def fake_search(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"items": fake_items, "total_count": 100}

    monkeypatch.setattr(s, "search_precedent", fake_search)

    r = await evaluate_case_strength("테스트", sample_size=5)

    assert r["analyzed"] == 4
    assert r["unclassified_count"] == 1
    assert r["outcome_distribution"]["원고승"] == 2
    assert r["outcome_distribution"]["원고일부승"] == 1
    assert r["outcome_distribution"]["기각"] == 1
    # 원고승 2 + 일부승 1 = 3 / 4 = 75.0
    assert r["win_rate_estimate_pct"] == 75.0
    # 대표 사례 라벨별 1건씩
    assert "원고승" in r["representative_cases"]
    assert r["representative_cases"]["원고승"]["case_number"] == "2024다1"
    assert any("법률 자문이 아닙니다" in d for d in r["disclaimers"])


async def test_evaluate_empty_query_raises() -> None:
    with pytest.raises(ValueError, match="비어있음"):
        await evaluate_case_strength("")


async def test_evaluate_no_items(monkeypatch: pytest.MonkeyPatch) -> None:
    """결과 0건 → win_rate=null, summary 안내."""
    import caselaw_mcp.tools.citizen.strength as s

    async def fake_search(*args: Any, **kwargs: Any) -> dict[str, Any]:
        return {"items": [], "total_count": 0}

    monkeypatch.setattr(s, "search_precedent", fake_search)
    r = await evaluate_case_strength("희귀검색어")
    assert r["analyzed"] == 0
    assert r["win_rate_estimate_pct"] is None
    assert "찾지 못했" in r["summary_text"]


async def test_evaluate_sample_size_clamped() -> None:
    """sample_size 100 초과는 100으로 클램프."""
    # 실제 호출 안 되도록 검색어가 search_precedent 까지 가지 않도록 mock 필요
    # 여기선 단순히 sample_size 처리 검증만
    import caselaw_mcp.tools.citizen.strength as s

    captured: dict[str, Any] = {}

    async def fake_search(*args: Any, **kwargs: Any) -> dict[str, Any]:
        captured["display"] = kwargs.get("display")
        return {"items": [], "total_count": 0}

    import pytest as _pt
    mp = _pt.MonkeyPatch()
    try:
        mp.setattr(s, "search_precedent", fake_search)
        await evaluate_case_strength("x", sample_size=999)
        assert captured["display"] == 100
    finally:
        mp.undo()
