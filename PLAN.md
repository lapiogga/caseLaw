# CaseLaw MCP — 종합 PLAN

> **작성일**: 2026-05-04 (월)
> **작성자**: Claude (Orchestrator) + 사용자 박재우
> **버전**: v1.0 (초안)
> **상위 문서**: `.planning/PROJECT.md`, `.planning/ROADMAP.md`

---

## 0. 한 줄 요약

법제처 국가법령정보 공동활용 OpenAPI(191종)를 **MCP(Model Context Protocol) 서버**로 래핑하여, Claude Desktop / Cursor / VS Code 같은 AI 코딩·대화 환경에서 변호사·로펌이 자연어로 판례를 검색·요약·인용할 수 있도록 한다.

---

## 1. 프로젝트 비전 (Why)

### 1.1 타겟 사용자
- **1차**: 소규모 로펌 / 개인 변호사 / 법무법인 송무팀
- **2차**: 법무사·노무사·변리사·사내법무팀
- **3차**: 로스쿨 학생, 법학 연구자

### 1.2 해결하는 문제
| 현재 (Pain Point) | 도입 후 (Value) |
|---|---|
| 판례 검색에 케이스넷·국가법령정보센터를 수동으로 열어 키워드 조합 시도 | "음주운전 인사사고 양형 5년치 추세 정리해줘" 한 줄로 끝 |
| 판례 본문 복사·정리 시간 과다 | AI가 사실관계·쟁점·판단을 구조화된 표로 추출 |
| 인용 근거 누락·할루시네이션 위험 | 실제 사건번호·선고일자·전문 URL을 AI가 직접 회신 |
| 관련 법령·조문 별도 조회 필요 | 같은 MCP에서 법령 본문도 동시 검색 |

### 1.3 측정 가능한 성공 기준 (UAT)
- [ ] 자연어 명령 1회로 판례 5건 이상 정확 검색 (사건번호 100% 실재)
- [ ] 본문 전문 추출 + 핵심 4요소(사실·쟁점·판단·결론) 자동 분리
- [ ] 응답시간: 캐시 미적중 5초, 캐시 적중 1초 이내
- [ ] 변호사가 30분 튜토리얼 후 자기 사건에 적용 가능

---

## 2. 시스템 아키텍처 (How)

### 2.1 전체 구성도

