"""cache.py — SQLite TTL 캐시 단위 테스트."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from caselaw_mcp.cache import Cache


@pytest.fixture
def tmp_cache(tmp_path: Path) -> Cache:
    return Cache(tmp_path / "test_cache.db")


async def test_set_get_basic(tmp_cache: Cache) -> None:
    await tmp_cache.set("k1", {"a": 1, "b": "한글"})
    got = await tmp_cache.get("k1")
    assert got == {"a": 1, "b": "한글"}


async def test_get_missing_returns_none(tmp_cache: Cache) -> None:
    assert await tmp_cache.get("never-set") is None


async def test_ttl_expiry(tmp_cache: Cache) -> None:
    # Windows SQLite 첫 init + write + read 가 0.1s 를 넘을 수 있어 0.5s 로 안정화
    await tmp_cache.set("short", {"x": 1}, ttl_seconds=0.5)
    assert await tmp_cache.get("short") == {"x": 1}
    await asyncio.sleep(0.6)
    assert await tmp_cache.get("short") is None


async def test_overwrite(tmp_cache: Cache) -> None:
    await tmp_cache.set("k", {"v": 1})
    await tmp_cache.set("k", {"v": 2})
    assert await tmp_cache.get("k") == {"v": 2}


async def test_purge_expired(tmp_cache: Cache) -> None:
    await tmp_cache.set("a", 1, ttl_seconds=0.3)
    await tmp_cache.set("b", 2)  # 영구
    await asyncio.sleep(0.5)
    purged = await tmp_cache.purge_expired()
    assert purged == 1
    assert await tmp_cache.get("a") is None
    assert await tmp_cache.get("b") == 2
