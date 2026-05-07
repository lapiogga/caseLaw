# VERSION STAMP — v0.11.0 (Outcome Prediction)

> **Initial Stamp**: 2026-05-05 13:20 KST (v0.8.0 Tri-Track)
> **Distribution Stamp**: 2026-05-06 KST (배포·문서·자동화 트랙 완료)
> **Multi-Client Stamp**: 2026-05-07 KST (Claude · Gemini · ChatGPT 3-클라이언트 동시 지원)
> **Doc Drafting Stamp**: 2026-05-08 KST (변호사 문서 초안 자동화 4종)
> **Outcome Prediction Stamp**: 2026-05-08 KST (변호사 결과 예측 4종)
> **Build**: 3-사용자 트랙 × 3-클라이언트 × 4-문서 초안 × 4-결과 예측 (양형·민사결과·소요기간·해결옵션)

## 마일스톤 인증

| 항목 | 값 |
|---|---|
| **Version** | v0.11.0 |
| **Codename** | Outcome Prediction |
| **MCP Tools** | **52** (이전 48 → +4 prediction) |
| **단위 테스트** | **352** PASS (이전 314 → +38 prediction) |
| **통합 smoke** | 19 시나리오 + HTTP Bearer 라이브 + drafting 4 doc + prediction 4 회귀 가드 |
| **UAT (Claude Desktop)** | ✅ v0.3.0 시점 통과 (2026-05-05 00:08 KST) |
| **지원 클라이언트** | 5 (Claude Desktop · Gemini CLI · Cursor · VS Code · ChatGPT) |
| **지원 transport** | 2 (stdio · streamable-http) |
| **지원 언어** | 5 (ko/en/zh/vi/ja) |
| **자동 생성 문서** | 4 (민사 소장 / 법률의견서 / 준비서면 / 형사 변호인 의견서) |
| **결과 예측 도구** | 4 (양형 분포 / 민사 결과 분포 / 소요 기간 / 해결옵션 비교) |

## 트랙별 도달 상태

### 트랙 1 — 변호사·로펌 (v0.3.0 ~ ✅)
- 27 tool: 판례·법령·헌재·해석례·심판례·위원회 12·특별심판 4·중앙부처 39·법령용어
- helper: analyze_trend, format_citation, compare_precedents
- citation: find_precedent_by_citation
- attachments: download_attachment, extract_attachment_links

### 트랙 2 — 일반인 사전진단 (v0.4.0 ~ ✅)
- 12 tool: set_user_mode, get_disclaimer, **triage_dispute** (50종 카테고리),
  **check_statute_of_limitations** (30종 시효), **estimate_litigation_cost** (인지법),
  **interview_facts** (6턴), **evaluate_case_strength**,
  **recommend_pro_bono** (전국+지역+도메인특화),
  **prepare_consultation_kit** (13섹션 마크다운)
- 일반인 7단계 워크플로 완성

### 트랙 3 — 외국인 사용자 (v0.8.0 신규 ✅)
- 5 tool: set/get_user_locale, get_disclaimer_localized,
  list_disclaimers_localized, get_foreigner_resources
- 5언어 면책 + 외국인 무료자원 4곳 (1345·1577-1366·1577-5432·이주민건강협회)

## Phase 0~11 누적 통계

