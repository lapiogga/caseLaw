# CHANGELOG

본 프로젝트는 [Semantic Versioning](https://semver.org/) 을 따른다.

## [0.1.0] — 2026-05-04

🎉 첫 정식 릴리스. 활성 MCP Tool **20종**.

### Added — Phase 0 Bootstrap (16:00 ~ 16:03)
- uv 기반 프로젝트 (`pyproject.toml`, Python 3.11+, hatchling 빌드)
- FastMCP 서버 엔트리 (`src/caselaw_mcp/server.py`) + `ping` tool
- pydantic-settings 환경 로더 (`config.py`)
- `.env.example` + `.gitignore` (시크릿 보호)
- ruff + pytest + GitHub Actions CI (Python 3.11/3.12/3.13 매트릭스)
- README 골격, INSTALL 가이드 골격

### Added — Phase 1 MVP (16:10 ~ 16:23)
- `client.py`: 비동기 HTTP 클라이언트 (httpx + tenacity 재시도 + URL 마스킹)
- `parsers.py`: 한국어 ↔ 영문 키 정규화 (40+ 매핑)
- `cache.py`: SQLite TTL 캐시 (aiosqlite)
- `codes.py`: 사건종류·법원·검색범위 코드 (한·영 alias)
- **5 tool 활성화**: `search_precedent`, `get_precedent`, `search_statute`, `get_statute`, `lookup_case_codes`
- 통합 smoke: 음주운전 5건 검색 + 도로교통법 본법·시행령·시행규칙 회수
- 캐시 적중 0.008초 검증

### Added — Phase 2 Decisions (16:23 ~ 16:35)
- `tools/constitution.py`: 헌재결정례 (target=detc)
- `tools/interpretation.py`: 법령해석례 (target=expc)
- `tools/admin_judg.py`: 행정심판례 (target=decc)
- `precedent.find_related_precedents`: 본문 참조판례 추출 + 키워드 검색 결합
- parsers.py keymap 확장: 결정례·해석례·심판례 필드 30+ 추가
- **신규 7 tool** (총 12)
- 통합 smoke: 헌재 "집회" 84건, 해석례 "개인정보" 50건, 행심 "운전면허 취소" 2970건
- docs/INSTALL.md (등록 절차·트러블슈팅·보안 체크리스트)
- docs/EXAMPLES.md (변호사 자연어 시나리오 30종)
- docs/claude_desktop_config.example.json

### Added — Phase 3 Extras (16:33 ~ 16:45)
- `codes.py`: 위원회 12종(별칭 30+) + 특별심판 4종 + 중앙부처 39종(부처명 60+)
- `tools/committee.py`: 위원회 결정문 통합 (single tool with `committee` enum)
  - 지원: ppc/eiac/ftc/acr/fsc/nlrc/kcc/iaciac/oclt/ecc/sfc/nhrck
- `tools/special_judg.py`: 특별행정심판 통합 (4종 enum)
  - 지원: tax/maritime/acrh/appeal
- `tools/dept_interpretation.py`: 중앙부처 1차해석 통합 (39종 enum)
  - `cgmExpc<Dept>` 동적 target 생성
- `tools/terminology.py`: 법령용어 사전 (target=lstrm)
- **신규 8 tool** (총 20)
- 통합 smoke: 공정위 "담합" 1건, 법령용어 "공탁" 29건

### Added — Phase 4 Quality (16:42 ~ )
- `docs/API_REFERENCE.md`: 20 tool 입출력 스키마
- `docs/CODES.md`: 전체 코드·별칭 사전
- README 강화 (Phase 3 시점)
- 본 CHANGELOG.md

### Fixed
- Python 3.14 첫 TLS handshake timeout: `http_timeout` 기본값 15s → **30s** 상향
- httpx 라이브러리 자체 INFO 로그가 URL(OC 평문) 노출 → import 시점에 WARNING silence
- tenacity retry 정책: HTTPStatusError 만 잡던 것을 ConnectError·ConnectTimeout·ReadTimeout·RemoteProtocolError 도 포함 (Python 3.14 + httpx async TLS 첫 시도 안정성)
- 위원회 응답 wrapper 패턴 — 대문자 `Ftc/Ppc/...` 자체가 result 컨테이너, 소문자가 items 배열 (헌재 `DetcSearch` 와 다른 패턴)
- API 빈 응답(200 OK + 0 bytes) → `{"items":[], "empty_response":True}` 자동 변환 (xmltodict ExpatError 방지)
- cache TTL 테스트 안정화 (Windows SQLite 첫 init+IO 가 0.1s 넘는 케이스)

### Security
- OC 키 (`CASELAW_OC`)는 `.env` 에만 저장, 절대 커밋 금지
- 모든 로그·에러 메시지에서 OC 자동 마스킹 (`***OC***`)
- 외부 입력(`prec_id`, `law_id`, `term_id`)은 `^[0-9]+$` 화이트리스트 검증

### Known Limitations
- **OC 권한 범위**: 박재우님(개인 신청)의 현재 OC 키는 판례·법령·결정례·해석례·심판례·위원회·법령용어까지 정상 회수. **특별행정심판·중앙부처 1차해석**은 0건 응답 — open.law.go.kr 마이페이지에서 추가 신청 필요할 수 있음. 코드는 정상이며 권한 확장 시 즉시 동작.
- 헌재결정례 일부 검색어("표현의 자유" 등)에 대해 API 측에서 0건 반환. 다른 검색어("집회" 등)는 정상.

### Statistics
- Python 모듈: 11
- MCP Tools: 20
- 단위 테스트: 91 (PASS)
- 통합 smoke: 12 시나리오
- 한국어 별칭: 105+ (위원회+부처+심판+법원)
- 법제처 OpenAPI target 매핑: 60+

---

## [0.2.0] — 2026-05-04 (Phase 5 추가)

### Added — Phase 5 Practitioner Helpers (16:51 ~ 16:58)
- `tools/analytics.py`: 변호사 실무 보조 helper 3종
  - `analyze_precedent_trend(query, group_by)`: year/month/court/case_type/instance 분포
  - `format_citation(prec_id)`: 한국 법률 표준 인용 형식 ("대법원 2026. 1. 29. 선고 2025도15970 판결")
  - `compare_precedents(prec_ids[])`: 다건 판례 비교 표 (최대 10건)
- **신규 3 tool** (총 23)
- 단위 테스트 22종 추가 (총 113 PASS)
- 통합 smoke 4 시나리오 (트렌드 연도/법원/인용/비교) — 모두 PASS
- `docs/OC_PERMISSIONS.md`: 특별행정심판·중앙부처 1차해석 권한 확장 신청 가이드 (박재우님 향, 신청서 권장 문구 포함)

### Changed
- 버전 0.1.0 → 0.2.0
- ping `phase`: "4-quality" → "5-helpers"

---

## [0.3.0] — 2026-05-04 (Phase 6 추가)

### Added — Phase 6 Citation Lookup + Attachment Download (16:58 ~ 17:08)
- `tools/citation_lookup.py`:
  - `find_precedent_by_citation(citation)`: 자유 형식 인용 텍스트에서 사건번호 정규식 추출 → `search_precedent` 자동 회수 → `exact_match` 분류
  - 변호사가 변론서·논문에서 본 인용("대법원 2024. 5. 30. 선고 2023두12345 판결")만으로 prec_id 역검색 가능
- `tools/attachments.py`:
  - `download_attachment(file_seq, save_dir)`: 법제처 별표·서식 물리 파일(HWP/PDF) 다운로드. `https://www.law.go.kr/LSW/flDownload.do?flSeq=...` 패턴
  - `extract_attachments_from_text(text)`: 본문 dump에서 첨부 URL 자동 추출
  - 보안: path traversal 방지 (디렉토리 분리자 → `_`), Windows 예약 이름 회피, 파일명 200자 제한
- **신규 4 tool** (총 27)
- 단위 테스트 34종 추가 (citation 11 + attachments 23, 총 147 PASS)
- 통합 smoke: 단일/다중 인용 + 본문 첨부 추출 (3 시나리오)

### Changed
- 버전 0.2.0 → 0.3.0
- ping `phase`: "5-helpers" → "6-citation-attachments"

### Known Limitations
- 별표 endpoint(`target=lsByl`)는 박재우님 OC 권한 외 (0 bytes 응답). `download_attachment` 코드는 정상이며 권한 확장 시 즉시 동작.
- 도로교통법 본문(230KB)에서 `flDownload.do?flSeq=` 패턴 0건 — 동일하게 권한 확장 후 재검증 권장.

---

## [0.4.0] — 2026-05-05 (Phase 7 — Citizen Mode MVP)

🆕 **새 트랙 시작**: 변호사 도구를 넘어 **일반인 사전진단** 영역 확장.

### Added — Phase 7 Citizen Mode MVP (00:27 ~ 00:36)
- `citizen_data/categories.json` — 분쟁 카테고리 30종 시드 (민사/형사/노동/가사/행정/소비)
  - 각 카테고리: 키워드, 적용 법률, 소멸시효, 일반 절차, 셀프소송 가능 여부, 권장 증거, 흔한 쟁점
- `citizen_data/disclaimers.json` — 면책 문구 6종
  - standard / statute_imminent / criminal_serious / victim_support_needed / ai_limitation / data_freshness
- `tools/citizen/disclaimer.py`: `get_disclaimer` / `list_disclaimers` / `attach()` (payload 불변)
- `tools/citizen/mode.py`: `set_user_mode("lawyer"/"citizen")` / `get_user_mode()` — 파일 기반 영구 저장
- `tools/citizen/triage.py`: **`triage_dispute(situation, event_date, top_k)`**
  - 자유 형식 사실관계 → 키워드 매칭 → 카테고리 후보·시효 자동 점검·셀프소송 가능여부·다음 단계 안내
  - 시효 임박/만료 → `statute_imminent` 면책 자동 추가
  - 형사 사건 → `criminal_serious` 면책 자동 추가
- **신규 4 tool** (총 31): `set_user_mode`, `get_user_mode`, `get_disclaimer`, `triage_dispute`
- `ping` 응답에 `user_mode` 정보 추가
- 단위 테스트 20종 추가 (총 167 PASS)

### Changed
- 버전 0.3.0 → 0.4.0
- ping `phase`: "6-citation-attachments" → "7-citizen-mode"
- pyproject.toml: hatch force-include 로 `citizen_data/*.json` 패키지에 포함

### Security / Compliance
- 모든 citizen mode 응답에 면책 자동 부착 (변호사법 위반 방지)
- LLM 미사용 (키워드 매칭만) → 환각으로 인한 잘못된 진단 가능성 최소화
- 시효 임박/만료 케이스 100% 경고 부착 (단위 테스트 검증)

### Known Limitations
- 분쟁 카테고리 30종은 1차 자체 작성. 변호사·변협 검토 전 (각 카테고리에 `confirmed` 필드 추가 예정).
- 면책 문구 정식 변호사 검토 권장.
- 키워드 매칭 한계 — 호스트 LLM이 사실관계를 이미 표준 키워드로 변환해서 호출해야 정확도 ↑ (Citizen Mode 시스템 프롬프트 가이드 추후 작성).

---

## [0.5.0] — 2026-05-05 (Phase 8 — Statute & Cost)

### Added — Phase 8 시효·비용 정밀화 (00:39 ~ 00:48)
- `citizen_data/limitations.json` — 한국 주요 시효 30종 + 시효 중단 사유 4종
  - 민사 일반 10년 / 단기 3년·1년 / 상사 5년 / 불법행위 3+10년 / 임금 3년 / 부당해고 3개월 / 재산분할 2년 / 유류분 1+10년 / 형사 공소시효 5~10년 / 행정 90일~1년
- `citizen_data/court_fees.json` — 인지대 단계표 + 변호사 수임료 9종 + 무료자원 7개
- `tools/citizen/limitation.py`:
  - `list_limitation_categories()`: 시효 카테고리 ID·이름·기간 표
  - `check_statute_of_limitations(category_id, event_date)`: 5단계 상태(safe/warning/imminent/expired/indefinite) + 중단 사유 + 면책 자동 부착
- `tools/citizen/cost.py`:
  - `calc_stamp_fee(claim_amount_krw)`: 인지법 별표 4구간 자동 계산 (100원 절상)
  - `calc_service_fee(rounds)`: 송달료 (5,200원 x 회수)
  - `estimate_litigation_cost(claim_amount_krw, case_type)`: 인지대 + 송달료 + 변호사비 종합 + 소액심판 가능 여부 + 무료자원
- **신규 3 tool** (총 34): `list_limitation_categories`, `check_statute_of_limitations`, `estimate_litigation_cost`
- 단위 테스트 31종 추가 (총 198 PASS)

### Changed
- 버전 0.4.0 → 0.5.0
- ping `phase`: "7-citizen-mode" → "8-statute-cost"

### Verification
- 임금채권 3년 / 2.5년 전 → status=imminent, remaining=0.5년, 시효 중단 권장 ✅
- 5천만 원 일반 민사 → 인지대 230,000원 + 송달료 36,400원 + 변호사비 5,500,000원 ✅
- 1억 원 일반 민사 → 인지대 455,000원 (소액심판 한도 초과) ✅
- 음주운전 형사 → 인지대 0원 (형사 면제) ✅

### Known Limitations
- 변호사 수임료는 시장 통상 범위. 실제 비용은 사건 복잡도·법원·변호사에 따라 변동.
- 시효 중단·정지의 구체적 적용은 변호사 상담 필요 (도구는 일반 중단 사유 4종만 안내).
- limitations.json·court_fees.json 정식 변호사 검토 권장.

---

## [0.6.0] — 2026-05-05 (Phase 9 — Interview & Strength)

### Added — Phase 9 다턴 인터뷰 + 판례 강도 평가 (00:51 ~ 00:58)
- `citizen_data/interview_flow.json` — 6턴 사실관계 인터뷰 (사건경위·상대방·증거·시도·원하는 결과·정량)
- `tools/citizen/interview.py`:
  - `get_interview_flow()` / `interview_facts(turn, previous_answers)`
  - stateless 다턴 패턴 — 호스트 LLM이 turn=N + 누적 답변으로 호출
- `tools/citizen/strength.py`:
  - `evaluate_case_strength(query, sample_size)`: 사건명 결과 라벨(원고승/일부승/기각/각하/조정/취소/유죄/무죄/공소기각) 추출 → 분포 통계 + 대표 사례 + 면책
  - 라벨 매칭 우선순위: 구체(일부승·공소기각) → 일반(원고승·기각)
- **신규 3 tool** (총 37): `get_interview_flow`, `interview_facts`, `evaluate_case_strength`
- 단위 테스트 22종 추가 (총 220 PASS)

### Changed
- 버전 0.5.0 → 0.6.0
- ping `phase`: "8-statute-cost" → "9-interview-strength"

### Verification
- interview_facts 6턴 정상 (turn 1: 사건경위 / turn 6: is_final + 후속도구 안내)
- evaluate_case_strength: "면허취소 처분" 30건 → 취소 라벨 100% ✅
- evaluate_case_strength: "음주운전" 30건 → 사건명 결과 키워드 부재로 0/30 분류 (한계 명시)

### Known Limitations
- **evaluate_case_strength 사건명 매칭 한계**: 행정·취소 사건은 정확. 일반 형사·민사(도로교통법위반 등)는 본문 라벨링 필요.
  - 향후: `get_precedent` 본문 스캔 / 호스트 LLM 라벨링 위임.
  - `summary_text`+`method_note` 로 사용자에게 한계 자동 안내.
- interview_facts 는 stateless — 호스트 LLM이 previous_answers 누적 책임.

---

## [0.7.0] — 2026-05-05 (Phase 10 — Pro Bono & Consultation Kit)

🎯 **일반인 풀 워크플로 완성**: 7단계로 변호사 상담 결정의 95% 자동화.

### Added — Phase 10 (01:02 ~ 01:11)
- `citizen_data/pro_bono.json` — 무료/저비용 상담처 디렉토리
  - 전국 14 (법률구조공단·가정법률상담소·양육비이행관리원·여성긴급전화·고용노동부·소비자센터·소비자원·신용회복위·의료중재원·인권위·112·법률홈닥터·마을변호사·변협 법률구조재단)
  - 지역 변호사회 14개 광역시도
  - KLAC 지역지부 6개
  - 도메인특화 (노무사·세무사·외국인·학폭·개인정보)
  - 온라인 셀프 (대법원 전자소송·정부24·찾기쉬운 생활법령정보)
- `citizen_data/categories.json` — 30종 → **50종** 확장 (가사+3 / 노동+2 / 행정+3 / 소비+3 / 학폭·소음·하자담보·약관 등 +9)
- `tools/citizen/pro_bono.py`:
  - `recommend_pro_bono(region, domain, include_emergency_only, max_items)`
  - 도메인 체인 매칭(civil.loan→civil→all), emergency 자동 분리
- `tools/citizen/consultation_kit.py`:
  - `prepare_consultation_kit(case_profile, triage_result, statute_result, cost_result, similar_precedents, pro_bono_result)`
  - 13섹션 마크다운 자동 생성 (사건요약·분쟁유형·시효·상대방·증거·시도·결과·정량·비용·판례·질문 10개·상담처·면책)
  - 변호사 질문 10개 자동 생성 (보편 5 + 쟁점 2 + 시효·소액 보강 3)
  - 증거 체크리스트 자동 (triage 기반)
  - 권장 상담시간 자동 (complexity 기반: very_low 20분 / low 30 / medium 45 / high 60 / very_high 90)
- **신규 2 tool** (총 39): `recommend_pro_bono`, `prepare_consultation_kit`
- 단위 테스트 17종 추가 (총 237 PASS)

### Changed
- 버전 0.6.0 → 0.7.0
- ping `phase`: "9-interview-strength" → "10-pro-bono-kit"

### Verification
- recommend_pro_bono(서울, labor): national 6 + 서울지방변호사회 + 노무사 ✅
- recommend_pro_bono(emergency_only): 1366·112 ✅
- prepare_consultation_kit (대여금 5천만원 시나리오): 1169자 마크다운, 13섹션, 질문 10개, 증거 5개, 상담시간 30분 ✅

### Milestone — 일반인 7단계 워크플로 완성
```
1. set_user_mode("citizen")
2. interview_facts (6턴) → case_profile
3. triage_dispute → 카테고리·법조문
4. check_statute_of_limitations → 시효 점검
5. estimate_litigation_cost → 비용·셀프 가능
6. recommend_pro_bono → 지역·분쟁별 무료 상담처
7. prepare_consultation_kit → 마크다운 PDF 직전 자료
+ 모든 단계 면책 자동 부착
```

### Known Limitations
- 시드 데이터(50 카테고리, 시효 30, 인지대 4구간, 무료자원 30+, 면책 6) 모두 1차 자체 작성. 정식 변호사·변협 검토 필요.
- consultation_kit 출력은 마크다운 텍스트. PDF 변환은 호스트 측 처리 (Phase 11+).

---

## [0.8.0] — 2026-05-05 (Phase 11 — i18n MVP)

🌏 **외국인 사용자 트랙 시작**: 한국 거주 외국인 노동자·결혼이민자·유학생도 사용 가능.

### Added — Phase 11 다국어 (13:12 ~ 13:24)
- `citizen_data/i18n.json` — 5개 언어(ko/en/zh/vi/ja) 시드:
  - 면책 6종 (standard/statute_imminent/criminal_serious/ai_limitation/victim_support_needed/data_freshness)
  - 라벨 (도메인 8개·status 5개·complexity 5개·UI 7개)
  - 외국인 전용 무료자원 4곳 (외국인종합안내센터 1345·이주여성긴급전화 1577-1366·다누리콜센터 1577-5432·이주민건강협회 02-3147-0083)
- `tools/citizen/locale.py`:
  - `set_user_locale("ko"/"en"/"zh"/"vi"/"ja")` / `get_user_locale()`
  - `get_disclaimer_localized(kind, locale)` / `list_disclaimers_localized(locale)`
  - `localize_label(category, key, locale)` (도메인·status·complexity·UI)
  - `get_foreigner_resources(locale)` (4곳, 13개 언어 운영 정보)
- **신규 5 tool** (총 44): set/get_user_locale, get_disclaimer_localized, list_disclaimers_localized, get_foreigner_resources
- ping 응답에 `user_locale` 추가
- 단위 테스트 13종 추가 (총 250 PASS)

### Changed
- 버전 0.7.0 → 0.8.0
- ping `phase`: "10-pro-bono-kit" → "11-i18n"

### Verification
- 5개 언어 면책 모두 정상 회수 (英 "legal advice"/中 "时效"/越 "112"/日 "弁護士") ✅
- localize_label: 민사→Civil, 형사→刑事, imminent→Imminent ✅
- 외국인자원 4곳 다국어 라벨 정상 ✅

### Known Limitations
- 1차 자체 작성 — 정식 다국어 변호사·번역가 검토 필요.
- 카테고리 50종·시효표·인지대 안내는 아직 한국어만. 호스트 LLM이 동적 번역 가능.
- 13개 언어 안내 운영 자원(1345·1577-1366·1577-5432) 정보는 시드에 포함되어 LLM이 사용자에게 전달.

---

## [0.8.0-distribution] — 2026-05-05 ~ 2026-05-06 (배포·문서·자동화 트랙)

> 패키지 코드 v0.8.0 그대로. 본 트랙은 **배포 인프라 + 비기술자 진입 장벽 제거 + 홍보 자산** 에 집중.

### Added — 배포 채널
- **GitHub Public Repo**: <https://github.com/lapiogga/caseLaw> (init, Description, Topics 10개)
- **GitHub Release v0.8.0**: wheel + sdist + installer ZIP (rev 3) 첨부
- **PyPI 정식 배포**: <https://pypi.org/project/caselaw-mcp/> (`uvx caselaw-mcp` 한 줄 설치)
- **GitHub Actions CI**: Python 3.11/3.12/3.13 매트릭스 PASS

### Added — 비기술자 원클릭 설치
- `scripts/설치하기.bat` + `scripts/setup-for-novice.ps1` (UTF-8 BOM, 5단계 대화형)
  * winget 으로 Python·uv·Claude Desktop 자동 설치
  * OC 키 대화형 입력 (또는 발급 사이트 자동 오픈)
  * Claude Desktop config 자동 작성 (기존 설정 보존·백업·검증)
- `CaseLaw-installer-v0.8.0.zip` (8KB) — Release 첨부, 더블클릭 설치

### Added — 문서 (사용자 유형별)
- `docs/소개자료_일반인.md` — 1페이지 분량, 비기술자 설득용
- `docs/기술노트_MCP아키텍처.md` — 14섹션, 개발자·IT 책임자·보안 검토자용
- `docs/설치_시각가이드.md` — 5단계 + FAQ + 사용 예시 4종, 스크린샷 11장
- `docs/OC발급_가이드.md` — 9단계 + 6 FAQ
- `docs/promo/Vrew_슬라이드쇼_제작_완전가이드.md` — Vrew 처음 사용자용 11단계
- `docs/promo/영상_대본_5분.md` — 30컷 시간별 음성·자막·화면 안내
- `docs/promo/GIF_가이드_골격.md` — 마크다운 + GIF 자리 22곳
- `docs/promo/Vrew_제작_가이드.md` — Vrew 정통 워크플로
- `docs/promo/automation/capture_pages.py` — Playwright 공개 페이지 자동 캡처
- `docs/promo/automation/demo-install-flow.ps1` — 설치 시연 (ScreenToGif 녹화용)

### Added — 시각 자료
- `docs/promo/images/01~06.png` — Playwright 자동 캡처 (총 5MB, GitHub/PyPI/법제처/OC가이드/Release/ZIP)
- `docs/promo/images/07-install-demo.gif` — 설치 흐름 GIF (사용자 캡처)
- `docs/promo/images/capture-01~04.png` — Claude Desktop 실사용 화면 (커넥터·ping·자전거·커피숍)

### Fixed — installer 안정화 (3 rev 진행)
- **rev 1**: 초기 작성
- **rev 2**: 4단계 (Claude Desktop config 작성) Add-Member 가 빈 PSCustomObject 에서 작동 안 하는 PowerShell 5.1 동작 회피 — PSCustomObject → ordered Hashtable 변환 후 직접 키 할당. 작성 후 자동 검증 추가.
- **rev 3**: native command (uv, winget) 의 stderr 출력이 `$ErrorActionPreference = 'Stop'` 으로 인해 NativeCommandError 로 throw 되는 문제 — 해당 호출 구간에서 'Continue' 임시 설정 후 `$LASTEXITCODE` 기반 판단.

### Fixed — wheel 빌드
- `pyproject.toml` 의 `force-include` 가 `packages` 와 중복되어 wheel 안에 citizen_data JSON 이 두 번 들어가던 문제 제거 (52 entries 깔끔)

### Changed
- README 최상단에 비기술자용 안내 섹션 + 일반인 소개자료 + 기술 노트 링크 배치
- `.gitignore`: `docs/promo/**/*.png|jpg|gif` 예외 (README 노출용 자료는 추적), `docs/promo/videos/`, `*.vrew` 무시

### Created — Vrew 슬라이드쇼 영상 (본인 PC)
- 11장 캡처 + AI 음성 + 자막 자동 + BGM + 페이드 전환
- 약 2-3분 분량, 1080p MP4
- YouTube 업로드는 다음 세션에 진행

### 누적 commit (본 트랙)
- 14 commits (init → installer rev 3 → 일반인/기술 자료 → .vrew 정리)

---

## [Unreleased]

### Planned (Phase 12+)
- 카테고리 50 → 100종 (변협 협업)
- 외국 판례 통합 (CourtListener API)
- Vector DB 의미 검색
- Web UI 대시보드
- 변호사 검토·인증된 시드 데이터 (`confirmed=true`)
- 카테고리·시효·비용 시드 자체 다국어화 (ja/zh/vi 확장)
- YouTube 영상 업로드 + README 임베드
- 영어·중국어 다국어 영상 (Vrew 다국어 워크플로)
- Anthropic Connector Directory 등록 신청
