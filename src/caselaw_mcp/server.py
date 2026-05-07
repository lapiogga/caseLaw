"""CaseLaw MCP 서버 엔트리포인트.

활성 tool (Phase 2 시점):
- ping
- search_precedent / get_precedent / find_related_precedents (판례)
- search_statute / get_statute (현행법령)
- search_constitutional_decision / get_constitutional_decision (헌재결정례)
- search_law_interpretation / get_law_interpretation (법령해석례)
- search_admin_judgment / get_admin_judgment (행정심판례)
- lookup_case_codes (정적 코드표)
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from typing import Any

from mcp.server.fastmcp import FastMCP

from caselaw_mcp import __version__
from caselaw_mcp.auth import BearerAuthMiddleware, get_auth_token
from caselaw_mcp.codes import CASE_TYPE, CASE_TYPE_EN, COURT_ALIASES, SEARCH_SCOPE
from caselaw_mcp.config import get_settings
from caselaw_mcp.tools import admin_judg as adj_tools
from caselaw_mcp.tools import analytics as anl_tools
from caselaw_mcp.tools import attachments as atc_tools
from caselaw_mcp.tools import citation_lookup as cit_tools
from caselaw_mcp.tools import committee as cmt_tools
from caselaw_mcp.tools import constitution as con_tools
from caselaw_mcp.tools import dept_interpretation as dept_tools
from caselaw_mcp.tools import interpretation as exp_tools
from caselaw_mcp.tools import precedent as prec_tools
from caselaw_mcp.tools import special_judg as spc_tools
from caselaw_mcp.tools import statute as law_tools
from caselaw_mcp.tools import terminology as trm_tools
from caselaw_mcp.tools.citizen import consultation_kit as cit_kit
from caselaw_mcp.tools.citizen import cost as cit_cost
from caselaw_mcp.tools.citizen import disclaimer as cit_disclaimer
from caselaw_mcp.tools.citizen import interview as cit_interview
from caselaw_mcp.tools.citizen import limitation as cit_limit
from caselaw_mcp.tools.citizen import locale as cit_locale
from caselaw_mcp.tools.citizen import mode as cit_mode
from caselaw_mcp.tools.citizen import pro_bono as cit_probono
from caselaw_mcp.tools.citizen import strength as cit_strength
from caselaw_mcp.tools.citizen import triage as cit_triage

mcp = FastMCP(
    "caselaw-mcp",
    instructions=(
        "법제처 국가법령정보 공동활용 OpenAPI 기반 MCP 서버. "
        "한국 판례·법령·헌재결정례·법령해석례·행정심판례를 검색·조회한다. "
        "search_*로 목록을, get_*로 본문을 받는다. "
        "find_related_precedents 로 관련 판례를 추천."
    ),
    # HTTP transport 친화 옵션 (stdio 모드에는 영향 없음).
    stateless_http=True,
    json_response=True,
)


# ─────────────────────────────────────────────
# Healthcheck
# ─────────────────────────────────────────────
@mcp.tool()
def ping() -> dict[str, Any]:
    """서버 헬스체크."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": __version__,
        "time_utc": datetime.now(UTC).isoformat(),
        "oc_configured": bool(settings.oc),
        "phase": "12-multi-client",
        "user_locale": cit_locale.get_user_locale(),
        "user_mode": cit_mode.get_user_mode(),
    }