```
┌─────────────────────────────────────────────────────────────┐
│  [User] 변호사 자연어 명령                                    │
│   "최근 3년 음주운전 양형 판례 5개 요약, 표로 정리"            │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│  [Host] Claude Desktop / Cursor / VS Code                    │
│   - LLM이 어떤 MCP tool을 호출할지 판단                       │
└────────────────────────┬────────────────────────────────────┘
                         ↓ stdio (JSON-RPC over MCP)
┌─────────────────────────────────────────────────────────────┐
│  [CaseLaw MCP Server]  (Python, 본 프로젝트)                  │
│  ├─ tools/precedent.py   판례 검색·본문                       │
│  ├─ tools/constitution.py 헌재결정례                          │
│  ├─ tools/interpretation.py 법령해석례                        │
│  ├─ tools/admin_judg.py    행정심판례                         │
│  ├─ tools/committee.py     위원회 결정문 (12종)               │
│  ├─ tools/statute.py       현행법령 본문                      │
│  ├─ client.py              법제처 API HTTP 클라이언트         │
│  ├─ parsers.py             XML/JSON → dict 정규화             │
│  ├─ cache.py               SQLite 로컬 캐시                   │
│  └─ codes.py               사건종류·법원·부처 코드 매핑       │
└────────────────────────┬────────────────────────────────────┘
                         ↓ HTTPS GET
┌─────────────────────────────────────────────────────────────┐
│  [법제처 OpenAPI]                                             │
│   https://www.law.go.kr/DRF/lawSearch.do  (목록)             │
│   https://www.law.go.kr/DRF/lawService.do (본문)             │
│   인증: OC=<사용자ID>  (lapiogga 등)                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 기술 스택 (자체 결정)

| 영역 | 선택 | 근거 |
|---|---|---|
| **언어** | Python 3.11+ | MCP SDK(공식) 가장 성숙, 데이터 가공 라이브러리 풍부, 사용자가 Windows 환경 |
| **MCP SDK** | `mcp` (Anthropic 공식) | 공식 표준, FastMCP 패턴 지원, stdio/SSE 양쪽 |
| **HTTP 클라이언트** | `httpx` (async) | 비동기 병렬 호출(다건 검색 시 속도 ↑), 재시도 미들웨어 |
| **XML 파싱** | `xmltodict` + `lxml` | 법제처 XML이 비교적 단순, dict 변환이 직관적 |
| **데이터 검증** | `pydantic` v2 | MCP tool 입출력 스키마 자동 생성 |
| **캐시** | SQLite (`aiosqlite`) | 판례 본문은 한번 받으면 불변 → 캐시 가치 큼. 외부 의존성 0 |
| **설정 관리** | `pydantic-settings` + `.env` | OC 키 등 시크릿 보호 |
| **로깅** | `structlog` | JSON 구조화 로그, 호출 추적 |
| **테스트** | `pytest` + `pytest-asyncio` + `respx` | HTTP 모킹으로 외부 API 의존 없이 테스트 |
| **패키지 관리** | `uv` | pip보다 10x 빠름, lock 파일 안정적 |
| **포맷터/린터** | `ruff` (단일 도구) | black + isort + flake8 통합 |

### 2.3 디렉토리 구조

```
CaseLaw/
├── PLAN.md                       ← 본 문서 (사용자 1차 검토용)
├── README.md                     ← 설치·사용법
├── CLAUDE.md                     ← Claude Code 지침 (이미 존재)
├── pyproject.toml                ← uv 프로젝트 정의
├── uv.lock
├── .env.example                  ← OC 키 템플릿
├── .gitignore
├── src/
│   └── caselaw_mcp/
│       ├── __init__.py
│       ├── server.py             ← MCP 엔트리포인트
│       ├── client.py             ← 법제처 HTTP 클라이언트
│       ├── config.py             ← 환경변수 로딩
│       ├── cache.py              ← SQLite 캐시 레이어
│       ├── codes.py              ← 사건종류/법원/부처 코드표
│       ├── parsers.py            ← XML/JSON 응답 정규화
│       ├── models.py             ← pydantic 응답 모델
│       └── tools/
│           ├── __init__.py
│           ├── precedent.py      ← 판례 (Phase 1)
│           ├── constitution.py   ← 헌재결정례 (Phase 2)
│           ├── interpretation.py ← 법령해석례 (Phase 2)
│           ├── admin_judg.py     ← 행정심판례 (Phase 2)
│           ├── statute.py        ← 현행법령 (Phase 2)
│           ├── committee.py      ← 위원회 결정문 (Phase 3)
│           └── terminology.py    ← 법령용어 (Phase 3)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/                 ← 실제 API 응답 샘플 (캡처)
├── docs/
│   ├── API_REFERENCE.md          ← 각 tool 입출력 스키마
│   ├── INSTALL.md                ← Claude Desktop 등록 방법
│   ├── EXAMPLES.md               ← 변호사용 자연어 예시 30개
│   └── CODES.md                  ← 사건종류/법원 코드 풀 리스트
├── .planning/                    ← GSD 플래닝 (워크 추적)
│   ├── PROJECT.md
│   ├── ROADMAP.md
│   ├── PROMPTS-LOG.md            ← 글로벌 규칙 (rules/prompts-log.md)
│   ├── research/
│   └── phases/
│       └── phase-0-bootstrap/
└── reference/                    ← 기존 가이드 HTML/MD (이동 권장)
    ├── caselaw_api_guide_1.html
    ├── caselaw_api_howto_1.html
    ├── caselaw_api_get.html
    ├── caselaw_vibecoding_guide.md
    └── foreign_caselaw_api_case.md
