"""사용자 언어 설정 + 다국어 면책·라벨 회수.

지원 언어: ko (한국어 기본) / en / zh / vi / ja
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import Any

from caselaw_mcp.config import get_settings

SUPPORTED_LOCALES: tuple[str, ...] = ("ko", "en", "zh", "vi", "ja")
DEFAULT_LOCALE = "ko"


def _state_path() -> Path:
    settings = get_settings()
    return settings.cache_path.parent / "locale.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    text = (
        resources.files("caselaw_mcp.citizen_data")
        .joinpath("i18n.json")
        .read_text(encoding="utf-8")
    )
    return json.loads(text)


# ─────────────────────────────────────────────
# 모드 (lawyer 모드와 별개로 locale 만 관리)
# ─────────────────────────────────────────────
def get_user_locale() -> dict[str, str]:
    p = _state_path()
    if not p.exists():
        return {"locale": DEFAULT_LOCALE, "source": "default"}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        loc = data.get("locale")
        if loc in SUPPORTED_LOCALES:
            return {"locale": loc, "source": "file", "path": str(p)}
    except (OSError, ValueError):
        pass
    return {"locale": DEFAULT_LOCALE, "source": "fallback"}


def set_user_locale(locale: str) -> dict[str, str]:
    """사용자 언어 변경.

    Args:
        locale: 'ko' | 'en' | 'zh' | 'vi' | 'ja'
    """
    if locale not in SUPPORTED_LOCALES:
        raise ValueError(f"locale must be one of {SUPPORTED_LOCALES}, got {locale!r}")
    p = _state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"locale": locale}, ensure_ascii=False), encoding="utf-8")
    return {"locale": locale, "source": "file", "path": str(p), "changed": True}


# ─────────────────────────────────────────────
# 다국어 면책·라벨 회수
# ─────────────────────────────────────────────
def get_disclaimer_localized(
    kind: str = "standard",
    locale: str | None = None,
) -> dict[str, str]:
    """면책 문구를 지정 언어로 반환.

    Args:
        kind: 'standard' / 'statute_imminent' / 'criminal_serious'
              / 'victim_support_needed' / 'ai_limitation' / 'data_freshness'
        locale: 'ko' / 'en' / 'zh' / 'vi' / 'ja'. None 이면 사용자 설정.
    """
    if locale is None:
        locale = get_user_locale()["locale"]
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    data = _load()
    disc = data["disclaimers"]
    if kind not in disc:
        kind = "standard"
    text = disc[kind].get(locale) or disc[kind][DEFAULT_LOCALE]
    return {"kind": kind, "locale": locale, "text": text}


def list_disclaimers_localized(locale: str | None = None) -> dict[str, str]:
    """모든 면책 문구를 지정 언어로 dict 반환."""
    if locale is None:
        locale = get_user_locale()["locale"]
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE
    out: dict[str, str] = {}
    for kind, by_loc in _load()["disclaimers"].items():
        out[kind] = by_loc.get(locale) or by_loc[DEFAULT_LOCALE]
    return out


def localize_label(
    category: str,
    key: str,
    locale: str | None = None,
) -> str:
    """단일 라벨 다국어 변환.

    Args:
        category: 'domains' | 'status' | 'complexity' | 'ui'
        key: 라벨 키 (예: '민사', 'safe', 'low', 'case_summary')
        locale: 언어. None=사용자 설정.

    Returns:
        매칭 안 되면 원본 key 반환.
    """
    if locale is None:
        locale = get_user_locale()["locale"]
    labels = _load().get("labels", {})
    cat = labels.get(category, {})
    entry = cat.get(key)
    if entry is None:
        return key
    if locale in entry:
        return entry[locale]
    return entry.get(DEFAULT_LOCALE, key)


def get_foreigner_resources(locale: str | None = None) -> dict[str, Any]:
    """외국인 전용 무료 상담처 (다국어 운영). 4곳.

    Args:
        locale: 사용자 언어. 응답의 name 필드를 해당 언어로 반환.
    """
    if locale is None:
        locale = get_user_locale()["locale"]
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    out = []
    for entry in _load().get("foreigner_resources", []):
        name = entry["name"].get(locale) or entry["name"][DEFAULT_LOCALE]
        out.append(
            {
                "name": name,
                "phone": entry["phone"],
                "supported_languages": entry["languages"],
                "scope": entry["scope"],
            }
        )
    return {
        "locale": locale,
        "items": out,
        "count": len(out),
    }