# ─────────────────────────────────────────────
# Precedent (판례)
# ─────────────────────────────────────────────
@mcp.tool()
async def search_precedent(
    query: str,
    court: str | None = None,
    case_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """대한민국 판례 목록 검색 (대법원·고등·지방법원 등).

    Args:
        query: 검색어
        court: "대법원"/"supreme" 등. None=전체
        case_type: "형사"/"criminal"/"400102" 등
        date_from / date_to: 선고일자 YYYYMMDD
        search_scope: "title" / "body"
        display: 1~100, page: 1부터
    """
    return await prec_tools.search_precedent(
        query,
        court=court,
        case_type=case_type,
        date_from=date_from,
        date_to=date_to,
        search_scope=search_scope,
        display=display,
        page=page,
    )


@mcp.tool()
async def get_precedent(prec_id: str) -> dict[str, Any]:
    """판례 본문(판시사항·판결요지·참조조문·참조판례·전문) 조회."""
    return await prec_tools.get_precedent(prec_id)


@mcp.tool()
async def find_related_precedents(prec_id: str, max_items: int = 10) -> dict[str, Any]:
    """본문 참조판례 + 사건명 키워드로 관련 판례 추천.

    Returns:
        {source_prec_id, referenced_text, referenced_cases, candidates[]}
        각 candidate 의 'source' 가 'referenced'(명시) 또는 'keyword'(검색).
    """
    return await prec_tools.find_related_precedents(prec_id, max_items=max_items)


# ─────────────────────────────────────────────
# Statute (현행법령)
# ─────────────────────────────────────────────
@mcp.tool()
async def search_statute(
    query: str,
    effective_date: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """대한민국 현행법령 목록 검색 (시행일 기준)."""
    return await law_tools.search_statute(
        query,
        effective_date=effective_date,
        search_scope=search_scope,
        display=display,
        page=page,
    )


@mcp.tool()
async def get_statute(
    law_id: str | None = None,
    law_name: str | None = None,
) -> dict[str, Any]:
    """법령 본문 조회. law_id(권장) 또는 law_name 중 하나."""
    return await law_tools.get_statute(law_id=law_id, law_name=law_name)


# ─────────────────────────────────────────────
# Constitutional Decision (헌재결정례)
# ─────────────────────────────────────────────
@mcp.tool()
async def search_constitutional_decision(
    query: str,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """헌법재판소 결정례 목록 검색."""
    return await con_tools.search_constitutional_decision(
        query,
        date_from=date_from,
        date_to=date_to,
        search_scope=search_scope,
        display=display,
        page=page,
    )


@mcp.tool()
async def get_constitutional_decision(detc_id: str) -> dict[str, Any]:
    """헌재결정례 본문 조회."""
    return await con_tools.get_constitutional_decision(detc_id)


# ─────────────────────────────────────────────
# Law Interpretation (법령해석례)
# ─────────────────────────────────────────────
@mcp.tool()
async def search_law_interpretation(
    query: str,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """법령해석례 목록 검색."""
    return await exp_tools.search_law_interpretation(
        query,
        date_from=date_from,
        date_to=date_to,
        search_scope=search_scope,
        display=display,
        page=page,
    )


@mcp.tool()
async def get_law_interpretation(expc_id: str) -> dict[str, Any]:
    """법령해석례 본문 조회."""
    return await exp_tools.get_law_interpretation(expc_id)


# ─────────────────────────────────────────────
# Administrative Judgment (행정심판례)
# ─────────────────────────────────────────────
@mcp.tool()
async def search_admin_judgment(
    query: str,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """행정심판례(국민권익위·각급 행심위) 목록 검색."""
    return await adj_tools.search_admin_judgment(
        query,
        date_from=date_from,
        date_to=date_to,
        search_scope=search_scope,
        display=display,
        page=page,
    )


@mcp.tool()
async def get_admin_judgment(decc_id: str) -> dict[str, Any]:
    """행정심판례 본문 조회."""
    return await adj_tools.get_admin_judgment(decc_id)


# ─────────────────────────────────────────────
# Committee Decisions (12종 통합)
# ─────────────────────────────────────────────
@mcp.tool()
async def search_committee_decision(
    committee: str,
    query: str,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """위원회 결정문 통합 검색 (12종 위원회).

    Args:
        committee: "ftc"/"공정거래"/"공정위" 등. 지원 영문 약어:
            ppc, eiac, ftc, acr, fsc, nlrc, kcc, iaciac,
            oclt, ecc, sfc, nhrck (한국어 별칭도 다수 매핑)
        query, date_from, date_to, search_scope, display, page
    """
    return await cmt_tools.search_committee_decision(
        committee,
        query,
        date_from=date_from,
        date_to=date_to,
        search_scope=search_scope,
        display=display,
        page=page,
    )


@mcp.tool()
async def get_committee_decision(committee: str, doc_id: str) -> dict[str, Any]:
    """위원회 결정문 본문 조회. committee 별칭은 search_committee_decision 동일."""
    return await cmt_tools.get_committee_decision(committee, doc_id)


# ─────────────────────────────────────────────
# Special Administrative Judgment (4종 통합)
# ─────────────────────────────────────────────
@mcp.tool()
async def search_special_admin_judgment(
    tribunal: str,
    query: str,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """특별행정심판례 통합 검색.

    Args:
        tribunal: "tax"(조세심판원) / "maritime"(해양안전심판원) /
                  "acrh"(국민권익위원회 특별) / "appeal"(소청심사위원회).
                  한국어("조세심판원","해양안전","소청") 별칭 지원.
    """
    return await spc_tools.search_special_admin_judgment(
        tribunal,
        query,
        date_from=date_from,
        date_to=date_to,
        search_scope=search_scope,
        display=display,
        page=page,
    )


@mcp.tool()
async def get_special_admin_judgment(tribunal: str, doc_id: str) -> dict[str, Any]:
    """특별행정심판례 본문 조회."""
    return await spc_tools.get_special_admin_judgment(tribunal, doc_id)


# ─────────────────────────────────────────────
# Central Department Interpretation (39종 통합)
# ─────────────────────────────────────────────
@mcp.tool()
async def search_central_dept_interpretation(
    dept: str,
    query: str,
    date_from: str | None = None,
    date_to: str | None = None,
    search_scope: str | None = None,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """중앙부처 1차 법령해석 통합 검색 (39개 부처).

    Args:
        dept: 영문 약어("moj","moel","mois") 또는 한국어 부처명
              ("법무부","고용노동부","행정안전부" 등). 39종 지원.
    """
    return await dept_tools.search_central_dept_interpretation(
        dept,
        query,
        date_from=date_from,
        date_to=date_to,
        search_scope=search_scope,
        display=display,
        page=page,
    )


@mcp.tool()
async def get_central_dept_interpretation(dept: str, doc_id: str) -> dict[str, Any]:
    """중앙부처 1차 법령해석 본문 조회.

    참고: 일부 부처(재정경제부 moef, 국세청 nts)는 본문 조회 미지원.
    """
    return await dept_tools.get_central_dept_interpretation(dept, doc_id)


# ─────────────────────────────────────────────
# Legal Terminology (법령용어)
# ─────────────────────────────────────────────
@mcp.tool()
async def search_legal_term(
    query: str,
    display: int = 20,
    page: int = 1,
) -> dict[str, Any]:
    """법령용어 사전 검색."""
    return await trm_tools.search_legal_term(query, display=display, page=page)


@mcp.tool()
async def get_legal_term(term_id: str) -> dict[str, Any]:
    """법령용어 본문 조회."""
    return await trm_tools.get_legal_term(term_id)


# ─────────────────────────────────────────────
# Analytics & Practitioner Helpers (Phase 5)
# ─────────────────────────────────────────────
@mcp.tool()
async def analyze_precedent_trend(
    query: str,
    group_by: str = "year",
    court: str | None = None,
    case_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    sample_size: int = 100,
) -> dict[str, Any]:
    """판례 결과를 그룹별로 카운트해 트렌드 반환 (변호사 변론 준비용).

    Args:
        query: 검색어 (예: "음주운전")
        group_by: "year" / "month" / "court" / "case_type" / "instance"
        court, case_type, date_from, date_to: search_precedent 와 동일
        sample_size: 분석할 최대 판례 수 (1~100)

    예시 시나리오:
        "최근 3년 음주운전 판례를 연도별로 정리"
        → analyze_precedent_trend("음주운전", group_by="year", date_from="20230101")
    """
    return await anl_tools.analyze_precedent_trend(
        query,
        group_by=group_by,  # type: ignore[arg-type]
        court=court,
        case_type=case_type,
        date_from=date_from,
        date_to=date_to,
        sample_size=sample_size,
    )


@mcp.tool()
async def format_citation(prec_id: str) -> dict[str, Any]:
    """판례를 한국 법률 표준 인용 형식으로 변환.

    예: prec_id 616247 → "대법원 2026. 1. 29. 선고 2025도15970 판결"
    """
    return await anl_tools.format_citation(prec_id)


@mcp.tool()
async def compare_precedents(prec_ids: list[str]) -> dict[str, Any]:
    """여러 판례를 한 번에 가져와 핵심 필드 비교 표 반환 (최대 10건)."""
    return await anl_tools.compare_precedents(prec_ids)


# ─────────────────────────────────────────────
# Citation Lookup (Phase 6)
# ─────────────────────────────────────────────
@mcp.tool()
async def find_precedent_by_citation(
    citation: str,
    max_items: int = 5,
) -> dict[str, Any]:
    """인용 텍스트(예: "대법원 2024. 5. 30. 선고 2023두12345 판결")에서 사건번호를
    자동 추출하고 prec_id 와 본문 후보를 회수.

    변호사가 변론서·논문에서 본 인용만 갖고 있을 때 prec_id 역검색.
    """
    return await cit_tools.find_precedent_by_citation(citation, max_items=max_items)


# ─────────────────────────────────────────────
# Attachment Download (Phase 6)
# ─────────────────────────────────────────────
@mcp.tool()
async def download_attachment(
    file_seq: str,
    save_dir: str = ".",
    filename: str | None = None,
) -> dict[str, Any]:
    """법령 별표·서식 물리 파일(HWP/PDF)을 flSeq 로 다운로드.

    flSeq는 법령 본문 응답의 `<별표서식파일링크>` 또는 `<별표서식PDF파일링크>`
    값에서 추출. 응답 본문 텍스트 안 `flDownload.do?flSeq=<번호>` 패턴.

    ⚠️ 박재우님 OC 권한에서 별표 endpoint 가 0건이면 본문에 flSeq가 없을 수 있음.
       권한 확장(docs/OC_PERMISSIONS.md) 후 즉시 활용.
    """
    return await atc_tools.download_attachment(file_seq, save_dir, filename=filename)


@mcp.tool()
def extract_attachment_links(text: str) -> list[dict[str, str]]:
    """주어진 텍스트(법령 본문 dump 등)에서 flDownload.do?flSeq=... URL을 모두 추출.

    LLM 이 get_statute 응답을 받은 뒤 본 도구를 호출해 다운로드 가능 첨부 목록을 회수.
    """
    return atc_tools.extract_attachments_from_text(text)


# ─────────────────────────────────────────────
# Citizen Mode (Phase 7) — 일반인 사전진단
# ─────────────────────────────────────────────
@mcp.tool()
def set_user_mode(mode: str) -> dict[str, str]:
    """사용자 모드 변경: "lawyer" (전문) 또는 "citizen" (일반인 사전진단).

    citizen 모드에서는 응답에 면책 고지 자동 부착, 한자·법조문을 일상어로
    풀이, 무료자원·시효 점검을 적극 제공.
    """
    return cit_mode.set_user_mode(mode)


@mcp.tool()
def get_user_mode() -> dict[str, str]:
    """현재 사용자 모드 조회."""
    return cit_mode.get_user_mode()


@mcp.tool()
def get_disclaimer(kind: str = "standard") -> dict[str, str]:
    """면책 문구 반환.

    Args:
        kind: 'standard' / 'statute_imminent' / 'criminal_serious'
              / 'victim_support_needed' / 'ai_limitation' / 'data_freshness'
    """
    return {"kind": kind, "text": cit_disclaimer.get_disclaimer(kind)}


@mcp.tool()
def triage_dispute(
    situation: str,
    event_date: str | None = None,
    top_k: int = 3,
) -> dict[str, Any]:
    """일반인 사실관계 → 분쟁 카테고리 후보·법조문·시효·추천 경로.

    Args:
        situation: 자유 형식 사실관계 (한국어)
            예: "3년 전 친구한테 5천만 원 빌려줬는데 안 갚음, 차용증은 카톡뿐"
        event_date: 사건 발생일 (YYYY-MM-DD), 시효 점검용
        top_k: 후보 수 1~5 (기본 3)

    내장 분쟁 카테고리 30종 (대여금·임대차·교통사고·임금체불·이혼·상속 등)에서
    키워드 매칭 후 시효 자동 점검 + 셀프 vs 변호사 권장 + 면책 고지 자동 부착.
    """
    return cit_triage.triage_dispute(situation, event_date, top_k=top_k)


@mcp.tool()
def list_limitation_categories() -> list[dict[str, Any]]:
    """시효 카테고리 ID·이름·기간 표 반환 (check_statute_of_limitations 의 category_id 참고)."""
    return cit_limit.list_limitation_categories()


@mcp.tool()
def check_statute_of_limitations(category_id: str, event_date: str) -> dict[str, Any]:
    """소멸시효·공소시효 정밀 점검.

    Args:
        category_id: 시효 카테고리 ID. list_limitation_categories 로 조회.
            예: "civil.general"(일반 채권 10년), "tort"(불법행위 3/10년),
                "wage"(임금 3년), "criminal.dui"(음주운전 5년),
                "labor.unfair_dismissal"(부당해고 3개월),
                "family.property_division"(재산분할 2년)
        event_date: 시효 기산점 YYYY-MM-DD

    경과·잔여 일수, 시효 중단 가능 사유, 상태 평가
    (safe / warning / imminent / expired / indefinite) 반환.
    """
    return cit_limit.check_statute_of_limitations(category_id, event_date)


@mcp.tool()
def estimate_litigation_cost(
    claim_amount_krw: int,
    case_type: str = "civil_general",
) -> dict[str, Any]:
    """소송 비용 종합 견적 (인지대 + 송달료 + 변호사 수임료).

    Args:
        claim_amount_krw: 청구 소가 (원). 형사·행정·가사는 0 또는 명목값.
        case_type: "civil_general" / "civil_small_claim" / "criminal_general"
                   / "criminal_dui" / "family_divorce" / "labor_dismissal"
                   / "administrative" / "real_estate" / "medical"

    인지법 별표 기반 인지대 자동 계산 + 송달료 + 변호사비 통상 범위
    + 소액사건심판 가능여부 + 무료자원 안내.
    """
    return cit_cost.estimate_litigation_cost(claim_amount_krw, case_type)


@mcp.tool()
def get_interview_flow() -> list[dict[str, Any]]:
    """6턴 사실관계 인터뷰 플로우 전체 (LLM 사전 학습용)."""
    return cit_interview.get_interview_flow()


@mcp.tool()
def interview_facts(
    turn: int = 1,
    previous_answers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """다턴 사실관계 인터뷰 — N번째 턴 질문 + 누적 case profile 반환.

    Args:
        turn: 1~6. 호스트 LLM이 사용자 답변 받은 후 turn+1로 호출.
        previous_answers: 이전 턴들의 답변 누적
            (예: {"incident_summary": "...", "counterparty": "..."})

    6턴 완료 시 case_profile 종합 + triage_dispute / check_statute_of_limitations
    / estimate_litigation_cost 후속 호출 권장 안내.
    """
    return cit_interview.interview_facts(turn, previous_answers)


@mcp.tool()
async def evaluate_case_strength(
    query: str,
    sample_size: int = 30,
    court: str | None = None,
    case_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict[str, Any]:
    """유사 판례 결과 라벨링 → 승소율 분포 (참고용, 단정 금지).

    Args:
        query: 검색어 (예: "음주운전 면허취소", "임금체불 사직")
        sample_size: 분석할 최대 판례 수 1~100
        court / case_type / date_from / date_to: search_precedent 파라미터

    사건명에서 결과 키워드 추출 (원고승/일부승/기각/취소/유죄/무죄 등)
    → 분포 통계 + 대표 사례 + 면책 자동 부착.
    """
    return await cit_strength.evaluate_case_strength(
        query,
        sample_size=sample_size,
        court=court,
        case_type=case_type,
        date_from=date_from,
        date_to=date_to,
    )


@mcp.tool()
def recommend_pro_bono(
    region: str | None = None,
    domain: str | None = None,
    include_emergency_only: bool = False,
    max_items: int = 15,
) -> dict[str, Any]:
    """지역·분쟁별 무료/저비용 법률 상담처 추천.

    Args:
        region: 지역명 ("서울"/"부산"/"광주"/"경기북부"/"대전·세종·충남" 등). None=전국만.
        domain: 분쟁 유형 (triage_dispute 카테고리 ID 또는 도메인).
                예: "civil.loan", "labor", "criminal.sexual", "family", "consumer".
                None=모든 도메인.
        include_emergency_only: True 면 112·1366·117 등 긴급만.
        max_items: 1~30 (기본 15).

    Returns:
        national / regional_bar / regional_klac / domain_specialized
        / online_self_litigation / emergency 분류된 추천 목록.
    """
    return cit_probono.recommend_pro_bono(
        region=region,
        domain=domain,
        include_emergency_only=include_emergency_only,
        max_items=max_items,
    )


# ─────────────────────────────────────────────
# i18n (Phase 11) — 다국어 면책·라벨
# ─────────────────────────────────────────────
@mcp.tool()
def set_user_locale(locale: str) -> dict[str, str]:
    """사용자 언어 변경. 'ko'/'en'/'zh'/'vi'/'ja'."""
    return cit_locale.set_user_locale(locale)


@mcp.tool()
def get_user_locale() -> dict[str, str]:
    """현재 사용자 언어."""
    return cit_locale.get_user_locale()


@mcp.tool()
def get_disclaimer_localized(
    kind: str = "standard",
    locale: str | None = None,
) -> dict[str, str]:
    """면책 문구 다국어 (standard/statute_imminent/criminal_serious 등 6종 x 5언어)."""
    return cit_locale.get_disclaimer_localized(kind, locale=locale)


@mcp.tool()
def list_disclaimers_localized(locale: str | None = None) -> dict[str, str]:
    """모든 면책 문구를 지정 언어로 dict 반환."""
    return cit_locale.list_disclaimers_localized(locale=locale)


@mcp.tool()
def get_foreigner_resources(locale: str | None = None) -> dict[str, Any]:
    """외국인 전용 다국어 무료 상담처 4곳 (외국인종합안내센터·이주여성긴급·다누리 등)."""
    return cit_locale.get_foreigner_resources(locale=locale)


@mcp.tool()
def prepare_consultation_kit(
    case_profile: dict[str, str],
    triage_result: dict[str, Any] | None = None,
    statute_result: dict[str, Any] | None = None,
    cost_result: dict[str, Any] | None = None,
    similar_precedents: list[dict[str, Any]] | None = None,
    pro_bono_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """변호사 상담 준비 키트 — case_profile 기반 마크다운 자료 자동 생성.

    Args:
        case_profile: interview_facts 6턴 결과 (incident_summary / counterparty
            / evidence / actions_taken / desired_outcome / quantitative)
        triage_result: triage_dispute 응답 (선택, 권장)
        statute_result: check_statute_of_limitations 응답 (선택)
        cost_result: estimate_litigation_cost 응답 (선택)
        similar_precedents: search_precedent items 3건 권장 (선택)
        pro_bono_result: recommend_pro_bono 응답 (선택)

    Returns:
        markdown (변호사에게 전달 가능) + 증거 체크리스트 + 변호사 질문 10개
        + next_steps + estimated_lawyer_session_minutes.
    """
    return cit_kit.prepare_consultation_kit(
        case_profile,
        triage_result=triage_result,
        statute_result=statute_result,
        cost_result=cost_result,
        similar_precedents=similar_precedents,
        pro_bono_result=pro_bono_result,
    )


# ─────────────────────────────────────────────
# Static lookup
# ─────────────────────────────────────────────
@mcp.tool()
def lookup_case_codes() -> dict[str, Any]:
    """판례·법령 검색 코드 매핑표 (사건종류·법원·검색범위)."""
    return {
        "case_type": CASE_TYPE,
        "case_type_en": CASE_TYPE_EN,
        "court_aliases": COURT_ALIASES,
        "search_scope": SEARCH_SCOPE,
        "note": (
            "search_precedent(case_type='형사' or 'criminal' or '400102') 동일. "
            "court='대법원' or 'supreme' 동일."
        ),
    }


# ─────────────────────────────────────────────
# Entrypoint
# ─────────────────────────────────────────────
def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="caselaw-mcp",
        description="CaseLaw MCP 서버 (법제처 OpenAPI 기반).",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="전송 방식. stdio (기본, Claude Desktop·Gemini CLI·Cursor 등) / http (ChatGPT·원격).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="HTTP 모드 listen 주소 (기본 127.0.0.1; 외부 노출은 0.0.0.0).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP 모드 listen 포트 (기본 8000).",
    )
    parser.add_argument(
        "--path",
        default="/mcp",
        help="HTTP 모드 마운트 경로 (기본 /mcp).",
    )
    return parser


def _run_http(host: str, port: int, mount_path: str) -> None:
    """Starlette 위에 mcp.streamable_http_app 을 마운트하고 Bearer 인증을 감싼다."""
    import contextlib

    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount

    # mount path 아래 루트(/)로 mcp 앱이 노출되도록 streamable_http_path 를 / 로 변경.
    mcp.settings.streamable_http_path = "/"

    @contextlib.asynccontextmanager
    async def lifespan(_app: Starlette):
        async with mcp.session_manager.run():
            yield

    inner_app = Starlette(
        routes=[Mount(mount_path, app=mcp.streamable_http_app())],
        lifespan=lifespan,
    )
    asgi_app = BearerAuthMiddleware(inner_app, get_auth_token())
    uvicorn.run(asgi_app, host=host, port=port, log_level="info")


def main() -> None:
    args = _build_arg_parser().parse_args()
    try:
        if args.transport == "stdio":
            mcp.run()
        else:
            _run_http(args.host, args.port, args.path)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
