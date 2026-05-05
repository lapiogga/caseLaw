"""면책 문구 — 변호사법 준수·법률자문 회피 가드레일.

원칙: 모든 citizen mode 응답에 standard 면책을 자동 부착.
시효 임박·형사 중대·피해자 지원 필요 시 추가 문구.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from typing import Any


@lru_cache(maxsize=1)
def _load() -> dict[str, str]:
    text = resources.files("caselaw_mcp.citizen_data").joinpath("disclaimers.json").read_text(
        encoding="utf-8"
    )
    return {k: v for k, v in json.loads(text).items() if not k.startswith("_")}


def get_disclaimer(kind: str = "standard") -> str:
    """단일 면책 문구 반환.

    Args:
        kind: 'standard' | 'statute_imminent' | 'criminal_serious'
              | 'victim_support_needed' | 'ai_limitation' | 'data_freshness'
    """
    data = _load()
    if kind not in data:
        return data["standard"]
    return data[kind]


def list_disclaimers() -> dict[str, str]:
    """모든 면책 문구 반환 (LLM이 컨텍스트별 선택)."""
    return dict(_load())


def attach(payload: dict[str, Any], kinds: list[str] | None = None) -> dict[str, Any]:
    """payload 에 disclaimers 키를 추가해 반환 (원본 불변).

    Args:
        payload: tool 응답 dict
        kinds: 부착할 면책 종류 (기본 ['standard'])
    """
    if kinds is None:
        kinds = ["standard"]
    data = _load()
    notices = [data[k] for k in kinds if k in data]
    return {**payload, "disclaimers": notices}
