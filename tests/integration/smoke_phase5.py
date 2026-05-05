"""Phase 5 실 API smoke — 통계·인용·비교 helper."""

from __future__ import annotations

import asyncio
import sys

from caselaw_mcp.tools.analytics import (
    analyze_precedent_trend,
    compare_precedents,
    format_citation,
)
from caselaw_mcp.tools.precedent import search_precedent


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    # I) 트렌드 — 음주운전 판례 연도별
    print("=" * 70)
    print("Test I: analyze_precedent_trend('음주운전', group_by='year')")
    print("=" * 70)
    trend_year = await analyze_precedent_trend("음주운전", group_by="year", sample_size=50)
    print(
        f"total_analyzed={trend_year['total_analyzed']}, "
        f"total_available={trend_year['total_available']}"
    )
    for d in trend_year["distribution"][:10]:
        print(f"  {d['key']}: {d['count']} 건")

    # I-2) 트렌드 — 법원별
    print()
    print("=" * 70)
    print("Test I-2: analyze_precedent_trend('음주운전', group_by='court')")
    print("=" * 70)
    trend_court = await analyze_precedent_trend("음주운전", group_by="court", sample_size=50)
    for d in trend_court["distribution"][:10]:
        print(f"  {d['key']}: {d['count']} 건")

    # J) 인용 형식 — 첫 판례
    print()
    print("=" * 70)
    print("Test J: format_citation (음주운전 첫 판례)")
    print("=" * 70)
    base = await search_precedent("음주운전", display=1)
    if base["items"]:
        pid = base["items"][0]["prec_id"]
        c = await format_citation(pid)
        print(f"  citation:       {c['citation']}")
        print(f"  short_citation: {c['short_citation']}")

    # K) 비교 — 음주운전 상위 3건
    print()
    print("=" * 70)
    print("Test K: compare_precedents (음주운전 상위 3건)")
    print("=" * 70)
    top3 = await search_precedent("음주운전", display=3)
    pids = [it["prec_id"] for it in top3["items"]][:3]
    cmp_result = await compare_precedents(pids)
    print(f"비교 건수: {cmp_result['count']}")
    for r in cmp_result["rows"]:
        print(f"  - {r.get('case_number')} | {r.get('court')} | {r.get('judgment_date')}")
        n = r.get("case_name") or ""
        if n:
            print(f"    사건명: {n[:100]}")

    print()
    print("=" * 70)
    print("DONE — Phase 5 정상 동작 확인")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
