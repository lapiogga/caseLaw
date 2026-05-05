# 기술 노트 — 법제처 OPEN API 기반 MCP 서비스

> **CaseLaw MCP v0.8.0** 의 시스템 구성·통신 모델·보안·확장성에 대한 기술 자료.
> 대상 독자: 변호사 IT 책임자, 법률 AI 도구 개발자, MCP 프로토콜 평가자, 보안 검토자.

---

## 1. 개요

CaseLaw MCP 는 한국 법제처가 운영하는 **국가법령정보 공동활용 OPEN API** (191종 데이터셋) 를 **Model Context Protocol (MCP)** 표준으로 추상화하는 서버이다. Claude Desktop · Cursor · VS Code 같은 MCP 호스트와 STDIO transport 로 연결되어, LLM 이 한국 판례·법령·결정례를 자연어로 검색·인용할 수 있게 한다.

### 핵심 설계 원칙

| 원칙 | 구현 |
|---|---|
| **할루시네이션 방지** | 모든 응답은 법제처 OpenAPI 의 실제 데이터에서만 발췌. LLM 이 사건번호·법령조문을 임의로 생성하지 못하도록 tool 출력에 raw 데이터를 그대로 전달 |
| **개인정보 무전송** | 사용자 입력은 본인 PC 의 MCP 호스트에서만 처리. 별도 서버 인프라 없음. 본 MCP 는 stdin/stdout 만 사용 |
| **법제처 부하 최소화** | SQLite TTL 캐시 (24시간 TTL, 같은 검색의 두 번째 호출은 0.008초) + 5 req/sec rate limit |
| **OC 키 보안** | `.env` 또는 MCP host config 의 환경변수에서만 읽음. 모든 로그·에러 메시지에서 자동 마스킹 |
| **3-트랙 사용자** | 변호사 (Tool 27) + 일반인 사전진단 (Tool 12) + 외국인 i18n (Tool 5) 동일 서버에서 활성 |

---

## 2. 시스템 구성

```
┌─────────────────────────────────────────────────────────────────┐
│                      사용자 PC (Windows)                         │
│                                                                  │
│  ┌────────────────────┐         ┌────────────────────────────┐  │
│  │   Claude Desktop    │  STDIO  │   caselaw-mcp 서버         │  │
│  │   (MCP Host, LLM)   │◄───────►│   (Python 3.11+, FastMCP)  │  │
│  └────────────────────┘  JSON-   └─────────────┬──────────────┘  │
│                            RPC                  │                  │
│                                                 │ HTTPS            │
│                                                 ▼                  │
│                                   ┌─────────────────────────┐    │
│                                   │ SQLite TTL 캐시          │    │
│                                   │ ~/.caselaw_mcp/cache.db │    │
│                                   └──────────┬──────────────┘    │
└──────────────────────────────────────────────┼───────────────────┘
                                                │ 캐시 미스 시
                                                ▼
                              ┌───────────────────────────────────┐
                              │  법제처 OPEN API                    │
                              │  open.law.go.kr/DRF/lawSearch.do   │
                              │  open.law.go.kr/DRF/lawService.do  │
                              │  ... (60+ target 매핑)              │
                              └───────────────────────────────────┘
```

### 컴포넌트 역할

| 컴포넌트 | 책임 |
|---|---|
| **Claude Desktop** | LLM 추론, MCP host, 사용자 자연어 입력 → tool call 변환 |
| **caselaw-mcp 서버** | MCP 프로토콜 구현, tool 정의 44개 노출, 법제처 OpenAPI 호출, 응답 파싱·정규화 |
| **SQLite TTL 캐시** | 같은 검색 반복 호출 시 법제처 부하 감소 (TTL 24h) |
| **법제처 OPEN API** | 정부 운영 (Korea Ministry of Government Legislation), 판례·법령·결정례·해석례·심판례·위원회 결정·중앙부처 해석 등 191종 |

---

## 3. MCP Tool 카테고리 (총 44개)

### 트랙 1 — 변호사·로펌 (27 tool)

