"""법제처 API 응답(한국어 키) → 영문 snake_case dict 정규화.

목적: LLM이 응답을 일관된 스키마로 받도록 한국어 키를 표준화.
원본 한국어 값은 보존(법원명·사건명 등은 한국어가 정답).
"""

from __future__ import annotations

from typing import Any, Final

import xmltodict

# ─────────────────────────────────────────────
# 키 매핑 — 판례 (precListGuide / precInfoGuide)
# ─────────────────────────────────────────────
PREC_KEYMAP: Final[dict[str, str]] = {
    "판례일련번호": "prec_id",
    "사건번호": "case_number",
    "사건명": "case_name",
    "법원명/처분청": "court",
    "법원명": "court",
    "법원종류코드": "court_code",
    "사건종류명": "case_type",
    "사건종류코드": "case_type_code",
    "심급": "instance",
    "구분": "decision_type",  # 판결/결정 등
    "선고일자": "judgment_date",
    "선고": "judgment",
    "판결유형": "judgment_form",
    "판례상세링크": "detail_url",
    "판시사항": "holdings",
    "판결요지": "summary",
    "참조조문": "referenced_articles",
    "참조판례": "referenced_precedents",
    "판례내용": "full_text",
    "키워드": "query",
    "id": "row_id",
    "totalCnt": "total_count",
    "page": "page",
    "target": "target",
    "prec": "items",
}

# ─────────────────────────────────────────────
# 키 매핑 — 법령 (lsEfYdListGuide / lsEfYdInfoGuide)
# ─────────────────────────────────────────────
LAW_KEYMAP: Final[dict[str, str]] = {
    "법령일련번호": "law_id",
    "법령ID": "law_id",
    "법령명한글": "law_name",
    "법령명": "law_name",
    "법령약칭명": "law_short_name",
    "법령구분명": "law_type",
    "공포일자": "promulgation_date",
    "공포번호": "promulgation_number",
    "시행일자": "effective_date",
    "제정·개정구분명": "revision_type",
    "제개정구분명": "revision_type",
    "소관부처명": "ministry",
    "소관부처코드": "ministry_code",
    "법령상세링크": "detail_url",
    "현행연혁구분": "status",
    "조문": "articles",
    "조문내용": "article_text",
    "조문번호": "article_number",
    "조문제목": "article_title",
    "부칙": "addenda",
    "별표": "appendix",
    "기본정보": "basic_info",
    "law": "items",
    "LawSearch": "result",
    "PrecSearch": "result",
    "DetcSearch": "result",
    "Expc": "result",
    "Decc": "result",
    "detc": "items",
    "Detc": "items",
    "expc": "items",
    "decc": "items",
    "Prec": "items",
    "id": "row_id",
    "totalCnt": "total_count",
    "numOfRows": "num_of_rows",
    "resultCode": "result_code",
    "resultMsg": "result_msg",
    "section": "section",
    "page": "page",
    "target": "target",
    # 결정례 / 해석례 / 심판례 공통 필드
    "안건명": "case_name",
    "안건번호": "case_number",
    "법령해석례일련번호": "expc_id",
    "법령해석상세링크": "detail_url",
    "회신기관명": "responder",
    "회신기관코드": "responder_code",
    "회신일자": "response_date",
    "질의기관명": "inquirer",
    "질의기관코드": "inquirer_code",
    "행정심판재결례일련번호": "decc_id",
    "행정심판재결례상세링크": "detail_url",
    "재결구분명": "decision_division",
    "재결구분코드": "decision_division_code",
    "의결일자": "decision_date",
    "처리일자": "processed_date",
    "신청청": "applicant",
    "처분청": "agency",
    "헌재결정례일련번호": "detc_id",
    "헌재결정례상세링크": "detail_url",
    "종국일자": "final_date",
    "결정유형": "decision_type",
    "사건구분": "case_division",
    "사건구분코드": "case_division_code",
    # 위원회 결정문 12종 — 실제 응답: 최상위가 <Cmt>(대문자), 안에 <cmt>(소문자) 배열
    "Ppc": "result", "ppc": "items",
    "Eiac": "result", "eiac": "items",
    "Ftc": "result", "ftc": "items",
    "Acr": "result", "acr": "items",
    "Fsc": "result", "fsc": "items",
    "Nlrc": "result", "nlrc": "items",
    "Kcc": "result", "kcc": "items",
    "Iaciac": "result", "iaciac": "items",
    "Oclt": "result", "oclt": "items",
    "Ecc": "result", "ecc": "items",
    "Sfc": "result", "sfc": "items",
    "Nhrck": "result", "nhrck": "items",
    # 위원회 공통 한국어 필드
    "기관명": "institution",
    "회의구분": "meeting_type",
    "결정구분": "decision_division_label",
    # 특별행정심판 4종 — 실제 응답 wrapper 패턴 동일 (대문자 → result)
    "SpecialDeccTt": "result", "specialDeccTt": "items",
    "SpecialDeccKmst": "result", "specialDeccKmst": "items",
    "SpecialDeccAcr": "result", "specialDeccAcr": "items",
    "SpecialDeccAdap": "result", "specialDeccAdap": "items",
    # 중앙부처 1차 해석 — 일관 wrapper (CgmExpc<Dept>)
    "CgmExpc": "result",
    # 법령용어
    "LsTrmSearch": "result",
    "lstrm": "items",
    "법령용어ID": "term_id",
    "법령용어명": "term_name",
    "법령용어설명": "term_definition",
    "법령용어상세링크": "detail_url",
    "법령용어상세검색": "detail_search_url",
    "사전구분코드": "dict_division_code",
    "용어유형코드": "term_type_code",
    # 위원회·심판 공통
    "결정일자": "decision_date",
    "결정번호": "decision_number",
    "처분일자": "disposition_date",
    "처분내용": "disposition_content",
    "처분기관": "disposition_agency",
    "결정문일련번호": "doc_serial_id",
    "결정문상세링크": "detail_url",
}


