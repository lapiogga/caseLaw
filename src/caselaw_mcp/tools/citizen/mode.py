"""사용자 모드 토글 — lawyer / citizen.

상태는 캐시 DB와 같은 디렉토리의 mode.json 에 보관 (단순 파일 IO).
프로세스 재시작 후에도 유지.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from caselaw_mcp.config import get_settings

Mode = Literal["lawyer", "citizen"]
VALID_MODES: tuple[str, ...] = ("lawyer", "citizen")
DEFAULT_MODE: Mode = "lawyer"


def _state_path() -> Path:
    settings = get_settings()
    return settings.cache_path.parent / "mode.json"


def get_user_mode() -> dict[str, str]:
    """현재 모드 반환."""
    p = _state_path()
    if not p.exists():
        return {"mode": DEFAULT_MODE, "source": "default"}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        m = data.get("mode")
        if m in VALID_MODES:
            return {"mode": m, "source": "file", "path": str(p)}
    except (OSError, ValueError):
        pass
    return {"mode": DEFAULT_MODE, "source": "fallback"}


def set_user_mode(mode: str) -> dict[str, str]:
    """모드 변경.

    Args:
        mode: 'lawyer' (전문 모드) 또는 'citizen' (일반인 모드)
    """
    if mode not in VALID_MODES:
        raise ValueError(
            f"mode must be one of {VALID_MODES}, got {mode!r}"
        )
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"mode": mode}, ensure_ascii=False), encoding="utf-8")
    return {"mode": mode, "source": "file", "path": str(p), "changed": True}


def is_citizen_mode() -> bool:
    return get_user_mode()["mode"] == "citizen"