| 카테고리 | Tool 수 | 핵심 기능 |
|---|---|---|
| 판례 | 3 | search/get/find_related — 대법원·고등·지방, 참조판례 자동 추출 |
| 법령 | 2 | search/get — 시행일 기준 본법·시행령·시행규칙 |
| 헌재결정 | 2 | search/get — 위헌법률심판·헌법소원 |
| 법령해석례 | 2 | search/get — 법제처 해석 |
| 행정심판례 | 2 | search/get — 행정심판위원회 |
| 위원회 결정 | 1 | 12개 위원회 통합 (공정위·금융위·국가인권위 등) `committee` enum |
| 특별행정심판 | 1 | 4개 통합 (조세심판원·해양안전심판원·국민권익특별·소청심사위) |
| 중앙부처 1차 해석 | 1 | 39개 부처 통합 `dept` enum (`cgmExpc<Dept>` 동적 target) |
| 법령용어 사전 | 1 | 법령 정의 용어 |
| Helper | 3 | analyze_trend, format_citation, compare_precedents |
| 인용 역검색 | 1 | "대법원 2025도15970 판결" → prec_id 자동 매칭 |
| 첨부 파일 | 2 | download_attachment + extract_attachment_links (path traversal 방지 포함) |
| 메타 | 6 | ping, lookup_case_codes 등 |

### 트랙 2 — 일반인 사전진단 (12 tool)

7단계 워크플로:

```
1. set_user_mode("citizen")
2. triage_dispute(상황) → 50종 분쟁 카테고리 매칭 + 적용 법률 + 면책 부착
3. check_statute_of_limitations(category, event_date) → 30종 시효 + 5단계 상태 (safe/warning/imminent/expired/indefinite)
4. estimate_litigation_cost(claim_amount) → 인지법 4구간 + 변호사비 9종 + 무료자원 7개
5. interview_facts(turn, answer) → 6턴 stateless 인터뷰
6. evaluate_case_strength(facts) → 9종 판결 라벨 (원고승, 원고일부승, 기각, 공소기각...)
7. recommend_pro_bono(region, domain) → 전국 14 + 지역 14 + KLAC 6 + 도메인특화
8. prepare_consultation_kit(profile) → 13섹션 마크다운 + 변호사 질문 10개 자동
```

### 트랙 3 — 외국인 사용자 (5 tool)

- `set/get_user_locale` — `ko/en/zh/vi/ja`
- `get_disclaimer_localized` / `list_disclaimers_localized` — 6종 면책 × 5언어 = 30개
- `get_foreigner_resources` — 외국인종합안내센터 1345 · 이주여성긴급전화 1577-1366 · 다누리콜센터 1577-5432 · 이주민건강협회

---

## 4. 통신 모델

### MCP STDIO Transport

```
Claude Desktop ──stdin──> caselaw-mcp 서버
              <──stdout── (JSON-RPC 응답)
```

- **프로토콜**: MCP (Anthropic 표준), JSON-RPC 2.0 위에서 동작
- **인증**: 별도 인증 없음 — 같은 사용자 PC 안에서만 통신, OS 권한이 보안 경계
- **세션**: 호스트 시작 시 spawn, 호스트 종료 시 자동 종료

### 외부 API 호출 (HTTPS)

```python
# client.py 핵심 (httpx + tenacity)
async def request(target: str, params: dict) -> dict:
    masked_url = mask_oc(url)  # OC 키 자동 마스킹
    response = await httpx_client.get(url, params=params)
    return parse_xml_or_json(response)

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type((
        httpx.HTTPStatusError,
        httpx.ConnectError,
        httpx.ConnectTimeout,
        httpx.ReadTimeout,
        httpx.RemoteProtocolError,
    )),
)
```

| 항목 | 값 |
|---|---|
| 비동기 클라이언트 | httpx AsyncClient |
| 재시도 정책 | 지수 백오프 5회, 2~30초 |
| 타임아웃 | 기본 30초 (env `CASELAW_HTTP_TIMEOUT`) |
| Rate limit | 5 req/sec (env `CASELAW_RATE_LIMIT_PER_SEC`) |
| Empty response 처리 | 200 OK + 0 bytes → `{items: [], empty_response: True}` 자동 변환 (xmltodict ExpatError 방지) |

---

## 5. 데이터 흐름 — 변호사 시나리오

```
[사용자]
  "음주운전 양형 5건 사건번호 함께 표로 정리"
       │
       ▼
[Claude Desktop / LLM]
  자연어 → tool call:
  search_precedent(keyword="음주운전", display=5)
       │ stdin (JSON-RPC)
       ▼
[caselaw-mcp 서버]
  ① 캐시 조회 (cache.py) → MISS
  ② client.py.request(target="prec", params=...)
  ③ httpx GET https://www.law.go.kr/DRF/lawSearch.do?target=prec&...
       │ HTTPS
       ▼
[법제처 OPEN API]
  XML 응답 (231건 메타데이터)
       │
       ▼
[caselaw-mcp 서버]
  ④ parsers.py: 한국어→영문 키 정규화 (60+ 매핑)
  ⑤ cache.py: TTL 24h 저장
  ⑥ tool 응답 반환
       │ stdout (JSON-RPC)
       ▼
[Claude Desktop / LLM]
  추가로 get_precedent(prec_id) × 5 호출
  → 본문·판시사항·판결요지 회수
  → 표 생성하여 사용자에게 출력
       │
       ▼
[사용자]
  실제 사건번호 + 법원 + 판시사항 표
```

