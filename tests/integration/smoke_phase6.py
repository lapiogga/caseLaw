"""Phase 6 실 API smoke — 인용 역검색 + 첨부 추출."""

from __future__ import annotations

import asyncio
import sys

from caselaw_mcp.tools.attachments import extract_attachments_from_text
from caselaw_mcp.tools.citation_lookup import find_precedent_by_citation
from caselaw_mcp.tools.statute import get_statute


async def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    # L) 변호사가 변론서에서 본 인용 그대로 입력
    print("=" * 70)
    print("Test L: find_precedent_by_citation('대법원 2025. 1. 29. 선고 2025도15970 판결')")
    print("=" * 70)
    r1 = await find_precedent_by_citation("대법원 2025. 1. 29. 선고 2025도15970 판결")
    print(f"extracted: {r1['extracted_case_numbers']}")
    for m in r1["matches"]:
        print(f"  case_number: {m['case_number']} (exact_match={m.get('exact_match')})")
        for c in m.get("candidates", [])[:3]:
            print(
                f"    -> prec_id={c.get('prec_id')} | {c.get('court')} | {c.get('judgment_date')}"
            )

    # L-2) 여러 사건번호 동시 추출
    print()
    print("=" * 70)
    print("Test L-2: find_precedent_by_citation (여러 인용)")
    print("=" * 70)
    text = (
        "이 사건의 핵심 선례는 대법원 2012. 11. 29. 선고 2012도10269 판결과 "
        "헌법재판소 2018헌바8 결정입니다."
    )
    r2 = await find_precedent_by_citation(text)
    print(f"extracted: {r2['extracted_case_numbers']}")
    for m in r2["matches"]:
        cand = m.get("candidates", [])
        print(f"  {m['case_number']}: {len(cand)} 건 (exact={m.get('exact_match')})")

    # M) 법령 본문에서 첨부 링크 추출 (도로교통법)
    print()
    print("=" * 70)
    print("Test M: get_statute('도로교통법') 본문 → extract_attachment_links")
    print("=" * 70)
    import json

    law = await get_statute(law_id="001638")
    dump = json.dumps(law, ensure_ascii=False)
    attachments = extract_attachments_from_text(dump)
    print(f"법령 본문 길이(JSON dump): {len(dump):,} chars")
    print(f"발견된 첨부 링크: {len(attachments)}건")
    for a in attachments[:5]:
        print(f"  flSeq={a['file_seq']} | {a['url']}")

    print()
    print("=" * 70)
    print("DONE — Phase 6 정상 동작 확인")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
