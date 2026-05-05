"""attachments — 첨부 다운로드 helper 단위 테스트 (네트워크 무관 부분)."""

from __future__ import annotations

import pytest

from caselaw_mcp.tools.attachments import (
    _ext_from_content_type,
    _filename_from_headers,
    _safe_filename,
    download_attachment,
    extract_attachments_from_text,
)


@pytest.mark.parametrize(
    ("ct", "expected"),
    [
        ("application/pdf", ".pdf"),
        ("application/x-hwp", ".hwp"),
        ("application/vnd.hancom.hwp", ".hwp"),
        ("application/msword", ".docx"),
        ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
        ("application/vnd.ms-excel", ".xlsx"),
        ("text/plain", ".bin"),
        ("", ".bin"),
    ],
)
def test_ext_from_content_type(ct: str, expected: str) -> None:
    assert _ext_from_content_type(ct) == expected


@pytest.mark.parametrize(
    ("disp", "expected"),
    [
        ('attachment; filename="별표1.hwp"', "별표1.hwp"),
        ("attachment; filename=table.pdf", "table.pdf"),
        ("attachment; filename*=UTF-8''%EB%B3%84%ED%91%9C1.hwp", "별표1.hwp"),
        (None, None),
        ("inline", None),
    ],
)
def test_filename_from_headers(disp: str | None, expected: str | None) -> None:
    assert _filename_from_headers(disp) == expected


@pytest.mark.parametrize(
    ("inp", "expected_safe"),
    [
        ("normal.pdf", "normal.pdf"),
        # / 는 _ 로 치환되어 path traversal 차단 (.. 자체는 unsafe 패턴 외이므로 보존)
        ("../../etc/passwd", "_.._etc_passwd"),
        ("file:with*illegal?chars.txt", "file_with_illegal_chars.txt"),
        ("CON.pdf", "_CON.pdf"),
        ("PRN", "_PRN"),
        ("", "attachment.bin"),
        (".", "attachment.bin"),
        ("..", "attachment.bin"),
    ],
)
def test_safe_filename(inp: str, expected_safe: str) -> None:
    out = _safe_filename(inp)
    assert out == expected_safe


def test_extract_attachments_from_text_basic() -> None:
    text = (
        "본문에 별표 링크 두 개: "
        "https://www.law.go.kr/LSW/flDownload.do?flSeq=162492787 그리고 "
        "/LSW/flDownload.do?flSeq=999"
    )
    out = extract_attachments_from_text(text)
    seqs = [x["file_seq"] for x in out]
    assert "162492787" in seqs
    assert "999" in seqs


def test_extract_attachments_dedup() -> None:
    text = "flDownload.do?flSeq=1 / flDownload.do?flSeq=1 / flDownload.do?flSeq=2"
    out = extract_attachments_from_text(text)
    assert [x["file_seq"] for x in out] == ["1", "2"]


def test_extract_attachments_empty() -> None:
    assert extract_attachments_from_text("") == []
    assert extract_attachments_from_text("no attachments") == []


async def test_download_attachment_invalid_seq_raises() -> None:
    with pytest.raises(ValueError, match="숫자여야"):
        await download_attachment("abc", ".")