```

---

## 3. MCP Tool 설계 (What)

### 3.1 Phase 1 — MVP (판례 + 법령) ★ 최우선

| Tool | 입력 (주요) | 출력 | 매핑 API |
|---|---|---|---|
| `search_precedent` | `query`, `court_name?`, `case_type?`, `date_from?`, `date_to?`, `display=20`, `page=1` | 판례 메타 리스트 (사건번호·선고일자·법원·요지) + 본문 fetch ID | precListGuide |
| `get_precedent` | `prec_id` (판례일련번호) | 판시사항·판결요지·참조조문·참조판례·전문 | precInfoGuide |
| `search_statute` | `query`, `effective_date?`, `display`, `page` | 법령 메타 리스트 | lsEfYdListGuide |
| `get_statute` | `law_id` or `law_name` | 본문·조문·부칙·별표 | lsEfYdInfoGuide |
| `lookup_case_codes` | (없음) | 사건종류 코드 매핑표 | 내장 데이터 |

**왜 법령도 Phase 1?** 변호사가 판례를 보는 순간 거의 반드시 근거 법조문을 같이 본다. 한 MCP 호출 안에서 "참조조문 2조→그 조문 본문 조회"가 자연스럽게 이어져야 한다.

### 3.2 Phase 2 — 결정례·해석례·심판례 확장

| Tool | 매핑 API |
|---|---|
| `search_constitutional_decision` / `get_constitutional_decision` | detcListGuide / detcInfoGuide |
| `search_law_interpretation` / `get_law_interpretation` | expcListGuide / expcInfoGuide |
| `search_admin_judgment` / `get_admin_judgment` | deccListGuide / deccInfoGuide |
| `find_related_precedents(prec_id)` | precInfoGuide의 참조판례 + 추가 검색 |

### 3.3 Phase 3 — 위원회 결정문 + 부가 (선택)

12개 위원회(개인정보보호·고용보험심사·공정거래·국민권익·금융·노동·방송미디어통신·산재보상·중앙토지수용·중앙환경분쟁·증선·국가인권) 결정문은 단일 `search_committee_decision(committee, query)` + `get_committee_decision(committee, doc_id)` 형태로 통합. 기관별 separate tool은 LLM이 라우팅 어렵게 만든다.

추가:
- `search_terminology` (법령용어 사전)
- `search_special_admin_judgment` (조세심판원 등 특별 행정심판)
- `search_central_dept_interpretation` (중앙부처 1차 해석 — 39종, 동일 패턴 통합)

### 3.4 도구 명명 규칙
- 모두 영문 snake_case (LLM 함수 호출 안정성)
- `search_*` = 목록 조회 (페이지네이션)
- `get_*` = 본문 조회 (단건)
- `lookup_*` = 코드 매핑 등 정적 데이터
- `find_*` = 파생 검색 (관계·추천)

---

## 4. 핵심 구현 결정 (Decisions)

### 4.1 응답 포맷
**`type=JSON` 우선 호출, 실패 시 XML fallback.** 가이드(vibecoding) 권장사항. JSON 미지원 엔드포인트 (일부 법령 본문)는 XML로 받아 `xmltodict`로 dict 변환 후 동일 스키마로 정규화.

### 4.2 캐싱 전략
- **본문 (get_*)**: 영구 캐시 (판례·법령은 사실상 불변). 캐시 키 = `(api_target, doc_id)`. TTL 30일 → 자동 갱신.
- **목록 (search_*)**: 1시간 TTL (신규 등록 판례 반영을 위함).
- **코드 매핑 (lookup_*)**: 빌드 타임 정적 → 캐시 불필요.
- 저장소: `~/.caselaw_mcp/cache.db` (사용자 홈)

### 4.3 인증 키 (OC)
- 환경변수 `CASELAW_OC` 로 받음. 미설정 시 명확한 에러 메시지.
- 사용자 박재우의 승인 ID 확인 필요 → **다음 단계에서 확인 받기** (별도 질문).
- `.env` 절대 커밋 금지 (글로벌 규칙).

### 4.4 Rate Limit & 재시도
- 법제처 명시 정책 부재 → **보수적 적용**: 초당 5건, burst 10.
- httpx + tenacity 지수 백오프 (1·2·4·8초, 최대 5회).
- 429/5xx 응답 시 자동 재시도, 4xx (400/401/404) 즉시 반환.

### 4.5 페이지네이션
- 법제처 API 1회 최대 100건. 사용자 요청 `display>100`일 때 자동 다중 호출 + concat.
- LLM 컨텍스트 보호를 위해 기본 `display=20`, 최대 `display=100` 강제.

### 4.6 에러 메시지 정책
- MCP tool 에러는 **LLM이 다음 시도를 결정할 수 있도록** 구조화:
  ```json
  {"error": "no_results", "hint": "쿼리를 더 짧게 줄이거나 court_name 제거를 시도하세요"}
  ```
- 사용자 노출 메시지는 한국어, 로그는 영어 (디버깅 용이).

### 4.7 보안
- OC 키는 절대 응답·로그에 노출 금지 (URL 마스킹).
- 외부 사용자가 만든 docID 파라미터는 `^[0-9]+$` 화이트리스트.
- HWP/PDF 다운로드 URL은 도메인 화이트리스트 (`law.go.kr`만 허용).

---

## 5. Phase별 로드맵

| Phase | 범위 | 산출물 | 예상 | 검증 |
|---|---|---|---|---|
| **Phase 0** | 부트스트랩 | uv 프로젝트, MCP 서버 hello-world, .env 템플릿, CI(ruff+pytest) | 0.5일 | `mcp dev` 로 도구 1개(`ping`) 호출 성공 |
| **Phase 1** | 판례 + 법령 MVP | 5 tool (search/get_precedent, search/get_statute, lookup_case_codes), SQLite 캐시, 코드 매핑 | 2일 | Claude Desktop에서 "음주운전 판례 5개" 자연어 명령 성공, 사건번호 실재 검증 |
| **Phase 2** | 결정례·해석례·심판례 | 6 tool 추가, 관련판례 추천 | 1.5일 | 헌재결정례·법령해석례 자연어 질의 성공 |
| **Phase 3** | 위원회·부가 (선택) | 통합 위원회 tool, 법령용어, 특별 심판 | 1일 | 공정위·노동위 결정문 검색 성공 |
| **Phase 4** | 품질·배포 | 통합 테스트, 변호사 시나리오 30종 검증, INSTALL/EXAMPLES 문서, 패키징 (PyPI 또는 GitHub Release) | 1일 | 외부 변호사 1명 30분 내 설치+사용 성공 |

**총 예상**: 6일 (Phase 0~4 전부)
**최소 가용**: Phase 0+1 = 2.5일 → 변호사 1명에게 데모 가능 수준

---

## 6. Agent 팀 분담 (오케스트레이션)

CLAUDE.md 지침에 따라 본 작업은 단일 메인이 아닌 **Agent Teams** 방식으로 진행한다.

| 팀 Agent | 담당 | 사용 모델 |
|---|---|---|
| **planner** (Lead) | 본 문서 유지·갱신, Phase 분기, 의사결정 기록 | opus |
| **architect** | 모듈 구조·Pydantic 모델·MCP tool 인터페이스 설계 | opus |
| **api-explorer** (sub) | 법제처 각 API 실제 호출 → 응답 샘플 캡처 → fixtures 저장 | sonnet |
| **tdd-guide** | RED → GREEN → REFACTOR 사이클로 각 tool 구현 | opus |
| **code-reviewer** | 매 PR 단위 보안·스타일·중복 검토 | opus |
| **security-reviewer** | OC 키 누출, 인젝션, URL 화이트리스트 검증 | opus |
| **doc-updater** | API_REFERENCE / EXAMPLES / INSTALL 문서 동기화 | sonnet |

병렬 처리 원칙: 의존성 없는 tool 구현(예: precedent vs statute)은 동시 spawn.

---

## 7. 위험 & 미해결 항목

| 위험 | 영향 | 완화 |
|---|---|---|
| 사용자 OC 키 (박재우 ID) 미확인 | Phase 1 실호출 불가 | **다음 단계 즉시 확인** |
| 법제처 API rate limit 정책 불명확 | 운영 중 차단 가능 | 초당 5건 보수 운용 + 모니터링 |
| 일부 API XML만 지원 | 파서 분기 복잡 | xmltodict로 통일 변환 |
| 법령·판례 본문 길이 (수만 토큰) | LLM 컨텍스트 초과 | 본문 chunking + 요약 옵션 (`detail_level=summary|full`) |
| HWP 별표 다운로드 (변호사 수요) | 별도 처리 필요 | Phase 3에서 옵션으로 추가 |
| MCP host 다양성 (Claude Desktop / Cursor 차이) | 등록 방법 다름 | INSTALL.md에 호스트별 분기 |

---

## 8. 즉시 실행 항목 (PLAN 승인 후)

CLAUDE.md "사용자 의사결정 대기 말고 recommended로 즉시 수행" 원칙에 따라, 사용자가 본 PLAN에 큰 이의가 없으면 다음을 자동 진행한다:

1. ✅ `.planning/` 디렉토리 + PROJECT.md + ROADMAP.md 작성 (본 응답에서 동시 진행)
2. ✅ PROMPTS-LOG.md 초기화 (글로벌 규칙)
3. ⏭ Phase 0 부트스트랩 시작 (다음 응답에서 사용자 확인 후)
4. ⏭ 사용자에게 OC 키 1회 확인 요청 (Phase 1 시작 직전)

---

## 9. 사용자 확인 필요 항목 (1회만)

> 본 PLAN을 그대로 진행할지, 아래 항목 중 변경이 필요한지만 알려주시면 됩니다.

| # | 항목 | 추천안 (변경 없으면 이대로 진행) |
|---|---|---|
| Q1 | 구현 언어 | **Python 3.11+** (Node/TS도 가능하나 MCP SDK 성숙도·데이터 가공·Windows 호환성에서 Python 우위) |
| Q2 | Phase 1 범위에 "법령" 포함 여부 | **포함** (판례만 있으면 변호사 워크플로우 미완성) |
| Q3 | 캐시 위치 | `~/.caselaw_mcp/cache.db` (Windows: `C:\Users\User\.caselaw_mcp\cache.db`) |
| Q4 | OC 키 (법제처 API 인증 ID) | **다음 응답에서 직접 입력 요청** — `.env` 비공개 |
| Q5 | 배포 방식 | 1차: GitHub Release + uv 설치 스크립트 / 2차: PyPI |
| Q6 | 영문 판례 (영문법령 lsEng*) | **MVP 제외** — 한국 변호사 수요 적음 |

---

## 10. 다음 행동

본 응답으로 다음 4개 파일이 동시 생성됩니다:
- `PLAN.md` (본 문서)
- `.planning/PROJECT.md` (프로젝트 정의)
- `.planning/ROADMAP.md` (Phase 분해)
- `.planning/PROMPTS-LOG.md` (사용자 프롬프트 시계열, 글로벌 규칙)

사용자께서 본 PLAN을 한 번 훑어보시고 "진행" 또는 "수정 사항"만 알려주시면, 다음 응답부터 Phase 0 부트스트랩을 즉시 착수합니다.
