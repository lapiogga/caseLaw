"""prediction 모듈 단위 테스트.

라벨링 휴리스틱 + 집계 함수 + duration/resolution 시드 기반 도구.
predict_sentencing/predict_civil_outcome 의 async 외부 API 호출은
respx mock 또는 별도 통합 smoke 에서 검증 (단위는 _aggregate 동기 함수만).
"""

from __future__ import annotations

import pytest

from caselaw_mcp.tools.prediction import (
    civil_outcome,
    duration,
    resolution,
    sentencing,
)
from caselaw_mcp.tools.prediction.duration import DISCLAIMER_MARKER
from caselaw_mcp.tools.prediction.labels import (
    aggregate_label_distribution,
    extract_awarded_amount,
    label_civil_outcome,
    label_sentencing,
    sample_size_warning,
)


# ─────────────────────────────────────────────
# labels — 민사 결과 라벨링
# ─────────────────────────────────────────────
class TestCivilOutcomeLabel:
    def test_granted(self) -> None:
        assert (
            label_civil_outcome("피고는 원고에게 5천만원을 지급하라. 청구를 인용한다.") == "granted"
        )
        assert label_civil_outcome("원고 승소") == "granted"

    def test_dismissed(self) -> None:
        assert label_civil_outcome("원고의 청구를 모두 기각한다") == "dismissed"
        assert label_civil_outcome("원고 패소 판결") == "dismissed"

    def test_partial(self) -> None:
        assert label_civil_outcome("청구를 일부 인용하고 나머지 기각") == "partial"
        assert label_civil_outcome("일부 승소") == "partial"

    def test_withdrawn(self) -> None:
        assert label_civil_outcome("화해권고결정 확정") == "withdrawn"
        assert label_civil_outcome("소를 취하한다") == "withdrawn"

    def test_unknown(self) -> None:
        assert label_civil_outcome("도로교통법위반(음주운전)") == "unknown"
        assert label_civil_outcome("") == "unknown"
        assert label_civil_outcome(None) == "unknown"  # type: ignore[arg-type]

    def test_partial_takes_precedence_over_granted(self) -> None:
        # "일부 인용" 이 "인용" 보다 먼저 매칭되어야
        text = "청구를 일부 인용하고 나머지를 인용한다"
        assert label_civil_outcome(text) == "partial"


# ─────────────────────────────────────────────
# labels — 형사 양형 라벨링
# ─────────────────────────────────────────────
class TestSentencingLabel:
    def test_acquitted(self) -> None:
        assert label_sentencing("피고인에게 무죄를 선고한다") == "acquitted"
        assert label_sentencing("공소를 기각한다") == "acquitted"

    def test_suspended_sentence(self) -> None:
        assert label_sentencing("징역 6월에 처한다. 다만 집행을 유예한다") == "suspended_sentence"
        assert label_sentencing("선고유예") == "suspended_sentence"

    def test_fine(self) -> None:
        assert label_sentencing("피고인을 벌금 200만원에 처한다") == "fine"

    def test_imprisonment(self) -> None:
        # 집행유예 키워드 없으면 실형
        assert label_sentencing("피고인을 징역 1년에 처한다") == "imprisonment"
        assert label_sentencing("금고 6월") == "imprisonment"

    def test_suspended_takes_precedence_over_imprisonment(self) -> None:
        # "징역 + 집유" 시 집유로 분류 (실형 아님)
        text = "징역 6월에 처한다. 다만 집행유예 1년"
        assert label_sentencing(text) == "suspended_sentence"

    def test_unknown(self) -> None:
        assert label_sentencing("도로교통법위반(음주운전)") == "unknown"
        assert label_sentencing("") == "unknown"


# ─────────────────────────────────────────────
# labels — 인정 금액 추출
# ─────────────────────────────────────────────
class TestExtractAwardedAmount:
    def test_with_comma(self) -> None:
        assert extract_awarded_amount("피고는 원고에게 50,000,000원을 지급하라") == 50_000_000

    def test_without_comma(self) -> None:
        assert extract_awarded_amount("5000000원 지급") == 5_000_000

    def test_no_amount(self) -> None:
        assert extract_awarded_amount("청구를 기각한다") is None

    def test_invalid_input(self) -> None:
        assert extract_awarded_amount(None) is None  # type: ignore[arg-type]
        assert extract_awarded_amount(123) is None  # type: ignore[arg-type]