def _merge_keymaps(*maps: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in maps:
        out.update(m)
    return out


COMBINED_KEYMAP: Final[dict[str, str]] = _merge_keymaps(PREC_KEYMAP, LAW_KEYMAP)


# ─────────────────────────────────────────────
# 정규화 함수
# ─────────────────────────────────────────────
def normalize(obj: Any, keymap: dict[str, str] = COMBINED_KEYMAP) -> Any:
    """재귀적으로 dict 키를 영문 snake_case 로 변환.

    - dict: 키 매핑 (없으면 원본 유지)
    - list: 원소 단위 재귀
    - 기타(스칼라): 그대로 반환
    """
    if isinstance(obj, dict):
        return {keymap.get(k, k): normalize(v, keymap) for k, v in obj.items()}
    if isinstance(obj, list):
        return [normalize(item, keymap) for item in obj]
    return obj


def parse_xml(text: str, keymap: dict[str, str] = COMBINED_KEYMAP) -> dict[str, Any]:
    """XML 응답 → dict + 키 정규화."""
    raw = xmltodict.parse(text)
    return normalize(raw, keymap)


def parse_json(payload: dict[str, Any], keymap: dict[str, str] = COMBINED_KEYMAP) -> dict[str, Any]:
    """JSON 응답 dict → 키 정규화."""
    return normalize(payload, keymap)


def extract_items(normalized: dict[str, Any]) -> list[dict[str, Any]]:
    """정규화된 응답에서 `items` 리스트만 추출.

    법제처 응답은 보통 `{"result": {"items": [...]}}` 구조.
    `items` 가 단건일 때 dict 가 오기도 하므로 list 로 통일.
    """
    result = normalized.get("result") or normalized
    items = result.get("items") if isinstance(result, dict) else None
    if items is None:
        return []
    if isinstance(items, dict):
        return [items]
    return list(items)
