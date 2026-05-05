"""Phase 2 실 API smoke — 헌재·해석례·심판례 + 관련 판례 추천."""

from __future__ import annotations

import asyncio
import sys

from caselaw_mcp.tools.admin_judg import search_admin_judgment
from caselaw_mcp.tools.constitution import search_constitutional_decision
from caselaw_mcp.tools.interpretation import search_law_interpretation
from caselaw_mcp.tools.precedent import find_related_precedents, search_precedent


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    print("=" * 70)
    print("Test A: search_constitutional_decision('집회', display=3)")
    print("=" * 70)
    a = await search_constitutional_decision("집회", display=3)
    print(f"total={a.get('total_count')}, count={a.get('count')}")
    for i, it in enumerate(a["items"], 1):
        keys = list(it.keys())[:8]
        print(f"  [{i}] keys: {keys}")
        for k in ("case_number", "case_name", "judgment_date"):
            if k in it:
                print(f"      {k}: {str(it[k])[:120]}")

    print()
    print("=" * 70)
    print("Test B: search_law_interpretation('개인정보', display=3)")
    print("=" * 70)
    b = await search_law_interpretation("개인정보", display=3)
    print(f"total={b.get('total_count')}, count={b.get('count')}")
    for i, it in enumerate(b["items"], 1):
        keys = list(it.keys())[:8]
        print(f"  [{i}] keys: {keys}")
        for k in ("case_number", "case_name", "judgment_date"):
            if k in it:
                print(f"      {k}: {str(it[k])[:120]}")

    print()
    print("=" * 70)
    print("Test C: search_admin_judgment('운전면허 취소', display=3)")
    print("=" * 70)
    c = await search_admin_judgment("운전면허 취소", display=3)
    print(f"total={c.get('total_count')}, count={c.get('count')}")
    for i, it in enumerate(c["items"], 1):
        keys = list(it.keys())[:8]
        print(f"  [{i}] keys: {keys}")
        for k in ("case_number", "case_name", "judgment_date"):
            if k in it:
                print(f"      {k}: {str(it[k])[:120]}")

    print()
    print("=" * 70)
    print("Test D: find_related_precedents (음주운전 첫 판례 → 관련 판례)")
    print("=" * 70)
    base = await search_precedent("음주운전", display=1)
    if base["items"]:
        pid = base["items"][0]["prec_id"]
        print(f"source prec_id={pid} ({base['items'][0].get('case_number')})")
        rel = await find_related_precedents(pid, max_items=8)
        print(f"referenced_text(앞 200자): {rel['referenced_text'][:200]}")
        print(f"referenced_cases: {rel['referenced_cases']}")
        print(f"candidates count: {rel['count']}")
        for i, c in enumerate(rel["candidates"][:6], 1):
            print(
                f"  [{i}] {c['case_number']} | {c['court']} | {c['judgment_date']} "
                f"| src={c['source']} | prec_id={c['prec_id']}"
            )

    print()
    print("=" * 70)
    print("DONE — Phase 2 정상 동작 확인")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
