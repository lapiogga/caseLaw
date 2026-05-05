# CaseLaw MCP

> 법제처 국가법령정보 공동활용 OpenAPI(191종)를 **MCP(Model Context Protocol) 서버**로 표준화하여, 변호사·로펌이 Claude Desktop / Cursor / VS Code 등 자연어 환경에서 한국 판례·법령·결정례를 검색·인용·요약할 수 있게 한다.

[![Tests](https://img.shields.io/badge/tests-250%20passed-brightgreen)]() [![Tools](https://img.shields.io/badge/MCP%20tools-44-blue)]() [![Python](https://img.shields.io/badge/python-3.11%2B-blue)]() [![Languages](https://img.shields.io/badge/i18n-ko%2Fen%2Fzh%2Fvi%2Fja-orange)]() [![License](https://img.shields.io/badge/license-MIT-green)]()

**상태**: v0.8.0 — Tri-Track (변호사 + 일반인 + 외국인) 완성. 활성 MCP Tool **44종**.

---

## 한 줄 요약

> 변호사가 채팅창에 *"음주운전 양형 5건, 사건번호·법원·판시사항 표로 정리"* 라고 입력하면, Claude 가 자동으로 본 MCP 의 `search_precedent` + `get_precedent` 를 호출하여 실제 대법원 판례를 회수·정리한다. 인용 사건번호는 100% 실재.
>
> 일반인은 *"3년 전 친구한테 5천만원 빌려줬는데 안 갚아요. 어떻게 해야 하죠?"* 라고 입력하면 분쟁 분류·시효 점검·소송비용·무료자원·변호사 상담 키트까지 자동 생성된다.

---

## 빠른 시작 (다른 사람이 본 MCP 를 설치할 때)

### 사전 준비 (5분)

1. **OC 키 발급** (무료): <https://open.law.go.kr/LSO/openApi/cuAskList.do>
   - 회원가입 → 활용신청 → 마이페이지 → API인증키관리에서 ID 확인
2. **필수 도구**:
   - Python 3.11+ (<https://python.org>)
   - uv (`winget install astral-sh.uv`)
   - Claude Desktop (<https://claude.ai/download>)
   - Git (`winget install Git.Git`)

### 설치

```powershell
# 1. 저장소 clone
git clone https://github.com/lapiogga/caselaw-mcp.git
cd caselaw-mcp

# 2. 의존성 설치
uv sync --extra dev

# 3. OC 키 .env 작성 (시크릿이므로 config 가 아닌 .env 사용)
"CASELAW_OC=발급받은_ID" | Out-File -Encoding ASCII .env

# 4. Claude Desktop 자동 등록 (MSIX/일반 설치 모두 대응)
.\scripts\install-caselaw-mcp.ps1

# 5. Claude Desktop 완전 재시작 후 채팅창에:
#    "caselaw 로 ping 해줘"
#    → {"status":"ok","oc_configured":true,"phase":"11-i18n"} 반환되면 성공
```

상세: [docs/INSTALL.md](docs/INSTALL.md) (Cursor / VS Code 포함)

---

## 개발자용 (소스 수정·기여)

```powershell
# 1. uv 설치 (이미 했다면 건너뜀)
irm https://astral.sh/uv/install.ps1 | iex

# 2. 저장소 받기 + 의존성 동기화
git clone https://github.com/lapiogga/caselaw-mcp.git
cd caselaw-mcp
uv sync --extra dev

# 3. 환경변수 설정
copy .env.example .env
# .env 열어 CASELAW_OC=<본인_ID> 입력
#  - 발급: https://open.law.go.kr/LSO/openApi/cuAskList.do
#  - 마이페이지 → API인증키관리에서 확인

# 4. 테스트
uv run pytest -v       # 91 passed

# 5. MCP Inspector (디버깅 UI)
uv run mcp dev src\caselaw_mcp\server.py

# 6. Claude Desktop 등록 — docs\INSTALL.md 참고
```

---

## MCP Tools 한눈에 (20종)

| 카테고리 | Tools | 비고 |
|---|---|---|
| 헬스 | `ping` | 서버·OC 키 상태 |
| **판례** | `search_precedent` / `get_precedent` / `find_related_precedents` | 대법원·고등·지방. 참조판례 자동 추출 |
| **현행법령** | `search_statute` / `get_statute` | 시행일 기준 |
| 헌재 | `search_constitutional_decision` / `get_constitutional_decision` | |
| 법령해석례 | `search_law_interpretation` / `get_law_interpretation` | 법제처 해석 |
| 행정심판례 | `search_admin_judgment` / `get_admin_judgment` | 국민권익위·각급 행심위 |
| 위원회 결정문 | `search_committee_decision` / `get_committee_decision` | **12종 enum** (공정위·노동위·금융위 등) |
| 특별행정심판 | `search_special_admin_judgment` / `get_special_admin_judgment` | **4종 enum** (조세·해양·소청 등) |
| 중앙부처 해석 | `search_central_dept_interpretation` / `get_central_dept_interpretation` | **39개 부처 enum** |
| 법령용어 | `search_legal_term` / `get_legal_term` | 사전 |
| 정적 | `lookup_case_codes` | 코드 매핑표 |

자세한 입출력 스키마: [`docs/API_REFERENCE.md`](./docs/API_REFERENCE.md)
전체 코드·별칭 사전: [`docs/CODES.md`](./docs/CODES.md)

---

## 자연어 사용 예시 (Claude Desktop)

```
음주운전 관련 최근 대법원 판례 5개 찾아서 사건명만 정리해줘.

방금 검색한 첫 번째 판례의 판시사항·판결요지·참조조문을 표로 정리.

도로교통법 시행 중인 본문에서 음주운전 관련 조항(제44조 부근) 발췌.

공정거래위원회 담합 관련 결정문 5건.

법령용어 "공탁" 사전 검색.
```

전체 30종 시나리오: [`docs/EXAMPLES.md`](./docs/EXAMPLES.md)

---

## 디렉토리 구조

```
CaseLaw/
├── PLAN.md                     # 종합 계획서
├── README.md
├── CHANGELOG.md                # 버전 히스토리
├── pyproject.toml              # uv 프로젝트
├── .env.example                # OC 키 템플릿
├── src/caselaw_mcp/
│   ├── server.py               # FastMCP 엔트리 (20 tool 등록)
│   ├── client.py               # 비동기 HTTP + 재시도 + URL 마스킹
│   ├── parsers.py              # XML/JSON → 영문 키 정규화 (60+ 키)
│   ├── cache.py                # SQLite TTL 캐시
│   ├── codes.py                # 사건종류·법원·위원회·부처 코드 (105+ 별칭)
│   ├── config.py               # pydantic-settings 환경 로더
│   └── tools/
│       ├── precedent.py        # 판례 + find_related
│       ├── statute.py          # 현행법령
│       ├── constitution.py     # 헌재결정례
│       ├── interpretation.py   # 법령해석례
│       ├── admin_judg.py       # 행정심판례
│       ├── committee.py        # 위원회 12종 통합
│       ├── special_judg.py     # 특별행정심판 4종 통합
│       ├── dept_interpretation.py # 중앙부처 39종 통합
│       └── terminology.py      # 법령용어
├── tests/
│   ├── unit/                   # 91 단위 테스트
│   └── integration/
│       ├── smoke_live.py       # Phase 1 시나리오 4종
│       ├── smoke_phase2.py     # Phase 2 시나리오 4종
│       └── smoke_phase3.py     # Phase 3 시나리오 4종
├── docs/
│   ├── INSTALL.md              # Claude Desktop / Cursor 등록
│   ├── API_REFERENCE.md        # 20 tool 입출력 스키마
│   ├── CODES.md                # 전체 코드·별칭 사전
│   ├── EXAMPLES.md             # 변호사 자연어 30종
│   └── claude_desktop_config.example.json
├── reference/                  # 법제처 OpenAPI 가이드 원본
└── .planning/                  # GSD 플래닝 (PROJECT/ROADMAP/PROMPTS-LOG/phases/*)
```

---

## 로드맵 진행

| Phase | 내용 | 상태 |
|---|---|---|
| 0 | Bootstrap (uv, ping tool, CI) | ✅ |
| 1 | 판례 + 법령 MVP (5 tool) | ✅ |
| 2 | 헌재·해석례·심판례 + 관련판례 추천 | ✅ |
| 3 | 위원회 12 + 특별심판 4 + 중앙부처 39 + 법령용어 | ✅ |
| **4** | **품질·배포 (API_REFERENCE / CODES / CHANGELOG / Release)** | ✅ |
| 5+ | 외국 판례 연동 (CourtListener·Find Case Law) — 백로그 | ⏭ |

상세: [`PLAN.md`](./PLAN.md) · [`.planning/ROADMAP.md`](./.planning/ROADMAP.md)

---

## 보안

- `.env` (OC 키) **절대 커밋 금지** — `.gitignore` 4번 줄에 등록
- OC 키 로그·에러 메시지에 평문 노출 금지 — `client.py` 가 자동 마스킹 (`***OC***`)
- httpx 라이브러리 자체 INFO 로그도 silence (URL 평문 노출 방지)
- 모든 외부 입력(`prec_id`, `law_id`, `term_id`)은 `^[0-9]+$` 화이트리스트 검증

자세한 체크리스트: [`docs/INSTALL.md#5-보안-체크리스트`](./docs/INSTALL.md)

---

## 성능

- 캐시 적중 시 응답 **0.008초** (목표 <1초의 125배)
- 본문 영구 캐시 (판례·결정문 불변), 목록 1시간 TTL, 법령용어 24시간
- httpx 비동기 + tenacity 재시도 (5회 지수 백오프)
- Rate limit: 기본 5 req/sec (asyncio.Semaphore)

---

## 기여

이슈·PR 환영. 한국어 OK.

---

## 라이선스

MIT (예정 — 정식 release 시 LICENSE 파일 추가)

---

## 문의

박재우 · lapiogga@gmail.com
