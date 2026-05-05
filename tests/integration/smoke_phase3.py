"""Phase 3 실 API smoke — 위원회·특별심판·중앙부처·법령용어."""

from __future__ import annotations

import asyncio
import sys

from caselaw_mcp.tools.committee import search_committee_decision
from caselaw_mcp.tools.dept_interpretation import search_central_dept_interpretation
from caselaw_mcp.tools.special_judg import search_special_admin_judgment
from caselaw_mcp.tools.terminology import search_legal_term


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    # 위원회 결정문 — 공정거래위원회 "담합"
    print("=" * 70)
    print("Test E: search_committee_decision('공정거래', '담합', display=3)")
    print("=" * 70)
    e = await search_committee_decision("공정거래", "담합", display=3)
    print(f"committee={e.get('committee')}, total={e.get('total_count')}, count={e.get('count')}")
    for i, it in enumerate(e["items"], 1):
        keys = list(it.keys())[:8]
        print(f"  [{i}] keys: {keys}")
        for k in ("case_number", "case_name", "decision_date"):
            if k in it:
                print(f"      {k}: {str(it[k])[:140]}")

    # 특별행정심판 — 조세심판원 "양도소득세"
    print()
    print("=" * 70)
    print("Test F: search_special_admin_judgment('조세', '양도소득세', display=3)")
    print("=" * 70)
    f = await search_special_admin_judgment("조세", "양도소득세", display=3)
    print(f"tribunal={f.get('tribunal')}, total={f.get('total_count')}, count={f.get('count')}")
    for i, it in enumerate(f["items"], 1):
        keys = list(it.keys())[:8]
        print(f"  [{i}] keys: {keys}")
        for k in ("case_number", "case_name", "decision_date"):
            if k in it:
                print(f"      {k}: {str(it[k])[:140]}")

    # 중앙부처 — 법무부 "공탁"
    print()
    print("=" * 70)
    print("Test G: search_central_dept_interpretation('법무부', '공탁', display=3)")
    print("=" * 70)
    g = await search_central_dept_interpretation("법무부", "공탁", display=3)
    print(f"dept={g.get('dept')}, total={g.get('total_count')}, count={g.get('count')}")
    for i, it in enumerate(g["items"], 1):
        keys = list(it.keys())[:8]
        print(f"  [{i}] keys: {keys}")
        for k in ("case_number", "case_name"):
            if k in it:
                print(f"      {k}: {str(it[k])[:140]}")

    # 법령용어 — "공탁"
    print()
    print("=" * 70)
    print("Test H: search_legal_term('공탁', display=3)")
    print("=" * 70)
    h = await search_legal_term("공탁", display=3)
    print(f"total={h.get('total_count')}, count={h.get('count')}")
    for i, it in enumerate(h["items"], 1):
        keys = list(it.keys())[:8]
        print(f"  [{i}] keys: {keys}")
        for k in ("term_name", "term_definition", "term_id"):
            if k in it:
                print(f"      {k}: {str(it[k])[:140]}")

    print()
    print("=" * 70)
    print("DONE — Phase 3 정상 동작 확인")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