# ─────────────────────────────────────────────
# labels — 분포 집계 + 표본 가드
# ─────────────────────────────────────────────
class TestAggregation:
    def test_distribution_basic(self) -> None:
        labels = ["granted", "granted", "dismissed", "partial", "unknown"]
        dist = aggregate_label_distribution(
            labels, ("granted", "partial", "dismissed", "withdrawn", "unknown")
        )
        assert dist["granted"]["count"] == 2
        assert dist["granted"]["percent"] == 40.0
        assert dist["partial"]["count"] == 1
        assert dist["dismissed"]["count"] == 1
        assert dist["withdrawn"]["count"] == 0
        assert dist["unknown"]["count"] == 1

    def test_distribution_empty(self) -> None:
        dist = aggregate_label_distribution([], ("granted", "dismissed"))
        assert dist["granted"]["count"] == 0
        assert dist["granted"]["percent"] == 0.0

    def test_sample_size_warning_thresholds(self) -> None:
        # N<5 → 강한 거부 메시지
        assert "최소 5건" in sample_size_warning(2)
        # 5<=N<10 → 미흡 경고
        assert "참고용" in sample_size_warning(7)
        # 10<=N<30 → 보통 경고
        assert "95%" in sample_size_warning(20)
        # N>=30 → None
        assert sample_size_warning(30) is None
        assert sample_size_warning(100) is None


# ─────────────────────────────────────────────
# duration — 사건 소요 기간
# ─────────────────────────────────────────────
class TestEstimateCaseDuration:
    def test_default_inputs(self) -> None:
        result = duration.estimate()
        assert result["doc_type"] == "case_duration_estimate"
        assert result["case_type"] == "민사"
        assert result["instance"] == "1심"
        assert result["mean_months"] == 5
        assert DISCLAIMER_MARKER in result["markdown"]

    def test_criminal_3rd_complex(self) -> None:
        result = duration.estimate(case_type="형사", instance="3심", complexity="복잡")
        assert result["case_type"] == "형사"
        assert result["mean_months"] == 6  # 시드 값

    def test_english_aliases(self) -> None:
        result = duration.estimate(case_type="civil", instance="appeal", complexity="complex")
        assert result["case_type"] == "민사"
        assert result["instance"] == "2심"
        assert result["complexity"] == "복잡"

    def test_unknown_complexity_defaults_to_보통(self) -> None:
        result = duration.estimate(complexity="extreme")
        assert result["complexity"] == "보통"


# ─────────────────────────────────────────────
# resolution — 분쟁 해결 옵션 비교
# ─────────────────────────────────────────────
class TestDisputeResolutionOptions:
    def test_default_returns_recommendation(self) -> None:
        result = resolution.options(dispute_type="civil", claim_amount=50_000_000)
        assert result["doc_type"] == "dispute_resolution_comparison"
        assert result["recommendation"] in {"lawsuit", "mediation", "settlement", "arbitration"}
        assert DISCLAIMER_MARKER in result["markdown"]

    def test_speed_priority_favors_settlement_or_mediation(self) -> None:
        result = resolution.options(speed_priority=True)
        # 속도 우선 시 화해(settlement) 또는 조정(mediation) 최고점
        assert result["recommendation"] in {"settlement", "mediation"}

    def test_relationship_priority_favors_settlement(self) -> None:
        result = resolution.options(relationship_priority=True)
        assert result["recommendation"] == "settlement"

    def test_criminal_penalizes_settlement(self) -> None:
        result_civil = resolution.options(dispute_type="civil", speed_priority=True)
        result_criminal = resolution.options(dispute_type="criminal", speed_priority=True)
        # 형사 사건 시 settlement 점수 차감 → mediation/lawsuit 으로 추천 변경 가능
        sc = result_criminal["options"]["settlement"]["本件 score"]
        sv = result_civil["options"]["settlement"]["本件 score"]
        assert sc < sv

    def test_all_4_options_in_matrix(self) -> None:
        result = resolution.options()
        keys = set(result["options"].keys())
        assert keys == {"lawsuit", "mediation", "settlement", "arbitration"}


