"""i18n locale 단위 테스트."""

from __future__ import annotations

from pathlib import Path

import pytest

from caselaw_mcp.tools.citizen import locale as loc


@pytest.fixture
def isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from caselaw_mcp import config as cfg

    fake = cfg.Settings(oc="x", cache_path=tmp_path / "c.db")
    monkeypatch.setattr(cfg, "get_settings", lambda: fake)
    monkeypatch.setattr(loc, "get_settings", lambda: fake)
    return tmp_path


def test_default_locale(isolated: Path) -> None:
    assert loc.get_user_locale()["locale"] == "ko"


def test_set_get(isolated: Path) -> None:
    loc.set_user_locale("en")
    assert loc.get_user_locale()["locale"] == "en"


def test_invalid_locale_raises(isolated: Path) -> None:
    with pytest.raises(ValueError, match="locale must be"):
        loc.set_user_locale("fr")


def test_disclaimer_localized_en(isolated: Path) -> None:
    r = loc.get_disclaimer_localized("standard", locale="en")
    assert r["locale"] == "en"
    assert "legal advice" in r["text"]


def test_disclaimer_localized_zh(isolated: Path) -> None:
    r = loc.get_disclaimer_localized("statute_imminent", locale="zh")
    assert "时效" in r["text"] or "诉讼" in r["text"]


def test_disclaimer_localized_vi(isolated: Path) -> None:
    r = loc.get_disclaimer_localized("criminal_serious", locale="vi")
    assert "112" in r["text"]


def test_disclaimer_localized_ja(isolated: Path) -> None:
    r = loc.get_disclaimer_localized("standard", locale="ja")
    assert "弁護士" in r["text"]


def test_list_disclaimers_localized(isolated: Path) -> None:
    r = loc.list_disclaimers_localized(locale="en")
    assert "standard" in r
    assert "statute_imminent" in r
    assert all(isinstance(v, str) for v in r.values())


def test_localize_label_domain(isolated: Path) -> None:
    assert loc.localize_label("domains", "민사", locale="en") == "Civil"
    assert loc.localize_label("domains", "형사", locale="zh") == "刑事"


def test_localize_label_status(isolated: Path) -> None:
    assert loc.localize_label("status", "imminent", locale="en") == "Imminent"
    assert loc.localize_label("status", "expired", locale="vi") == "Đã hết hạn"


def test_localize_label_unknown_returns_key(isolated: Path) -> None:
    assert loc.localize_label("domains", "unknown_xyz", locale="en") == "unknown_xyz"


def test_foreigner_resources(isolated: Path) -> None:
    r = loc.get_foreigner_resources(locale="en")
    assert r["count"] == 4
    names = [it["name"] for it in r["items"]]
    assert any("Foreigner" in n or "Migrant" in n or "Danuri" in n for n in names)


def test_foreigner_resources_vi(isolated: Path) -> None:
    r = loc.get_foreigner_resources(locale="vi")
    assert r["count"] == 4
    # 베트남어 라벨 확인
    assert any("nước ngoài" in it["name"] or "Danuri" in it["name"] for it in r["items"])
