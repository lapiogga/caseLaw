"""소멸시효·공소시효 정밀 점검.

시효 표 매트릭스 + 경과 일수 계산 + 중단·정지 사유 안내.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from functools import lru_cache
from importlib import resources
from typing import Any

from caselaw_mcp.tools.citizen.disclaimer import attach


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    text = (
        resources.files("caselaw_mcp.citizen_data")
        .joinpath("limitations.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


def _years_since(event_iso: str) -> tuple[date, float]:
    s = event_iso.strip().replace(".", "-").replace("/", "-")
    if len(s) == 8 and s.isdigit():
        s = f"{s[:4]}-{s[4:6]}-{s[6:8]}"
    d = datetime.strptime(s, "%Y-%m-%d").date()
    delta = date.today() - d
    return d, round(delta.days / 365.25, 3)


def list_limitation_categories() -> list[dict[str, Any]]:
    """전체 시효 카테고리 ID·이름·기간 표 (LLM 참고용)."""
    return [
        {
            "id": item["id"],
            "category": item["category"],
            "period_years": item.get("period_years"),
            "alt_period_years": item.get("alt_period_years"),
            "law": item.get("law"),
        }
        for item in _load()["limitations"]
    ]


def check_statute_of_limitations(
    category_id: str,
    event_date: str,
) -> dict[str, Any]:
    """소멸시효·공소시효 정밀 점검.

    Args:
        category_id: 시효 카테고리 ID (list_limitation_categories 로 조회).
            예: "civil.general", "tort", "wage", "criminal.dui",
                "labor.unfair_dismissal", "family.property_division"
        event_date: 사건 발생일 또는 시효 기산점 (YYYY-MM-DD)

    Returns:
        {
            "category", "period_years", "law", "law_detail",
            "event_date", "today", "elapsed_years", "remaining_years",
            "status": "safe" | "imminent" | "expired" | "indefinite",
            "advice": str,
            "interruption_events": [...],          # 시효 중단 가능 사유
            "interruption_applicable": bool,
            "examples": [...],
            "disclaimers": [...]
        }
    """
    if not category_id or not category_id.strip():
        raise ValueError("category_id 비어있음")
    if not event_date or not event_date.strip():
        raise ValueError("event_date 비어있음")

    data = _load()
    item = next((x for x in data["limitations"] if x["id"] == category_id.strip()), None)
    if item is None:
        valid_ids = [x["id"] for x in data["limitations"]]
        raise ValueError(
            f"category_id={category_id!r} 인식 불가. 유효 ID: {valid_ids[:10]}... (총 {len(valid_ids)}개)"
        )

    parsed_date, elapsed = _years_since(event_date)
    period = item.get("period_years")
    alt_period = item.get("alt_period_years")

    response: dict[str, Any] = {
        "category_id": category_id,
        "category": item["category"],
        "period_years": period,
        "alt_period_years": alt_period,
        "law": item.get("law"),
        "law_detail": item.get("law_detail"),
        "event_date": parsed_date.isoformat(),
        "today": date.today().isoformat(),
        "elapsed_years": elapsed,
        "examples": item.get("examples", []),
        "interruption_applicable": item.get("interruption_applicable", False),
        "note": item.get("note"),
    }

    if period is None:
        response["status"] = "indefinite"
        response["advice"] = (
            "본 카테고리는 정해진 기간이 없거나 별도 규정이 있습니다 "
            "(예: 정지·폐지). 변호사 상담 권장."
        )
        kinds = ["standard", "ai_limitation"]
    else:
        remaining = round(period - elapsed, 3)
        response["remaining_years"] = remaining
        response["remaining_days"] = int(remaining * 365.25)

        if alt_period is not None:
            response["alt_remaining_years"] = round(alt_period - elapsed, 3)

        if remaining <= 0:
            response["status"] = "expired"
            response["advice"] = (
                f"⚠️ 시효 만료 가능성 ({elapsed}년 경과 / 한도 {period}년). "
                "단, 시효 중단·정지 사유가 있을 수 있으므로 즉시 변호사 상담 필요."
            )
            kinds = ["statute_imminent", "standard", "ai_limitation"]
        elif remaining < 1.0:
            response["status"] = "imminent"
            response["advice"] = (
                f"⚠️ 시효 임박 (약 {remaining}년 남음). 즉시 변호사 상담 + "
                "내용증명·지급명령 등 시효 중단 조치 권장."
            )
            kinds = ["statute_imminent", "standard", "ai_limitation"]
        elif remaining < 2.0:
            response["status"] = "warning"
            response["advice"] = (
                f"시효 1~2년 내 ({remaining}년 남음). 변호사 상담 후 증거 보전·내용증명 등 권장."
            )
            kinds = ["standard", "ai_limitation"]
        else:
            response["status"] = "safe"
            response["advice"] = f"안전 (약 {remaining}년 남음). 다만 증거 보전은 미리."
            kinds = ["standard", "ai_limitation"]

    if item.get("interruption_applicable", False):
        response["interruption_events"] = data["interruption_events"]
    else:
        response["interruption_events"] = []
        response["interruption_note"] = (
            "공소시효·제소기간 등은 일반적으로 중단 사유가 적용되지 않거나 제한됩니다."
        )

    return attach(response, kinds=kinds)
