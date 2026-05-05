"""SQLite TTL 캐시.

판례·법령 본문은 사실상 불변이므로 영구 캐시 가치가 크다.
목록은 1시간 TTL (신규 등록 반영 위함).

스키마: cache(key TEXT PRIMARY KEY, value TEXT, expires_at REAL)
expires_at = unix epoch (UTC). NULL이면 영구.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import aiosqlite

_INIT_SQL = """
CREATE TABLE IF NOT EXISTS cache (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    expires_at REAL
);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache(expires_at);
"""


class Cache:
    """비동기 SQLite TTL 캐시. 단일 프로세스용."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._initialized = False

    async def _ensure_init(self) -> None:
        if self._initialized:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(_INIT_SQL)
            await db.commit()
        self._initialized = True

    async def get(self, key: str) -> Any | None:
        await self._ensure_init()
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            )
            row = await cur.fetchone()
            if row is None:
                return None
            value_str, expires_at = row
            if expires_at is not None and expires_at < time.time():
                # 만료 — 정리하고 miss 반환
                await db.execute("DELETE FROM cache WHERE key = ?", (key,))
                await db.commit()
                return None
            return json.loads(value_str)

    async def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        """ttl_seconds=None 이면 영구 보관."""
        await self._ensure_init()
        expires_at = time.time() + ttl_seconds if ttl_seconds is not None else None
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO cache(key, value, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(value, ensure_ascii=False), expires_at),
            )
            await db.commit()

    async def purge_expired(self) -> int:
        """만료 항목 일괄 삭제. 정리된 행 수 반환."""
        await self._ensure_init()
        async with aiosqlite.connect(self.path) as db:
            cur = await db.execute(
                "DELETE FROM cache WHERE expires_at IS NOT NULL AND expires_at < ?",
                (time.time(),),
            )
            await db.commit()
            return cur.rowcount or 0
