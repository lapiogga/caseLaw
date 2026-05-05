"""법제처 API 코드 매핑.

LLM이 자연어("형사", "민사")로 요청하면 사용자가 코드(400102 등)를 외울 필요 없이
자동 변환해 주기 위한 정적 매핑 테이블.
"""

from __future__ import annotations

from typing import Final

# ─────────────────────────────────────────────
# 사건종류 코드 (판례 검색 prncYd / curt 보조)
# ─────────────────────────────────────────────
# 출처: caselaw_vibecoding_guide.md + 법제처 검색 파라미터
# 추가 코드는 실호출 검증 후 확장
CASE_TYPE: Final[dict[str, str]] = {
    "민사": "400101",
    "형사": "400102",
    "특별": "400103",
    "가사": "400104",
    "행정": "400105",
    "특허": "400106",
}

# 영문 alias (LLM 친화)
CASE_TYPE_EN: Final[dict[str, str]] = {
    "civil": "400101",
    "criminal": "400102",
    "special": "400103",
    "family": "400104",
    "administrative": "400105",
    "admin": "400105",
    "patent": "400106",
}


def resolve_case_type(value: str | None) -> str | None:
    """'형사' / 'criminal' / '400102' 모두 받아 코드를 반환. 매칭 실패 시 None."""
    if not value:
        return None
    v = value.strip().lower()
    if v in CASE_TYPE:
        return CASE_TYPE[v]
    if v in CASE_TYPE_EN:
        return CASE_TYPE_EN[v]
    if v.isdigit() and len(v) == 6:
        return v
    # 한글 그대로
    if value.strip() in CASE_TYPE:
        return CASE_TYPE[value.strip()]
    return None


# ─────────────────────────────────────────────
# 법원명 (curt 파라미터)
# ─────────────────────────────────────────────
COURT_ALIASES: Final[dict[str, str]] = {
    "supreme": "대법원",
    "constitutional": "헌법재판소",
    "high": "고등법원",
    "district": "지방법원",
}


def resolve_court(value: str | None) -> str | None:
    """영문 alias → 한국어 법원명. 한국어로 들어오면 그대로 반환."""
    if not value:
        return None
    v = value.strip().lower()
    return COURT_ALIASES.get(v, value.strip())


# ─────────────────────────────────────────────
# 검색 범위 (search 파라미터)
# ─────────────────────────────────────────────
SEARCH_SCOPE: Final[dict[str, int]] = {
    "title": 1,  # 사건명·법령명 검색
    "body": 2,  # 본문(요지·전문) 검색
}


def resolve_search_scope(value: str | int | None) -> int | None:
    """'title' / 'body' / 1 / 2 모두 허용."""
    if value is None:
        return None
    if isinstance(value, int):
        return value if value in (1, 2) else None
    v = value.strip().lower()
    return SEARCH_SCOPE.get(v)


# ─────────────────────────────────────────────
# 위원회 결정문 12종 (target 매핑)
# ─────────────────────────────────────────────
COMMITTEE: Final[dict[str, str]] = {
    "ppc": "ppc",  # 개인정보보호위원회
    "eiac": "eiac",  # 고용보험심사위원회
    "ftc": "ftc",  # 공정거래위원회
    "acr": "acr",  # 국민권익위원회
    "fsc": "fsc",  # 금융위원회
    "nlrc": "nlrc",  # 노동위원회
    "kcc": "kcc",  # 방송미디어통신위원회
    "iaciac": "iaciac",  # 산업재해보상보험재심사위원회
    "oclt": "oclt",  # 중앙토지수용위원회
    "ecc": "ecc",  # 중앙환경분쟁조정위원회
    "sfc": "sfc",  # 증권선물위원회
    "nhrck": "nhrck",  # 국가인권위원회
}

# 한국어 별칭
COMMITTEE_ALIASES: Final[dict[str, str]] = {
    "개인정보": "ppc",
    "개인정보보호": "ppc",
    "개인정보보호위원회": "ppc",
    "고용보험": "eiac",
    "고용보험심사": "eiac",
    "공정거래": "ftc",
    "공정거래위원회": "ftc",
    "공정위": "ftc",
    "국민권익": "acr",
    "권익위": "acr",
    "국민권익위원회": "acr",
    "금융": "fsc",
    "금융위원회": "fsc",
    "금융위": "fsc",
    "노동": "nlrc",
    "노동위": "nlrc",
    "노동위원회": "nlrc",
    "방송미디어통신": "kcc",
    "방통위": "kcc",
    "방송통신": "kcc",
    "산재": "iaciac",
    "산재보상": "iaciac",
    "산업재해": "iaciac",
    "토지수용": "oclt",
    "중앙토지수용": "oclt",
    "환경분쟁": "ecc",
    "중앙환경분쟁": "ecc",
    "증권선물": "sfc",
    "증선위": "sfc",
    "증권선물위원회": "sfc",
    "인권": "nhrck",
    "국가인권": "nhrck",
    "국가인권위원회": "nhrck",
}


def resolve_committee(value: str) -> str | None:
    """영문 코드 또는 한국어 별칭 → 위원회 target 코드."""
    if not value:
        return None
    v = value.strip().lower()
    if v in COMMITTEE:
        return COMMITTEE[v]
    return COMMITTEE_ALIASES.get(value.strip()) or COMMITTEE_ALIASES.get(v)


# ─────────────────────────────────────────────
# 특별행정심판 4종
# ─────────────────────────────────────────────
SPECIAL_TRIBUNAL: Final[dict[str, str]] = {
    "tax": "specialDeccTt",  # 조세심판원
    "maritime": "specialDeccKmst",  # 해양안전심판원
    "acrh": "specialDeccAcr",  # 국민권익위원회 (특별행정심판)
    "appeal": "specialDeccAdap",  # 인사혁신처 소청심사위원회
}

