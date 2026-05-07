"""한국 판결문 결과 라벨링 휴리스틱.

사건명 + 판시사항 + 본문 일부 텍스트에서 판결 결과를 키워드로 추론.
재판부·시기·구체 사실관계에 따라 분류 정확도가 달라지므로,
unknown 카테고리에 분류 불가 케이스를 솔직히 모은다.

Phase 9 evaluate_case_strength 의 라벨 9 종을 5 종으로 축약 (집계 정확도 ↑).
"""

from __future__ import annotations

from typing import Any, Literal

# ─────────────────────────────────────────────
# 라벨 타입
# ─────────────────────────────────────────────
CivilLabel = Literal["granted", "partial", "dismissed", "withdrawn", "unknown"]
SentencingLabel = Literal[
    "acquitted",  # 무죄
    "suspended_sentence",  # 선고유예 / 집행유예
    "fine",  # 벌금
    "imprisonment",  # 실형 (징역·금고)
    "unknown",  # 분류 불가
]

CIVIL_LABELS: tuple[CivilLabel, ...] = ("granted", "partial", "dismissed", "withdrawn", "unknown")
SENTENCING_LABELS: tuple[SentencingLabel, ...] = (
    "acquitted",
    "suspended_sentence",
    "fine",
    "imprisonment",
    "unknown",
)


# ─────────────────────────────────────────────
# 민사 결과 라벨링
# ─────────────────────────────────────────────
def label_civil_outcome(text: str) -> CivilLabel:
    """민사 판결문 텍스트(사건명+판시사항+본문 일부) 에서 결과 라벨 추론.

    우선순위:
    1. 명시 키워드 ("청구를 기각", "청구를 인용") — 가장 신뢰
    2. 약식 키워드 ("원고 패소", "원고 승소")
    3. 부분 키워드 ("일부 인용")
    4. 전부 미매칭 → unknown
    """
    if not isinstance(text, str):
        return "unknown"
    t = text.replace("\n", " ").replace("  ", " ")

    # withdrawn (취하·화해) — 다른 라벨보다 먼저 (인용·기각 키워드 함께 나올 수 있음)
    if any(kw in t for kw in ["소취하", "소를 취하", "화해권고결정", "강제조정 성립"]):
        return "withdrawn"

    # 일부 인용은 "인용" 만 보고 granted 로 잘못 잡지 않도록 먼저 검사
    if any(kw in t for kw in ["일부 인용", "일부인용", "일부 승소", "일부패소"]):
        return "partial"

    # 기각 (피고 승소 = 원고 패소)
    if any(kw in t for kw in ["청구를 기각", "청구 기각", "원고의 청구를 모두 기각", "원고 패소"]):
        return "dismissed"

    # 인용 (원고 승소)
    if any(
        kw in t
        for kw in [
            "청구를 인용",
            "청구를 모두 인용",
            "청구를 받아들",
            "원고 승소",
            "원고의 청구를 인용",
        ]
    ):
        return "granted"

    return "unknown"


# ─────────────────────────────────────────────
# 형사 양형 라벨링
# ─────────────────────────────────────────────
def label_sentencing(text: str) -> SentencingLabel:
    """형사 판결문 텍스트에서 양형 라벨 추론.

    우선순위:
    1. 무죄·공소기각 (다른 라벨과 충돌 없음, 가장 먼저)
    2. 집행유예 / 선고유예
    3. 벌금형
    4. 실형 (징역·금고)
    5. 미매칭 → unknown
    """
    if not isinstance(text, str):
        return "unknown"
    t = text.replace("\n", " ").replace("  ", " ")

    # 무죄 / 공소기각 / 면소
    if any(
        kw in t
        for kw in [
            "무죄를 선고",
            "무죄로 한다",
            "공소를 기각",
            "공소기각",
            "면소를 선고",
            "면소판결",
        ]
    ):
        return "acquitted"

    # 선고유예 / 집행유예 (한국 형사 양형의 주된 보호처분)
    if any(
        kw in t
        for kw in [
            "선고유예",
            "집행유예",
            "집행을 유예",
            "유예한다",
        ]
    ):
        return "suspended_sentence"

    # 벌금형 (집유 키워드 뒤에 검사 — 벌금 + 집유 동시 나올 수 있음)
    if any(kw in t for kw in ["벌금", "과료를 선고"]):
        return "fine"

    # 실형 (징역·금고). "징역" 단독 ≠ 실형(집유 가능) 이므로 위에서 집유 먼저 매칭
    if any(kw in t for kw in ["징역", "금고", "구류"]):
        return "imprisonment"

    return "unknown"


# ─────────────────────────────────────────────
# 청구금액 추출 (민사 인용 시 인정 금액)
# ─────────────────────────────────────────────
def extract_awarded_amount(text: str) -> int | None:
    """판결문 텍스트에서 인정 금액 (원) 추출. 실패 시 None.

    한국 판결문 형식: "피고는 원고에게 50,000,000원을 지급하라" / "5천만원" 등
    숫자 + "원" 패턴만 안전하게 잡고, 한글 숫자(천만/억) 변환은 별도 모듈로.
    """
    if not isinstance(text, str):
        return None

    import re

    # "50,000,000원" 또는 "50000000원" 패턴
    m = re.search(r"([\d,]+)\s*원", text)
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


# ─────────────────────────────────────────────
# 분포 집계 헬퍼
# ─────────────────────────────────────────────
def aggregate_label_distribution(
    labels: list[str],
    label_universe: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    """라벨 리스트 → 카운트·비율 표.

    빈 카테고리도 0 으로 출력 (집계 일관성).
    """
    total = len(labels)
    distribution: dict[str, dict[str, Any]] = {}
    for label in label_universe:
        count = sum(1 for x in labels if x == label)
        percent = (count / total * 100) if total > 0 else 0.0
        distribution[label] = {"count": count, "percent": round(percent, 1)}
    return distribution


def sample_size_warning(n: int) -> str | None:
    """표본 크기 경고. None=정상, 문자열=경고/거부 사유."""
    if n < 5:
        return f"표본 부족: N={n} (최소 5건 필요). 검색 키워드를 넓히세요."
    if n < 10:
        return f"표본 미흡: N={n} (10건 미만). 결과는 참고용 그림자 데이터로만 사용."
    if n < 30:
        return f"표본 보통: N={n} (30건 미만). 95% 신뢰구간이 넓을 수 있음."
    return None
