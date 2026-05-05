"""실 API smoke 테스트 — 직접 실행용 (pytest 자동 수집 비대상).

실행:
    uv run python tests/integration/smoke_live.py

OC 환경변수 필요. 결과를 UTF-8 파일로 출력하면 한국어 깨짐 없음.
"""

from __future__ import annotations

import asyncio
import sys
import time

from caselaw_mcp.tools.precedent import get_precedent, search_precedent
from caselaw_mcp.tools.statute import search_statute


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    print("=" * 70)
    print("Test 1: search_precedent('음주운전', display=5)")
    print("=" * 70)
    r1 = await search_precedent("음주운전", display=5)
    print(f"total_count={r1.get('total_count')}, count={r1.get('count')}")
    for i, it in enumerate(r1["items"], 1):
        print(
            f"  [{i}] {it.get('case_number')} | {it.get('court')} | "
            f"{it.get('judgment_date')} | prec_id={it.get('prec_id')}"
        )
        n = it.get("case_name") or ""
        if n:
            print(f"      사건명: {n[:140]}")

    if not r1["items"]:
        print("ABORT — no items")
        return

    fid = r1["items"][0]["prec_id"]

    print()
    print("=" * 70)
    print(f"Test 2: get_precedent({fid})")
    print("=" * 70)
    d = await get_precedent(fid)
    print(f"top-level keys: {list(d.keys())[:25]}")
    for k in (
        "case_number",
        "court",
        "judgment_date",
        "holdings",
        "summary",
        "referenced_articles",
        "referenced_precedents",
    ):
        v = d.get(k)
        if v:
            s = str(v)
            print(f"  {k}: {s[:200]}{'...(생략)' if len(s) > 200 else ''}")

    print()
    print("=" * 70)
    print("Test 3: search_statute('도로교통법', display=3)")
    print("=" * 70)
    s = await search_statute("도로교통법", display=3)
    print(f"total_count={s.get('total_count')}, count={s.get('count')}")
    for i, it in enumerate(s["items"], 1):
        print(
            f"  [{i}] {it.get('law_name')} | 시행={it.get('effective_date')} | "
            f"law_id={it.get('law_id')} | 부처={it.get('ministry')}"
        )

    print()
    print("=" * 70)
    print("Test 4: 캐시 적중 검증 (같은 검색 재호출)")
    print("=" * 70)
    t0 = time.time()
    _ = await search_precedent("음주운전", display=5)
    elapsed = time.time() - t0
    print(
        f"second call elapsed: {elapsed:.3f}s ({'CACHE HIT ✓' if elapsed < 0.1 else 'CACHE MISS'})"
    )

    print()
    print("=" * 70)
    print("DONE — Phase 1 MVP 정상 동작 확인")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
