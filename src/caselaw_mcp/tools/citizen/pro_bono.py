"""무료/저비용 법률 상담처 추천.

지역(전국·17개 광역시도) x 분쟁 유형(domain) 필터링.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any

from caselaw_mcp.tools.citizen.disclaimer import attach


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    text = resources.files("caselaw_mcp.citizen_data").joinpath(
        "pro_bono.json"
    ).read_text(encoding="utf-8")
    return json.loads(text)


# 도메인 prefix 매칭: "civil.loan" → ["civil.loan", "civil", "all"]
def _domain_chain(domain: str) -> list[str]:
    if not domain:
        return ["all"]
    parts = domain.strip().split(".")
    chain = ["all"]
    for i in range(1, len(parts) + 1):
        chain.append(".".join(parts[:i]))
    return list(reversed(chain))  # 구체 → 일반 → all


def _matches_domain(entry_domains: list[str], chain: list[str]) -> bool:
    return any(d in entry_domains for d in chain)


def recommend_pro_bono(
    region: str | None = None,
    domain: str | None = None,
    *,
    include_emergency_only: bool = False,
    max_items: int = 15,
) -> dict[str, Any]:
    """지역·분쟁 유형별 무료/저비용 법률 상담처 추천.

    Args:
        region: 지역명 (예: "서울", "부산", "광주", "경기북부", "대전·세종·충남")
                None 이면 전국 항목만.
        domain: 분쟁 유형. triage_dispute / 카테고리 ID 와 호환.
                예: "civil.loan", "labor", "criminal.sexual", "consumer".
                None 이면 모든 도메인.
        include_emergency_only: True 면 emergency=true 항목만 (112·1366 등).
        max_items: 최대 반환 건수 (1~30).

    Returns:
        {
            "region", "domain",
            "national": [...],        # 전국 무료 (도메인 매칭)
            "regional_bar": [...],    # 지역 변호사회
            "regional_klac": [...],   # 지역 법률구조공단
            "domain_specialized": [...],
            "online_self_litigation": [...],  # 셀프 소송 자원
            "emergency": [...],       # 긴급(112·1366·117 등) 별도 강조
            "total_recommended", "disclaimers"
        }
    """
    data = _load()
    max_items = max(1, min(30, max_items))
    chain = _domain_chain(domain or "")

    # 1. 전국 (도메인 매칭)
    national = []
    emergency = []
    for entry in data["national"]:
        if include_emergency_only and not entry.get("emergency"):
            continue
        if domain is None or _matches_domain(entry.get("domains", []), chain):
            if entry.get("emergency"):
                emergency.append(entry)
            else:
                national.append(entry)

    # 2. 지역 변호사회 / KLAC (region 매칭)
    regional_bar: list[dict[str, Any]] = []
    regional_klac: list[dict[str, Any]] = []
    if region and not include_emergency_only:
        rgn = region.strip()
        for entry in data["regional_bar_associations"]:
            if rgn in entry.get("region", "") or entry.get("region", "") in rgn:
                regional_bar.append(entry)
        for entry in data["regional_klac_offices"]:
            if rgn in entry.get("region", "") or entry.get("region", "") in rgn:
                regional_klac.append(entry)

    # 3. 도메인 특화
    domain_specialized: list[dict[str, Any]] = []
    if domain and not include_emergency_only:
        spec = data.get("domain_specialized", {})
        for d in chain:
            if d in spec:
                domain_specialized.extend(spec[d])

    # 4. 온라인 셀프 소송 (항상 포함)
    online = data.get("online_self_litigation", []) if not include_emergency_only else []

    total = len(national) + len(regional_bar) + len(regional_klac) + len(domain_specialized) + len(emergency)

    return attach(
        {
            "region": region,
            "domain": domain,
            "domain_chain": chain,
            "national": national[:max_items],
            "regional_bar": regional_bar,
            "regional_klac": regional_klac,
            "domain_specialized": domain_specialized,
            "online_self_litigation": online,
            "emergency": emergency,
            "total_recommended": total,
        },
        kinds=["standard", "ai_limitation"],
    )
