"""parsers.py — 응답 정규화 단위 테스트."""

from __future__ import annotations

from caselaw_mcp.parsers import extract_items, normalize, parse_json


def test_normalize_dict_keys() -> None:
    raw = {
        "사건번호": "2025도15970",
        "선고일자": "2026.01.29",
        "법원명": "대법원",
        "alien_field": "should-pass-through",
    }
    out = normalize(raw)
    assert out["case_number"] == "2025도15970"
    assert out["judgment_date"] == "2026.01.29"
    assert out["court"] == "대법원"
    assert out["alien_field"] == "should-pass-through"


def test_normalize_nested_list() -> None:
    raw = {
        "PrecSearch": {
            "키워드": "음주운전",
            "page": "1",
            "prec": [
                {"사건번호": "2025도1", "판례일련번호": "100"},
                {"사건번호": "2025도2", "판례일련번호": "200"},
            ],
        }
    }
    out = normalize(raw)
    items = out["result"]["items"]
    assert len(items) == 2
    assert items[0]["case_number"] == "2025도1"
    assert items[0]["prec_id"] == "100"


def test_extract_items_normal_case() -> None:
    normalized = {
        "result": {
            "items": [{"prec_id": "1"}, {"prec_id": "2"}],
            "total_count": "2",
        }
    }
    items = extract_items(normalized)
    assert len(items) == 2
    assert items[0]["prec_id"] == "1"


def test_extract_items_single_dict_becomes_list() -> None:
    normalized = {"result": {"items": {"prec_id": "1"}}}
    items = extract_items(normalized)
    assert items == [{"prec_id": "1"}]


def test_extract_items_empty() -> None:
    assert extract_items({"result": {}}) == []
    assert extract_items({}) == []


def test_parse_json_passthrough() -> None:
    raw = {"PrecSearch": {"키워드": "X", "prec": [{"사건번호": "9"}]}}
    out = parse_json(raw)
    assert out["result"]["items"][0]["case_number"] == "9"