SPECIAL_TRIBUNAL_ALIASES: Final[dict[str, str]] = {
    "조세": "tax",
    "조세심판": "tax",
    "조세심판원": "tax",
    "해양": "maritime",
    "해양안전": "maritime",
    "해양안전심판원": "maritime",
    "권익특별": "acrh",
    "국민권익특별": "acrh",
    "소청": "appeal",
    "소청심사": "appeal",
    "소청심사위원회": "appeal",
}


def resolve_special_tribunal(value: str) -> str | None:
    if not value:
        return None
    v = value.strip().lower()
    if v in SPECIAL_TRIBUNAL:
        return SPECIAL_TRIBUNAL[v]
    alias = SPECIAL_TRIBUNAL_ALIASES.get(value.strip()) or SPECIAL_TRIBUNAL_ALIASES.get(v)
    return SPECIAL_TRIBUNAL.get(alias) if alias else None


# ─────────────────────────────────────────────
# 중앙부처 1차 해석 39종
# (key=영문 약어, value=API target 의 일부 — list/info 분기는 호출부에서)
# ─────────────────────────────────────────────
CENTRAL_DEPT: Final[dict[str, str]] = {
    "moel": "Moel",      # 고용노동부
    "molit": "Molit",    # 국토교통부
    "moef": "Moef",      # 재정경제부 (목록만)
    "mof": "Mof",        # 해양수산부
    "mois": "Mois",      # 행정안전부
    "me": "Me",          # 기후에너지환경부
    "kcs": "Kcs",        # 관세청
    "nts": "Nts",        # 국세청 (목록만)
    "moe": "Moe",        # 교육부
    "msit": "Msit",      # 과학기술정보통신부
    "mpva": "Mpva",      # 국가보훈부
    "mnd": "Mnd",        # 국방부
    "mafra": "Mafra",    # 농림축산식품부
    "mcst": "Mcst",      # 문화체육관광부
    "moj": "Moj",        # 법무부
    "mohw": "Mohw",      # 보건복지부
    "motie": "Motie",    # 산업통상부
    "mogef": "Mogef",    # 성평등가족부
    "mofa": "Mofa",      # 외교부
    "mss": "Mss",        # 중소벤처기업부
    "mou": "Mou",        # 통일부
    "moleg": "Moleg",    # 법제처
    "mfds": "Mfds",      # 식품의약품안전처
    "mpm": "Mpm",        # 인사혁신처
    "kma": "Kma",        # 기상청
    "khs": "Khs",        # 국가유산청
    "rda": "Rda",        # 농촌진흥청
    "npa": "Npa",        # 경찰청
    "dapa": "Dapa",      # 방위사업청
    "mma": "Mma",        # 병무청
    "kfs": "Kfs",        # 산림청
    "nfa": "Nfa",        # 소방청
    "oka": "Oka",        # 재외동포청
    "pps": "Pps",        # 조달청
    "kdca": "Kdca",      # 질병관리청
    "kostat": "Kostat",  # 국가데이터처
    "kipo": "Kipo",      # 지식재산처
    "kcg": "Kcg",        # 해양경찰청
    "naacc": "Naacc",    # 행정중심복합도시건설청
}

CENTRAL_DEPT_ALIASES: Final[dict[str, str]] = {
    "고용노동부": "moel", "고용노동": "moel", "노동부": "moel",
    "국토교통부": "molit", "국토부": "molit", "국토": "molit",
    "재정경제부": "moef", "재경부": "moef",
    "해양수산부": "mof", "해수부": "mof",
    "행정안전부": "mois", "행안부": "mois",
    "기후에너지환경부": "me", "환경부": "me",
    "관세청": "kcs",
    "국세청": "nts",
    "교육부": "moe",
    "과학기술정보통신부": "msit", "과기정통부": "msit", "과기부": "msit",
    "국가보훈부": "mpva", "보훈부": "mpva",
    "국방부": "mnd",
    "농림축산식품부": "mafra", "농림부": "mafra",
    "문화체육관광부": "mcst", "문체부": "mcst",
    "법무부": "moj",
    "보건복지부": "mohw", "복지부": "mohw",
    "산업통상부": "motie", "산자부": "motie",
    "성평등가족부": "mogef", "여성가족부": "mogef", "여가부": "mogef",
    "외교부": "mofa",
    "중소벤처기업부": "mss", "중기부": "mss",
    "통일부": "mou",
    "법제처": "moleg",
    "식품의약품안전처": "mfds", "식약처": "mfds",
    "인사혁신처": "mpm",
    "기상청": "kma",
    "국가유산청": "khs", "문화재청": "khs",
    "농촌진흥청": "rda", "농진청": "rda",
    "경찰청": "npa",
    "방위사업청": "dapa",
    "병무청": "mma",
    "산림청": "kfs",
    "소방청": "nfa",
    "재외동포청": "oka",
    "조달청": "pps",
    "질병관리청": "kdca", "질병청": "kdca",
    "국가데이터처": "kostat", "통계청": "kostat",
    "지식재산처": "kipo", "특허청": "kipo",
    "해양경찰청": "kcg", "해경청": "kcg",
    "행정중심복합도시건설청": "naacc", "행복청": "naacc",
}


def resolve_central_dept(value: str) -> str | None:
    """영문 약어/한국어 부처명 → 부처 코드 (소문자)."""
    if not value:
        return None
    v = value.strip().lower()
    if v in CENTRAL_DEPT:
        return v
    alias = CENTRAL_DEPT_ALIASES.get(value.strip()) or CENTRAL_DEPT_ALIASES.get(v)
    return alias