---

## 6. 기술 스택

| 계층 | 기술 |
|---|---|
| 언어 | Python 3.11+ (3.14.4 까지 검증) |
| MCP 라이브러리 | `mcp >= 1.2.0` (Anthropic 공식 FastMCP) |
| HTTP 클라이언트 | `httpx >= 0.27.0` (async) |
| 재시도 | `tenacity >= 8.3.0` |
| XML 파싱 | `xmltodict >= 0.13.0` |
| 캐시 | `aiosqlite >= 0.20.0` |
| 환경 로더 | `pydantic-settings >= 2.3.0` |
| 로깅 | `structlog >= 24.1.0` |
| 빌드 | hatchling |
| 패키지 관리 | uv (또는 pip) |
| Lint·테스트 | ruff + pytest + respx |
| CI | GitHub Actions (Python 3.11/3.12/3.13 매트릭스) |
| 배포 | PyPI (`uvx caselaw-mcp` 한 줄 설치) + GitHub Release ZIP |

---

## 7. 보안 모델

### 위협 표면

| 위협 | 방어 |
|---|---|
| OC 키 노출 | `.env` 또는 host config 환경변수에서만 읽음. 모든 로그·에러에서 `***OC***` 자동 마스킹 (httpx INFO 로그도 import 시점에 silence) |
| 외부 입력으로 인한 SQL/XML 주입 | `prec_id`, `law_id`, `term_id` 등은 `^[0-9]+$` 화이트리스트 검증 후 API 호출 |
| 첨부 파일 path traversal | `flDownload.do` helper 에서 파일명 sanitize (예약 이름·`..`·드라이브 문자 차단) |
| 부정 응답 처리 | 빈 응답·malformed XML → 안전한 default 반환 (xmltodict ExpatError 방지) |
| LLM 할루시네이션 | tool 응답에 raw 데이터 (사건번호, 법령조문 ID) 그대로 노출. LLM 이 임의 생성하지 못하도록 검색 결과를 "사실 소스" 로 제시 |

### 데이터 처리

```
┌─ 사용자 PC (사용자 OS 권한 경계) ────────────────────┐
│                                                       │
│  사용자 입력 (텍스트)                                  │
│       │                                               │
│       ▼                                               │
│  Claude Desktop (Anthropic API 호출 — 사용자가 동의한  │
│       │           Claude Pro/Team 약관 따름)          │
│       ▼                                               │
│  caselaw-mcp 서버 (별도 서버 없음, 사용자 PC 안)      │
│       │                                               │
│       ├── ~/.caselaw_mcp/cache.db (사용자 홈에만)     │
│       │                                               │
│       └── HTTPS (OC 키만, 본문 내용 X)                │
│              ▼                                        │
│        법제처 OPEN API (정부 운영)                    │
└───────────────────────────────────────────────────────┘
```

**사용자 입력 자체는 법제처 API 로 전송되지 않음.** 검색 키워드만 (예: "음주운전") 전송.

---

## 8. 성능

| 항목 | 값 |
|---|---|
| 첫 캐시 미스 호출 | 0.5~3초 (네트워크 + XML 파싱) |
| 캐시 적중 호출 | **0.008초** (SQLite 로컬 조회) |
| Rate limit | 5 req/sec (사용자별, 법제처 부하 보호) |
| 동시 처리 | httpx AsyncClient + asyncio (단일 사용자 동시 호출 가능) |
| 메모리 사용량 | 약 50-100MB (SQLite + httpx + Python 런타임) |
| 패키지 용량 | wheel 92.5KB + sdist 158KB (가벼움) |

---

## 9. 확장성·유지보수

### 새 데이터셋 추가 (법제처 API 191종 → 일부만 사용 중)

```python
# tools/new_data.py
from ..client import request

async def search_new(keyword: str, display: int = 20) -> dict:
    return await request("new_target_id", {"query": keyword, "display": display})

# server.py 에 등록
mcp.add_tool(search_new)
```

`parsers.py` 의 keymap 에 신규 응답 키 추가 (한국어 → 영문 snake_case).

