"""client.py — 모킹 기반 HTTP 클라이언트 단위 테스트.

실 API 호출 없이 httpx 모킹(respx)으로 검증.
실 호출은 tests/integration/ 에서 별도 검증.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from caselaw_mcp.client import BASE_SEARCH, BASE_SERVICE, CaseLawAPIError, CaseLawClient
from caselaw_mcp.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(oc="test_oc", rate_limit_per_sec=10, http_timeout=5.0)


def test_missing_oc_raises() -> None:
    with pytest.raises(CaseLawAPIError, match="CASELAW_OC"):
        CaseLawClient(Settings(oc=""))


@respx.mock
async def test_search_json_success(settings: Settings) -> None:
    payload = {
        "PrecSearch": {
            "키워드": "음주운전",
            "page": "1",
            "totalCnt": "2",
            "prec": [
                {"사건번호": "2025도1", "판례일련번호": "100"},
                {"사건번호": "2025도2", "판례일련번호": "200"},
            ],
        }
    }
    respx.get(BASE_SEARCH).mock(return_value=httpx.Response(200, json=payload))

    async with CaseLawClient(settings) as client:
        result = await client.search(target="prec", query="음주운전", display=2)

    items = result["result"]["items"]
    assert len(items) == 2
    assert items[0]["prec_id"] == "100"
    assert items[1]["case_number"] == "2025도2"


@respx.mock
async def test_detail_json_success(settings: Settings) -> None:
    payload = {"PrecService": {"판시사항": "X", "판결요지": "Y", "판례일련번호": "100"}}
    respx.get(BASE_SERVICE).mock(return_value=httpx.Response(200, json=payload))

    async with CaseLawClient(settings) as client:
        result = await client.detail(target="prec", doc_id=100)

    assert result["PrecService"]["holdings"] == "X"


@respx.mock
async def test_500_then_success_retries(settings: Settings) -> None:
    """5xx → 재시도 → 성공."""
    payload = {"PrecSearch": {"prec": []}}
    route = respx.get(BASE_SEARCH).mock(
        side_effect=[
            httpx.Response(500),
            httpx.Response(200, json=payload),
        ]
    )

    async with CaseLawClient(settings) as client:
        result = await client.search(target="prec", query="x")

    assert route.call_count == 2
    assert result["result"]["items"] == []


@respx.mock
async def test_404_no_retry_raises(settings: Settings) -> None:
    respx.get(BASE_SEARCH).mock(return_value=httpx.Response(404, text="Not Found"))

    async with CaseLawClient(settings) as client:
        with pytest.raises(CaseLawAPIError, match="HTTP 404"):
            await client.search(target="prec", query="x")


@respx.mock
async def test_oc_not_in_logs_or_errors(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    """OC 값이 로그·에러 메시지에 평문으로 노출되면 안 된다."""
    respx.get(BASE_SEARCH).mock(return_value=httpx.Response(404, text="Bad OC=test_oc here"))

    import logging

    with caplog.at_level(logging.INFO):
        async with CaseLawClient(settings) as client:
            with pytest.raises(CaseLawAPIError) as exc_info:
                await client.search(target="prec", query="x")

    # 에러 본문에서 OC 마스킹
    assert "test_oc" not in (exc_info.value.body or "")
    assert "***OC***" in (exc_info.value.body or "")
    # 로그에서도 OC 마스킹
    for record in caplog.records:
        assert "test_oc" not in record.getMessage() or "***OC***" in record.getMessage()
