"""법령 별표·서식 파일 다운로드 helper.

법제처 가이드 명시 패턴:
    https://www.law.go.kr/LSW/flDownload.do?flSeq=<번호>

본문조회 응답에 `<별표서식파일링크>` 또는 `<별표서식PDF파일링크>` 가 있을 때,
또는 사용자가 직접 flSeq 를 알 때 호출.

⚠️ 박재우님 OC 권한에서는 별표 endpoint 가 0건 반환될 수 있음 (docs/OC_PERMISSIONS.md 참고).
권한 확장 시 즉시 동작.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import httpx

from caselaw_mcp.config import get_settings

DOWNLOAD_BASE = "https://www.law.go.kr/LSW/flDownload.do"


async def download_attachment(
    file_seq: str | int,
    save_dir: str | Path = ".",
    *,
    filename: str | None = None,
) -> dict[str, Any]:
    """flSeq 로 별표/서식 물리 파일 다운로드.

    Args:
        file_seq: 법제처 응답에 포함된 flSeq (숫자)
        save_dir: 저장 디렉토리. 없으면 자동 생성.
        filename: 강제 파일명. 미지정 시 응답 헤더의 Content-Disposition 또는 'attachment_<seq>'

    Returns:
        {"file_seq", "saved_path", "size_bytes", "content_type"}
    """
    seq = str(file_seq).strip()
    if not seq.isdigit():
        raise ValueError(f"file_seq 는 숫자여야 함: {seq!r}")

    save_dir_path = Path(save_dir).expanduser().resolve()
    save_dir_path.mkdir(parents=True, exist_ok=True)

    settings = get_settings()
    async with httpx.AsyncClient(
        timeout=settings.http_timeout,
        follow_redirects=True,
        headers={"User-Agent": "caselaw-mcp/0.2.0"},
    ) as client:
        resp = await client.get(DOWNLOAD_BASE, params={"flSeq": seq})
        if resp.status_code != 200:
            raise RuntimeError(f"다운로드 실패 HTTP {resp.status_code} (flSeq={seq})")
        if not resp.content:
            raise RuntimeError(f"빈 응답 (flSeq={seq}) — 권한 또는 잘못된 seq 가능")

        # 파일명 추출
        if filename is None:
            filename = (
                _filename_from_headers(resp.headers.get("content-disposition"))
                or f"attachment_{seq}{_ext_from_content_type(resp.headers.get('content-type', ''))}"
            )
        # 안전한 파일명 (path traversal 방지)
        filename = _safe_filename(filename)
        target = save_dir_path / filename
        target.write_bytes(resp.content)

    return {
        "file_seq": seq,
        "saved_path": str(target),
        "size_bytes": len(resp.content),
        "content_type": resp.headers.get("content-type"),
        "filename": filename,
    }


def extract_attachments_from_text(text: str) -> list[dict[str, str]]:
    """본문(JSON dump 한 문자열) 에서 flSeq URL 패턴을 모두 추출.

    응답 본문에 `flDownload.do?flSeq=12345` 가 포함되어 있으면 회수.
    """
    pattern = re.compile(r"flDownload\.do\?flSeq=(\d+)")
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for m in pattern.finditer(text or ""):
        seq = m.group(1)
        if seq in seen:
            continue
        seen.add(seq)
        out.append({"file_seq": seq, "url": f"{DOWNLOAD_BASE}?flSeq={seq}"})
    return out


def _filename_from_headers(disposition: str | None) -> str | None:
    """Content-Disposition: attachment; filename=... 또는 filename*=UTF-8''..."""
    if not disposition:
        return None
    # filename*= (RFC 5987)
    m = re.search(r"filename\*=(?:UTF-8'')?([^;]+)", disposition, re.IGNORECASE)
    if m:
        from urllib.parse import unquote

        return unquote(m.group(1).strip().strip('"'))
    m = re.search(r'filename="?([^";]+)"?', disposition, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def _ext_from_content_type(ct: str) -> str:
    ct = ct.lower()
    if "pdf" in ct:
        return ".pdf"
    if "hwp" in ct or "hancom" in ct:
        return ".hwp"
    if "msword" in ct or "wordprocessingml" in ct:
        return ".docx"
    if "excel" in ct or "spreadsheetml" in ct:
        return ".xlsx"
    return ".bin"


_UNSAFE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _safe_filename(name: str) -> str:
    """경로 분리자·제어문자 제거 (path traversal 방지)."""
    cleaned = _UNSAFE.sub("_", name).strip(" .")
    if not cleaned or cleaned in (".", ".."):
        cleaned = "attachment.bin"
    # Windows 예약 이름 회피
    if cleaned.upper().split(".")[0] in {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }:
        cleaned = "_" + cleaned
    return cleaned[:200]  # 길이 제한