# ─────────────────────────────────────────────
# sentencing._aggregate (동기 — async predict 외부 API 의존 없음)
# ─────────────────────────────────────────────
class TestSentencingAggregate:
    def test_balanced_distribution(self) -> None:
        texts = [
            "피고인을 벌금 200만원에 처한다",  # fine
            "피고인을 벌금 100만원에 처한다",  # fine
            "징역 6월에 집행유예 1년",  # suspended
            "징역 1년 실형",  # imprisonment
            "도로교통법위반",  # unknown
        ]
        out = sentencing._aggregate(texts, "음주운전")
        assert out["doc_type"] == "sentencing_prediction"
        assert out["sample_size"] == 5
        d = out["label_distribution"]
        assert d["fine"]["count"] == 2
        assert d["suspended_sentence"]["count"] == 1
        assert d["imprisonment"]["count"] == 1
        assert d["unknown"]["count"] == 1
        assert DISCLAIMER_MARKER in out["markdown"]

    def test_warning_below_10(self) -> None:
        texts = ["벌금 100만원"] * 7  # N=7
        out = sentencing._aggregate(texts, "test")
        assert out["sample_size"] == 7
        assert "참고용" in out["sample_size_warning"]


# ─────────────────────────────────────────────
# civil_outcome._aggregate
# ─────────────────────────────────────────────
class TestCivilOutcomeAggregate:
    def test_balanced_distribution_with_amount(self) -> None:
        texts = [
            "피고는 원고에게 50,000,000원을 지급하라. 청구를 인용한다.",  # granted
            "피고는 원고에게 30,000,000원을 지급하라. 청구를 일부 인용한다.",  # partial
            "원고의 청구를 기각한다",  # dismissed
            "화해권고결정 확정",  # withdrawn
            "도로교통법위반",  # unknown
        ]
        out = civil_outcome._aggregate(texts, "대여금")
        assert out["doc_type"] == "civil_outcome_prediction"
        assert out["sample_size"] == 5
        d = out["label_distribution"]
        assert d["granted"]["count"] == 1
        assert d["partial"]["count"] == 1
        assert d["dismissed"]["count"] == 1
        assert d["withdrawn"]["count"] == 1
        assert d["unknown"]["count"] == 1
        # 인정 금액 — granted/partial 케이스에서만
        assert out["amount_stats"]["count"] == 2
        assert out["amount_stats"]["mean"] == 40_000_000
        assert DISCLAIMER_MARKER in out["markdown"]

    def test_no_amount_when_all_dismissed(self) -> None:
        texts = ["원고의 청구를 기각한다"] * 5
        out = civil_outcome._aggregate(texts, "test")
        assert out["amount_stats"] is None


# ─────────────────────────────────────────────
# 면책 회귀 가드 — duration · resolution · sentencing aggregate · civil aggregate
# ─────────────────────────────────────────────
def _all_predict_outputs() -> list[tuple[str, dict]]:
    return [
        ("duration", duration.estimate(case_type="민사", instance="1심", complexity="보통")),
        ("resolution", resolution.options(dispute_type="civil", claim_amount=10_000_000)),
        (
            "sentencing",
            sentencing._aggregate(["벌금 100만원"] * 5, "test"),
        ),
        (
            "civil_outcome",
            civil_outcome._aggregate(["청구를 인용한다 50,000,000원"] * 5, "test"),
        ),
    ]


@pytest.mark.parametrize("kind,result", _all_predict_outputs())
def test_all_predict_attach_disclaimer(kind: str, result: dict) -> None:
    assert DISCLAIMER_MARKER in result["markdown"], f"{kind}: disclaimer 누락"


# ─────────────────────────────────────────────
# async predict — 표본 부족 가드 (외부 API 호출 없이 검증)
# ─────────────────────────────────────────────
@pytest.mark.asyncio
async def test_predict_sentencing_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="query"):
        await sentencing.predict(query="")


@pytest.mark.asyncio
async def test_predict_civil_rejects_empty_query() -> None:
    with pytest.raises(ValueError, match="query"):
        await civil_outcome.predict(query="  ")
