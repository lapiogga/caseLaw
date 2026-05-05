# API_REFERENCE — CaseLaw MCP

> 활성 MCP Tool **20종** 입출력 스키마. v0.1.0 기준.

## 목차

- [헬스체크](#헬스체크)
  - [`ping`](#ping)
- [판례 (Precedent)](#판례)
  - [`search_precedent`](#search_precedent)
  - [`get_precedent`](#get_precedent)
  - [`find_related_precedents`](#find_related_precedents)
- [현행법령 (Statute)](#현행법령)
  - [`search_statute`](#search_statute)
  - [`get_statute`](#get_statute)
- [헌재결정례 (Constitutional)](#헌재결정례)
  - [`search_constitutional_decision`](#search_constitutional_decision)
  - [`get_constitutional_decision`](#get_constitutional_decision)
- [법령해석례 (Interpretation)](#법령해석례)
  - [`search_law_interpretation`](#search_law_interpretation)
  - [`get_law_interpretation`](#get_law_interpretation)
- [행정심판례 (Admin Judgment)](#행정심판례)
  - [`search_admin_judgment`](#search_admin_judgment)
  - [`get_admin_judgment`](#get_admin_judgment)
- [위원회 결정문 12종 (Committee)](#위원회-결정문-12종)
  - [`search_committee_decision`](#search_committee_decision)
  - [`get_committee_decision`](#get_committee_decision)
- [특별행정심판 4종 (Special)](#특별행정심판-4종)
  - [`search_special_admin_judgment`](#search_special_admin_judgment)
  - [`get_special_admin_judgment`](#get_special_admin_judgment)
- [중앙부처 1차 해석 39종 (Central Dept)](#중앙부처-1차-해석-39종)
  - [`search_central_dept_interpretation`](#search_central_dept_interpretation)
  - [`get_central_dept_interpretation`](#get_central_dept_interpretation)
- [법령용어 (Terminology)](#법령용어)
  - [`search_legal_term`](#search_legal_term)
  - [`get_legal_term`](#get_legal_term)
- [정적 코드표](#정적-코드표)
  - [`lookup_case_codes`](#lookup_case_codes)

---

## 공통

- **인증**: `CASELAW_OC` 환경변수 1개 (자동 주입)
- **응답 포맷**: 모든 한국어 키는 영문 snake_case 로 정규화 (예: `사건번호` → `case_number`)
- **캐시**: 본문(`get_*`) 영구, 목록(`search_*`) 1시간 TTL, 법령용어 24시간
- **페이지네이션**: `display` 1~100 자동 클램프, `page` 1부터
- **검색 범위**: `search_scope = "title"|"body"` (사건명만 / 본문만)
- **빈 응답**: API가 200 + 0 bytes 반환 시 `{"items": [], "count": 0, "empty_response": True}` 자동 변환

---

## 헬스체크

### `ping`

**입력**: 없음

**출력**:
```json
{
  "status": "ok",
  "version": "0.1.0",
  "time_utc": "2026-05-04T07:42:00.123+00:00",
  "oc_configured": true,
  "phase": "4-quality"
}
```

---

## 판례

### `search_precedent`

대법원·고등·지방법원 판례 목록 검색.

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `query` | str | (필수) | 검색어 |
| `court` | str? | None | "대법원"/"supreme"/"고등법원" 등 |
| `case_type` | str? | None | "형사"/"criminal"/"400102" 등 |
| `date_from` | str? | None | 선고일자 시작 YYYYMMDD |
| `date_to` | str? | None | 선고일자 종료 YYYYMMDD |
| `search_scope` | str? | None | "title" / "body" |
| `display` | int | 20 | 1~100 |
| `page` | int | 1 | 1부터 |

**출력**:
```json
{
  "items": [
    {
      "prec_id": "616247",
      "case_number": "2025도15970",
      "case_name": "사기·도로교통법위반(음주운전)·...",
      "court": "대법원",
      "case_type": "형사",
      "case_type_code": "400102",
      "instance": "대법",
      "decision_type": "판결",
      "judgment_date": "2026.01.29",
      "judgment_form": "판결",
      "detail_url": "/DRF/lawService.do?...&ID=616247&type=HTML"
    }
  ],
  "total_count": 231,
  "page": 1,
  "query": "음주운전",
  "count": 5
}
```

### `get_precedent`

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `prec_id` | str | `search_precedent` 결과의 `prec_id` |

**출력 (주요 필드)**:
```json
{
  "prec_id": "616247",
  "case_number": "2025도15970",
  "case_name": "...",
  "court": "대법원",
  "judgment_date": "20260129",
  "holdings": "<br/> 금고 이상의 형을 선고받아... 누범사유에 여전히 해당하는지 여부(적극)<br/>",
  "summary": "<br/> 형의 실효 등에 관한 법률... 위 규정에 따라 형이 실효된...<br/>",
  "referenced_articles": "형의 실효 등에 관한 법률 제7조 제1항, 형법 제35조",
  "referenced_precedents": "대법원 2004. 10. 15. 선고 2004도4869 판결, ...",
  "full_text": "(전문)"
}
```

### `find_related_precedents`

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `prec_id` | str | (필수) | 시작 판례 |
| `max_items` | int | 10 | 반환 최대 건수 |

**출력**:
```json
{
  "source_prec_id": "616247",
  "referenced_text": "대법원 2004. 10. 15. 선고 2004도4869 판결, ...",
  "referenced_cases": ["2004도4869", "2012도10269", "2018헌바8"],
  "candidates": [
    {
      "case_number": "2012도10269",
      "prec_id": "166962",
      "court": "대법원",
      "judgment_date": "2012.11.29",
      "case_name": "...",
      "source": "referenced"
    }
  ],
  "count": 8
}
```

`source` 값: `"referenced"`(본문 명시) | `"keyword"`(사건명 키워드 검색)

---

## 현행법령

### `search_statute`

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `query` | str | (필수) | 법령명 |
| `effective_date` | str? | None | 시행일 기준 YYYYMMDD |
| `search_scope` | str? | None | "title"/"body" |
| `display` | int | 20 | 1~100 |
| `page` | int | 1 | |

**출력 (item)**:
```json
{
  "law_id": "001638",
  "law_name": "도로교통법",
  "law_short_name": "도교법",
  "law_type": "법률",
  "promulgation_date": "...",
  "effective_date": "20260402",
  "ministry": "경찰청",
  "ministry_code": "...",
  "detail_url": "/DRF/lawService.do?...&ID=001638"
}
```

### `get_statute`

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `law_id` | str? | 권장. `search_statute` 의 `law_id` |
| `law_name` | str? | id 모를 때 대체 |

**출력**: `basic_info`, `articles[]`, `addenda[]`, `appendix[]` 등 법령 본문 전체.

---

## 헌재결정례

### `search_constitutional_decision`

| 파라미터 | 타입 | 기본값 |
|---|---|---|
| `query` | str | (필수) |
| `date_from` | str? | None |
| `date_to` | str? | None |
| `search_scope` | str? | None |
| `display` | int | 20 |
| `page` | int | 1 |

**출력 (item)**:
```json
{
  "detc_id": "151422",
  "case_number": "2019헌마605",
  "case_name": "2008년 촛불집회 과거사 진상규명 대상 제외 등 위헌확인",
  "final_date": "...",
  "detail_url": "..."
}
```

### `get_constitutional_decision`

| 파라미터 | 타입 |
|---|---|
| `detc_id` | str |

---

## 법령해석례

### `search_law_interpretation`

파라미터: `search_constitutional_decision` 와 동일.

**출력 (item)**:
```json
{
  "expc_id": "328859",
  "case_number": "20-0370",
  "case_name": "개인정보보호위원회 - 「감정평가...」 제47조제1항에 따른...",
  "responder": "법제처",
  "responder_code": "1170000",
  "inquirer": "개인정보보호위원회",
  "inquirer_code": "...",
  "response_date": "2020.11.05",
  "detail_url": "..."
}
```

### `get_law_interpretation`

| 파라미터 | 타입 |
|---|---|
| `expc_id` | str |

---

## 행정심판례

### `search_admin_judgment`

파라미터: `search_constitutional_decision` 와 동일.

**출력 (item)**:
```json
{
  "decc_id": "265021",
  "case_number": "2018경기행심191",
  "case_name": "개인택시운송사업면허 및 택시운전자격 취소처분 취소청구",
  "agency": "...",
  "decision_division_code": "...",
  "decision_date": "2018.04.02",
  "detail_url": "..."
}
```

### `get_admin_judgment`

| 파라미터 | 타입 |
|---|---|
| `decc_id` | str |

---

## 위원회 결정문 12종

### `search_committee_decision`

| 파라미터 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `committee` | str | (필수) | "ftc"/"공정거래"/"공정위" 등. 자세한 별칭은 [CODES.md](./CODES.md#위원회-12종) 참고 |
| `query` | str | (필수) | |
| `date_from` | str? | None | |
| `date_to` | str? | None | |
| `search_scope` | str? | None | |
| `display` | int | 20 | |
| `page` | int | 1 | |

**지원 위원회 12종**: `ppc / eiac / ftc / acr / fsc / nlrc / kcc / iaciac / oclt / ecc / sfc / nhrck`

**출력 (item, 위원회별 약간 상이)**:
```json
{
  "doc_serial_id": "9721",
  "case_number": "2009협심0509",
  "case_name": "군납유류 입찰담합 관련 과징금...",
  "decision_number": "제 2009 - 013호",
  "decision_date": "2009.4.15.",
  "detail_url": "..."
}
```

### `get_committee_decision`

| 파라미터 | 타입 |
|---|---|
| `committee` | str |
| `doc_id` | str |

---

## 특별행정심판 4종

### `search_special_admin_judgment`

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `tribunal` | str | "tax"(조세심판원) / "maritime"(해양안전심판원) / "acrh"(국민권익특별) / "appeal"(소청심사위원회) |
| (이하 동일) | | |

> **주의**: 박재우님의 OC 키는 본 도메인 미승인일 수 있음. open.law.go.kr 마이페이지에서 추가 신청 시 즉시 활성화.

### `get_special_admin_judgment`

| 파라미터 | 타입 |
|---|---|
| `tribunal` | str |
| `doc_id` | str |

---

## 중앙부처 1차 해석 39종

### `search_central_dept_interpretation`

| 파라미터 | 타입 | 설명 |
|---|---|---|
| `dept` | str | 영문 약어("moj","moel"...) 또는 한국어("법무부","고용노동부"...). 39종 [CODES.md](./CODES.md#중앙부처-39종) |
| (이하 동일) | | |

> **주의**: 동일하게 OC 권한 범위 확인 필요.

### `get_central_dept_interpretation`

일부 부처(`moef`, `nts`)는 본문 조회 미지원 (가이드 표 기준).

---

## 법령용어

### `search_legal_term`

| 파라미터 | 타입 |
|---|---|
| `query` | str |
| `display` | int (기본 20) |
| `page` | int (기본 1) |

**출력 (item)**:
```json
{
  "term_id": "851917",
  "term_name": "공탁(공탁 신청 및 성립)",
  "detail_url": "/DRF/lawService.do?...&trmSeqs=851917",
  "detail_search_url": "/LSW/lsTrmInfoR.do?trmSeqs=851917",
  "dict_division_code": "011405"
}
```

### `get_legal_term`

| 파라미터 | 타입 |
|---|---|
| `term_id` | str |

---

## 정적 코드표

### `lookup_case_codes`

**입력**: 없음

**출력**:
```json
{
  "case_type": {"민사": "400101", "형사": "400102", "특별": "400103", ...},
  "case_type_en": {"civil": "400101", "criminal": "400102", ...},
  "court_aliases": {"supreme": "대법원", "constitutional": "헌법재판소", ...},
  "search_scope": {"title": 1, "body": 2},
  "note": "search_precedent(case_type='형사' or 'criminal' or '400102') 동일."
}
```

전체 코드·별칭은 [CODES.md](./CODES.md) 참조.

---

## 에러 처리

모든 tool은 다음 형태로 실패 가능:

| Exception | 의미 | 후속 |
|---|---|---|
| `ValueError` | 입력 검증 실패 (예: `prec_id` 가 숫자 아님) | LLM 이 입력 보정 |
| `CaseLawAPIError` | HTTP 4xx/5xx, JSON 파싱 실패 등 | OC 키·네트워크 점검 |

빈 결과는 **에러가 아니다** — `{"items": [], "count": 0, "total_count": 0}` 정상 반환.

OC 키 미설정 시 `CaseLawClient` 초기화 단계에서 즉시 `CaseLawAPIError("CASELAW_OC 환경변수 미설정...")`.
