# VERSION STAMP — v0.8.0

> **Stamped**: 2026-05-05 13:20 KST
> **Build**: 변호사 + 일반인 + 외국인 사용자 3-트랙 통합 MCP

## 마일스톤 인증

| 항목 | 값 |
|---|---|
| **Version** | v0.8.0 |
| **Codename** | Tri-Track (Lawyer + Citizen + Foreigner) |
| **MCP Tools** | 44 |
| **단위 테스트** | 250 PASS |
| **통합 smoke** | 19 시나리오 |
| **UAT (Claude Desktop)** | ✅ v0.3.0 시점 통과 (2026-05-05 00:08 KST) |
| **지원 언어** | 5 (ko/en/zh/vi/ja) |

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

## 다음 마일스톤 (v0.9.0+ 예고)

- 카테고리 50 → 100종 (변협 협업)
- 외국 판례 통합 (CourtListener)
- Vector DB 의미 검색
- Web UI 대시보드
- 변호사 검토 인증 (`confirmed=true` 시드)
- 카테고리·시효·비용 시드 자체 다국어화

## 동결 코드 영역 (v0.8.0)

이후 변경 시 후방호환 책임:
- `src/caselaw_mcp/server.py` 의 44 tool signature
- `src/caselaw_mcp/parsers.py` 의 응답 키 매핑 (영문 snake_case)
- `client.py` 의 OC 환경변수·캐시 경로
- `tools/citizen/{mode,locale}.py` 의 파일 기반 상태 (~/.caselaw_mcp/{mode,locale}.json)
- `citizen_data/*.json` 시드 (추가만, 기존 ID 변경·제거 금지)
- `docs/API_REFERENCE.md` 에 명시된 입출력 스키마

신규 기능은 **추가만** (기존 tool 제거·rename 금지).