### 새 언어 추가 (현재 5개)

`citizen_data/i18n.json` 에 새 언어 항목 추가 → 기존 trio (locale.py, get_disclaimer_localized 등) 가 자동 인식.

### 외국 판례 통합 (Backlog)

CourtListener (미국), Find Case Law UK 등을 별도 tool 카테고리로 추가 가능. 현재는 한국 법제처만 활성.

---

## 10. 동결 코드 영역 (v0.8.0 기준)

후방 호환 책임 — 변경 시 major version 올릴 것:

| 영역 | 사유 |
|---|---|
| `src/caselaw_mcp/server.py` 의 44 tool signature | MCP 호스트와 직접 contract |
| `src/caselaw_mcp/parsers.py` 의 응답 키 매핑 | 사용자 코드/LLM 프롬프트가 의존 |
| `client.py` 의 OC 환경변수·캐시 경로 | 사용자 환경 의존 |
| `tools/citizen/{mode,locale}.py` 의 파일 기반 상태 (`~/.caselaw_mcp/{mode,locale}.json`) | 영속 상태 |
| `citizen_data/*.json` 시드 (categories/limitations/court_fees/pro_bono/interview/i18n) | ID 변경·제거 금지, 추가만 |
| `docs/API_REFERENCE.md` 명시 입출력 스키마 | 사용자가 의존하는 contract |

---

## 11. 라이선스·기여

| 항목 | 값 |
|---|---|
| 라이선스 | MIT (무료, 상업적 사용 가능, 수정·재배포 가능) |
| 저자 | 박재우 ([lapiogga@gmail.com](mailto:lapiogga@gmail.com)) |
| 기여 | GitHub Pull Request 환영 |
| 행동 강령 | (정해질 예정) |
| 보안 신고 | GitHub Security Advisories 권장 |

### 데이터 출처

- **법제처 국가법령정보 공동활용 OPEN API** — 정부 데이터, 활용신청자에게 무료 제공
- 본 MCP 는 법제처 데이터의 **비공식 클라이언트 라이브러리** 이며, 법제처와 직접적 관계 없음

---

## 12. 향후 로드맵 (v0.9.0+)

| 항목 | 우선순위 | 추정 |
|---|---|---|
| 분쟁 카테고리 50 → 100종 (변협 협업) | High | 분기 |
| 외국 판례 통합 (CourtListener, Find Case Law UK) | Medium | 분기 |
| Vector DB 의미 검색 | Medium | 별도 인프라 필요 |
| Web UI 대시보드 (MCP 외 일반 변호사용) | Low | 큰 작업 |
| 변호사 검토 인증 (`confirmed=true` 시드) | Medium | 변협 협업 |
| 카테고리·시효·비용 시드 자체 다국어화 | Medium | 지금은 한국어만, 호스트 LLM 동적 번역 |
| Anthropic Connector Directory 등록 | High | 심사 1주일 |

---

## 13. 통계 (v0.8.0 시점)

| 항목 | 수 |
|---|---|
| MCP Tools | 44 |
| Python 모듈 | 20 |
| 단위 테스트 | 250 PASS |
| 통합 smoke 시나리오 | 19 |
| 시드 JSON 파일 | 6 |
| 분쟁 카테고리 | 50 |
| 소멸시효 표 | 30 |
| 인지법 구간 | 4 |
| 무료 법률자원 | 30+ |
| 한국어 별칭 | 200+ |
| 법제처 OpenAPI target 매핑 | 60+ |
| 면책 문구 | 30 (6종 × 5언어) |
| 지원 언어 | 5 (ko/en/zh/vi/ja) |
| 누적 commit (v0.8.0) | 12 |

---

## 14. 참조

- 본 레포: <https://github.com/lapiogga/caseLaw>
- PyPI 패키지: <https://pypi.org/project/caselaw-mcp/>
- 법제처 OPEN API: <https://open.law.go.kr>
- MCP 표준: <https://modelcontextprotocol.io>
- Anthropic Claude: <https://claude.ai>
- API 레퍼런스 (전체 44 tool): `docs/API_REFERENCE.md`
- 코드 매핑 사전 (위원회·부처): `docs/CODES.md`
- 변호사 시나리오 30종: `docs/EXAMPLES.md`
- 일반인 모드 워크플로: `docs/CITIZEN_MODE.md`

---

> 본 문서는 v0.8.0 시점 기준이며, v0.9.0 이상에서는 수정될 수 있다. 최신 기술 사항은 `pyproject.toml` 과 `CHANGELOG.md` 를 참조한다.
