"""server.py transport CLI flag + HTTP 분기 단위 테스트.

실 uvicorn boot 은 통합 smoke 에서 별도로 수행. 여기서는 인자 파싱과
FastMCP 인스턴스의 HTTP 친화 옵션이 켜져 있는지만 검증.
"""

from __future__ import annotations

from caselaw_mcp.server import _build_arg_parser, mcp


def test_default_transport_is_stdio() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args([])
    assert args.transport == "stdio"


def test_http_transport_with_defaults() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(["--transport", "http"])
    assert args.transport == "http"
    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.path == "/mcp"


def test_http_transport_custom_host_port_path() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args(
        [
            "--transport",
            "http",
            "--host",
            "0.0.0.0",
            "--port",
            "9000",
            "--path",
            "/api/mcp",
        ]
    )
    assert args.host == "0.0.0.0"
    assert args.port == 9000
    assert args.path == "/api/mcp"


def test_invalid_transport_choice_rejected(capsys) -> None:
    parser = _build_arg_parser()
    try:
        parser.parse_args(["--transport", "websocket"])
    except SystemExit as exc:
        assert exc.code == 2
    err = capsys.readouterr().err
    assert "invalid choice" in err


def test_mcp_instance_has_http_friendly_options() -> None:
    """HTTP 모드에서 ChatGPT·Cloudflare Tunnel 호환을 위해 stateless+JSON 응답."""
    assert mcp.settings.stateless_http is True
    assert mcp.settings.json_response is True