| 항목 | 수 |
|---|---|
| MCP Tools | **44** |
| Python 모듈 | 20 |
| 단위 테스트 | 250 PASS |
| 통합 smoke | 19 시나리오 |
| 시드 데이터 JSON | 6 (categories 50 + limitations 30 + court_fees 4구간 + pro_bono 30+ + interview 6턴 + i18n 5언어) |
| 면책 문구 | 6종 × 5언어 = 30개 |
| 한국어 별칭 | 200+ |
| 법제처 OpenAPI target | 60+ |
| 문서 | 13개 (PLAN/README/CHANGELOG/LICENSE/VERSION-STAMP + docs/* 7개 + .planning/*) |
| 총 작업 시간 | 약 130분 (2026-05-04 16:00 ~ 2026-05-05 13:20) |

## 배포·문서 트랙 (2026-05-05 ~ 2026-05-06 추가) ✅

### 공개 배포
- GitHub Public Repo: <https://github.com/lapiogga/caseLaw>
- GitHub Release v0.8.0: wheel + sdist + installer ZIP (rev 3)
- PyPI: <https://pypi.org/project/caselaw-mcp/> (`uvx caselaw-mcp` 1줄 설치)
- CI: Python 3.11/3.12/3.13 PASS

### 비기술자 진입 장벽 제거
- 원클릭 .bat 설치기 (rev 3, 4단계 검증 + native stderr 처리 안정화)
- 7KB 사전 패키징 ZIP (Release 첨부, 더블클릭 설치)

### 사용자 유형별 문서 (8종)
- 일반인 1장 소개자료 + 개발자 14섹션 기술노트
- 시각 설치 가이드 (스크린샷 11장)
- OC 발급 9단계 가이드
- Vrew 영상 제작 완전 가이드 + 5분 대본 + GIF 골격
- Playwright 자동 캡처 스크립트 + 시연 시뮬레이터

### 시각 자료
- 자동 캡처 6장 (Playwright) + 사용자 캡처 5장 = 총 11장 (5MB)
- Vrew 슬라이드쇼 영상 1편 (사용자 본인 PC, 약 2-3분 1080p)

### 누적 commit (본 트랙)
- 14 commits (init → 배포 → 문서 → 영상 → 정리)

---

## 다음 마일스톤 (v0.9.0+ 예고)

### 콘텐츠
- 카테고리 50 → 100종 (변협 협업)
- 외국 판례 통합 (CourtListener)
- Vector DB 의미 검색
- 변호사 검토 인증 (`confirmed=true` 시드)
- 카테고리·시효·비용 시드 자체 다국어화

### 인프라·홍보
- YouTube 영상 업로드 + README 임베드
- 영어·중국어 다국어 영상 제작 (Vrew 다국어 워크플로)
- Anthropic Connector Directory 등록 신청
- Web UI 대시보드 (MCP 외 일반 변호사용)

## 동결 코드 영역 (v0.9.0)

이후 변경 시 후방호환 책임:
- `src/caselaw_mcp/server.py` 의 44 tool signature
- `src/caselaw_mcp/server.py` 의 CLI flag 4 (`--transport`, `--host`, `--port`, `--path`) — 인자 이름·기본값
- `src/caselaw_mcp/auth.py` 의 `CASELAW_AUTH_TOKEN` 환경변수 + `Authorization: Bearer` 검증 동작
- `src/caselaw_mcp/parsers.py` 의 응답 키 매핑 (영문 snake_case)
- `client.py` 의 OC 환경변수·캐시 경로
- `tools/citizen/{mode,locale}.py` 의 파일 기반 상태 (~/.caselaw_mcp/{mode,locale}.json)
- `citizen_data/*.json` 시드 (추가만, 기존 ID 변경·제거 금지)
- `docs/API_REFERENCE.md` 에 명시된 입출력 스키마
- HTTP 엔드포인트 기본값 `127.0.0.1:8000/mcp` (변경 시 가이드 동시 갱신)

신규 기능은 **추가만** (기존 tool 제거·rename 금지).

## v0.9.0 Multi-Client 라이브 검증

| 시나리오 | 명령 / 입력 | 결과 |
|---|---|---|
| stdio 회귀 | `pytest tests/` | 267 PASS / ruff PASS / format PASS |
| HTTP boot | `caselaw-mcp --transport http --port 18765` | uvicorn listen 정상 |
| Bearer 누락 | `curl POST /mcp/` (Authorization 없음) | HTTP 401 |
| Bearer 오류 | `curl POST /mcp/ -H 'Authorization: Bearer wrong'` | HTTP 401 |
| Bearer 정상 | `curl POST /mcp/ -H 'Authorization: Bearer <token>'` (initialize) | 200 + serverInfo + 한국어 instructions |

---

## 세션 마감 로그 (2026-05-07 ~ 2026-05-08)

본 세션은 **v0.8.0 Tri-Track 종료 시점**에서 시작해 **v0.11.0 Outcome Prediction**
까지 도달.

### 진행 요약 (3 마일스톤)

| 단계 | Phase | 버전 | 핵심 산출 |
|---|---|---|---|
| **1** | **Phase 12 — Multi-Client Edition** | v0.9.0 | HTTP transport + Bearer 인증 (auth.py) + Gemini CLI 가이드 + ChatGPT 우회 검토 + 5-클라이언트 매트릭스 |
| **2** | **Phase 13 — Practitioner Doc Drafting** | v0.10.0 | 변호사 문서 4종 자동 생성 (소장·의견서·준비서면·변호인 의견서) + 자동 면책 회귀 가드 |
| **3** | **Phase 14 — Outcome Prediction** | v0.11.0 | 결과 예측 4종 (양형·민사결과·기간·해결옵션) + 표본 가드 + 사법연감 시드 |

### 인프라 자동화 (본 세션 신규)

- **PyPI Trusted Publishing 워크플로우** (`.github/workflows/publish.yml`) 추가 →
  v0.10.0 부터 GitHub Release published 시 OIDC 자동 publish (토큰 노출 0)
- **CI 빨강 해소**: `docs/promo/automation/capture_pages.py` ruff format
- **sdist 슬림화**: 62MB → 157KB (promo 영상·캡처 exclude 패턴 추가)
- **Bearer 인증 결함 fix**: pydantic-settings `.env` 가 `os.environ` 미주입 →
  Settings 기반 일관 경로로 변경 (silent bypass 차단)
- **영상 정리**: mp4 git ignore 패턴 + 새 캡처 PNG 2장 add
- **README v0.11.0 전면 정합화**: 옛날 정보 (20 tool / 91 PASS / Phase 5 백로그)
  → 현재 (52 tool / 352 PASS / Phase 14 완료)

### 외부 배포 결과

- **GitHub main**: 16 commits push, CI 녹색 유지
- **GitHub Release v0.9.0 / v0.10.0 / v0.11.0** 정식 (각 wheel + sdist + ZIP installer 첨부)
- **PyPI v0.9.0 / v0.10.0 / v0.11.0** LIVE (Trusted Publishing 자동 — `uvx caselaw-mcp` 사용자 즉시 v0.11.0)
- **비기술자 ZIP** v0.11.0 (사용자 무액션 자동 업그레이드)
- **워킹트리·외부 노출**: 모두 클린 / 종료

### 라이브 UAT (사용자 검증 완료)

| 클라이언트 | 검증 시점 |
|---|---|
| Claude Desktop | v0.3.0 (2026-05-05) |
| Gemini CLI (OAuth) | v0.9.0 (2026-05-07, 헤드리스 모드 ping + 음주운전 5건 검색 회수) |
| ChatGPT Custom MCP | OAuth 2.1 미지원 정책으로 직결 보류 (Phase 15+ 후보) |

### 다음 세션 진입점 (백로그 우선순위)

1. **ChatGPT OAuth 2.1 Resource Server** — Auth0/Stytch IdP 통합으로 직결 완성
2. **Pack 2 Quality Guards** — citation_validator / precedent_consistency_check / brief_review_checklist (할루시네이션 방지)
3. **Pack 3 Pre-Drafting Workflow** — fact_pattern_extractor / timeline_builder / evidence_organizer (draft_* 입력 품질 ↑)
4. **ML 라벨링 정확도 향상** (Phase 14 휴리스틱 → 변호사 검수 데이터 기반 학습)
5. **외국 판례 통합** (CourtListener / Find Case Law UK)
6. **open-webui 자체 호스팅 가이드** (gemini.google.com 대체)
7. **변호사 베타 UAT 모집**

### 동결 코드 영역 갱신 (v0.11.0)

- `src/caselaw_mcp/server.py` 의 **52 tool signature**
- `src/caselaw_mcp/tools/drafting/templates.py` 의 `DISCLAIMER_MARKER` (회귀 가드 grep 대상)
- `src/caselaw_mcp/tools/prediction/labels.py` 의 5×5 라벨 universe (CIVIL_LABELS · SENTENCING_LABELS) — 추가만 가능
- `src/caselaw_mcp/prediction_data/duration_baselines.json` 의 18 baseline (추가만)
- 모든 `draft_*` / `predict_*` 출력 dict 의 키 (`doc_type`·`markdown` 필수)
- 표본 크기 가드 임계값 (5/10/30) — 변경 시 변호사 가이드 동시 갱신
- 그 외 v0.9.0 동결 영역 모두 유지
