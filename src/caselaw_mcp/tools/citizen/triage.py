"""triage_dispute — 자유 형식 사실관계 → 분쟁 카테고리 분류·추천 경로.

본 함수는 LLM이 아니라 **키워드 매칭 + 정적 매트릭스** 기반.
호스트 LLM이 본 결과를 받아 종합 판단.

원칙:
- 단정 금지 (best_match 가 아닌 candidates 형태)
- 면책 자동 부착
- 시효·무료자원 항상 함께 표시
"""

from __future__ import annotations

import json
from datetime import date, datetime
from functools import lru_cache
from importlib import resources
from typing import Any

from caselaw_mcp.tools.citizen.disclaimer import attach


@lru_cache(maxsize=1)
def _categories() -> list[dict[str, Any]]:
    text = resources.files("caselaw_mcp.citizen_data").joinpath("categories.json").read_text(
        encoding="utf-8"
    )
    return json.loads(text)["categories"]


def _match_score(situation: str, cat: dict[str, Any]) -> int:
    """단순 키워드 카운트 (소문자 무관)."""
    s = situation.lower()
    score = 0
    for kw in cat.get("keywords", []):
        if kw.lower() in s:
            score += 1
    return score


def _years_since(event_iso: str | None) -> float | None:
    """YYYY-MM-DD 또는 YYYYMMDD → 경과 연 수."""
    if not event_iso:
        return None
    s = event_iso.strip().replace(".", "-").replace("/", "-")
    if len(s) == 8 and s.isdigit():
        s = f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    try:
        d = datetime.strptime(s, "%Y-%m-%d").date()
    except ValueError:
        return None
    delta = date.today() - d
    return round(delta.days / 365.25, 2)


def triage_dispute(
    situation: str,
    event_date: str | None = None,
    *,
    top_k: int = 3,
) -> dict[str, Any]:
    """사실관계 텍스트 → 분쟁 카테고리 후보·추천 경로·시효 점검.

    Args:
        situation: 사용자가 직접 작성한 자유 형식 사실관계
            예: "3년 전 친구한테 5천만 원 빌려줬는데 안 갚음, 차용증은 카톡뿐"
        event_date: 사건 발생일 (YYYY-MM-DD 또는 YYYYMMDD), 시효 점검용
        top_k: 반환할 후보 수 (1~5, 기본 3)

    Returns:
        {
            "input": str,
            "candidates": [
                {
                    "id": "civil.loan",
                    "name": "대여금 반환청구",
                    "domain": "민사",
                    "score": 3,                          # 키워드 매칭 수
                    "applicable_laws": [...],
                    "limitation_period_years": 10,
                    "limitation_status": "안전 (약 7년 남음)",
                    "typical_path": "...",
                    "complexity": "low",
                    "self_litigation_possible": true,    # 소가 모를 시 None
                    "key_evidence": [...],
                    "common_issues": [...],
                    "support_resources": [...]           # 있으면
                }
            ],
            "matched_count": int,
            "event_date": str | null,
            "elapsed_years": float | null,
            "next_steps": [...],
            "disclaimers": [...]
        }
    """
    if not situation or not situation.strip():
        raise ValueError("situation 비어있음")
    top_k = max(1, min(5, top_k))

    elapsed = _years_since(event_date)

    scored: list[tuple[int, dict[str, Any]]] = []
    for cat in _categories():
        s = _match_score(situation, cat)
        if s > 0:
            scored.append((s, cat))
    scored.sort(key=lambda x: x[0], reverse=True)

    candidates = []
    needs_imminent_warning = False
    for score, cat in scored[:top_k]:
        item = {
            "id": cat["id"],
            "name": cat["name"],
            "domain": cat["domain"],
            "score": score,
            "applicable_laws": cat.get("applicable_laws", []),
            "limitation_period_years": cat.get("limitation_period_years"),
            "limitation_law": cat.get("limitation_law"),
            "typical_path": cat.get("typical_path"),
            "complexity": cat.get("complexity"),
            "key_evidence": cat.get("key_evidence", []),
            "common_issues": cat.get("common_issues", []),
        }
        if cat.get("support_resources"):
            item["support_resources"] = cat["support_resources"]

        # 시효 상태 평가
        if elapsed is not None and cat.get("limitation_period_years"):
            limit = float(cat["limitation_period_years"])
            remaining = limit - elapsed
            if remaining <= 0:
                item["limitation_status"] = (
                    f"⚠️ 시효 만료 가능성 ({elapsed}년 경과 / 한도 {limit}년)"
                )
                needs_imminent_warning = True
            elif remaining < 1.0:
                item["limitation_status"] = (
                    f"⚠️ 시효 임박 (약 {round(remaining, 2)}년 남음)"
                )
                needs_imminent_warning = True
            else:
                item["limitation_status"] = (
                    f"안전 (약 {round(remaining, 2)}년 남음)"
                )
        elif cat.get("limitation_period_years") is None:
            item["limitation_status"] = "별도 규정 — 변호사 확인 필요"

        # 셀프 소송 가능 여부
        threshold = cat.get("self_litigation_threshold_krw")
        if threshold is not None:
            item["self_litigation_threshold_krw"] = threshold
            item["self_litigation_note"] = (
                f"소가 {threshold:,}원 이하면 소액사건심판으로 변호사 없이 진행 가능"
            )

        candidates.append(item)

    next_steps = _suggest_next_steps(candidates, elapsed, needs_imminent_warning)

    response = {
        "input": situation,
        "candidates": candidates,
        "matched_count": len(scored),
        "event_date": event_date,
        "elapsed_years": elapsed,
        "next_steps": next_steps,
        "categories_database_size": len(_categories()),
    }

    kinds = ["standard", "ai_limitation"]
    if needs_imminent_warning:
        kinds.insert(0, "statute_imminent")
    if any("형사" in c.get("domain", "") for c in candidates):
        kinds.append("criminal_serious")
    return attach(response, kinds=kinds)


def _suggest_next_steps(
    candidates: list[dict[str, Any]],
    elapsed: float | None,
    imminent: bool,
) -> list[str]:
    steps: list[str] = []
    if not candidates:
        steps.append(
            "키워드 매칭 카테고리가 없습니다. 사실관계를 더 구체적으로 적거나, "
            "변호사 무료 상담(대한법률구조공단 132)을 이용해 주세요."
        )
        return steps

    if imminent:
        steps.append("🚨 시효 임박/만료 가능성 — 즉시 변호사 상담 권장 (지체하면 권리 상실).")

    primary = candidates[0]
    steps.append(f"가장 가능성 높은 분쟁 유형: {primary['name']} ({primary['domain']}).")
    if primary.get("typical_path"):
        steps.append(f"일반적 절차: {primary['typical_path']}")
    if primary.get("self_litigation_threshold_krw"):
        steps.append(primary.get("self_litigation_note", ""))
    steps.append("증거를 모으세요: " + ", ".join(primary.get("key_evidence", [])[:5]))
    steps.append(
        "무료 상담: 대한법률구조공단 132, 한국가정법률상담소 1644-7077, "
        "지역 마을변호사·구청 무료법률상담 확인."
    )
    return [s for s in steps if s]
