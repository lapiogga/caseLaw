"""공개 웹 페이지 자동 스크린샷 (Playwright).

사용:
    cd docs/promo/automation
    uv pip install playwright
    uv run python -m playwright install chromium
    uv run python capture_pages.py

결과:
    docs/promo/images/ 에 PNG 자동 생성

캡처 대상은 모두 공개 페이지로 로그인 없이 접근 가능.
법제처 회원가입·Claude Desktop 화면 등 인증 필요 화면은 제외 (사용자 본인 캡처 필요).
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

OUT_DIR = Path(__file__).resolve().parent.parent / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (slug, url, viewport_width, viewport_height, full_page, wait_selector)
PAGES = [
    (
        "01-github-repo",
        "https://github.com/lapiogga/caseLaw",
        1280, 800, True, "article",
    ),
    (
        "02-github-release",
        "https://github.com/lapiogga/caseLaw/releases/tag/v0.8.0",
        1280, 800, True, "h1",
    ),
    (
        "03-pypi-package",
        "https://pypi.org/project/caselaw-mcp/",
        1280, 800, True, "h1.package-header__name",
    ),
    (
        "04-bopjecheo-openapi",
        "https://open.law.go.kr/LSO/openApi/cuAskList.do",
        1280, 900, True, "body",
    ),
    (
        "05-oc-baalgup-guide",
        "https://github.com/lapiogga/caseLaw/blob/main/docs/OC%EB%B0%9C%EA%B8%89_%EA%B0%80%EC%9D%B4%EB%93%9C.md",
        1280, 900, True, "article",
    ),
    (
        "06-installer-zip-download",
        "https://github.com/lapiogga/caseLaw/releases/tag/v0.8.0",
        1280, 800, False, "details summary",
    ),
]


async def capture_one(
    pw,
    slug: str,
    url: str,
    width: int,
    height: int,
    full_page: bool,
    wait_selector: str,
) -> Path:
    """단일 페이지 캡처."""
    browser = await pw.chromium.launch(headless=True)
    ctx = await browser.new_context(
        viewport={"width": width, "height": height},
        locale="ko-KR",
        device_scale_factor=2,  # 레티나 품질
    )
    page = await ctx.new_page()
    print(f"  -> {url}")
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
    except Exception as e:
        print(f"     networkidle timeout ({e.__class__.__name__}), fallback to domcontentloaded")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)

    try:
        await page.wait_for_selector(wait_selector, timeout=10000)
    except Exception:
        print(f"     selector '{wait_selector}' not found, capture anyway")

    # 추가 1초 대기 (lazy-load 이미지)
    await page.wait_for_timeout(1500)

    out = OUT_DIR / f"{slug}.png"
    await page.screenshot(path=str(out), full_page=full_page)
    await browser.close()
    print(f"     saved: {out.name}  ({out.stat().st_size // 1024} KB)")
    return out


async def main() -> None:
    print(f"Output: {OUT_DIR}")
    print(f"Targets: {len(PAGES)} pages\n")

    async with async_playwright() as pw:
        for i, args in enumerate(PAGES, 1):
            print(f"[{i}/{len(PAGES)}] {args[0]}")
            try:
                await capture_one(pw, *args)
            except Exception as e:
                print(f"     [FAIL] {e}")
            print()

    print("Done. See docs/promo/images/")


if __name__ == "__main__":
    asyncio.run(main())
