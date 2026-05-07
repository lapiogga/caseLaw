"""환경변수 기반 설정 로더.

글로벌 규칙: 시크릿은 process env 로만 접근, 미설정 시 명확한 에러.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """CaseLaw MCP 런타임 설정."""

    # 법제처 OPEN API 인증 ID (이메일 ID 앞부분, 예: 'lapiogga')
    # Phase 0 에서는 비어 있어도 서버 부팅 가능 (ping tool 만 동작).
    # Phase 1 진입 시 필수.
    oc: str = Field(default="", description="법제처 OpenAPI 인증 ID")

    # 캐시 DB 경로
    cache_path: Path = Field(
        default_factory=lambda: Path.home() / ".caselaw_mcp" / "cache.db",
        description="SQLite 캐시 파일 경로",
    )

    # 로그 레벨
    log_level: str = Field(default="INFO")

    # Rate limit
    rate_limit_per_sec: int = Field(default=5, ge=1, le=50)

    # HTTP 타임아웃 (초). 첫 TLS 핸드셰이크 + 큰 본문(법령 전문) 고려.
    http_timeout: float = Field(default=30.0, gt=0)

    # HTTP transport Bearer 토큰 (외부 노출 시 필수, stdio 모드에서는 무시).
    # 미설정 시 인증 비활성 (로컬 신뢰 네트워크 한정).
    auth_token: str = Field(default="", description="HTTP transport Bearer 인증 토큰")

    model_config = SettingsConfigDict(
        env_prefix="CASELAW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    """싱글톤 풍 헬퍼. 테스트에서는 Settings() 를 직접 호출하여 override 가능."""
    return Settings()
